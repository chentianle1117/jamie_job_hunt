"""
Inspect Quantum Metric job board — find all open roles.
"""
import sys, time, json
from pathlib import Path

sys.path.insert(0, r"C:\Users\chent\Agentic_Workflows_2026\jamie-autopilot\lib")
from patchright.sync_api import sync_playwright

BOARD_URL = "https://jobs.lever.co/quantummetric"
PROFILE_DIR = r"C:\Users\chent\ats_agent_9409"
OUT_DIR = Path(r"C:\Users\chent\Agentic_Workflows_2026\oracle-job-search\outputs\2026-06-12-feed-first\applications\quantummetric_talent_dev_mgr\screenshots")
OUT_DIR.mkdir(exist_ok=True)

def main():
    with sync_playwright() as p:
        lock = Path(PROFILE_DIR) / "Default" / "LOCK"
        if lock.exists():
            try: lock.unlink()
            except: pass

        browser = p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_DIR,
            channel="chrome",
            headless=False,
            no_viewport=True,
            args=["--start-maximized"],
        )
        page = browser.pages[0] if browser.pages else browser.new_page()
        page.set_default_timeout(25000)

        print(f"Loading board: {BOARD_URL}")
        page.goto(BOARD_URL, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(5000)
        page.screenshot(path=str(OUT_DIR / "board_full.png"), full_page=True)

        # Get full board HTML
        board_html = page.content()
        board_text = page.inner_text("body")

        print(f"\n=== Board text (first 3000 chars) ===")
        print(board_text[:3000])

        # Try multiple selectors for role listings
        print("\n=== Checking selectors ===")
        selectors_to_try = [
            "a[data-qa='posting-name']",
            ".posting-title",
            ".posting-name",
            "h5.posting-title",
            "a[href*='/jobs.lever.co']",
            "a[href*='lever.co']",
            ".posting",
            "[class*='posting']",
            "li[class*='posting']",
        ]
        for sel in selectors_to_try:
            try:
                count = page.locator(sel).count()
                if count > 0:
                    print(f"  {sel}: {count} elements")
                    items = page.locator(sel).all()
                    for item in items[:5]:
                        txt = (item.text_content() or "").strip()[:100]
                        href = item.get_attribute("href") or ""
                        print(f"    - {txt!r} href={href[:80]!r}")
            except Exception as e:
                print(f"  {sel}: ERR {e}")

        # Get all links on the page
        print("\n=== All lever.co links ===")
        links = page.locator("a[href*='lever.co']").all()
        print(f"  Total lever.co links: {len(links)}")
        for l in links[:30]:
            href = l.get_attribute("href") or ""
            txt = (l.text_content() or "").strip()[:100]
            print(f"  [{txt!r}] -> {href}")

        page.screenshot(path=str(OUT_DIR / "board_inspect.png"), full_page=True)
        browser.close()

if __name__ == "__main__":
    main()
