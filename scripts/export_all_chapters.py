import os
import sys
import glob
import re
import json
import subprocess
import tempfile

sys.stdout.reconfigure(encoding='utf-8')

SRC_DIR = r"D:\SPhO_Train"
OUT_DIR = r"D:\hong_23-10\src\content\chapters"
META_PATH = r"D:\hong_23-10\public\books\co-so-vat-ly-tap-1\metadata.json"

os.makedirs(OUT_DIR, exist_ok=True)

with open(META_PATH, 'r', encoding='utf-8') as f:
    metadata = json.load(f)

chapter_slugs = {ch['number']: ch['slug'] for ch in metadata['chapters']}

def repl_hinh(m):
    fig_id = m.group(1).strip()
    caption = m.group(2).strip()
    return f"""
\\begin{{figure}}[htbp]
\\centering
\\includegraphics{{/Physics_read/assets/figures/Figure_{fig_id}.png}}
\\caption{{Hình {fig_id}: {caption}}}
\\end{{figure}}
"""

def unwrap_fbox_parbox(t):
    out = []
    i = 0
    while i < len(t):
        if t[i:i+6] == r'\fbox{':
            start = i + 6
            brace_count = 1
            j = start
            while j < len(t) and brace_count > 0:
                if t[j] == '{':
                    brace_count += 1
                elif t[j] == '}':
                    brace_count -= 1
                j += 1
            inside = t[start:j-1]
            m = re.match(r'^\s*\\parbox\{[^}]+\}\{', inside)
            if m:
                p_start = m.end()
                p_count = 1
                k = p_start
                while k < len(inside) and p_count > 0:
                    if inside[k] == '{':
                        p_count += 1
                    elif inside[k] == '}':
                        p_count -= 1
                    k += 1
                content = inside[p_start:k-1]
                out.append(f"\n\\begin{{quote}}\n\\textbf{{Khái niệm cốt lõi:}}\\\\\n{content}\n\\end{{quote}}\n")
            else:
                out.append(f"\n\\begin{{quote}}\n{inside}\n\\end{{quote}}\n")
            i = j
        else:
            out.append(t[i])
            i += 1
    return "".join(out)

def clean_latex(t):
    # Fix quad
    t = re.sub(r'\\quad', ' ', t)
    # Fix \chapter*{\\[0.5ex]}
    t = re.sub(r'\\chapter\*\{([^}]+)\\\\\[[^\]]*\]([^}]+)\}', r'\\chapter*{\1 — \2}', t)
    # Fix hinh
    t = re.sub(r'\\hinh\{([^}]+)\}\{((?:[^{}]|\{[^{}]*\})*)\}', repl_hinh, t)
    # Unwrap boxes
    t = unwrap_fbox_parbox(t)
    # Page markers
    t = re.sub(r'\\srcpage\{(\d+)\}', r'\n\\paragraph{[Trang \1]}\n', t)
    return t

def postprocess_html(html):
    # Transform [Trang XX]
    html = re.sub(
        r'<h4[^>]*>\[Trang (\d+)\]</h4>|<p><strong>\[Trang (\d+)\]</strong></p>',
        lambda m: f'<div class="page-divider" id="trang-{m.group(1) or m.group(2)}" data-page="{m.group(1) or m.group(2)}"><span>Trang {m.group(1) or m.group(2)}</span></div>',
        html
    )
    # Add class to figures
    html = re.sub(r'<figure>', '<figure class="book-figure">', html)
    # Style blockquotes
    html = re.sub(r'<blockquote>', '<blockquote class="callout-quote">', html)
    # Ensure images have loading=lazy
    html = re.sub(r'<img src="([^"]+)"', r'<img src="\1" loading="lazy"', html)
    return html

def extract_toc_from_html(html):
    headings = []
    pattern = r'<(h[1234])(?:\s+class="[^"]*")?(?:\s+id="([^"]*)")?[^>]*>(.*?)</\1>'
    for m in re.finditer(pattern, html, re.DOTALL):
        level = m.group(1)
        h_id = m.group(2) or ""
        raw_title = m.group(3)
        clean_title = re.sub(r'<[^>]+>', '', raw_title).strip()
        if not clean_title or clean_title.startswith("Trang") or clean_title.startswith("[Trang"):
            continue
        headings.append({
            "level": level,
            "id": h_id,
            "title": clean_title
        })
    return headings

toc_manifest = {}

for ch_num in range(1, 21):
    ch_str = f"ch{ch_num:02d}"
    slug = chapter_slugs.get(ch_num, f"{ch_str}")
    files = sorted(glob.glob(os.path.join(SRC_DIR, f"_read_{ch_str}_*.tex")))
    if not files:
        continue
    
    print(f"Exporting {ch_str} ({slug})...")
    raw_parts = []
    for f in files:
        with open(f, 'r', encoding='utf-8', errors='ignore') as fp:
            raw_parts.append(fp.read())
    combined = clean_latex("\n\n".join(raw_parts))
    
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.tex', delete=False) as tf:
        tf.write(combined)
        tf_name = tf.name
    
    res = subprocess.run(
        ["pandoc", tf_name, "-f", "latex", "-t", "html", "--katex"],
        capture_output=True,
        text=True,
        encoding="utf-8"
    )
    try:
        os.remove(tf_name)
    except:
        pass
    
    html = postprocess_html(res.stdout)
    out_file = os.path.join(OUT_DIR, f"{slug}.html")
    with open(out_file, 'w', encoding='utf-8') as fp:
        fp.write(html)
    
    toc = extract_toc_from_html(html)
    toc_manifest[slug] = toc

# Special
for ch_str, slug in [("ch21", "phu-luc"), ("ch22", "dap-an")]:
    files = sorted(glob.glob(os.path.join(SRC_DIR, f"_read_{ch_str}_*.tex")))
    if files:
        print(f"Exporting special {slug}...")
        raw_parts = []
        for f in files:
            with open(f, 'r', encoding='utf-8', errors='ignore') as fp:
                raw_parts.append(fp.read())
        combined = clean_latex("\n\n".join(raw_parts))
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.tex', delete=False) as tf:
            tf.write(combined)
            tf_name = tf.name
        res = subprocess.run(
            ["pandoc", tf_name, "-f", "latex", "-t", "html", "--katex"],
            capture_output=True,
            text=True,
            encoding="utf-8"
        )
        try:
            os.remove(tf_name)
        except:
            pass
        html = postprocess_html(res.stdout)
        out_file = os.path.join(OUT_DIR, f"{slug}.html")
        with open(out_file, 'w', encoding='utf-8') as fp:
            fp.write(html)
        toc = extract_toc_from_html(html)
        toc_manifest[slug] = toc

with open(os.path.join(OUT_DIR, "toc_manifest.json"), 'w', encoding='utf-8') as fp:
    json.dump(toc_manifest, fp, ensure_ascii=False, indent=2)

print("Export completed successfully!")
