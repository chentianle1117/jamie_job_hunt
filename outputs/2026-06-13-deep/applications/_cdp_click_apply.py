"""On an already-open LinkedIn job tab (or navigate fresh), click Apply and capture the external ATS URL.
Usage: python _cdp_click_apply.py <port> <linkedin_job_url>
Finds the tab matching the job url (or opens it), clicks the top 'Apply' button,
captures any newly-opened tab's URL (external ATS). Leaves tabs open.
"""
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from patchright.sync_api import sync_playwright

port = sys.argv[1]
job_url = sys.argv[2]
jid = job_url.rstrip("/").split("/")[-1]

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(f"http://localhost:{port}")
    ctx = browser.contexts[0]
    # find existing tab on this job, else open one
    page = None
    for pg in ctx.pages:
        if jid in pg.url:
            page = pg
            break
    if page is None:
        page = ctx.new_page()
        page.goto(job_url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(3500)

    before = set(pg.url for pg in ctx.pages)
    # the public (logged-out) LinkedIn apply button
    clicked = False
    for sel in [
        "button:has-text('Apply')",
        "a:has-text('Apply')",
        "button.jobs-apply-button",
        "[data-test-job-detail-apply-button]",
    ]:
        try:
            el = page.query_selector(sel)
            if el and el.is_visible():
                el.click(timeout=3000)
                clicked = True
                print(f"clicked: {sel}")
                break
        except Exception as e:
            print(f"sel {sel} -> {e}")
    page.wait_for_timeout(4500)

    # any new tab?
    new_urls = [pg.url for pg in ctx.pages if pg.url not in before]
    print("=== CLICKED ===", clicked)
    print("=== NEW_TABS ===")
    for u in new_urls:
        print(u)
    print("=== ALL_TABS ===")
    for pg in ctx.pages:
        print(pg.url[:160])
