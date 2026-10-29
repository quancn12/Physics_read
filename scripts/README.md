# 🛠️ Hướng dẫn Xử lý PDF & Xuất Search Index (Cuna Physics)

Script `process_books.py` được thiết kế để tự động hóa toàn bộ quy trình chuẩn bị dữ liệu cho website Cuna Physics, có khả năng **tái sử dụng 100%** cho các bộ tài liệu Vật lý tiếp theo (Vật lý 2, Vật lý 3, Chuyên đề Olympic, v.v.).

---

## 🌟 Chức năng của Script
1. **Chuẩn hóa tên file**: Xuất ra `public/books/<slug>/pdf/` theo quy ước `00-muc-luc.pdf`, `01-<slug>.pdf`, ..., `dap-an.pdf`, `phu-luc.pdf`.
2. **Linearize bằng QPDF (Fast Web View)**: Tối ưu hóa cấu trúc tệp PDF để trình duyệt/PDF.js có thể tải và hiển thị trang 1 ngay lập tức qua HTTP Range Requests mà không cần tải hết cả tệp.
3. **Nhúng Outline / Bookmarks**: Nhúng cây mục lục chi tiết (Chương ➔ Mục ➔ Tiểu mục) trực tiếp vào PDF để người đọc có thể mở danh mục bookmark trên bất kỳ trình xem PDF nào.
4. **Giữ nguyên chất lượng Vector**: Không nén mờ ảnh hay rasterize công thức toán học/chữ viết.
5. **Trích xuất toàn văn (Full-Text Extraction)**: Tạo file `search-index.json` sẵn sàng cho MiniSearch tìm kiếm full-text tiếng Việt có dấu và không dấu.
6. **Tạo Siêu dữ liệu (Metadata)**: Tự động xuất `metadata.json` chứa thông tin chương, số trang, ánh xạ trang đáp án và phụ lục.

---

## 📦 Yêu cầu Môi trường
Cài đặt các thư viện Python:
```bash
pip install fitz pikepdf
```
*(Lưu ý: `pikepdf` tích hợp sẵn engine C++ của QPDF 12+ nên không cần cài thêm QPDF rời trên hệ điều hành).*

---

## 🚀 Cách Chạy Cho Bộ Sách Mới

### 1. Cú pháp cơ bản:
```bash
python scripts/process_books.py \
  --source-dir "D:/SPhO_Train/output/demo" \
  --book-slug "co-so-vat-ly-tap-1" \
  --book-title "Cơ sở Vật lý Tập 1: Cơ học, Sóng và Nhiệt động lực học" \
  --output-base "public/books"
```

### 2. Các tham số tùy biến:
- `--source-dir`: Đường dẫn thư mục chứa các file PDF xuất ra từ LaTeX (mặc định: `D:\SPhO_Train\output\demo`).
- `--book-slug`: Slug định danh của cuốn sách trên URL web (ví dụ: `co-so-vat-ly-tap-1`, `co-so-vat-ly-tap-2`).
- `--book-title`: Tên hiển thị đầy đủ của cuốn sách.
- `--output-base`: Thư mục lưu kết quả (mặc định: `public/books`).
- `--toc-file`: File JSON chứa cây mục lục đã ánh xạ trang thực tế (`mapped_toc.json`).

---

## 📁 Kết quả Đầu ra Sau khi Chạy
```
public/books/<slug>/
├── pdf/
│   ├── 00-muc-luc.pdf
│   ├── 01-do-luong.pdf
│   ├── ...
│   ├── 20-entropy-va-dinh-luat-2-ndlh.pdf
│   ├── dap-an.pdf
│   └── phu-luc.pdf
├── metadata.json           # Siêu dữ liệu sách, chương, mục lục và mapping đáp án
├── search-index.json       # Toàn văn từng trang cho công cụ tìm kiếm
└── processing-report.json  # Bảng dung lượng trước/sau và thống kê
```
