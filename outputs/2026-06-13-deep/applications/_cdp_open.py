"""Attach to debug Chrome (CDP), open OWN tab, navigate to URL, dump text + apply link.
Usage: python _cdp_open.py <port> <url> [wait_ms]
Prints: TITLE, URL(final), then page innertext (truncated), then any 'apply' anchor hrefs.
Never closes other tabs.
"""
import sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from patchright.sync_api import sync_playwright

port = sys.argv[1]
url = sys.argv[2]
wait_ms = int(sys.argv[3]) if len(sys.argv) > 3 else 3500

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(f"http://localhost:{port}")
    ctx = browser.contexts[0]
    page = ctx.new_page()  # OWN tab
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(wait_ms)
        print("=== FINAL_URL ===")
        print(page.url)
        print("=== TITLE ===")
        print(page.title())
        # try to expand "see more" on LinkedIn JD
        for sel in ["button:has-text('See more')", "button:has-text('Show more')", "button[aria-label*='see more' i]"]:
            try:
                el = page.query_selector(sel)
                if el:
                    el.click(timeout=1500)
                    page.wait_for_timeout(600)
            except Exception:
                pass
        print("=== TEXT ===")
        txt = page.inner_text("body")
        print(txt[:9000])
        print("=== APPLY_LINKS ===")
        anchors = page.query_selector_all("a")
        seen = set()
        for a in anchors:
            try:
                href = a.get_attribute("href") or ""
                t = (a.inner_text() or "").strip().lower()
            except Exception:
                continue
            if not href:
                continue
            if ("apply" in t or "apply" in href.lower()) and href not in seen:
                seen.add(href)
                print(f"[{t[:30]}] {href[:160]}")
    finally:
        # leave the tab open (do not close) for follow-up driving
        pass
