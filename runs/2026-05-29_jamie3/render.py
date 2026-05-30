#!/usr/bin/env python3
"""Render resume.json + cover_letter.md -> PDFs for the 3 jamie3 roles, reusing render_pdfs functions."""
import json, sys
from pathlib import Path
sys.path.insert(0, r"C:\Users\chent\Agentic_Workflows_2026\oracle-job-search")
from render_pdfs import build_resume_html, build_cover_html, count_pdf_pages
from playwright.sync_api import sync_playwright

RUN = Path(r"C:\Users\chent\Agentic_Workflows_2026\oracle-job-search\runs\2026-05-29_jamie3")
ROLES = ["axon", "accuris", "chartis"]

results = []
with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(viewport={"width": 816, "height": 1056})
    page = ctx.new_page()
    for r in ROLES:
        d = RUN / r
        data = json.loads((d / "resume.json").read_text(encoding="utf-8"))
        html = build_resume_html(data)
        page.set_content(html, wait_until="networkidle"); page.wait_for_timeout(300)
        page.pdf(path=str(d / "resume.pdf"), format="Letter",
                 margin={"top":"0","right":"0","bottom":"0","left":"0"}, print_background=True)
        rp = count_pdf_pages(d / "resume.pdf")
        # screenshot of resume page 1
        page.set_viewport_size({"width":816,"height":1056})
        page.screenshot(path=str(d/"resume_preview.png"), clip={"x":0,"y":0,"width":816,"height":1056})

        cmd = (d / "cover_letter.md").read_text(encoding="utf-8")
        chtml = build_cover_html(cmd)
        page.set_content(chtml, wait_until="networkidle"); page.wait_for_timeout(200)
        page.pdf(path=str(d / "cover_letter.pdf"), format="Letter",
                 margin={"top":"0","right":"0","bottom":"0","left":"0"}, print_background=True)
        cp = count_pdf_pages(d / "cover_letter.pdf")
        page.screenshot(path=str(d/"cover_preview.png"), clip={"x":0,"y":0,"width":816,"height":1056})
        results.append({"role": r, "resume_pages": rp, "cover_pages": cp})
        print(f"[OK] {r}: resume={rp}p cover={cp}p", flush=True)
    browser.close()
print(json.dumps(results, indent=2))
