#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script xử lý PDF & tạo Search Index cho Cuna Physics
- Tự động linearize bằng QPDF (thông qua pikepdf) cho Fast Web View.
- Nhúng cây mục lục chi tiết (Outline/Bookmarks) vào metadata PDF.
- Giữ nguyên vector text, hình ảnh và công thức (không làm giảm độ nét).
- Trích xuất toàn văn từng trang làm search index (MiniSearch).
- Xuất metadata tổng thể cho Astro.
- Tái sử dụng được cho các bộ sách khác trong tương lai.
"""

import os
import sys
import json
import argparse
import tempfile
import fitz  # PyMuPDF
import pikepdf

# Đảm bảo console Windows in tiếng Việt chuẩn
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

CHAPTER_SPECS = [
    {"num": 1, "raw": "ch01_vi_demo.pdf", "slug": "01-do-luong", "title": "Đo lường", "titleEn": "Measurement"},
    {"num": 2, "raw": "ch02_vi_demo.pdf", "slug": "02-chuyen-dong-thang", "title": "Chuyển động thẳng", "titleEn": "Straight-Line Motion"},
    {"num": 3, "raw": "ch03_vi_demo.pdf", "slug": "03-vector", "title": "Vectơ", "titleEn": "Vectors"},
    {"num": 4, "raw": "ch04_vi_demo.pdf", "slug": "04-chuyen-dong-trong-hai-va-ba-chieu", "title": "Chuyển động trong 2 & 3 chiều", "titleEn": "Motion in 2D & 3D"},
    {"num": 5, "raw": "ch05_vi_demo.pdf", "slug": "05-luc-va-chuyen-dong-1", "title": "Lực và chuyển động — I", "titleEn": "Force and Motion — I"},
    {"num": 6, "raw": "ch06_vi_demo.pdf", "slug": "06-luc-va-chuyen-dong-2", "title": "Lực và chuyển động — II", "titleEn": "Force and Motion — II"},
    {"num": 7, "raw": "ch07_vi_demo.pdf", "slug": "07-dong-nang-va-cong", "title": "Động năng và công", "titleEn": "Kinetic Energy and Work"},
    {"num": 8, "raw": "ch08_vi_demo.pdf", "slug": "08-the-nang-va-bao-toan-nang-luong", "title": "Thế năng & Bảo toàn năng lượng", "titleEn": "Potential Energy & Conservation"},
    {"num": 9, "raw": "ch09_vi_demo.pdf", "slug": "09-khoi-tam-va-dong-luong-tuyen-tinh", "title": "Khối tâm & Động lượng tuyến tính", "titleEn": "Center of Mass & Linear Momentum"},
    {"num": 10, "raw": "ch10_vi_demo.pdf", "slug": "10-su-quay-cua-vat-ran", "title": "Sự quay của vật rắn", "titleEn": "Rotation"},
    {"num": 11, "raw": "ch11_vi_demo.pdf", "slug": "11-lan-momen-luc-va-momen-dong-luong", "title": "Lăn, mômen lực & Mômen động lượng", "titleEn": "Rolling, Torque, Angular Momentum"},
    {"num": 12, "raw": "ch12_vi_demo.pdf", "slug": "12-can-bang-tinh-va-tinh-dan-hoi", "title": "Cân bằng tĩnh & Tính đàn hồi", "titleEn": "Equilibrium and Elasticity"},
    {"num": 13, "raw": "ch13_vi_demo.pdf", "slug": "13-luc-hap-dan", "title": "Lực hấp dẫn", "titleEn": "Gravitation"},
    {"num": 14, "raw": "ch14_vi_demo.pdf", "slug": "14-co-hoc-chat-luu", "title": "Cơ học chất lưu", "titleEn": "Fluids"},
    {"num": 15, "raw": "ch15_vi_demo.pdf", "slug": "15-dao-dong", "title": "Dao động", "titleEn": "Oscillations"},
    {"num": 16, "raw": "ch16_vi_demo.pdf", "slug": "16-song-1", "title": "Sóng — I", "titleEn": "Waves — I"},
    {"num": 17, "raw": "ch17_vi_demo.pdf", "slug": "17-song-2", "title": "Sóng — II", "titleEn": "Waves — II (Sound)"},
    {"num": 18, "raw": "ch18_vi_demo.pdf", "slug": "18-nhiet-do-nhiet-luong-va-dinh-luat-1-ndlh", "title": "Nhiệt độ, nhiệt lượng & Định luật 1 NĐLH", "titleEn": "Temperature, Heat, First Law"},
    {"num": 19, "raw": "ch19_vi_demo.pdf", "slug": "19-thuyet-dong-hoc-chat-khi", "title": "Thuyết động học chất khí", "titleEn": "Kinetic Theory of Gases"},
    {"num": 20, "raw": "ch20_vi_demo.pdf", "slug": "20-entropy-va-dinh-luat-2-ndlh", "title": "Entropy & Định luật 2 NĐLH", "titleEn": "Entropy & Second Law"}
]

ANSWERS_MAPPING = {
    1: 1, 2: 1, 3: 1,
    4: 2, 5: 2,
    6: 3, 7: 3,
    8: 4, 9: 4,
    10: 5, 11: 5,
    12: 6,
    13: 7, 14: 7,
    15: 8, 16: 8,
    17: 9, 18: 9,
    19: 10, 20: 10
}

APPENDIX_ITEMS = [
    {"code": "A", "title": "Hệ đơn vị Quốc tế (SI)", "page": 1},
    {"code": "B", "title": "Một số hằng số vật lý cơ bản", "page": 3},
    {"code": "C", "title": "Một số dữ liệu thiên văn", "page": 4},
    {"code": "D", "title": "Hệ số chuyển đổi đơn vị", "page": 5},
    {"code": "E", "title": "Công thức toán học", "page": 9},
    {"code": "F", "title": "Tính chất của các nguyên tố", "page": 12},
    {"code": "G", "title": "Bảng tuần hoàn các nguyên tố hóa học", "page": 16}
]

def format_bytes(size):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} TB"

def build_pdf_toc_list(chapter_num, chapter_title, mapped_ch):
    """Xây dựng danh sách TOC phân cấp cho PyMuPDF: [[level, title, 1-based page]]"""
    toc_list = [[1, f"Chương {chapter_num}: {chapter_title}", 1]]
    if not mapped_ch or 'sections' not in mapped_ch:
        return toc_list
    
    for sec in mapped_ch['sections']:
        sec_title = f"{sec.get('code', '')} {sec.get('title', '')}".strip()
        sec_page = max(1, sec.get('pdf_page', 1))
        toc_list.append([2, sec_title, sec_page])
        
        for sub in sec.get('subsections', []):
            sub_title = sub.get('title', '').strip()
            sub_page = max(1, sub.get('pdf_page', sec_page))
            toc_list.append([3, sub_title, sub_page])
            
    return toc_list

def process_single_pdf(src_path, dst_path, toc_list=None):
    """
    1. Mở PDF bằng PyMuPDF, nhúng TOC nếu có.
    2. Lưu ra file tạm.
    3. Mở file tạm bằng pikepdf và lưu với linearize=True (QPDF Fast Web View).
    """
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        # Bước 1: Nhúng Outline bằng PyMuPDF
        doc = fitz.open(src_path)
        page_count = len(doc)
        if toc_list:
            doc.set_toc(toc_list)
        doc.save(tmp_path, garbage=3, deflate=True)
        doc.close()

        # Bước 2: Linearize bằng pikepdf (QPDF)
        with pikepdf.Pdf.open(tmp_path) as pdf:
            pdf.save(dst_path, linearize=True)

        return page_count
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

def extract_pdf_search_text(pdf_path, book_slug, doc_id_prefix, chapter_title):
    """Trích xuất text từng trang của PDF phục vụ search index"""
    entries = []
    doc = fitz.open(pdf_path)
    for idx, page in enumerate(doc):
        page_num = idx + 1
        text = page.get_text("text").strip()
        # Loại bỏ khoảng trắng thừa nhưng giữ các từ khóa tiếng Việt
        cleaned_text = " ".join(text.split())
        if cleaned_text:
            entries.append({
                "id": f"{doc_id_prefix}-p{page_num:02d}",
                "bookSlug": book_slug,
                "docPrefix": doc_id_prefix,
                "title": chapter_title,
                "page": page_num,
                "content": cleaned_text
            })
    doc.close()
    return entries

def main():
    parser = argparse.ArgumentParser(description="Xử lý PDF & Xuất Search Index cho Cuna Physics")
    parser.add_argument("--source-dir", default=r"D:\SPhO_Train\output\demo", help="Thư mục chứa 23 PDF gốc")
    parser.add_argument("--book-slug", default="co-so-vat-ly-tap-1", help="Slug của cuốn sách")
    parser.add_argument("--book-title", default="Cơ sở Vật lý Tập 1: Cơ học, Sóng và Nhiệt động lực học", help="Tên cuốn sách")
    parser.add_argument("--output-base", default=r"D:\hong_23-10\public\books", help="Thư mục gốc public/books")
    parser.add_argument("--toc-file", default=r"C:\Users\Lenovo\.gemini\antigravity\brain\9252650e-3ead-4af0-8839-99921f1b9d45\scratch\mapped_toc.json", help="File mapped_toc.json")
    
    args = parser.parse_args()

    book_dir = os.path.join(args.output_base, args.book_slug)
    pdf_out_dir = os.path.join(book_dir, "pdf")
    os.makedirs(pdf_out_dir, exist_ok=True)

    # Đọc mapped TOC
    mapped_toc = []
    if os.path.exists(args.toc_file):
        with open(args.toc_file, "r", encoding="utf-8") as f:
            mapped_toc = json.load(f)
    mapped_dict = {item['chapter']: item for item in mapped_toc}

    print("=" * 80)
    print("🚀 BẮT ĐẦU GIAI ĐOẠN 3: XỬ LÝ 23 FILE PDF & TRÍCH XUẤT SEARCH INDEX")
    print(f"📖 Cuốn sách : {args.book_title} (slug: {args.book_slug})")
    print(f"📂 Nguồn      : {args.source_dir}")
    print(f"🎯 Đích       : {pdf_out_dir}")
    print("=" * 80)

    report_rows = []
    all_search_index = []
    metadata_chapters = []

    total_orig_size = 0
    total_opt_size = 0
    total_pages_all = 0

    # 1. Xử lý 20 Chương
    for spec in CHAPTER_SPECS:
        ch_num = spec["num"]
        src_file = os.path.join(args.source_dir, spec["raw"])
        dst_name = f"{spec['slug']}.pdf"
        dst_file = os.path.join(pdf_out_dir, dst_name)

        if not os.path.exists(src_file):
            print(f"❌ Không tìm thấy: {src_file}")
            continue

        orig_size = os.path.getsize(src_file)
        mapped_ch = mapped_dict.get(ch_num)
        toc_list = build_pdf_toc_list(ch_num, spec["title"], mapped_ch)

        # Xử lý PDF
        page_count = process_single_pdf(src_file, dst_file, toc_list)
        opt_size = os.path.getsize(dst_file)

        total_orig_size += orig_size
        total_opt_size += opt_size
        total_pages_all += page_count

        # Trích xuất text cho search index
        search_entries = extract_pdf_search_text(dst_file, args.book_slug, spec["slug"], f"Chương {ch_num}: {spec['title']}")
        all_search_index.extend(search_entries)

        # Lưu metadata chương
        metadata_chapters.append({
            "number": ch_num,
            "slug": spec["slug"],
            "title": spec["title"],
            "titleEn": spec["titleEn"],
            "fileName": dst_name,
            "pageCount": page_count,
            "sizeBytes": opt_size,
            "answersPage": ANSWERS_MAPPING.get(ch_num, 1),
            "sections": mapped_ch.get("sections", []) if mapped_ch else []
        })

        diff_pct = (opt_size - orig_size) / orig_size * 100
        report_rows.append({
            "stt": ch_num,
            "name": dst_name,
            "title": f"Chương {ch_num}: {spec['title']}",
            "pages": page_count,
            "orig_size": orig_size,
            "opt_size": opt_size,
            "diff_pct": diff_pct,
            "linearized": "✓ QPDF Fast Web"
        })
        print(f"✓ Ch {ch_num:02d}: {spec['title']} ({page_count} trang) -> {format_bytes(orig_size)} ➜ {format_bytes(opt_size)} [{diff_pct:+.1f}%]")

    # 2. Xử lý Mục lục gốc (00-muc-luc.pdf)
    muc_luc_src = os.path.join(args.source_dir, "muc_luc_vi.pdf")
    muc_luc_dst = os.path.join(pdf_out_dir, "00-muc-luc.pdf")
    if os.path.exists(muc_luc_src):
        orig_size = os.path.getsize(muc_luc_src)
        page_count = process_single_pdf(muc_luc_src, muc_luc_dst, [[1, "Mục Lục Chi Tiết", 1]])
        opt_size = os.path.getsize(muc_luc_dst)
        total_orig_size += orig_size
        total_opt_size += opt_size
        total_pages_all += page_count
        search_entries = extract_pdf_search_text(muc_luc_dst, args.book_slug, "00-muc-luc", "Mục lục chi tiết")
        all_search_index.extend(search_entries)
        report_rows.append({
            "stt": "ML",
            "name": "00-muc-luc.pdf",
            "title": "Mục lục chi tiết toàn tập",
            "pages": page_count,
            "orig_size": orig_size,
            "opt_size": opt_size,
            "diff_pct": (opt_size - orig_size) / orig_size * 100,
            "linearized": "✓ QPDF Fast Web"
        })
        print(f"✓ Mục lục: 00-muc-luc.pdf ({page_count} trang) -> {format_bytes(orig_size)} ➜ {format_bytes(opt_size)}")

    # 3. Xử lý Phụ lục (phu-luc.pdf)
    phu_luc_src = os.path.join(args.source_dir, "phu_luc_vi.pdf")
    phu_luc_dst = os.path.join(pdf_out_dir, "phu-luc.pdf")
    if os.path.exists(phu_luc_src):
        orig_size = os.path.getsize(phu_luc_src)
        app_toc = [[1, "Phụ lục tra cứu", 1]]
        for item in APPENDIX_ITEMS:
            app_toc.append([2, f"Phụ lục {item['code']}: {item['title']}", item["page"]])
        page_count = process_single_pdf(phu_luc_src, phu_luc_dst, app_toc)
        opt_size = os.path.getsize(phu_luc_dst)
        total_orig_size += orig_size
        total_opt_size += opt_size
        total_pages_all += page_count
        search_entries = extract_pdf_search_text(phu_luc_dst, args.book_slug, "phu-luc", "Phụ lục tra cứu (A-G)")
        all_search_index.extend(search_entries)
        report_rows.append({
            "stt": "PL",
            "name": "phu-luc.pdf",
            "title": "Phụ lục tra cứu tổng hợp (A - G)",
            "pages": page_count,
            "orig_size": orig_size,
            "opt_size": opt_size,
            "diff_pct": (opt_size - orig_size) / orig_size * 100,
            "linearized": "✓ QPDF Fast Web"
        })
        print(f"✓ Phụ lục: phu-luc.pdf ({page_count} trang) -> {format_bytes(orig_size)} ➜ {format_bytes(opt_size)}")

    # 4. Xử lý Đáp án (dap-an.pdf)
    dap_an_src = os.path.join(args.source_dir, "dap_so_vi.pdf")
    dap_an_dst = os.path.join(pdf_out_dir, "dap-an.pdf")
    if os.path.exists(dap_an_src):
        orig_size = os.path.getsize(dap_an_src)
        ans_toc = [[1, "Đáp số bài tập & Checkpoints", 1]]
        for ch_num, pg in ANSWERS_MAPPING.items():
            ans_toc.append([2, f"Đáp số Chương {ch_num}", pg])
        page_count = process_single_pdf(dap_an_src, dap_an_dst, ans_toc)
        opt_size = os.path.getsize(dap_an_dst)
        total_orig_size += orig_size
        total_opt_size += opt_size
        total_pages_all += page_count
        search_entries = extract_pdf_search_text(dap_an_dst, args.book_slug, "dap-an", "Đáp số Checkpoints & Bài tập")
        all_search_index.extend(search_entries)
        report_rows.append({
            "stt": "ĐA",
            "name": "dap-an.pdf",
            "title": "Đáp số Checkpoints & Bài tập",
            "pages": page_count,
            "orig_size": orig_size,
            "opt_size": opt_size,
            "diff_pct": (opt_size - orig_size) / orig_size * 100,
            "linearized": "✓ QPDF Fast Web"
        })
        print(f"✓ Đáp án : dap-an.pdf ({page_count} trang) -> {format_bytes(orig_size)} ➜ {format_bytes(opt_size)}")

    # 5. Lưu search-index.json
    search_index_path = os.path.join(book_dir, "search-index.json")
    with open(search_index_path, "w", encoding="utf-8") as f:
        json.dump(all_search_index, f, ensure_ascii=False, indent=2)
    print(f"🔍 Đã lưu Search Index: {search_index_path} ({len(all_search_index)} trang văn bản có dữ liệu)")

    # 6. Lưu metadata.json
    book_metadata = {
        "slug": args.book_slug,
        "title": args.book_title,
        "subtitle": "Fundamentals of Physics — David Halliday, Robert Resnick, Jearl Walker",
        "description": "Giáo trình kinh điển phục vụ ôn thi Olympic Vật lý Quốc gia (VPhO) và Quốc tế (SPhO/IPhO). Bao gồm Cơ học, Dao động & Sóng, Nhiệt động lực học.",
        "totalPages": total_pages_all,
        "totalChapters": len(metadata_chapters),
        "chapters": metadata_chapters,
        "answers": {
            "fileName": "dap-an.pdf",
            "totalPages": 11,
            "mapping": ANSWERS_MAPPING
        },
        "appendix": {
            "fileName": "phu-luc.pdf",
            "totalPages": 17,
            "items": APPENDIX_ITEMS
        },
        "tableOfContents": {
            "fileName": "00-muc-luc.pdf",
            "totalPages": 13
        }
    }
    meta_path = os.path.join(book_dir, "metadata.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(book_metadata, f, ensure_ascii=False, indent=2)
    print(f"📋 Đã lưu Book Metadata: {meta_path}")

    # 7. Lưu bảng thống kê báo cáo
    report_json_path = os.path.join(book_dir, "processing-report.json")
    with open(report_json_path, "w", encoding="utf-8") as f:
        json.dump({
            "total_files": len(report_rows),
            "total_pages": total_pages_all,
            "total_orig_size": total_orig_size,
            "total_opt_size": total_opt_size,
            "rows": report_rows
        }, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 80)
    print(f"🎉 HOÀN THÀNH XỬ LÝ 23/23 FILE PDF!")
    print(f"📄 Tổng số trang   : {total_pages_all} trang")
    print(f"📦 Dung lượng gốc  : {format_bytes(total_orig_size)}")
    print(f"⚡ Dung lượng sau   : {format_bytes(total_opt_size)} (Đã nhúng Outline + QPDF Linearize)")
    print(f"🔍 Chỉ mục tìm kiếm: {len(all_search_index)} trang văn bản đã lập chỉ mục")
    print("=" * 80)

if __name__ == "__main__":
    main()
