import os
import glob
import time
import fitz

src_dir = r"D:\SPhO_Train\assets\figures"
dst_dir = r"D:\hong_23-10\public\assets\figures"

os.makedirs(dst_dir, exist_ok=True)

pdf_files = sorted(glob.glob(os.path.join(src_dir, "*.pdf")))
print(f"Total PDF figures to convert: {len(pdf_files)}")

t0 = time.time()
converted = 0
skipped = 0

for i, pdf_path in enumerate(pdf_files):
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    out_png = os.path.join(dst_dir, f"{base_name}.png")
    
    if os.path.exists(out_png) and os.path.getsize(out_png) > 0:
        skipped += 1
        continue
    
    try:
        doc = fitz.open(pdf_path)
        if len(doc) > 0:
            page = doc[0]
            # 160 DPI gives great readability and crisp formulas while keeping size ~30KB
            pix = page.get_pixmap(dpi=160)
            pix.save(out_png)
            converted += 1
        doc.close()
    except Exception as e:
        print(f"Error converting {base_name}: {e}")

    if (i + 1) % 100 == 0:
        elapsed = time.time() - t0
        print(f"Progress: {i+1}/{len(pdf_files)} (Converted: {converted}, Skipped: {skipped}, Elapsed: {elapsed:.1f}s)")

elapsed = time.time() - t0
print(f"DONE! Total converted: {converted}, Skipped: {skipped}, Time: {elapsed:.1f}s")
