# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Phan Huy Hoàng
**Nhóm:** I-M BACK
**Ngày:** 03/08/2026

> **Trạng thái:** Phần lập trình và đánh giá cá nhân đã hoàn thành: 42/42 bài test, 5 cặp similarity bằng local multilingual embedder và 5/5 truy vấn có đúng bằng chứng trong top-3 trên corpus 9 tài liệu chính thức. Phần so sánh với thành viên/nhóm khác không thuộc phạm vi cập nhật của báo cáo này.

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao nghĩa là gì?**

Hai vector văn bản có cosine similarity cao khi chúng gần cùng hướng trong không gian embedding. Điều này thường cho thấy hai đoạn có nội dung hoặc ý nghĩa gần nhau, dù cách dùng từ có thể khác nhau.

**Ví dụ có độ tương tự CAO:**

- Câu A: “Người mua cần gửi yêu cầu đổi trả khi sản phẩm bị lỗi.”
- Câu B: “Khách hàng có thể yêu cầu hoàn hàng nếu sản phẩm có lỗi.”
- Tại sao tương đồng: Cả hai cùng nói về quyền yêu cầu đổi/trả đối với hàng lỗi.

**Ví dụ có độ tương tự THẤP:**

- Câu A: “Người mua cần gửi bằng chứng khi hàng không đúng mô tả.”
- Câu B: “Trời hôm nay có nhiều mây và có thể mưa.”
- Tại sao khác: Hai câu thuộc hai chủ đề và mục đích hoàn toàn khác nhau: chính sách đổi trả và thời tiết.

**Tại sao cosine similarity được ưu tiên hơn khoảng cách Euclid cho text embeddings?**

Cosine tập trung vào hướng của vector, tức mẫu ngữ nghĩa, và ít bị ảnh hưởng bởi độ lớn vector do độ dài văn bản. Khoảng cách Euclid phụ thuộc cả hướng lẫn độ lớn nên hai văn bản cùng ý nhưng khác độ dài có thể bị xem là xa nhau hơn cần thiết.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10.000 ký tự, `chunk_size=500`, `overlap=50`:**

`ceil((10.000 - 50) / (500 - 50)) = ceil(9.950 / 450) = ceil(22,11) = 23`.

**Đáp án:** 23 chunks.

**Nếu overlap tăng lên 100:**

`ceil((10.000 - 100) / (500 - 100)) = ceil(9.900 / 400) = ceil(24,75) = 25`, tức tăng từ 23 lên 25 chunks. Overlap lớn hơn giữ thêm ngữ cảnh ở ranh giới chunk, giảm nguy cơ một ý quan trọng bị cắt đôi, nhưng làm tăng dữ liệu lặp, chi phí embedding và số ứng viên cần tìm kiếm.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`:**

Tôi dùng regex `(?<=[.!?])(?:[ \t]+|\n+)` để tách sau dấu kết câu nhưng giữ dấu câu ở câu phía trước. Các câu rỗng và khoảng trắng thừa được loại bỏ; văn bản rỗng trả về danh sách rỗng, còn số câu mỗi chunk luôn được ép tối thiểu là một.

**`RecursiveChunker.chunk` / `_split`:**

Thuật toán thử separator theo thứ tự ưu tiên, ghép các mảnh nhỏ vào buffer cho đến giới hạn `chunk_size`, rồi đệ quy mảnh quá dài bằng separator tiếp theo. Base case là đoạn đã vừa kích thước; nếu hết separator hoặc gặp separator rỗng, đoạn được cắt cứng theo số ký tự để luôn kết thúc và giữ kích thước hợp lệ.

**`compute_similarity` và `ChunkingStrategyComparator`:**

Cosine similarity được tính bằng tích vô hướng chia cho tích hai độ lớn vector, có bảo vệ vector zero và kiểm tra hai vector cùng chiều. Comparator chạy cả fixed-size, sentence và recursive, sau đó trả về số chunk, độ dài trung bình và danh sách chunk để có thể phân tích cả số lượng lẫn độ mạch lạc.

### Lớp EmbeddingStore

**`add_documents` + `search`:**

Mỗi `Document` được chuẩn hóa thành bản ghi gồm ID nội bộ duy nhất, nội dung, bản sao metadata và embedding. Store giữ bản in-memory làm nguồn dữ liệu ổn định, đồng thời mirror sang ChromaDB nếu thư viện khả dụng; tìm kiếm embedding truy vấn, tính cosine với từng bản ghi, sắp xếp score giảm dần và lấy `top_k`.

**`search_with_filter` + `delete_document`:**

Metadata được lọc trước khi tính similarity để chỉ xếp hạng đúng tập ứng viên. Khi xóa, tôi tìm mọi chunk có `metadata["doc_id"]` trùng ID tài liệu, xóa chúng khỏi in-memory store và đồng bộ lệnh xóa sang ChromaDB nếu backend này đang hoạt động.

### Tác tử KnowledgeBaseAgent

**`answer`:**

Agent truy xuất `top_k` chunk rồi đánh số từng nguồn trong phần `NGỮ CẢNH`, tách riêng phần `CÂU HỎI` và gọi `llm_fn`. Prompt yêu cầu chỉ dùng ngữ cảnh và phải nói không đủ thông tin khi thiếu bằng chứng; nếu store không trả kết quả, agent chèn thông báo ngữ cảnh rỗng thay vì để mô hình tự suy đoán.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

### Kết Quả Kiểm Thử

```text
platform win32 -- Python 3.11.15, pytest-9.1.1
collected 42 items
tests/test_solution.py .......................................... [100%]
============================= 42 passed in 0.10s =============================
```

**Số lượng bài test vượt qua:** 42 / 42.

**Lưu ý môi trường:** Đã xác nhận trực tiếp bằng Python 3.11.15 theo đúng phiên bản lab yêu cầu; toàn bộ 42 bài test đều vượt qua.

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

Tôi dự đoán trước theo ý nghĩa của câu, sau đó tính điểm bằng `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (384 chiều, vector đã chuẩn hóa) và hàm `compute_similarity()` đã triển khai.

| Cặp | Câu A | Câu B | Dự đoán trước khi chạy | Điểm local thực tế | Đánh giá dự đoán |
|------|-------|-------|------------------------|--------------------|------------------|
| 1 | Người mua cần gửi yêu cầu đổi trả khi hàng bị lỗi. | Khách hàng yêu cầu trả lại sản phẩm bị lỗi. | Cao | 0,784442 | Đúng |
| 2 | Người bán phải cung cấp mô tả sản phẩm chính xác. | Thông tin giá và tình trạng hàng phải đúng. | Cao | 0,599158 | Đúng |
| 3 | Sản phẩm bị cấm không được đăng bán. | Người bán có thể đăng mọi loại hàng hóa. | Cao về chủ đề nhưng đối lập lập trường | 0,208477 | Không cao như dự đoán |
| 4 | Người mua gửi bằng chứng khi hàng không đúng mô tả. | Trời hôm nay có nhiều mây và có thể mưa. | Thấp | -0,042767 | Đúng |
| 5 | Người bán phản hồi yêu cầu đổi trả theo quy trình. | Người bán chịu trách nhiệm xử lý yêu cầu hoàn hàng. | Cao | 0,713358 | Đúng |

**Kết quả bất ngờ nhất và phản ngẫm:**

Cặp 3 bất ngờ nhất: hai câu dùng cùng chủ đề “đăng bán sản phẩm” nhưng khác nhau bởi phủ định và lập trường, nên điểm chỉ 0,208477. Kết quả cho thấy embedding đa ngữ đã nhận ra phần liên quan về chủ đề nhưng khoảng cách vẫn lớn do ý nghĩa đối lập; cosine similarity đo độ gần biểu diễn, không phải bộ kiểm tra tính đúng/sai hay quan hệ suy luận.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

### Thiết lập đánh giá cá nhân

- Corpus: 9 tài liệu chính thức trong `data/k4_official`.
- Backend: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, chạy cục bộ.
- Chunking cá nhân: `RecursiveChunker(chunk_size=700)`.
- Tổng số chunk: 535; truy xuất `top_k=3`.
- Tiêu chí relevant: kết quả phải chứa đúng `doc_id` và đủ cụm bằng chứng định trước, không chỉ cùng chủ đề.
- Câu 2 lọc trước bằng `metadata_filter={"customer_role": "seller"}`.
- `KnowledgeBaseAgent` dùng `llm_fn` extractive xác định: chỉ sinh câu trả lời khi cụm bằng chứng có trong context; đây không phải mô hình chat sinh văn bản.

### 5 câu hỏi đánh giá cá nhân và gold answers

| # | Câu hỏi đánh giá | Gold answer | Chunk chứa bằng chứng |
|---|------------------|-------------|-----------------------|
| 1 | Sau khi đơn hàng Shopee được giao thành công, người mua có bao lâu để yêu cầu trả hàng hoặc hoàn tiền, kể cả với thực phẩm tươi sống và đông lạnh? | Thông thường là 15 ngày; riêng thực phẩm tươi sống và đông lạnh là 24 giờ kể từ khi giao thành công. | `shopee-return-refund-policy`, chunk 6 |
| 2 | Người bán Shopee có được đăng mỹ phẩm đã qua sử dụng hoặc mỹ phẩm handmade chưa có giấy công bố và chứng từ an toàn không? | Không; đây là nhóm sản phẩm bị cấm/hạn chế đăng bán. | `shopee-prohibited-restricted-products`, chunk 12; lọc `seller` |
| 3 | Tiki có trực tiếp lưu trữ thông tin thẻ thanh toán của khách hàng không, và bên nào chịu trách nhiệm lưu trữ bảo mật? | Tiki chỉ giữ token đã mã hóa, không trực tiếp lưu thông tin thẻ; Đối Tác Cổng Thanh Toán được cấp phép lưu trữ và bảo mật. | `tiki-payment-security-policy`, chunk 2 |
| 4 | Khi nhận hàng Tiki, khách hàng được kiểm tra đến mức nào và có được mở seal hoặc sử dụng thử sản phẩm không? | Được mở thùng để kiểm tra nhưng không được mở seal riêng hoặc kiểm tra sâu như cắm điện, sử dụng thử, ghi dữ liệu. | `tiki-inspection-on-delivery-policy`, chunk 0 |
| 5 | Tiki lưu trữ thông tin cá nhân của khách hàng trong bao lâu? | Đến khi khách hàng yêu cầu hoặc tự thực hiện hủy bỏ; dữ liệu luôn được bảo mật trên máy chủ Tiki. | `tiki-personal-data-protection-policy`, chunk 9 |

> Đây là bộ câu hỏi và kết quả thuộc phần đánh giá cá nhân. Báo cáo này không thực hiện so sánh với chiến lược hay kết quả của thành viên khác.

### Kết quả chạy thực tế

| # | Top-1 chunk truy xuất được (tóm tắt) | Score top-1 | Vị trí chunk đúng | Relevant trong top-3? | Câu trả lời của Agent (tóm tắt) |
|---|--------------------------------------|-------------|--------------------|-------------------------|---------------------------------|
| 1 | Quy định 15 ngày và ngoại lệ thực phẩm tươi sống/đông lạnh 24 giờ | 0,811260 | Rank 1 | Có | Thông thường 15 ngày; thực phẩm tươi sống và đông lạnh 24 giờ |
| 2 | Mở đầu danh sách sản phẩm cấm/hạn chế | 0,680549 | Rank 3 | Có | Không được đăng mỹ phẩm đã dùng hoặc handmade thiếu giấy tờ an toàn |
| 3 | Tiki chỉ giữ token mã hóa, đối tác cổng thanh toán giữ thông tin thẻ | 0,811719 | Rank 1 | Có | Tiki không trực tiếp giữ thông tin thẻ; đối tác cổng thanh toán bảo mật |
| 4 | Hướng dẫn ký biên bản đồng kiểm | 0,740177 | Rank 2 | Có | Được mở thùng nhưng không mở seal, cắm điện hay sử dụng thử |
| 5 | Phần giới thiệu chính sách quyền riêng tư Tiki | 0,700682 | Rank 2 | Có | Lưu đến khi khách hàng yêu cầu/tự hủy và bảo mật trên máy chủ Tiki |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 5 / 5.

**Phân bố thứ hạng của bằng chứng đúng:** 2 câu ở rank 1, 2 câu ở rank 2 và 1 câu ở rank 3.

**Nhận xét cá nhân từ lần chạy thử:**

Local multilingual embedder xếp đúng bằng chứng ở top-1 cho câu hỏi thời hạn đổi trả và bảo mật thẻ. Các câu 2, 4 và 5 cho thấy “đúng tài liệu” chưa đồng nghĩa “đúng đoạn”: phần mở đầu cùng chủ đề có thể đứng cao hơn đoạn chứa câu trả lời cụ thể. Metadata filter ở câu 2 loại các tài liệu dành riêng cho người mua và bảo đảm toàn bộ ứng viên đến từ chính sách người bán, nhưng chunk bằng chứng vẫn chỉ đứng rank 3; có thể cải thiện bằng chunking theo đề mục/điều khoản.

**Điều hay nhất học được từ thành viên/nhóm khác:** [Cần bổ sung sau buổi demo; chưa có dữ liệu để ghi trung thực.]

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá hiện tại |
|----------|---------------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (local multilingual embeddings) | 5 / 5 |
| Kết quả truy xuất cá nhân (5/5 relevant trong top-3) | 10 / 10 |
| **Tổng phần cá nhân đã có bằng chứng** | **60 / 60** |

> Điểm tự đánh giá trên phản ánh phần kỹ thuật cá nhân. Nội dung học hỏi/so sánh với thành viên khác được giữ ngoài phạm vi theo yêu cầu và chỉ có thể bổ sung sau hoạt động nhóm thực tế.
