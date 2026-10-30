import re
import json
import sys

def parse_and_format_answers(dap_an_html_path, out_json_path):
    with open(dap_an_html_path, "r", encoding="utf-8") as f:
        text = f.read()

    # Split into chapters by <h2 ...>Chương X</h2>
    parts = re.split(r'(<h2[^>]*>Chương\s+(\d+)</h2>)', text)
    print(f"Found {len(parts)} parts in dap-an.html")

    answers_by_chapter = {}

    for i in range(1, len(parts), 3):
        header_tag = parts[i]
        ch_num = int(parts[i+1])
        raw_content = parts[i+2].strip()

        # Normalize non-breaking spaces
        content = raw_content.replace('\xa0', ' ')

        # Process sections:
        # First remove outer paragraph tags
        # Replace <p><strong>CP</strong> with CP marker
        content = re.sub(
            r'<p>\s*<strong>CP</strong>\s*',
            r'<div class="ans-section-badge ans-badge-cp">📍 Điểm kiểm tra (Checkpoints)</div><div class="ans-list">',
            content
        )
        content = re.sub(
            r'<p>\s*<strong>Q</strong>\s*',
            r'<div class="ans-section-badge ans-badge-q">❓ Câu hỏi (Questions)</div><div class="ans-list">',
            content
        )
        content = re.sub(
            r'<p>\s*<strong>P</strong>\s*',
            r'<div class="ans-section-badge ans-badge-p">📝 Bài tập (Problems)</div><div class="ans-list">',
            content
        )

        # Standalone <strong>CP</strong> / <strong>Q</strong> / <strong>P</strong> if not matching above
        content = re.sub(
            r'<strong>CP</strong>\s*',
            r'</div><div class="ans-section-badge ans-badge-cp">📍 Điểm kiểm tra (Checkpoints)</div><div class="ans-list">',
            content
        )
        content = re.sub(
            r'<strong>Q</strong>\s*',
            r'</div><div class="ans-section-badge ans-badge-q">❓ Câu hỏi (Questions)</div><div class="ans-list">',
            content
        )
        content = re.sub(
            r'<strong>P</strong>\s*',
            r'</div><div class="ans-section-badge ans-badge-p">📝 Bài tập (Problems)</div><div class="ans-list">',
            content
        )

        content = content.replace('</p>', '</div>')
        content = content.replace('<p>', '')

        # Numbered items:
        # 1) Checkpoint items like 2.1.1
        content = re.sub(
            r'<strong>(\d+\.\d+\.\d+)</strong>\s*',
            r'</div><div class="ans-entry"><span class="ans-dash">–</span> <strong class="ans-num">Mục \1:</strong> ',
            content
        )
        # 2) Standard question / problem numbers: 1. or 23.
        content = re.sub(
            r'<strong>(\d+)\.</strong>\s*',
            r'</div><div class="ans-entry"><span class="ans-dash">–</span> <strong class="ans-num">Bài \1:</strong> ',
            content
        )

        # Clean leading closing div if any
        content = re.sub(r'^\s*</div>', '', content)
        # Clean empty lists
        content = re.sub(r'<div class="ans-list">\s*</div>', '', content)

        # Wrap in container
        final_html = f'<div class="chapter-answers-container">\n{header_tag}\n{content}\n</div>'
        answers_by_chapter[ch_num] = final_html

    with open(out_json_path, "w", encoding="utf-8") as f:
        json.dump(answers_by_chapter, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(answers_by_chapter)} chapters to {out_json_path}")

if __name__ == "__main__":
    parse_and_format_answers(
        r"D:\hong_23-10\src\content\chapters\dap-an.html",
        r"D:\hong_23-10\src\content\chapters\answers_by_chapter.json"
    )
