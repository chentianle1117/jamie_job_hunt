"""render_one.py — render a single application folder's resume.json + cover_letter.md to PDF.
Reuses render_pdfs.py's logic; just points APPS_DIR at an arbitrary run folder.

Usage: python render_one.py <apps_dir> <role_folder_name>
  e.g. python render_one.py outputs/2026-06-12-feed-first/applications valley_medical_od_partner
"""
import sys
from pathlib import Path
import render_pdfs as R
from playwright.sync_api import sync_playwright

apps_dir = Path(sys.argv[1]).resolve()
role_id = sys.argv[2]
R.APPS_DIR = apps_dir  # override the hardcoded run folder

with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(viewport={"width": 816, "height": 1056})
    page = ctx.new_page()
    report = R.render_role(role_id, page, is_carlos=False, screenshots_dir=None)
    browser.close()

if "blocker" in report:
    print("BLOCKER:", report["blocker"], "| pages:", report.get("current_page_count"))
    sys.exit(1)
print(f"[OK] {role_id}: resume={report.get('resume_pages')}p cover={report.get('cover_pages')}p")
print("  ", apps_dir / role_id / "resume.pdf")
print("  ", apps_dir / role_id / "cover_letter.pdf")
