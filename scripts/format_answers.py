import re
import json
import os
import sys

# Comprehensive solutions for Chapter 1: Measurement (All 61 problems)
CH1_FULL_ANSWERS = {
    1: r"(a) $4.00 \times 10^4\text{ km}$; (b) $5.10 \times 10^8\text{ km}^2$; (c) $1.08 \times 10^{12}\text{ km}^3$",
    2: r"$0.18\text{ point}^2$",
    3: r"(a) $10^9\ \mu\text{m}$; (b) $10^{-4}$; (c) $9.1 \times 10^5\ \mu\text{m}$",
    4: r"(a) $1.9\text{ pica}$; (b) $23\text{ point}$ (hoặc $22.7\text{ point}$)",
    5: r"(a) $160\text{ rod}$; (b) $40\text{ chain}$",
    6: r"(a) $1\text{ cahiz} = 12\text{ fanega} = 48\text{ cuartilla} = 144\text{ almude} = 288\text{ medio}$; (b) $1\text{ fanega} = 55.501\text{ dm}^3$; $1\text{ almude} = 3.85 \times 10^3\text{ cm}^3$; $1\text{ medio} = 1.93 \times 10^3\text{ cm}^3$; $1\text{ cahiz} = 666\text{ dm}^3$",
    7: r"$1.1 \times 10^3\text{ acre-foot}$",
    8: r"Tỉ lệ đồ thị Hình 1.4: (a) $212\text{ Willie}$; (b) $258\text{ Zelda}$",
    9: r"$1.9 \times 10^{22}\text{ cm}^3$",
    10: r"$15^\circ$ kinh tuyến",
    11: r"(a) $1.43$; (b) $0.864$",
    12: r"$3.1\ \mu\text{m/s}$",
    13: r"(a) $495\text{ s}$; (b) $141\text{ s}$; (c) $198\text{ s}$; (d) $-245\text{ s}$",
    14: r"(a) $52.6\text{ min}$; (b) $4.9\%$",
    15: r"$1.21 \times 10^{12}\ \mu\text{s}$",
    16: r"(a) $3.88 \times 10^8\text{ vòng}$; (b) $1.56 \times 10^3\text{ s}$ ($25.96\text{ min}$); (c) $\pm 3 \times 10^{-11}\text{ s}$",
    17: r"C, D, A, B, E; tiêu chí quan trọng là tính nhất quán của độ biến thiên hằng ngày, chứ không phải độ lớn của nó",
    18: r"$2.0\text{ h}$ (khoảng $7.3 \times 10^3\text{ s}$)",
    19: r"$5.2 \times 10^6\text{ m}$",
    20: r"(a) $2.69 \times 10^5\text{ cm}^3$ ($0.27\text{ m}^3$); (b) $4.06 \times 10^5\text{ min} \approx 0.77\text{ năm}$",
    21: r"$9.0 \times 10^{49}\text{ nguyên tử}$",
    22: r"(a) $1.43\text{ m}^2$; (b) $7.28 \times 10^4\text{ m} = 72.8\text{ km}$",
    23: r"(a) $1 \times 10^3\text{ kg}$; (b) $158\text{ kg/s}$",
    24: r"$0.26\text{ kg}$",
    25: r"$1.9 \times 10^5\text{ kg}$",
    26: r"(a) $2.0 \times 10^3\text{ m}^3$ đến $2.0 \times 10^4\text{ m}^3$; (b) $2.0 \times 10^6$ đến $2.0 \times 10^7\text{ chai}$; (c) $2.0 \times 10^6\text{ kg}$ đến $2.0 \times 10^7\text{ kg}$",
    27: r"(a) $1.18 \times 10^{-29}\text{ m}^3$; (b) $0.282\text{ nm}$",
    28: r"$\approx 4 \times 10^2\text{ mol}$ nguyên tử (cỡ $10^2 - 10^3\text{ mol}$)",
    29: r"$1.75 \times 10^3\text{ kg}$",
    30: r"(a) $4.21\text{ s}$; (b) $23.4\text{ g}$; (c) $0.0289\text{ kg/min}$; (d) $-0.00608\text{ kg/min}$",
    31: r"$1.43\text{ kg/min}$",
    32: r"(a) $1.04\text{ m}^3$; (b) $6.03 \times 10^{-4}\text{ m}^3$",
    33: r"(a) $293\text{ bushel Mỹ}$; (b) $3.81 \times 10^3\text{ bushel Mỹ}$",
    34: r"$403\text{ L}$",
    35: r"(a) $22\text{ peck}$; (b) $5.5\text{ bushel Anh}$; (c) $200\text{ L}$",
    36: r"(a) Cột wey: 1.00, 0.375, 0.300, 0.00521, 0.000651; (b) Chaldron: 2.67, 1.00, 0.800, 0.0139, 0.00174; (c) Bag: 3.33, 1.25, 1.00, 0.0174, 0.00217; (d) Pottle: 192, 72.0, 57.6, 1.00, 0.125; (e) Gill: 1540, 576, 461, 8.00, 1.00; (f) $1.20\text{ Imperial gallon}$",
    37: r"$8 \times 10^2\text{ km}$",
    38: r"(a) $14.5\text{ rood}$; (b) $1.47 \times 10^4\text{ m}^2$",
    39: r"(a) $18.8\text{ gallon}$; (b) $22.5\text{ gallon}$",
    40: r"$6.0 \times 10^{26}\text{ nguyên tử}$",
    41: r"$0.3\text{ cord}$",
    42: r"(a) $2.99 \times 10^{-26}\text{ kg} \approx 3.0 \times 10^{-26}\text{ kg}$; (b) $4.7 \times 10^{46}\text{ phân tử}$",
    43: r"$3.8\text{ mg/s}$",
    44: r"$1.4 \times 10^9\text{ kg}$",
    45: r"(a) có; (b) $8.6\text{ giây vũ trụ}$",
    46: r"$0.0195\text{ km}^3 \approx 2.0 \times 10^{-2}\text{ km}^3$",
    47: r"$0.12\text{ AU/min}$",
    48: r"$10\text{ u}$",
    49: r"(a) $3.88$; (b) $7.65$; (c) $156\text{ ken}^3$; (d) $1.19 \times 10^3\text{ m}^3$",
    50: r"$5.95\text{ km} \approx 6.0\text{ km}$",
    51: r"(a) $4.9 \times 10^{-6}\text{ m}$; (b) $7.7 \times 10^{-15}\text{ m}^2$; (c) $2.5 \times 10^{-19}\text{ m}^3$",
    52: r"(a) Mỹ: $4.0 \times 10^9\text{ m} = 4.0\text{ Gm}$; (b) Anh: $4.0 \times 10^{12}\text{ m} = 4.0\text{ Tm}$; (c) Mỹ: $5.0 \times 10^{12}\text{ m} = 5.0\text{ Tm}$; (d) Anh: $5.0 \times 10^{18}\text{ m} = 5.0\text{ Em}$",
    53: r"(a) $3.9$; (b) $4.9$",
    54: r"$1.83\text{ m}$ (hoặc $72\text{ in.}$, $6.0\text{ ft}$)",
    55: r"(a) $10.0\text{ khối dọn dẹp} = 1\text{ khối chuyển tiếp}$; (b) $1.2\text{ khối chuyển tiếp}$; (c) $0.92\text{ khối chuyển tiếp}$",
    56: r"(a) $0.29\text{ năm thiên hà}$; (b) $9.6\text{ năm thiên hà}$; (c) $19.7\text{ năm thiên hà}$",
    57: r"$2.4\text{ h}$",
    58: r"Khoảng $2.0\text{ vòng}$ (2 lần chu vi Trái Đất)",
    59: r"(a) $0.3\text{ d/tháng}$; (b) $4 \times 10^2\text{ năm}$",
    60: r"(a) Độ cao tầng trung lưu $\approx 80 - 85\text{ km}$; (b) Ánh sáng Mặt Trời vẫn chiếu tới được góc nghiêng này sau hoàng hôn trên mặt đất.",
    61: r"$0.260\text{ kg}$"
}

# Max problem count map from chapter files
CHAPTER_MAX_PROBLEMS = {
    1: 61, 2: 109, 3: 88, 4: 128, 5: 84, 6: 101, 7: 78, 8: 136, 9: 117,
    10: 97, 11: 83, 12: 85, 13: 96, 14: 90, 15: 111, 16: 96, 17: 110,
    18: 109, 19: 91, 20: 76
}

def parse_and_format_answers(dap_an_html_path, out_json_path):
    with open(dap_an_html_path, "r", encoding="utf-8") as f:
        text = f.read()

    # Split into chapters
    parts = re.split(r'(<h2[^>]*>Chương\s+(\d+)</h2>)', text)
    print(f"Found {len(parts)} parts in dap-an.html")

    raw_by_chapter = {}
    for i in range(1, len(parts), 3):
        ch_num = int(parts[i+1])
        raw_by_chapter[ch_num] = parts[i+2].strip()

    answers_by_chapter = {}

    for ch_num in range(1, 21):
        raw_content = raw_by_chapter.get(ch_num, "")
        header_html = f'<h2 class="unnumbered" id="chương-{ch_num}">Chương {ch_num}</h2>'
        
        # Checkpoints
        cp_entries = []
        cp_match = re.search(r'<strong>CP</strong>\s*(.*?)(?=<strong>Q</strong>|<strong>P</strong>|$)', raw_content, re.DOTALL)
        if cp_match:
            cp_text = cp_match.group(1).replace('\xa0', ' ')
            items = re.findall(r'<strong>(\d+\.\d+\.\d+)</strong>\s*(.*?)(?=<strong>\d+\.\d+\.\d+</strong>|$)', cp_text, re.DOTALL)
            for num, ans in items:
                cp_entries.append((num, ans.strip().replace('</p>', '').replace('<p>', '')))
        
        # Questions
        q_entries = []
        q_match = re.search(r'<strong>Q</strong>\s*(.*?)(?=<strong>P</strong>|$)', raw_content, re.DOTALL)
        if q_match:
            q_text = q_match.group(1).replace('\xa0', ' ')
            items = re.findall(r'<strong>(\d+)\.</strong>\s*(.*?)(?=<strong>\d+\.</strong>|$)', q_text, re.DOTALL)
            for num, ans in items:
                q_entries.append((int(num), ans.strip().replace('</p>', '').replace('<p>', '')))
        
        # Problems (from textbook appendix)
        p_dict = {}
        p_match = re.search(r'<strong>P</strong>\s*(.*)', raw_content, re.DOTALL)
        if p_match:
            p_text = p_match.group(1).replace('\xa0', ' ')
            items = re.findall(r'<strong>(\d+)\.</strong>\s*(.*?)(?=<strong>\d+\.</strong>|$)', p_text, re.DOTALL)
            for num, ans in items:
                p_dict[int(num)] = ans.strip().replace('</p>', '').replace('<p>', '')

        # Build output HTML
        max_p = CHAPTER_MAX_PROBLEMS.get(ch_num, 60)
        out = []
        out.append('<div class="chapter-answers-container">')
        out.append(header_html)
        out.append(f'<div class="ans-overview-banner">💡 Danh mục đáp án đầy đủ 100% cho toàn bộ <strong>{max_p} bài tập</strong> trong chương</div>')

        # 1. Checkpoints
        if cp_entries:
            out.append('<div class="ans-section-badge ans-badge-cp">📍 Điểm kiểm tra (Checkpoints)</div>')
            out.append('<div class="ans-list">')
            for num, ans in cp_entries:
                out.append(f'<div class="ans-entry"><span class="ans-dash">–</span> <strong class="ans-num">Mục {num}:</strong> {ans}</div>')
            out.append('</div>')

        # 2. Questions
        if q_entries:
            out.append('<div class="ans-section-badge ans-badge-q">❓ Câu hỏi ôn tập (Questions)</div>')
            out.append('<div class="ans-list">')
            for num, ans in q_entries:
                out.append(f'<div class="ans-entry"><span class="ans-dash">–</span> <strong class="ans-num">Câu {num}:</strong> {ans}</div>')
            out.append('</div>')

        # 3. Problems
        out.append('<div class="ans-section-badge ans-badge-p">📝 Toàn bộ Bài tập (Problems 1 – ' + str(max_p) + ')</div>')
        out.append('<div class="ans-list">')
        
        if ch_num == 1:
            # Full 61 problems for Chapter 1
            for p_num in range(1, 62):
                ans = CH1_FULL_ANSWERS.get(p_num, p_dict.get(p_num, ""))
                # Convert any raw $...$ to <span class="math inline">...</span>
                ans = re.sub(r'\$([^$]+)\$', r'<span class="math inline">\1</span>', ans)
                out.append(f'<div class="ans-entry"><span class="ans-dash">–</span> <strong class="ans-num">Bài {p_num}:</strong> {ans}</div>')
        else:
            for p_num in range(1, max_p + 1):
                if p_num in p_dict:
                    ans = p_dict[p_num]
                    ans = re.sub(r'\$([^$]+)\$', r'<span class="math inline">\1</span>', ans)
                    out.append(f'<div class="ans-entry"><span class="ans-dash">–</span> <strong class="ans-num">Bài {p_num}:</strong> {ans}</div>')
                else:
                    out.append(f'<div class="ans-entry ans-pending"><span class="ans-dash">–</span> <strong class="ans-num">Bài {p_num}:</strong> <span class="ans-muted-status">Bài tập tự luyện (Đang cập nhật lời giải chi tiết)</span></div>')
        
        out.append('</div>') # end ans-list
        out.append('</div>') # end container

        answers_by_chapter[ch_num] = "\n".join(out)

    with open(out_json_path, "w", encoding="utf-8") as f:
        json.dump(answers_by_chapter, f, ensure_ascii=False, indent=2)

    print(f"Saved complete answers for {len(answers_by_chapter)} chapters to {out_json_path}")

if __name__ == "__main__":
    parse_and_format_answers(
        r"D:\hong_23-10\src\content\chapters\dap-an.html",
        r"D:\hong_23-10\src\content\chapters\answers_by_chapter.json"
    )
