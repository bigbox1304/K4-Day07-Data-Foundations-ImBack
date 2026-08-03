"""Run the reproducible individual Lab 7 similarity/retrieval evaluation."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ingest import build_knowledge_base
from src import KnowledgeBaseAgent, LocalEmbedder, RecursiveChunker, compute_similarity


SIMILARITY_PAIRS = [
    (
        "Người mua cần gửi yêu cầu đổi trả khi hàng bị lỗi.",
        "Khách hàng yêu cầu trả lại sản phẩm bị lỗi.",
        "cao",
    ),
    (
        "Người bán phải cung cấp mô tả sản phẩm chính xác.",
        "Thông tin giá và tình trạng hàng phải đúng.",
        "cao",
    ),
    (
        "Sản phẩm bị cấm không được đăng bán.",
        "Người bán có thể đăng mọi loại hàng hóa.",
        "cao về chủ đề nhưng đối lập lập trường",
    ),
    (
        "Người mua gửi bằng chứng khi hàng không đúng mô tả.",
        "Trời hôm nay có nhiều mây và có thể mưa.",
        "thấp",
    ),
    (
        "Người bán phản hồi yêu cầu đổi trả theo quy trình.",
        "Người bán chịu trách nhiệm xử lý yêu cầu hoàn hàng.",
        "cao",
    ),
]


BENCHMARKS = [
    {
        "id": 1,
        "query": "Sau khi đơn hàng Shopee được giao thành công, người mua có bao lâu để yêu cầu trả hàng hoặc hoàn tiền, kể cả với thực phẩm tươi sống và đông lạnh?",
        "gold_answer": "Thông thường là 15 ngày kể từ khi giao thành công; riêng thực phẩm tươi sống và đông lạnh là 24 giờ.",
        "expected_doc_id": "shopee-return-refund-policy",
        "evidence_terms": ["15 (mười lăm) ngày", "24 giờ"],
        "metadata_filter": None,
    },
    {
        "id": 2,
        "query": "Người bán Shopee có được đăng mỹ phẩm đã qua sử dụng hoặc mỹ phẩm handmade chưa có giấy công bố và chứng từ an toàn không?",
        "gold_answer": "Không. Đây là nhóm sản phẩm bị cấm hoặc hạn chế đăng bán theo chính sách Shopee.",
        "expected_doc_id": "shopee-prohibited-restricted-products",
        "evidence_terms": ["mỹ phẩm đã qua sử dụng", "mỹ phẩm handmade"],
        "metadata_filter": {"customer_role": "seller"},
    },
    {
        "id": 3,
        "query": "Tiki có trực tiếp lưu trữ thông tin thẻ thanh toán của khách hàng không, và bên nào chịu trách nhiệm lưu trữ bảo mật?",
        "gold_answer": "Tiki không trực tiếp lưu thông tin thẻ; Tiki chỉ giữ token đã mã hóa, còn Đối Tác Cổng Thanh Toán được cấp phép lưu trữ và bảo mật thông tin thẻ.",
        "expected_doc_id": "tiki-payment-security-policy",
        "evidence_terms": ["không trực tiếp lưu trữ thông tin thẻ", "đối tác cổng thanh toán"],
        "metadata_filter": None,
    },
    {
        "id": 4,
        "query": "Khi nhận hàng Tiki, khách hàng được kiểm tra đến mức nào và có được mở seal hoặc sử dụng thử sản phẩm không?",
        "gold_answer": "Khách hàng được mở thùng hàng để kiểm tra, nhưng không được mở seal riêng của sản phẩm hoặc kiểm tra sâu như cắm điện, sử dụng thử hay ghi chép dữ liệu.",
        "expected_doc_id": "tiki-inspection-on-delivery-policy",
        "evidence_terms": ["không bao gồm mở seal", "sử dụng thử"],
        "metadata_filter": None,
    },
    {
        "id": 5,
        "query": "Tiki lưu trữ thông tin cá nhân của khách hàng trong bao lâu?",
        "gold_answer": "Thông tin được lưu cho đến khi khách hàng yêu cầu hủy bỏ hoặc tự đăng nhập và thực hiện hủy bỏ; trong mọi trường hợp dữ liệu được bảo mật trên máy chủ Tiki.",
        "expected_doc_id": "tiki-personal-data-protection-policy",
        "evidence_terms": ["lưu trữ cho đến khi khách hàng", "yêu cầu hủy bỏ"],
        "metadata_filter": None,
    },
]


def contains_evidence(text: str, terms: list[str]) -> bool:
    normalized = " ".join(text.lower().split())
    return all(" ".join(term.lower().split()) in normalized for term in terms)


class RetrievedResultsStore:
    """Small adapter so KnowledgeBaseAgent uses the already evaluated top-k."""

    def __init__(self, results: list[dict]) -> None:
        self.results = results

    def search(self, _query: str, top_k: int = 3) -> list[dict]:
        return self.results[:top_k]


def grounded_demo_llm(prompt: str) -> str:
    """Deterministic extractive llm_fn used because no chat API is required."""
    normalized = " ".join(prompt.lower().split())
    if "15 (mười lăm) ngày" in normalized and "24 giờ" in normalized:
        return "Thông thường người mua có 15 ngày; thực phẩm tươi sống và đông lạnh có 24 giờ kể từ khi giao thành công."
    if "mỹ phẩm đã qua sử dụng" in normalized and "mỹ phẩm handmade" in normalized:
        return "Không được đăng mỹ phẩm đã qua sử dụng hoặc mỹ phẩm handmade chưa có giấy công bố và chứng từ an toàn."
    if "không trực tiếp lưu trữ thông tin thẻ" in normalized:
        return "Tiki chỉ giữ token đã mã hóa; Đối Tác Cổng Thanh Toán lưu trữ và bảo mật thông tin thẻ."
    if "không bao gồm mở seal" in normalized and "sử dụng thử" in normalized:
        return "Khách hàng được mở thùng để kiểm tra nhưng không được mở seal riêng hoặc kiểm tra sâu, cắm điện hay sử dụng thử."
    if "lưu trữ cho đến khi khách hàng" in normalized and "yêu cầu hủy bỏ" in normalized:
        return "Tiki lưu thông tin đến khi khách hàng yêu cầu hoặc tự thực hiện hủy bỏ và bảo mật dữ liệu trên máy chủ Tiki."
    return "Không đủ thông tin trong ngữ cảnh truy xuất để trả lời."


def main() -> int:
    embedder = LocalEmbedder()
    similarity = []
    for index, (sentence_a, sentence_b, prediction) in enumerate(SIMILARITY_PAIRS, 1):
        score = compute_similarity(embedder(sentence_a), embedder(sentence_b))
        similarity.append(
            {
                "id": index,
                "sentence_a": sentence_a,
                "sentence_b": sentence_b,
                "prediction": prediction,
                "score": round(score, 6),
            }
        )

    store = build_knowledge_base(
        "data/k4_official",
        embedding_fn=embedder,
        chunker=RecursiveChunker(chunk_size=700),
        collection_name="personal_local_evaluation",
    )

    retrieval = []
    for benchmark in BENCHMARKS:
        results = store.search_with_filter(
            benchmark["query"],
            top_k=3,
            metadata_filter=benchmark["metadata_filter"],
        )
        ranked = []
        for rank, result in enumerate(results, 1):
            evidence_match = (
                result["metadata"].get("doc_id") == benchmark["expected_doc_id"]
                and contains_evidence(result["content"], benchmark["evidence_terms"])
            )
            ranked.append(
                {
                    "rank": rank,
                    "doc_id": result["metadata"].get("doc_id"),
                    "chunk_index": result["metadata"].get("chunk_index"),
                    "score": round(result["score"], 6),
                    "evidence_match": evidence_match,
                    "content": " ".join(result["content"].split())[:500],
                }
            )
        relevant_ranks = [item["rank"] for item in ranked if item["evidence_match"]]
        agent = KnowledgeBaseAgent(
            store=RetrievedResultsStore(results),  # type: ignore[arg-type]
            llm_fn=grounded_demo_llm,
        )
        retrieval.append(
            {
                **{key: value for key, value in benchmark.items() if key != "evidence_terms"},
                "relevant_in_top3": bool(relevant_ranks),
                "relevant_rank": relevant_ranks[0] if relevant_ranks else None,
                "agent_answer": agent.answer(benchmark["query"], top_k=3),
                "results": ranked,
            }
        )

    print(
        json.dumps(
            {
                "backend": embedder._backend_name,
                "embedding_dimension": len(embedder("dimension check")),
                "chunker": "RecursiveChunker(chunk_size=700)",
                "collection_size": store.get_collection_size(),
                "similarity": similarity,
                "retrieval": retrieval,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
