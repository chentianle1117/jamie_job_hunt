"""Quick PDF -> PNG for visual verification. Usage: python _pdf_to_png.py <pdf_path> <out_prefix>"""
import sys
import fitz  # PyMuPDF

pdf_path = sys.argv[1]
out_prefix = sys.argv[2]
doc = fitz.open(pdf_path)
for i, page in enumerate(doc):
    pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))  # 2x zoom ~ 144dpi
    out = f"{out_prefix}_p{i+1}.png"
    pix.save(out)
    print(f"  saved {out} ({pix.width}x{pix.height})")
print(f"[OK] {len(doc)} page(s) from {pdf_path}")
