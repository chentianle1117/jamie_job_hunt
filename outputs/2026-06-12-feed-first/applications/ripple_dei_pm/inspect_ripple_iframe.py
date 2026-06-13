#!/usr/bin/env python3
"""
Inspect the Ripple page iframe structure + find the Greenhouse form frame.
"""
import time
from patchright.sync_api import sync_playwright

DEBUG_PORT = 9404

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(f"http://localhost:{DEBUG_PORT}")
    ctx = browser.contexts[0]

    # Find the Ripple page
    ripple_page = None
    for pg in ctx.pages:
        if "ripple.com" in pg.url:
            ripple_page = pg
            break

    if not ripple_page:
        ripple_page = ctx.new_page()
        ripple_page.goto("https://ripple.com/careers/all-jobs/job/7951682/?gh_jid=7951682",
                          wait_until="networkidle", timeout=45000)
        time.sleep(4)

    print(f"Page URL: {ripple_page.url}")
    print(f"Page title: {ripple_page.title()}")
    print(f"\nAll frames ({len(ripple_page.frames)}):")
    for i, fr in enumerate(ripple_page.frames):
        print(f"  [{i}] url={fr.url!r}")

    # Try to find the Greenhouse frame
    gh_frame = None
    for fr in ripple_page.frames:
        if "greenhouse" in fr.url.lower() or "job-boards" in fr.url.lower() or "job_app" in fr.url.lower():
            gh_frame = fr
            print(f"\n  -> Found Greenhouse frame: {fr.url}")
            break

    if not gh_frame:
        print("\n  No Greenhouse frame found directly. Checking iframes in DOM...")
        iframes = ripple_page.query_selector_all("iframe")
        for iframe in iframes:
            src = iframe.get_attribute("src") or ""
            print(f"  iframe src={src!r}")

    if gh_frame:
        print("\nScanning form fields in Greenhouse frame...")
        try:
            fields = gh_frame.query_selector_all("input, textarea, select")
            print(f"  {len(fields)} fields found:")
            for f in fields:
                fid = f.get_attribute("id") or ""
                ftype = f.get_attribute("type") or f.tag_name
                fvis = f.is_visible()
                print(f"    id={fid!r:<40} type={ftype!r:<20} visible={fvis}")
        except Exception as e:
            print(f"  err: {e}")

        # Screenshot
        ripple_page.screenshot(path=r"C:\Users\chent\Agentic_Workflows_2026\oracle-job-search\outputs\2026-06-12-feed-first\applications\ripple_dei_pm\screenshots\inspect_01.png", full_page=True)
        print("\nScreenshot saved.")
    else:
        print("\n[ERROR] Could not locate Greenhouse frame")
        # Try direct navigation to greenhouse embed
        print("Trying direct Greenhouse URL...")
        ripple_page.goto("https://boards.greenhouse.io/ripple/jobs/7951682",
                          wait_until="networkidle", timeout=30000)
        time.sleep(3)
        print(f"  redirected to: {ripple_page.url}")
        print(f"  title: {ripple_page.title()}")
        print(f"  frames after nav: {len(ripple_page.frames)}")
        for i, fr in enumerate(ripple_page.frames):
            print(f"    [{i}] {fr.url!r}")
        ripple_page.screenshot(path=r"C:\Users\chent\Agentic_Workflows_2026\oracle-job-search\outputs\2026-06-12-feed-first\applications\ripple_dei_pm\screenshots\inspect_02_direct.png", full_page=True)
