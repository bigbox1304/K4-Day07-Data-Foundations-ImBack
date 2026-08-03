# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Lương Sỹ Linh  
**Nhóm:** IMBACK  
**Ngày:** 03/08/2026  
**Mã nguồn cá nhân:** `src/2A202601214/`

> **Phạm vi báo cáo:** Đây là báo cáo cá nhân, tập trung vào cách tôi kiểm chứng mã nguồn, thiết kế thí nghiệm và phân tích lỗi truy xuất. Bộ tài liệu và 5 câu hỏi benchmark dùng chung được lấy từ `report/REPORT_NHOM.md`.

**Tổng điểm phần cá nhân:** 60 = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### 1.1. Độ tương tự cosine

Cosine similarity đo góc giữa hai vector, không chỉ đo khoảng cách tuyệt đối giữa hai điểm. Giá trị càng gần 1 thì hai vector càng cùng hướng; với text embedding, điều đó thường gợi ý hai câu có chủ đề hoặc ý nghĩa gần nhau.

**Ví dụ tương đồng cao**

- Câu A: “Tôi muốn đổi trả sản phẩm bị lỗi.”
- Câu B: “Tôi cần hoàn hàng vì mặt hàng không hoạt động.”

Hai câu cùng biểu đạt nhu cầu trả lại một sản phẩm có vấn đề, dù dùng các từ “đổi trả”, “hoàn hàng”, “bị lỗi” và “không hoạt động” khác nhau.

**Ví dụ tương đồng thấp**

- Câu A: “Mỹ phẩm đã qua sử dụng bị cấm đăng bán.”
- Câu B: “Hôm nay tôi muốn đổi phương thức thanh toán.”

Một câu nói về quy định đăng bán sản phẩm, câu còn lại nói về thao tác thanh toán; mục đích và chủ đề khác nhau.

**Vì sao cosine phù hợp hơn Euclidean distance?**

Độ dài câu có thể làm thay đổi độ lớn vector nhưng không nhất thiết làm thay đổi ý nghĩa. Cosine tập trung vào hướng biểu diễn, vì vậy phù hợp hơn khi so sánh câu ngắn và câu dài cùng chủ đề. Trong project, các embedding local đã được chuẩn hóa nên cosine cũng có thể được tính ổn định bằng tích vô hướng chia cho chuẩn vector.

### 1.2. Bài toán fixed-size chunking

Với tài liệu dài 10.000 ký tự, `chunk_size=500`, `overlap=50`:

```
step = chunk_size - overlap = 500 - 50 = 450
number_of_chunks = ceil((10_000 - 50) / 450) = ceil(9_950 / 450) = 23
```

Vậy có **23 chunks**.

Nếu tăng `overlap=100`:

```
step = 500 - 100 = 400
number_of_chunks = ceil((10_000 - 100) / 400) = ceil(9_900 / 400) = 25
```

Số chunk tăng từ 23 lên 25. Overlap lớn giúp một câu hoặc điều kiện ở ranh giới có cơ hội xuất hiện trong cả hai chunk, nhưng đổi lại làm tăng dữ liệu trùng lặp, số vector cần lưu và chi phí tìm kiếm.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Điểm khác trong cách tiếp cận của tôi là xem RAG như một pipeline có hai nhiệm vụ riêng:

1. **Tăng recall:** dùng embedding để đưa các chunk có khả năng liên quan vào tập ứng viên.
2. **Kiểm tra grounding:** xác nhận chunk có đúng tài liệu và chứa đủ cụm bằng chứng trước khi coi là trả lời được.

Tôi không xem score cosine cao là bằng chứng đủ mạnh. Một chunk có thể cùng chủ đề nhưng không chứa điều khoản trả lời trực tiếp. Vì vậy, trong phần đánh giá cá nhân tôi ghi cả score, thứ hạng và trạng thái `evidence_match`.

### 2.1. Các hàm chia nhỏ

#### `SentenceChunker.chunk`

Tôi dùng regex có dạng `(?<=[.!?])(?:[ \t]+|\n+)`. Look-behind giữ dấu kết câu ở phía trước, sau đó loại bỏ khoảng trắng thừa và gom tối đa `max_sentences_per_chunk` câu vào một chunk. Văn bản rỗng trả về `[]`, còn giá trị `max_sentences_per_chunk` được ép tối thiểu bằng 1 để tránh vòng lặp hoặc chunk không hợp lệ.

#### `RecursiveChunker.chunk` / `_split`

Thuật toán thử separator theo thứ tự ưu tiên: đoạn trắng kép, xuống dòng, dấu chấm, khoảng trắng và cuối cùng là chuỗi rỗng. Nếu đoạn hiện tại đã ngắn hơn hoặc bằng `chunk_size`, đó là base case và được trả về ngay. Nếu một mảnh vẫn quá dài, hàm gọi đệ quy với các separator còn lại; khi hết separator thì cắt cứng theo kích thước để luôn kết thúc.

#### Cách tôi kiểm chứng các chunker

Tôi không chọn chunker chỉ dựa vào số lượng chunk. Tôi so sánh cả:

- số chunk;
- độ dài trung bình;
- vị trí của bằng chứng trong top-3;
- khả năng giữ nguyên một điều kiện hoặc ngoại lệ trong cùng chunk.

Thử nghiệm ablation cho thấy `SentenceChunker(max_sentences_per_chunk=4)` tạo 420 chunk nhưng semantic retrieval dễ bị nhiễu bởi tài liệu pháp quy OCR. `FixedSizeChunker(chunk_size=500, overlap=75)` tạo 659 chunk và cũng không ổn định khi câu hỏi có nhiều điều kiện. Pipeline `RecursiveChunker(chunk_size=700)` tạo 535 chunk và giữ được các điều khoản dài tốt hơn trên bộ benchmark.

### 2.2. `compute_similarity` và `EmbeddingStore`

`compute_similarity` tính:

```
dot(a, b) / (norm(a) * norm(b))
```

Hàm kiểm tra vector khác chiều và trả về 0.0 nếu một trong hai vector là vector 0. Với `EmbeddingStore`, mỗi tài liệu được chuẩn hóa thành record gồm ID, nội dung, metadata và embedding. In-memory store được dùng làm nguồn dữ liệu ổn định; ChromaDB chỉ là backend mirror tùy chọn.

`search` embed query, tính cosine với các record, sắp xếp giảm dần theo score và trả về tối đa `top_k`. `search_with_filter` lọc metadata trước rồi mới tính similarity. Đây là điểm quan trọng cho câu hỏi nhắm đến người bán. `delete_document` xóa mọi chunk có `metadata["doc_id"]` tương ứng và trả về trạng thái thành công/thất bại.

### 2.3. `KnowledgeBaseAgent.answer`

Agent gọi `store.search(question, top_k)`, đánh số từng chunk trong phần `NGỮ CẢNH`, đặt câu hỏi ở phần riêng và gọi `llm_fn`. Prompt yêu cầu chỉ sử dụng context và phải nói rõ khi thiếu thông tin. Cách tách context khỏi question giúp giảm nguy cơ LLM trả lời dựa trên kiến thức ngoài cơ sở dữ liệu.

Trong đánh giá cá nhân, tôi dùng một `llm_fn` extractive xác định: chỉ trả lời khi các cụm bằng chứng bắt buộc xuất hiện trong context. Đây là bộ kiểm tra grounding cho báo cáo, không phải khẳng định rằng project đã tích hợp một chat model thật.

### 2.4. Điểm khác so với hai hướng còn lại

- So với hướng **RecursiveChunker + metadata filter** của Nguyễn Tuấn Vũ, tôi tập trung vào phép đo `evidence_match` và phân biệt “đúng tài liệu” với “đúng đoạn bằng chứng”.
- So với hướng **RecursiveChunker + LocalEmbedder** của Phan Huy Hoàng, tôi bổ sung một tầng kiểm chứng deterministic sau retrieval và thực hiện ablation trước khi chọn cấu hình cuối.
- Do đó, kết luận của tôi không dựa riêng vào việc score cao hay câu trả lời nghe hợp lý; một kết quả chỉ được xem là grounded khi xác định được đúng `doc_id` và cụm thông tin cần thiết.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Tôi chạy test trên package cá nhân bằng PowerShell:

```powershell
$env:LAB_SOLUTION_PACKAGE="src.2A202601214"
python -m pytest tests -q
```

Kết quả:

```text
..........................................                               [100%]
42 passed in 0.09s
```

**Số lượng bài test vượt qua:** **42 / 42**.

Các nhóm chức năng đã được kiểm tra gồm:

- fixed-size, sentence và recursive chunking;
- cosine similarity với vector giống nhau, trực giao, đối nhau và vector 0;
- tạo record, thêm tài liệu và tìm kiếm top-k;
- lọc metadata;
- xóa tài liệu theo `doc_id`;
- dựng câu trả lời của `KnowledgeBaseAgent`.

Môi trường local embedding dùng:

- Python 3.12.2;
- `sentence-transformers==5.6.0`;
- `torch==2.13.0`;
- model `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`;
- embedding dimension: 384.

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

Tôi dự đoán trước dựa trên ý nghĩa, sau đó chạy model local. Các cặp dưới đây khác với các cặp trong hai báo cáo mẫu.

| Cặp | Câu A | Câu B | Dự đoán trước | Điểm local | Đánh giá |
|---|---|---|---|---:|---|
| 1 | Tôi muốn đổi trả sản phẩm bị lỗi. | Tôi cần hoàn hàng vì mặt hàng không hoạt động. | Cao | 0,874655 | Đúng |
| 2 | Tiki không lưu trực tiếp số thẻ của khách hàng. | Cổng thanh toán được cấp phép bảo mật thông tin thẻ. | Trung bình đến cao | 0,785612 | Đúng |
| 3 | Người bán phải mô tả sản phẩm chính xác. | Thời hạn kiểm tra hàng của người mua là bao lâu? | Thấp | 0,781396 | Sai |
| 4 | Khách hàng được mở thùng để kiểm tra hàng. | Khách hàng được cắm điện dùng thử sản phẩm. | Trung bình về chủ đề, khác về quy định | 0,922926 | Không phân biệt được tốt |
| 5 | Mỹ phẩm đã qua sử dụng bị cấm đăng bán. | Hôm nay tôi muốn đổi phương thức thanh toán. | Thấp | 0,827265 | Sai |

**Nhận xét:**

Cặp 4 cho điểm rất cao dù hai câu mô tả hai hành động trái ngược về mặt chính sách: được mở thùng không đồng nghĩa được cắm điện dùng thử. Cặp 5 cũng cho điểm cao bất ngờ. Điều này cho thấy embedding có thể nhận ra các từ và chủ đề chung như “khách hàng”, “sản phẩm”, “thanh toán”, nhưng không luôn mô hình hóa tốt phủ định, quan hệ được phép/bị cấm hoặc sự khác biệt giữa các thao tác.

Vì vậy, cosine similarity nên được dùng để tìm ứng viên, không nên dùng một mình để quyết định câu trả lời đúng/sai. Với chính sách thương mại điện tử, cần thêm đoạn bằng chứng và điều kiện nghiệp vụ.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

### Thiết lập

- Corpus: 9 tài liệu chính thức trong `data/k4_official`.
- Backend: local multilingual Sentence Transformer.
- Chunker được chọn sau ablation: `RecursiveChunker(chunk_size=700)`.
- Tổng số chunk: 535.
- Query 2 dùng `metadata_filter={"customer_role": "seller"}` theo yêu cầu K4.
- `top_k=3`.
- Chunk được đánh dấu relevant khi đúng `doc_id` và chứa đủ các cụm bằng chứng đã định trước.

### Bộ câu hỏi chung và kết quả chạy thực tế

| # | Câu hỏi | Top-1 chunk / bằng chứng | Score top-1 | Rank bằng chứng đúng | Relevant top-3? | Tóm tắt câu trả lời |
|---:|---|---|---:|---:|---|---|
| 1 | Sau khi đơn hàng Shopee giao thành công, người mua có bao lâu để yêu cầu trả hàng/hoàn tiền, kể cả thực phẩm tươi sống và đông lạnh? | Chính sách trả hàng; chunk 6 chứa 15 ngày và ngoại lệ 24 giờ | 0,811260 | 1 | Có | Thông thường 15 ngày; thực phẩm tươi sống và đông lạnh là 24 giờ. |
| 2 | Người bán Shopee có được đăng mỹ phẩm đã qua sử dụng hoặc mỹ phẩm handmade thiếu giấy tờ an toàn không? | Cùng tài liệu chính sách cấm/hạn chế; chunk 12 chứa hai cụm mỹ phẩm | 0,680549 | 3 | Có | Không được đăng các nhóm mỹ phẩm này theo chính sách Shopee. |
| 3 | Tiki có trực tiếp lưu trữ thông tin thẻ không, và bên nào chịu trách nhiệm bảo mật? | Chính sách bảo mật thanh toán; chunk 2 nêu token và đối tác cổng thanh toán | 0,811719 | 1 | Có | Tiki chỉ giữ token mã hóa; đối tác cổng thanh toán lưu trữ và bảo mật thông tin thẻ. |
| 4 | Khi nhận hàng Tiki có được mở seal hoặc sử dụng thử không? | Chính sách kiểm hàng; chunk 0 nêu mở thùng nhưng không mở seal/sử dụng thử | 0,740177 | 2 | Có | Được mở thùng kiểm tra, không được mở seal riêng hoặc kiểm tra sâu như cắm điện, dùng thử. |
| 5 | Tiki lưu trữ thông tin cá nhân trong bao lâu? | Chính sách bảo vệ dữ liệu cá nhân; chunk 9 nêu thời gian lưu | 0,700682 | 2 | Có | Lưu đến khi khách hàng yêu cầu hoặc tự thực hiện hủy bỏ; dữ liệu được bảo mật trên máy chủ Tiki. |

**Tổng số câu có chunk liên quan trong top-3:** **5 / 5**.

**Phân bố rank của bằng chứng:** rank 1 có 2 câu, rank 2 có 2 câu và rank 3 có 1 câu.

### Phân tích kết quả

Câu 1 và câu 3 có bằng chứng đứng đầu vì câu hỏi chứa nhiều từ khóa đặc trưng và tài liệu đích ngắn/ít nhiễu hơn. Câu 2 cần filter vai trò người bán; dù đã đúng tài liệu, đoạn chứa mỹ phẩm vẫn đứng rank 3 vì tài liệu có danh sách sản phẩm cấm rất dài. Câu 4 và câu 5 cho thấy “đúng tài liệu” chưa đồng nghĩa “đúng điều khoản”: các đoạn giới thiệu chung có thể đứng trước đoạn trả lời trực tiếp.

Trong hai ablation cá nhân, SentenceChunker tạo chunk dễ đọc nhưng semantic search bị kéo về tài liệu pháp quy có phần OCR khó đọc. Fixed-size với overlap giữ lại nhiều nội dung lặp nhưng không tự giải quyết được nhiễu nguồn. Recursive 700 đạt recall tốt hơn trong benchmark, nên tôi chọn nó cho kết quả cuối; lớp kiểm tra bằng chứng giúp nhìn thấy những trường hợp top-1 chỉ đúng chủ đề.

### Câu trả lời grounded

Để tránh biến điểm similarity thành câu trả lời tự động, tôi dùng câu trả lời extractive trong evaluation. Nếu context không chứa đủ bằng chứng, hàm trả về “Không đủ thông tin trong ngữ cảnh truy xuất” thay vì tự suy đoán. Với 5 câu benchmark, cả 5 câu đều có thể sinh câu trả lời khớp gold answer từ context.

### Bài học từ thành viên khác

Qua cách làm của Nguyễn Tuấn Vũ, tôi thấy metadata `customer_role` có giá trị thực tế khi câu hỏi nói rõ “người bán” hoặc “người mua”. Qua cách làm của Phan Huy Hoàng, tôi thấy việc dùng local multilingual embedding quan trọng hơn mock embedding khi corpus có tiếng Việt. Phần tôi bổ sung là kiểm tra evidence ở cấp chunk: một hệ thống có thể đúng tài liệu nhưng vẫn chưa đưa đúng điều khoản vào context.

---

## 6. Tự đánh giá

| Tiêu chí | Điểm tự đánh giá | Căn cứ |
|---|---:|---|
| Khởi động (Warm-up) | 5 / 5 | Giải thích cosine và tính đúng số chunk ở hai mức overlap. |
| Hướng tiếp cận của tôi | 10 / 10 | Có mô tả pipeline hai tầng, ablation và grounding gate. |
| Hoàn thiện code | 30 / 30 | 42/42 test pass trên package cá nhân. |
| Dự đoán độ tương tự | 5 / 5 | Có 5 cặp riêng, số đo local và phân tích các dự đoán sai. |
| Kết quả truy xuất cá nhân | 10 / 10 | 5/5 câu có bằng chứng liên quan trong top-3 và câu trả lời đúng. |
| **Tổng phần cá nhân** | **60 / 60** |  |

## 7. Kết luận cá nhân

Bài học chính của tôi là retrieval không chỉ là chọn vector có cosine cao nhất. Với dữ liệu chính sách, cần quan tâm đồng thời đến cấu trúc văn bản, metadata, nguồn tài liệu, vị trí bằng chứng và khả năng kiểm chứng câu trả lời. Recursive chunking giúp giữ điều khoản đủ dài; local embedding giúp tìm theo ngữ nghĩa tiếng Việt; còn evidence gate giúp phát hiện trường hợp hệ thống chỉ tìm đúng chủ đề nhưng chưa tìm đúng câu trả lời.

Nếu phát triển tiếp, tôi sẽ bổ sung metadata `section_title`, `clause_id` và chất lượng trích xuất OCR. Khi đó có thể rerank theo điều khoản thay vì chỉ dựa vào score embedding, đồng thời hiển thị nguồn và đoạn bằng chứng trực tiếp cho người dùng.
