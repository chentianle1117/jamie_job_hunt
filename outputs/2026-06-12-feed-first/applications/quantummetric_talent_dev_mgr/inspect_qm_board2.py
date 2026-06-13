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

def safe(s):
    return s.encode("ascii", "replace").decode("ascii")

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

        # Get title and URL
        print(f"Title: {safe(page.title())}")
        print(f"URL: {page.url}")

        # Extract all postings via JS
        postings = page.evaluate('''() => {
            const out = [];
            // Try various Lever selectors
            const selectors = [
                "[data-qa='posting-name']",
                ".posting-title",
                ".posting-name",
                "h5",
                "a[href*='lever.co']",
            ];
            const seen = new Set();
            for (const sel of selectors) {
                document.querySelectorAll(sel).forEach(el => {
                    const href = el.getAttribute("href") || (el.tagName === "A" ? "" : "");
                    const txt = (el.textContent || "").trim();
                    if (txt && !seen.has(txt)) {
                        seen.add(txt);
                        out.push({text: txt.substring(0, 200), href: (href || "").substring(0, 200)});
                    }
                });
            }
            return out;
        }''')

        print(f"\nTotal postings found: {len(postings)}")
        for p2 in postings:
            print(f"  [{safe(p2['text'])!r}] -> {safe(p2['href'])!r}")

        # Also get the full page text and save to file
        board_text = page.inner_text("body")
        board_text_safe = board_text.encode("ascii", "replace").decode("ascii")
        print(f"\n=== Board text excerpt (first 2000 chars) ===")
        print(board_text_safe[:2000])

        # Save full board text
        board_file = OUT_DIR.parent / "board_text.txt"
        with open(board_file, "w", encoding="utf-8") as f:
            f.write(board_text)
        print(f"\nFull board text saved to {board_file}")

        browser.close()

if __name__ == "__main__":
    main()
