#!/usr/bin/env python3
"""
Deep inspect of Ripple page - find where the form is and how to access it.
"""
import time, json
from patchright.sync_api import sync_playwright

DEBUG_PORT = 9404

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(f"http://localhost:{DEBUG_PORT}")
    ctx = browser.contexts[0]

    page = ctx.new_page()
    page.set_default_timeout(30000)

    # Navigate fresh
    print("Loading Ripple careers page...")
    try:
        page.goto("https://ripple.com/careers/all-jobs/job/7951682/?gh_jid=7951682",
                  wait_until="networkidle", timeout=45000)
    except Exception as e:
        print(f"  timeout: {e}")
    time.sleep(6)

    print(f"URL: {page.url}")
    print(f"Title: {page.title()}")
    print(f"Frames count: {len(page.frames)}")
    for i, fr in enumerate(page.frames):
        print(f"  [{i}] {fr.url!r}")

    # Accept cookies
    try:
        btn = page.get_by_text("Accept Cookies").first
        if btn.is_visible(timeout=2000):
            btn.click(); time.sleep(1)
            print("Accepted cookies")
    except: pass

    # Find ALL iframes including lazy-loaded ones
    iframes = page.evaluate("""() => {
        const iframes = document.querySelectorAll('iframe');
        return [...iframes].map(f => ({
            src: f.src,
            srcdoc: (f.srcdoc||'').substring(0,100),
            id: f.id,
            className: f.className,
            width: f.width,
            height: f.height,
            loaded: f.contentDocument !== null
        }));
    }""")
    print(f"\nDOM iframes ({len(iframes)}):")
    for iframe in iframes:
        print(f"  src={iframe['src']!r}, id={iframe['id']!r}, loaded={iframe['loaded']}")

    # Find forms
    forms = page.evaluate("""() => {
        return [...document.querySelectorAll('form')].map(f => ({
            id: f.id,
            action: f.action,
            inputs: [...f.querySelectorAll('input,textarea,select')].length
        }));
    }""")
    print(f"\nForms ({len(forms)}):")
    for form in forms:
        print(f"  id={form['id']!r} action={form['action']!r} inputs={form['inputs']}")

    # Scroll down to trigger lazy loading
    print("\nScrolling to trigger lazy load...")
    page.evaluate("window.scrollTo(0, 600)")
    time.sleep(3)
    page.evaluate("window.scrollTo(0, 1200)")
    time.sleep(3)

    # Re-check iframes after scroll
    iframes2 = page.evaluate("""() => {
        const iframes = document.querySelectorAll('iframe');
        return [...iframes].map(f => ({src: f.src, id: f.id, loaded: f.contentDocument !== null}));
    }""")
    print(f"\nDOM iframes after scroll ({len(iframes2)}):")
    for iframe in iframes2:
        print(f"  src={iframe['src']!r}")

    # Check frames again
    print(f"\nFrames after scroll: {len(page.frames)}")
    for i, fr in enumerate(page.frames):
        print(f"  [{i}] {fr.url!r}")

    # Look for any buttons/links that might reveal the application form
    buttons = page.evaluate("""() => {
        return [...document.querySelectorAll('a, button')].filter(b => {
            const t = (b.textContent||b.innerText||'').toLowerCase();
            return t.includes('apply') || t.includes('application') || t.includes('submit');
        }).map(b => ({tag:b.tagName, text:(b.textContent||'').trim().substring(0,60), href:b.href||''}));
    }""")
    print(f"\nApply-related buttons/links ({len(buttons)}):")
    for btn in buttons[:10]:
        print(f"  {btn['tag']}: {btn['text']!r} href={btn['href']!r}")

    # Try clicking the Application tab if visible
    try:
        app_tab = page.get_by_text("Application", exact=True).first
        if app_tab.is_visible(timeout=2000):
            app_tab.click()
            time.sleep(3)
            print("\nClicked 'Application' tab")
    except: pass

    # Check for the form section by scrolling to it
    try:
        app_section = page.locator("#application, .application, [data-testid*='application']").first
        if app_section.count() > 0:
            app_section.scroll_into_view_if_needed()
            time.sleep(2)
            print("Scrolled to application section")
    except: pass

    # Final iframe check
    iframes3 = page.evaluate("""() => {
        const iframes = document.querySelectorAll('iframe');
        return [...iframes].map(f => ({src: f.src, loaded: f.contentDocument !== null}));
    }""")
    print(f"\nFinal iframe check ({len(iframes3)}):")
    for iframe in iframes3:
        print(f"  src={iframe['src']!r}")

    # Frames check
    print(f"\nFinal frames: {len(page.frames)}")
    for i, fr in enumerate(page.frames):
        print(f"  [{i}] {fr.url!r}")

    page.screenshot(path=r"C:\Users\chent\Agentic_Workflows_2026\oracle-job-search\outputs\2026-06-12-feed-first\applications\ripple_dei_pm\screenshots\inspect_v2.png", full_page=True)
    print("\nScreenshot saved.")

    # Get full page HTML to understand structure
    html = page.content()
    # Find the section with the form
    gh_idx = html.lower().find("greenhouse")
    print(f"\n'greenhouse' in page HTML at index: {gh_idx}")
    if gh_idx >= 0:
        print(f"  context: {html[max(0,gh_idx-200):gh_idx+400]}")
