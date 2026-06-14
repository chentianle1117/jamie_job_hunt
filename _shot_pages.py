"""Render a role's resume + cover HTML to PNG for visual verification.
Usage: python _shot_pages.py <apps_dir> <slug>
Writes _verify_resume.png and _verify_cover.png into the role folder.
"""
import sys, json
from pathlib import Path
import render_pdfs as R
from playwright.sync_api import sync_playwright

apps_dir = Path(sys.argv[1]).resolve()
slug = sys.argv[2]
role_dir = apps_dir / slug
data = json.loads((role_dir / "resume.json").read_text(encoding="utf-8"))

# Determine the font scale that fit (mirror render_role autofit) by checking the pdf? Simpler:
# just render at 1.0 first; if resume overflowed, the PDF render already used a smaller scale.
# For the PNG we render at the scale that produced 1 page in the pdf step — approximate by
# re-running the same autofit loop and stopping at 1 page via page height check.

with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(viewport={"width": 816, "height": 1056}, device_scale_factor=2)
    page = ctx.new_page()

    # resume: find fitting scale
    scales = [1.0, 0.97, 0.94, 0.91, 0.88, 0.86]
    chosen = 1.0
    for s in scales:
        html = R.build_resume_html(data, font_scale=s)
        page.set_content(html, wait_until="networkidle")
        page.wait_for_timeout(150)
        # measure body scroll height vs one letter page at 96dpi (1056px)
        h = page.evaluate("() => document.body.scrollHeight")
        chosen = s
        if h <= 1056:
            break
    html = R.build_resume_html(data, font_scale=chosen)
    page.set_content(html, wait_until="networkidle")
    page.wait_for_timeout(200)
    page.screenshot(path=str(role_dir / "_verify_resume.png"),
                    clip={"x": 0, "y": 0, "width": 816, "height": 1056})
    print(f"resume PNG @ scale={chosen} (bodyH measured) -> _verify_resume.png")

    # cover
    cover_md = (role_dir / "cover_letter.md").read_text(encoding="utf-8")
    cover_html = R.build_cover_html(cover_md, location=data.get("header", {}).get("location"))
    page.set_content(cover_html, wait_until="networkidle")
    page.wait_for_timeout(200)
    page.screenshot(path=str(role_dir / "_verify_cover.png"),
                    clip={"x": 0, "y": 0, "width": 816, "height": 1056})
    paras = cover_html.count("<p>")
    print(f"cover PNG -> _verify_cover.png | body <p> count={paras}")
    browser.close()
