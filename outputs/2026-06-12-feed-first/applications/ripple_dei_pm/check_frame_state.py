#!/usr/bin/env python3
"""Check the current state of the Greenhouse frame after submit attempt."""
import time
from patchright.sync_api import sync_playwright

DEBUG_PORT = 9404

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(f"http://localhost:{DEBUG_PORT}")
    ctx = browser.contexts[0]

    # Find the ripple page
    ripple_page = None
    for pg in ctx.pages:
        if "ripple" in pg.url:
            ripple_page = pg
            break

    if not ripple_page:
        print("No Ripple page found")
        exit()

    # Find the GH frame
    gh_fr = None
    for fr in ripple_page.frames:
        if "greenhouse.io" in fr.url and "embed" in fr.url:
            gh_fr = fr
            break

    if not gh_fr:
        print("No GH frame found")
        print(f"Frames: {[f.url for f in ripple_page.frames]}")
        exit()

    print(f"GH frame URL: {gh_fr.url[:80]}")

    # Get full frame body
    try:
        body = gh_fr.inner_text("body")
        print(f"\nFrame body (full):\n{body[:5000]}")
    except Exception as e:
        print(f"body err: {e}")

    # Check for error messages
    try:
        errors = gh_fr.locator('.error, [class*="error"], .field-error, [aria-invalid="true"]').all()
        print(f"\nError elements: {len(errors)}")
        for e in errors[:20]:
            t = (e.text_content() or "").strip()
            if t: print(f"  - {t[:200]}")
    except Exception as e:
        print(f"errors err: {e}")

    # Check for success indicators
    try:
        success_text = gh_fr.evaluate("""() => {
            const body = document.body.innerText.toLowerCase();
            return {
                has_thank_you: body.includes('thank you'),
                has_received: body.includes('received'),
                has_submitted: body.includes('submitted'),
                has_application: body.includes('application'),
                has_form: document.querySelector('form') !== null,
                has_first_name: document.getElementById('first_name') !== null,
                first_name_visible: document.getElementById('first_name')?.getBoundingClientRect().width > 0,
                title: document.title,
                h1: document.querySelector('h1')?.innerText || '',
                h2: document.querySelector('h2')?.innerText || '',
                // Check submit button state
                submit_btns: [...document.querySelectorAll('button, input[type=submit]')]
                    .map(b => ({text:(b.textContent||b.value||'').trim().substring(0,30), disabled:b.disabled})),
            };
        }""")
        print(f"\nState check: {success_text}")
    except Exception as e:
        print(f"state check err: {e}")

    # Screenshot
    ripple_page.screenshot(path=r"C:\Users\chent\Agentic_Workflows_2026\oracle-job-search\outputs\2026-06-12-feed-first\applications\ripple_dei_pm\screenshots\check_frame.png", full_page=True)
    print("\nScreenshot saved to check_frame.png")
