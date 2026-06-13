#!/usr/bin/env python3
"""Quick check of what's in the CDP right now."""
import time
from patchright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://localhost:9404")
    ctx = browser.contexts[0]
    print(f"Pages: {len(ctx.pages)}")
    for i, pg in enumerate(ctx.pages):
        print(f"  [{i}] {pg.url!r}")
        print(f"    frames: {len(pg.frames)}")
        for j, fr in enumerate(pg.frames):
            print(f"      [{j}] {fr.url!r}")

    # Find ripple page
    ripple = None
    for pg in ctx.pages:
        if "ripple" in pg.url:
            ripple = pg; break

    if ripple:
        print(f"\nRipple page ready state: {ripple.evaluate('() => document.readyState')}")
        # Get all iframe srcs
        iframes = ripple.evaluate("""() => [...document.querySelectorAll('iframe')].map(f=>({src:f.src,id:f.id}))""")
        print(f"\nIframes in DOM: {iframes}")
        ripple.screenshot(path=r"C:\Users\chent\Agentic_Workflows_2026\oracle-job-search\outputs\2026-06-12-feed-first\applications\ripple_dei_pm\screenshots\live_check.png", full_page=True)
        print("Screenshot saved")
