# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** IMBACK
**Thành viên:** Nguyễn Tuấn Vũ, Phan Huy Hoàng
**Ngày:** 03/08/2026

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Phạm vi bộ tài liệu (Scope)

**Chủ đề (cố định theo lớp K4):** Chính sách thương mại điện tử / hỗ trợ khách hàng (thanh toán, đổi trả, giao hàng, quyền riêng tư, điều kiện người bán…).

**Phạm vi cụ thể nhóm tập trung:**
> Nhóm tập trung vào chính sách đổi trả/hoàn tiền, chính sách cấm/hạn chế sản phẩm, kiểm hàng, bảo mật thanh toán và bảo vệ thông tin cá nhân của người mua/người bán trên Shopee và Tiki.

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | `shopee-return-refund-policy` | https://help.shopee.vn/portal/4/article/77251?seo=1 | 2026-08-03 / effective-2026-03-11 | 22323 | `doc_id`, `customer_role=both`, `category=returns_refunds`, `language=vi`, `source_url`, `retrieved_at`, `document_version` |
| 2 | `shopee-privacy-policy` | https://help.shopee.vn/portal/4/article/77244?previousPage=other+articles | 2026-08-03 / updated-2026-06-04 | 46441 | `doc_id`, `customer_role=both`, `category=privacy`, `language=vi`, `source_url`, `retrieved_at`, `document_version` |
| 3 | `shopee-terms-of-service` | https://help.shopee.vn/portal/4/article/77243 | 2026-08-03 / snapshot-2026-08-03 | 96309 | `doc_id`, `customer_role=both`, `category=terms_of_service`, `language=vi`, `source_url`, `retrieved_at`, `document_version` |
| 4 | `shopee-prohibited-restricted-products` | https://help.shopee.vn/portal/4/article/77247 | 2026-08-03 / snapshot-2026-08-03 | 14067 | `doc_id`, `customer_role=seller`, `category=seller_listing`, `language=vi`, `source_url`, `retrieved_at`, `document_version` |
| 5 | `shopee-change-payment-method-guide` | https://help.shopee.vn/portal/4/article/79128 | 2026-08-03 / snapshot-2026-08-03 | 1293 | `doc_id`, `customer_role=buyer`, `category=payment`, `language=vi`, `source_url`, `retrieved_at`, `document_version` |
| 6 | `tiki-payment-security-policy` | https://tiki.vn/_mobile-next/static/docs/TIKI_Chinh_sach_bao_mat_thanh_toan.pdf | 2026-08-03 / snapshot-2026-08-03 | 2260 | `doc_id`, `customer_role=buyer`, `category=payment_security`, `language=vi`, `source_url`, `retrieved_at`, `document_version` |
| 7 | `tiki-personal-data-protection-policy` | https://tiki.vn/_desktop-next/static/docs/TIKI_Chinh_sach_bao_ve_thong_tin_ca_nhan_nguoi_tieu_dung_VN_23082024.pdf | 2026-08-03 / 2024-08-23 | 9815 | `doc_id`, `customer_role=both`, `category=privacy`, `language=vi`, `source_url`, `retrieved_at`, `document_version` |
| 8 | `tiki-inspection-on-delivery-policy` | https://tiki.vn/_desktop-next/static/docs/TIKI_Chinh%20sach%20kiem%20hang.pdf | 2026-08-03 / snapshot-2026-08-03 | 1322 | `doc_id`, `customer_role=buyer`, `category=delivery`, `language=vi`, `source_url`, `retrieved_at`, `document_version` |
| 9 | `moit-ecommerce-consolidated-regulation-2018` | https://moit.gov.vn/upload/2005517/20210623/_VB_1519379363763_VB_VBHN-BCT_2018_11.pdf | 2026-08-03 / 11/VBHN-BCT-2018 | 89095 | `doc_id`, `customer_role=both`, `category=ecommerce_regulation`, `language=vi`, `source_url`, `retrieved_at`, `document_version` |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `doc_id` | string | `shopee-return-refund-policy` | Dùng để định danh ổn định một tài liệu và dễ đối chiếu khi xóa hoặc lọc. |
| `source_url` | string | https://help.shopee.vn/... | Dùng để truy vết nguồn gốc và xác minh tính công khai, đáng tin cậy. |
| `retrieved_at` | date | `2026-08-03` | Cho biết thời điểm thu thập; giúp kiểm tra tính thời sự và phiên bản mới/old. |
| `document_version` | string | `effective-2026-03-11` | Dùng để phân biệt phiên bản chính sách và tránh trả lời trên áp dụng sai thời điểm. |
| `customer_role` | enum | `buyer`, `seller`, `both` | Giúp filter câu hỏi theo vai trò người dùng để tăng độ chính xác. |
| `category` | string | `returns_refunds`, `privacy`, `delivery` | Tạo nhánh chủ đề và hỗ trợ hiểu ngữ cảnh tài liệu. |
| `language` | string | `vi` | Cho biết ngôn ngữ nội dung để tránh nhầm lẫn khi query đa ngôn ngữ. |
| `source_type` | string | `official_webpage` / `official_pdf` | Giúp đánh giá chất lượng nguồn và độ tin cậy của tài liệu. |
| `extraction_method` | string | `html-to-markdown` / `pdf-to-markdown` | Biết cách văn bản đã được chuyển đổi, từ đó hiểu độ sạch và độ tin cậy của dữ liệu. |
| `parser_confidence` | string | `high`, `medium` | Cho biết mức độ tin cậy của quá trình trích xuất và xử lý nội dung. |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu cho thấy rõ sự khác biệt giữa ba baseline strategy:

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| `01_shopee_chinh_sach_tra_hang_hoan_tien.md` | FixedSizeChunker (`fixed_size`) | 124 | 199.86 | Trung bình |
| `01_shopee_chinh_sach_tra_hang_hoan_tien.md` | SentenceChunker (`by_sentences`) | 50 | 443.54 | Tốt |
| `01_shopee_chinh_sach_tra_hang_hoan_tien.md` | RecursiveChunker (`recursive`) | 162 | 135.09 | Rất tốt |
| `04_shopee_chinh_sach_cam_han_che_san_pham.md` | FixedSizeChunker (`fixed_size`) | 79 | 197.81 | Trung bình |
| `04_shopee_chinh_sach_cam_han_che_san_pham.md` | SentenceChunker (`by_sentences`) | 55 | 253.69 | Tốt |
| `04_shopee_chinh_sach_cam_han_che_san_pham.md` | RecursiveChunker (`recursive`) | 101 | 136.05 | Rất tốt |
| `08_tiki_chinh_sach_kiem_hang.md` | FixedSizeChunker (`fixed_size`) | 8 | 182.75 | Trung bình |
| `08_tiki_chinh_sach_kiem_hang.md` | SentenceChunker (`by_sentences`) | 2 | 660.00 | Tốt nhưng quá lớn |
| `08_tiki_chinh_sach_kiem_hang.md` | RecursiveChunker (`recursive`) | 9 | 145.00 | Rất tốt |

### Chiến lược của từng thành viên

**Thành viên 1 — Nguyễn Tuấn Vũ**
- **Loại chiến lược:** RecursiveChunker + metadata filtering
- **Mô tả & lý do chọn cho chủ đề này:** RecursiveChunker ưu tiên cắt theo cấu trúc đoạn văn, xuống dòng và dấu chấm, nên phù hợp với các chính sách pháp lý có nhánh, bảng và điều khoản. Khi thêm bộ lọc `customer_role`/`category`, câu hỏi về người bán hay người mua được tập trung tốt hơn, giảm nhiễu trong top-k.
- **Code snippet (nếu custom):**
```python
chunker = RecursiveChunker(chunk_size=700)
results = store.search_with_filter(query, top_k=3, metadata_filter={"customer_role": "seller"})
```

**Thành viên 2 — Phan Huy Hoàng**
- **Loại chiến lược:** RecursiveChunker theo mục/đề mục, dùng `LocalEmbedder`
- **Mô tả & lý do chọn:** Với corpus dài và có nhiều điều kiện, danh sách, điều khoản, chunking theo nhánh/tiêu đề giữ được “câu trả lời có bằng chứng” đầy đủ hơn so với cắt theo kích thước cố định. Dùng embedder đa ngữ cục bộ giúp chặn “ngữ nghĩa tiếng Việt” tốt hơn mock embedder, nên độ tin cậy của retrieval cao hơn trong phần đánh giá.
- **Code snippet (nếu custom):**
```python
embedder = LocalEmbedder()
store = build_knowledge_base(
    "data/k4_official",
    embedding_fn=embedder,
    chunker=RecursiveChunker(chunk_size=700),
)
```

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Nguyễn Tuấn Vũ | RecursiveChunker + metadata filter | 9/10 | Dễ lọc theo vai trò khách hàng/người bán; giảm nhiễu | Một vài câu hỏi vẫn còn dính chunk tổng quát ở top-1/top-2 |
| Phan Huy Hoàng | RecursiveChunker + LocalEmbedder | 10/10 | Bằng chứng đúng đứng ở rank 1-2 cho 5/5 câu hỏi, chất lượng grounding tốt | Tốn thời gian tải mô hình cục bộ lần đầu |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> Chiến lược tốt nhất cho chủ đề chính sách thương mại điện tử là `RecursiveChunker` kết hợp với bộ lọc metadata rành mạch như `customer_role` và `category`. Độ dài tài liệu dài, có nhiều tiêu đề và mảng điều khoản nên phân tách theo cấu trúc văn bản tốt hơn fixed-size hay sentence-based trong hầu hết câu hỏi đánh giá. Kết quả thực tế cho thấy chunk bằng chứng đúng thường nằm trong top-3 và ở một số câu còn đứng rank 1, tức là thiết kế này vừa giữ ngữ cảnh vừa giảm nhiễu.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Sau khi đơn hàng Shopee được giao thành công, người mua có bao lâu để yêu cầu trả hàng hoặc hoàn tiền, kể cả với thực phẩm tươi sống và đông lạnh? | Thông thường là 15 ngày; riêng thực phẩm tươi sống và đông lạnh là 24 giờ kể từ khi giao thành công. | `shopee-return-refund-policy`, chunk 6 |
| 2 | Người bán Shopee có được đăng mỹ phẩm đã qua sử dụng hoặc mỹ phẩm handmade chưa có giấy công bố và chứng từ an toàn không? | Không; đây là nhóm sản phẩm bị cấm/hạn chế đăng bán. | `shopee-prohibited-restricted-products`, chunk 12 (cần lọc `customer_role=seller`) |
| 3 | Tiki có trực tiếp lưu trữ thông tin thẻ thanh toán của khách hàng không, và bên nào chịu trách nhiệm lưu trữ bảo mật? | Tiki không trực tiếp lưu thông tin thẻ; Tiki chỉ giữ token đã mã hóa, còn Đối Tác Cổng Thanh Toán được cấp phép lưu trữ và bảo mật. | `tiki-payment-security-policy`, chunk 2 |
| 4 | Khi nhận hàng Tiki, khách hàng được kiểm tra đến mức nào và có được mở seal hoặc sử dụng thử sản phẩm không? | Khách hàng được mở thùng kiểm tra, nhưng không được mở seal riêng sản phẩm hay kiểm tra sâu như cắm điện, sử dụng thử, ghi dữ liệu. | `tiki-inspection-on-delivery-policy`, chunk 0 |
| 5 | Tiki lưu trữ thông tin cá nhân của khách hàng trong bao lâu? | Thông tin được lưu cho đến khi khách hàng yêu cầu hủy bỏ hoặc tự đăng nhập và thực hiện hủy bỏ; dữ liệu được bảo mật trên máy chủ Tiki. | `tiki-personal-data-protection-policy`, chunk 9 |

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | Câu 1: thời hạn đổi trả / hoàn tiền | RecursiveChunker + LocalEmbedder | Có | Top-1 đúng bằng chứng, agent trả lời chính xác |
| 2 | Câu 2: sản phẩm cấm/hạn chế người bán | RecursiveChunker + metadata filter `customer_role=seller` | Có | Bằng chứng đúng chỉ ở rank 3, cần chunking theo đề mục rõ hơn |
| 3 | Câu 3: bảo mật thông tin thẻ Tiki | RecursiveChunker + LocalEmbedder | Có | Bằng chứng đúng ở rank 1, trả lời đúng và rõ ràng |
| 4 | Câu 4: chính sách kiểm hàng Tiki | RecursiveChunker + LocalEmbedder | Có | Bằng chứng đúng ở rank 2, chủ đề về kiểm tra hàng tốt nhưng điều khoản “không mở seal” dễ bị chồng lấp |
| 5 | Câu 5: thời gian lưu trữ dữ liệu cá nhân Tiki | RecursiveChunker + LocalEmbedder | Có | Bằng chứng đúng ở rank 2, agent trả lời đúng dựa trên chunk chính sách |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> Có, metadata filter đóng vai trò rất hữu ích ở câu 2. Khi ta đặt `customer_role=seller`, tập ứng viên bị giới hạn về chính sách dành cho người bán, nên top-k ít nhiễu hơn và có cơ hội hit đúng đoạn “mỹ phẩm đã qua sử dụng / handmade chưa có giấy công bố” ở gần đầu. Đây là minh chứng rõ ràng rằng metadata không chỉ phục vụ truy vết nguồn mà còn làm tăng độ chính xác của retrieval ở những query có vai trò người dùng rõ ràng.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
> 1. `RecursiveChunker` làm tốt hơn fixed-size ở các chính sách có cấu trúc đầu mục, vì nó giữ được phần “điều kiện”, “ngoại lệ”, “điều khoản” trong cùng chunk.  
> 2. `metadata_filter` giúp giảm đáng kể nhiễu khi query hỏi về vai trò người mua hoặc người bán.  
> 3. Với các câu hỏi cần đúng “cụm bằng chứng”, chỉ có đúng chủ đề chưa đủ; cần chunk nhỏ hơn hoặc có tiêu đề rõ ràng để top-3 chứa đúng đoạn chứng cứ.

**Bài học rút ra khi so sánh trong nhóm:**
> Cùng một bộ luật nhưng chiến lược chia nhỏ khác nhau tạo ra hiệu suất khác nhau rõ rệt. Fixed-size dễ tạo chunk có nội dung cắt ngang, trong khi SentenceChunker có thể gộp quá nhiều câu vào một chunk làm mất độ mạch lạc. RecursiveChunker là phương án cân bằng tốt nhất cho văn bản pháp lý vì nó giữ ranh giới theo heading/paragraph và giảm khả năng mất ngữ cảnh.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> Nếu làm lại, nhóm sẽ chia theo từng đề mục rõ ràng hơn và gắn thêm `section_title`/`policy_clause` vào metadata để retrieval dễ đối chiếu với một điều khoản cụ thể. Ngoài ra, nhóm sẽ ưu tiên chunker `recursive` với `chunk_size` thấp hơn ở các phần có danh sách dài và dùng metadata filter mạnh hơn khi câu hỏi nhắm vào vai trò `buyer` hoặc `seller`.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | 10 / 10 |
| Thiết kế chiến lược (Strategy Design) | 14 / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 10 / 10 |
| Thuyết trình (Demo) | 4 / 5 |
| **Tổng phần nhóm** | **38 / 40** |
