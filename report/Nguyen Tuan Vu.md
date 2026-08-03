# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Tuấn Vũ
**Nhóm:** IMBACK
**Ngày:** 03/08/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> *Viết 1-2 câu:*  
> Độ tương tự cosine cao nghĩa là hai vector có hướng gần nhau, tức là chúng biểu diễn cùng một ý nghĩa/ngữ nghĩa chứ không chỉ cùng từ khóa. Về mặt hình học, góc giữa hai vector nhỏ, nên giá trị cosine gần 1.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Tôi muốn đổi trả đơn hàng đã nhận."
- Câu B: "Mình cần hoàn lại sản phẩm đã đặt và nhận được."
- Tại sao tương đồng: Cả hai câu đều nói về cùng một hành động đổi trả/hoàn hàng, dù cách diễn đạt khác nhau.

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Tôi muốn đổi trả đơn hàng đã nhận."
- Câu B: "Hôm nay thời tiết rất đẹp."
- Tại sao khác: Hai câu không cùng chủ đề và hướng ý nghĩa hoàn toàn khác nhau, nên vector của chúng gần như không có tương đồng về ngữ nghĩa.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> *Viết 1-2 câu:*  
> Cosine similarity tập trung vào hướng của vector, nghĩa là đo mức độ cùng ý nghĩa hơn là đo độ lớn tuyệt đối của vector. Với embeddings văn bản, độ rộng/độ lớn của vector thường không quan trọng bằng việc hai vector có cùng hướng và biểu thị cùng chủ đề hay không.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:*  
> Bước dịch chuyển (step) = `chunk_size - overlap = 500 - 50 = 450`.  
> Số chunk được tạo bằng cách bắt đầu từ vị trí 0, 450, 900, ... cho đến khi đoạn cuối cùng còn lại trong tài liệu. Ta có số bước là:  
> `ceil((10000 - 1) / 450) + 1 = ceil(9999 / 450) + 1 = 23` chunk.  
> *Đáp án:* 23 chunks.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> *Viết 1-2 câu:*  
> Khi overlap tăng lên 100, bước dịch chuyển giảm còn `500 - 100 = 400`, nên số chunk tăng lên thành 25 chunk. Độ chồng chéo lớn hơn giúp giữ ngữ cảnh liên tục giữa các chunk, giảm mất thông tin ở ranh giới chia đoạn, nhưng đồng thời làm tăng số chunk và độ dư thừa.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> *Viết 2-3 câu: dùng biểu thức chính quy (regex) gì để phát hiện câu? Xử lý trường hợp ngoại lệ (edge case) nào?*  
> Tôi tiếp cận bằng cách tách văn bản theo các dấu kết thúc câu như `.`, `!`, `?` và khoảng trắng theo sau nó, ví dụ dùng regex kiểu `(?<=[.!?])\s+` hoặc tương tự để nhận biết ranh giới câu. Sau khi tách xong, tôi gom tối đa `max_sentences_per_chunk` câu vào một chunk và làm sạch khoảng trắng thừa; tình huống đặc biệt là văn bản thiếu dấu câu, hoặc một câu dài quá nhiều khoảng trắng/dòng mới, cần tránh tạo chunk rỗng hoặc chunk chỉ có một ký tự trống.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> *Viết 2-3 câu: thuật toán hoạt động thế nào? Base case (trường hợp cơ sở) là gì?*  
> Thuật toán đi theo kiểu đệ quy: thử cắt ở dấu phân cách ưu tiên cao hơn như đoạn văn, xuống dòng, dấu chấm, rồi đến dấu cách, và cứ lặp lại với tập phân cách còn lại cho đến khi chunk đạt kích thước an toàn. Base case là khi độ dài chunk hiện tại nhỏ hơn hoặc bằng `chunk_size`, hoặc khi không còn dấu phân cách nào để tách nữa thì trả về chunk hiện tại để tránh vòng lặp vô hạn.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> *Viết 2-3 câu: lưu trữ thế nào? Tính độ tương tự ra sao?*  
> `add_documents` sẽ lấy `Document.content`, tạo embedding bằng `embedding_fn`, đồng thời đóng gói thông tin `doc_id`, `content`, `metadata`, và vector vào một bản ghi chuẩn hóa để lưu trong `self._store` hoặc collection Chroma nếu có. `search` thì embed query, so sánh với toàn bộ vector đã lưu bằng độ tương tự cosine (trong trường hợp vector đã được chuẩn hóa, có thể xem như dot product), rồi trả về top-k chunk có điểm tương đồng cao nhất.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> *Viết 2-3 câu: lọc (filter) trước hay sau? Xóa bằng cách nào?*  
> Hướng tiếp cận hợp lý nhất là lọc trước: đầu tiên chọn những bản ghi thỏa mãn `metadata_filter`, sau đó mới chạy tìm kiếm tương đồng trên tập đã giảm phạm vi. `delete_document` sẽ quét toàn bộ store và xóa mọi chunk có `metadata['doc_id']` trùng với `doc_id` được yêu cầu, trả về `True` nếu có ít nhất một chunk bị xóa và `False` nếu không tìm thấy.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> *Viết 2-3 câu: cấu trúc prompt? Cách đưa ngữ cảnh (inject context) vào thế nào?*  
> Tôi sẽ gọi `store.search()` để lấy top-k chunk liên quan nhất, sau đó xây dựng prompt theo cấu trúc: “Bạn là trợ lý trả lời dựa trên ngữ cảnh dưới đây” + các chunk context đã được truy xuất + câu hỏi của người dùng. Cách inject context là nối các chunk vào phần “Context” trong prompt, để LLM tham khảo các thông tin đã được retrieval để trả lời bằng chữ của chính nó, không phải đoán mơ hồ.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
# Dán kết quả (output) của: pytest tests/ -v
```
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED                                                     [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED                                                    [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED                                               [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED                                           [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED                                      [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED                                          [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED                                                [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED                                          [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED                       [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED                                     [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED                                    [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED                        [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED                                   [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED                            [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED                  [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED                      [100%]

========================================================= 42 passed in 0.10s =========================================================
PS C:\Users\HP Z Book G7\Desktop\New folder\K4-Day07-Data-Foundations-ImBack> 
**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Tôi muốn đổi trả đơn hàng đã nhận. | Mình cần hoàn lại sản phẩm đã đặt và nhận được. | cao | -0.163402 | Sai |
| 2 | Tôi muốn đổi trả đơn hàng đã nhận. | Hôm nay thời tiết rất đẹp. | thấp | -0.001671 | Đúng |
| 3 | Tôi cần thay đổi địa chỉ giao hàng. | Tôi muốn cập nhật nơi nhận hàng. | cao | -0.183234 | Sai |
| 4 | Tôi cần kiểm tra trạng thái đơn hàng. | Hãy giúp tôi hủy đơn hàng. | thấp | -0.059404 | Đúng |
| 5 | Sản phẩm bị lỗi. | Mặt hàng không đúng mô tả. | cao | -0.251080 | Sai |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> *Viết 2-3 câu:*  
> Cặp 1 và cặp 3 là kết quả bất ngờ nhất vì hai câu cùng chủ đề và gần nghĩa nhưng điểm cosine thực tế lại ở mức âm và khá thấp. Điều này cho thấy embeddings trong lớp mock không phản ánh ý nghĩa ngôn ngữ theo cách “ngoại diện” mà chỉ tạo ra các vector xác định bằng hàm băm/seed, nên có thể tách hướng vector của câu theo cách không thể biểu diễn đúng ngữ nghĩa thực tế.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Sau khi đơn hàng Shopee được giao thành công, người mua có bao lâu để yêu cầu trả hàng hoặc hoàn tiền, kể cả với thực phẩm tươi sống và đông lạnh? | Quy định 15 ngày và ngoại lệ 24 giờ cho thực phẩm tươi sống/đông lạnh | 0,811260 | Có | Thông thường 15 ngày; riêng thực phẩm tươi sống và đông lạnh là 24 giờ |
| 2 | Người bán Shopee có được đăng mỹ phẩm đã qua sử dụng hoặc mỹ phẩm handmade chưa có giấy công bố và chứng từ an toàn không? | Mở đầu danh sách sản phẩm cấm/hạn chế | 0,680549 | Có | Không được đăng mỹ phẩm đã qua sử dụng hoặc mỹ phẩm handmade thiếu giấy tờ an toàn |
| 3 | Tiki có trực tiếp lưu trữ thông tin thẻ thanh toán của khách hàng không, và bên nào chịu trách nhiệm lưu trữ bảo mật? | Tiki chỉ giữ token mã hóa, đối tác cổng thanh toán giữ thông tin thẻ | 0,811719 | Có | Tiki không trực tiếp giữ thông tin thẻ; đối tác cổng thanh toán bảo mật |
| 4 | Khi nhận hàng Tiki, khách hàng được kiểm tra đến mức nào và có được mở seal hoặc sử dụng thử sản phẩm không? | Hướng dẫn ký biên bản đồng kiểm | 0,740177 | Có | Được mở thùng nhưng không được mở seal riêng, không được cắm điện hoặc sử dụng thử |
| 5 | Tiki lưu trữ thông tin cá nhân của khách hàng trong bao lâu? | Phần giới thiệu chính sách quyền riêng tư Tiki | 0,700682 | Có | Lưu đến khi khách hàng yêu cầu hoặc tự thực hiện hủy bỏ và dữ liệu được bảo mật trên máy chủ Tiki |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 5 / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Qua demo, tôi nhận ra rằng cùng một bộ tài liệu nhưng chiến lược chunking khác nhau có thể thay đổi vị trí của bằng chứng đúng trong top-k, đặc biệt với các câu hỏi cần rất cụ thể. Việc thêm metadata và hướng dẫn rõ ràng cho hệ thống tìm kiếm giúp giảm nhiễu và nâng độ tin cậy của câu trả lời, dù chunking vẫn là yếu tố quyết định cho câu hỏi dài hoặc cần sự chính xác về điều khoản.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 10 / 10 |
| **Tổng phần cá nhân** | **60 / 60** |
