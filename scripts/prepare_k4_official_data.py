"""Import converted official K4 documents into an ingest-ready directory.

The script preserves the source text, removes conversion/UI markup from Shopee
pages, and prepends the flat YAML metadata required by ``ingest.py``.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


DOCUMENTS = [
    {
        "filename": "01_shopee_chinh_sach_tra_hang_hoan_tien.md",
        "doc_id": "shopee-return-refund-policy",
        "title": "Chính sách trả hàng và hoàn tiền Shopee",
        "customer_role": "both",
        "category": "returns_refunds",
        "source_url": "https://help.shopee.vn/portal/4/article/77251?seo=1",
        "document_version": "effective-2026-03-11",
        "source_type": "official_webpage",
        "extraction_method": "html-to-markdown",
        "parser_confidence": "medium",
        "shopee_page": True,
    },
    {
        "filename": "02_shopee_chinh_sach_bao_mat.md",
        "doc_id": "shopee-privacy-policy",
        "title": "Chính sách bảo mật Shopee",
        "customer_role": "both",
        "category": "privacy",
        "source_url": "https://help.shopee.vn/portal/4/article/77244?previousPage=other+articles",
        "document_version": "updated-2026-06-04",
        "source_type": "official_webpage",
        "extraction_method": "html-to-markdown",
        "parser_confidence": "medium",
        "shopee_page": True,
    },
    {
        "filename": "03_shopee_dieu_khoan_dich_vu.md",
        "doc_id": "shopee-terms-of-service",
        "title": "Điều khoản dịch vụ Shopee",
        "customer_role": "both",
        "category": "terms_of_service",
        "source_url": "https://help.shopee.vn/portal/4/article/77243",
        "document_version": "snapshot-2026-08-03",
        "source_type": "official_webpage",
        "extraction_method": "html-to-markdown",
        "parser_confidence": "medium",
        "shopee_page": True,
    },
    {
        "filename": "04_shopee_chinh_sach_cam_han_che_san_pham.md",
        "doc_id": "shopee-prohibited-restricted-products",
        "title": "Chính sách cấm và hạn chế sản phẩm Shopee",
        "customer_role": "seller",
        "category": "seller_listing",
        "source_url": "https://help.shopee.vn/portal/4/article/77247",
        "document_version": "snapshot-2026-08-03",
        "source_type": "official_webpage",
        "extraction_method": "html-to-markdown",
        "parser_confidence": "medium",
        "shopee_page": True,
    },
    {
        "filename": "05_shopee_huong_dan_doi_phuong_thuc_thanh_toan.md",
        "doc_id": "shopee-change-payment-method-guide",
        "title": "Hướng dẫn đổi phương thức thanh toán Shopee",
        "customer_role": "buyer",
        "category": "payment",
        "source_url": "https://help.shopee.vn/portal/4/article/79128",
        "document_version": "snapshot-2026-08-03",
        "source_type": "official_webpage",
        "extraction_method": "html-to-markdown",
        "parser_confidence": "medium",
        "shopee_page": True,
    },
    {
        "filename": "06_tiki_chinh_sach_bao_mat_thanh_toan.md",
        "doc_id": "tiki-payment-security-policy",
        "title": "Chính sách bảo mật thanh toán Tiki",
        "customer_role": "buyer",
        "category": "payment_security",
        "source_url": "https://tiki.vn/_mobile-next/static/docs/TIKI_Chinh_sach_bao_mat_thanh_toan.pdf",
        "document_version": "snapshot-2026-08-03",
        "source_type": "official_pdf",
        "extraction_method": "pdf-to-markdown",
        "parser_confidence": "high",
        "shopee_page": False,
    },
    {
        "filename": "07_tiki_chinh_sach_bao_ve_thong_tin_ca_nhan.md",
        "doc_id": "tiki-personal-data-protection-policy",
        "title": "Chính sách bảo vệ thông tin cá nhân Tiki",
        "customer_role": "both",
        "category": "privacy",
        "source_url": "https://tiki.vn/_desktop-next/static/docs/TIKI_Chinh_sach_bao_ve_thong_tin_ca_nhan_nguoi_tieu_dung_VN_23082024.pdf",
        "document_version": "2024-08-23",
        "source_type": "official_pdf",
        "extraction_method": "pdf-to-markdown",
        "parser_confidence": "high",
        "shopee_page": False,
    },
    {
        "filename": "08_tiki_chinh_sach_kiem_hang.md",
        "doc_id": "tiki-inspection-on-delivery-policy",
        "title": "Chính sách kiểm hàng Tiki",
        "customer_role": "buyer",
        "category": "delivery",
        "source_url": "https://tiki.vn/_desktop-next/static/docs/TIKI_Chinh%20sach%20kiem%20hang.pdf",
        "document_version": "snapshot-2026-08-03",
        "source_type": "official_pdf",
        "extraction_method": "pdf-to-markdown",
        "parser_confidence": "high",
        "shopee_page": False,
    },
    {
        "filename": "09_moit_quy_dinh_thuong_mai_dien_tu.md",
        "doc_id": "moit-ecommerce-consolidated-regulation-2018",
        "title": "Văn bản hợp nhất quy định về thương mại điện tử",
        "customer_role": "both",
        "category": "ecommerce_regulation",
        "source_url": "https://moit.gov.vn/upload/2005517/20210623/_VB_1519379363763_VB_VBHN-BCT_2018_11.pdf",
        "document_version": "11/VBHN-BCT-2018",
        "source_type": "official_pdf",
        "extraction_method": "pdf-ocr-to-markdown",
        "parser_confidence": "low",
        "shopee_page": False,
    },
]


def extract_shopee_article(text: str) -> str:
    """Keep only the official article body from converted Help Centre pages."""
    lines = text.splitlines()
    try:
        start = next(index for index, line in enumerate(lines) if "#hcArticleTitle" in line)
        rate_start = next(
            index
            for index in range(start + 1, len(lines))
            if "rate_wrap___" in lines[index]
        )
    except StopIteration as exc:
        raise ValueError("could not locate Shopee article boundaries") from exc

    article = lines[start:rate_start]
    while article and (not article[-1].strip() or article[-1].lstrip().startswith(":::")):
        article.pop()
    return "\n".join(article)


def clean_converted_markdown(text: str) -> str:
    """Remove Pandoc UI containers and presentational span attributes."""
    text = re.sub(r"(?m)^:::+(?:\s+.*)?$", "", text)

    # Pandoc emits source spans as [text]{style="..."}; preserve text only.
    span_pattern = re.compile(r"\[([^\[\]]*?)\]\{[^{}\n]*\}", re.DOTALL)
    previous = None
    while text != previous:
        previous = text
        text = span_pattern.sub(r"\1", text)

    text = re.sub(r"\{#hcArticleTitle[^}]*\}", "", text)
    text = re.sub(r"(?m)^[ \t]+$", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() + "\n"


def make_front_matter(config: dict[str, object]) -> str:
    fields = [
        "doc_id",
        "title",
        "customer_role",
        "category",
        "language",
        "source_url",
        "retrieved_at",
        "document_version",
        "source_type",
        "extraction_method",
        "parser_confidence",
    ]
    values = dict(config)
    values["language"] = "vi"
    values["retrieved_at"] = "2026-08-03"
    rows = ["---"]
    for field in fields:
        value = str(values[field]).replace('"', '\\"')
        rows.append(f'{field}: "{value}"')
    rows.extend(["---", ""])
    return "\n".join(rows)


def prepare(source_dir: Path, target_dir: Path) -> None:
    missing = [item["filename"] for item in DOCUMENTS if not (source_dir / str(item["filename"])).is_file()]
    if missing:
        raise FileNotFoundError(f"missing source files: {', '.join(map(str, missing))}")

    target_dir.mkdir(parents=True, exist_ok=True)
    for config in DOCUMENTS:
        filename = str(config["filename"])
        source_text = (source_dir / filename).read_text(encoding="utf-8")
        body = extract_shopee_article(source_text) if config["shopee_page"] else source_text
        body = clean_converted_markdown(body)
        output = make_front_matter(config) + body
        destination = target_dir / filename
        destination.write_text(output, encoding="utf-8", newline="\n")
        print(f"PREPARED {filename}: {len(body)} body characters")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_dir", type=Path)
    parser.add_argument("target_dir", type=Path)
    args = parser.parse_args()
    prepare(args.source_dir.resolve(), args.target_dir.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
