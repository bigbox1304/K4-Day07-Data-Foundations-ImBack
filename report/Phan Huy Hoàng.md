# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** [Phan Huy Hoàng]
**Nhóm:** [I-M BACK]
**Ngày:** 03/08/2026

> **Trạng thái:** Phần lập trình cá nhân đã hoàn thành và vượt qua 42/42 bài test. Các số liệu ở Phần 4–5 là kết quả chạy thử có kiểm soát trên dữ liệu khởi động và mock embedder; cần chạy lại bằng local embedder trên bộ 5–10 tài liệu cùng 5 câu hỏi chính thức của nhóm trước khi nộp.

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
platform win32 -- Python 3.13.3, pytest-9.1.1
collected 42 items
tests/test_solution.py .......................................... [100%]
============================= 42 passed in 0.12s =============================
```

**Số lượng bài test vượt qua:** 42 / 42.

**Lưu ý môi trường:** Lab quy định Python 3.11 nhưng máy kiểm thử hiện chỉ tìm thấy Python 3.13.3. Cần chạy xác nhận lại trên Python 3.11 trước khi nộp chính thức; lần chạy hiện tại không có lỗi.

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

Tôi dự đoán trước theo ý nghĩa của câu. Do máy chưa có `sentence-transformers`, cột “Điểm thực tế” dưới đây dùng `_mock_embed` 64 chiều của lab và ngưỡng minh họa `0,20`; mock chỉ kiểm tra luồng tính toán, không đo ngữ nghĩa.

| Cặp | Câu A | Câu B | Dự đoán | Điểm mock thực tế | Đúng theo ngưỡng tạm? |
|------|-------|-------|---------|-------------------|----------------------|
| 1 | Người mua cần gửi yêu cầu đổi trả khi hàng bị lỗi. | Khách hàng yêu cầu trả lại sản phẩm bị lỗi. | Cao | 0,095772 | Không |
| 2 | Người bán phải cung cấp mô tả sản phẩm chính xác. | Thông tin giá và tình trạng hàng phải đúng. | Cao | -0,030965 | Không |
| 3 | Sản phẩm bị cấm không được đăng bán. | Người bán có thể đăng mọi loại hàng hóa. | Cao về chủ đề, đối lập về lập trường | 0,201121 | Đúng về độ gần chủ đề |
| 4 | Người mua gửi bằng chứng khi hàng không đúng mô tả. | Trời hôm nay có nhiều mây và có thể mưa. | Thấp | -0,067187 | Đúng |
| 5 | Người bán phản hồi yêu cầu đổi trả theo quy trình. | Người bán chịu trách nhiệm xử lý yêu cầu hoàn hàng. | Cao | 0,040765 | Không |

**Kết quả bất ngờ nhất và phản ngẫm:**

Cặp 5 gần nghĩa nhưng điểm mock chỉ 0,040765, trong khi cặp 3 chứa hai phát biểu đối lập lại cao nhất. Điều này không phản ánh embedding ngữ nghĩa mà cho thấy mock vector gần ngẫu nhiên theo toàn chuỗi; vì thế không được dùng kết quả này để kết luận chất lượng chunking hoặc khả năng hiểu tiếng Việt. Một embedder thật cũng có thể cho cặp 3 điểm cao vì similarity đo độ gần chủ đề, không tự động kiểm tra quan hệ đúng/sai hay phủ định.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

### Kết quả chạy thử — chưa phải benchmark chính thức của nhóm

Thiết lập tạm: 2 tài liệu mẫu trong `data/k4_ecommerce`, `SentenceChunker(max_sentences_per_chunk=2)`, `_mock_embed`, `top_k=3`; câu 5 lọc `metadata_filter={"customer_role": "seller"}`. Bộ dữ liệu tự ghi rõ chỉ là template `example.com`, chưa đủ yêu cầu 5–10 nguồn công khai, còn `REPORT_NHOM.md` chưa có 5 câu hỏi thống nhất.

| # | Câu hỏi ứng viên | Top-1 chunk truy xuất được (tóm tắt) | Score | Top-3 có chunk trả lời đúng? | Câu trả lời trích xuất từ Top-1 (tóm tắt) |
|---|------------------|--------------------------------------|-------|----------------------------|------------------------------------------|
| 1 | Người mua cần làm gì khi hàng bị lỗi hoặc không đúng mô tả? | Người bán phản hồi yêu cầu đổi trả theo quy trình | 0,162018 | Không | Chỉ nêu trách nhiệm phản hồi của người bán, thiếu yêu cầu/bằng chứng của người mua |
| 2 | Ai chịu trách nhiệm cung cấp giá, mô tả và tình trạng hàng chính xác? | Sản phẩm hạn chế hoặc cấm không được đăng bán | 0,201998 | Không | Không trả lời đúng chủ thể chịu trách nhiệm |
| 3 | Sản phẩm bị hạn chế hoặc bị cấm có được đăng bán không? | Hàng hạn chế/cấm không được đăng bán | 0,037669 | Có, ở Top-1 | Không được đăng bán |
| 4 | Người bán phải làm gì khi nhận yêu cầu đổi trả? | Người bán phản hồi theo quy trình của sàn | 0,127936 | Có, ở Top-1 | Phản hồi theo quy trình của sàn |
| 5 | Quy định đăng sản phẩm nào áp dụng cho người bán? | Hàng hạn chế/cấm không được đăng bán | 0,241965 | Có, ở Top-1 | Không đăng sản phẩm bị hạn chế hoặc bị cấm |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 3 / 5 trong lần chạy mock tạm thời.

**Nhận xét cá nhân từ lần chạy thử:**

Metadata filter ở câu 5 loại toàn bộ chunk dành cho người mua và giúp giới hạn đúng tài liệu người bán. Hai thất bại đầu cho thấy mock embedding không xếp hạng theo nghĩa; ngoài ra câu template/hướng dẫn còn nằm trong body và trở thành chunk nhiễu, nên khi chuẩn bị corpus thật cần loại phần chú thích template trước khi ingest.

**Điều hay nhất học được từ thành viên/nhóm khác:** [Cần bổ sung sau buổi demo; chưa có dữ liệu để ghi trung thực.]

**Việc bắt buộc hoàn tất trước khi nộp:**

1. Nhóm bổ sung 5–10 tài liệu có nguồn thật và metadata bắt buộc.
2. Chốt đúng 5 benchmark queries và gold answers trong `REPORT_NHOM.md`.
3. Cài local embedder, đặt `EMBEDDING_PROVIDER=local`, chạy lại bảng trên cùng câu hỏi của nhóm.
4. Thay kết quả tạm, ghi câu trả lời agent thực tế và bổ sung bài học từ buổi demo.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá hiện tại |
|----------|---------------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (kết quả mock, chờ local) | 2 / 5 |
| Kết quả truy xuất (kết quả tạm, chưa có benchmark nhóm) | 0 / 10 |
| **Tổng phần cá nhân đã có bằng chứng** | **47 / 60** |

> Sau khi nhóm cung cấp corpus và benchmark chính thức, hai phần cuối có thể được hoàn thiện và tự đánh giá lại; không nên tự chấm tối đa dựa trên dữ liệu template và mock embedder.
