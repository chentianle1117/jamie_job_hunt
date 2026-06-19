"""Render a single role package with the autofit loop from render_pdfs.py.
Usage: python _render_one.py <abs_role_dir>
"""
import sys, json
from pathlib import Path
import render_pdfs as R
from playwright.sync_api import sync_playwright

role_dir = Path(sys.argv[1]).resolve()
# point the module's APPS_DIR at the parent so render_role(role_id) resolves correctly
R.APPS_DIR = role_dir.parent
role_id = role_dir.name

with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(viewport={"width": 816, "height": 1056})
    page = ctx.new_page()
    rep = R.render_role(role_id, page, is_carlos=False, screenshots_dir=None)
    browser.close()
print(json.dumps(rep, indent=1)[:1200])
