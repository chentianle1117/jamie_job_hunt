"""Render each role's resume.json + cover_letter.md to PNG for visual verification."""
import sys, os
sys.path.insert(0, r"C:\Users\chent\Agentic_Workflows_2026\oracle-job-search")
import json
import render_pdfs as R
from playwright.sync_api import sync_playwright

base = r"C:\Users\chent\Agentic_Workflows_2026\oracle-job-search\outputs\2026-06-13-deep\applications"
slugs = ["sierra_people_ops", "chime_senior_people_partner", "vercel_senior_hrbp_epd"]

with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(viewport={"width": 816, "height": 1056}, device_scale_factor=2)
    page = ctx.new_page()
    for slug in slugs:
        role_dir = os.path.join(base, slug)
        data = json.loads(open(os.path.join(role_dir, "resume.json"), encoding="utf-8").read())
        # resume PNG (find the autofit scale that yields 1 page already used; just render at 1.0 for preview, fallback small)
        # Use same autofit logic to match the PDF appearance
        scales = [1.0, 0.97, 0.94, 0.91, 0.88, 0.86]
        chosen_html = None
        for sc in scales:
            html = R.build_resume_html(data, font_scale=sc)
            page.set_content(html, wait_until="networkidle")
            page.wait_for_timeout(200)
            pdfpath = os.path.join(role_dir, "_tmp_probe.pdf")
            page.pdf(path=pdfpath, format="Letter", margin={"top":"0","right":"0","bottom":"0","left":"0"}, print_background=True)
            if R.count_pdf_pages(pdfpath) == 1:
                chosen_html = html
                os.remove(pdfpath)
                break
            os.remove(pdfpath)
        if chosen_html is None:
            chosen_html = R.build_resume_html(data, font_scale=0.86)
        page.set_content(chosen_html, wait_until="networkidle")
        page.wait_for_timeout(250)
        page.screenshot(path=os.path.join(role_dir, "preview_resume.png"), clip={"x":0,"y":0,"width":816,"height":1056})
        # cover PNG
        cover_md = open(os.path.join(role_dir, "cover_letter.md"), encoding="utf-8").read()
        cover_html = R.build_cover_html(cover_md, location=data.get("header",{}).get("location"))
        page.set_content(cover_html, wait_until="networkidle")
        page.wait_for_timeout(200)
        page.screenshot(path=os.path.join(role_dir, "preview_cover.png"), clip={"x":0,"y":0,"width":816,"height":1056})
        print("PNG done:", slug)
    browser.close()
print("ALL PNGs rendered.")
