"""Check what the current Chrome tab shows - was the form submitted?"""
import sys, time, json
from pathlib import Path
sys.path.insert(0, str(Path(r"C:\Users\chent\Agentic_Workflows_2026\jamie-autopilot\lib")))
from patchright.sync_api import sync_playwright

PROFILE_DIR = r"C:\Users\chent\ats_agent_9410"

lock = Path(PROFILE_DIR) / "Default" / "LOCK"
if lock.exists():
    try: lock.unlink()
    except: pass

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        user_data_dir=PROFILE_DIR, channel="chrome", headless=False, no_viewport=True,
        args=["--remote-debugging-port=9410"], ignore_default_args=["--enable-automation"],
    )
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    # Don't navigate - just check current state
    time.sleep(2)

    print(f"URL: {page.url}")
    print(f"Title: {page.title()}")

    body = page.inner_text("body")
    print(f"\nFull body text:\n{body[:2000]}")

    # Also check for specific success/error indicators
    checks = page.evaluate('''() => {
        const body = document.body;
        const text = body.innerText || "";
        return {
            has_thank_you: text.toLowerCase().includes("thank you"),
            has_submitted: text.toLowerCase().includes("submitted"),
            has_received: text.toLowerCase().includes("received your application"),
            has_apply_button: !!document.querySelector('a[href*="apply"], button[type="submit"]'),
            has_form: !!document.querySelector("form"),
            has_errors: [...document.querySelectorAll(".error,[class*=error]")].map(e => (e.innerText||"").trim().substring(0,60)).filter(t=>t.length>3),
            page_h1: document.querySelector("h1")?.innerText||"",
            page_h2: document.querySelector("h2")?.innerText||"",
        };
    }''')
    print(f"\nPage checks: {json.dumps(checks, indent=2)}")

    # Take a screenshot of just the top 800px
    page.evaluate("window.scrollTo(0,0)")
    time.sleep(0.5)
    page.screenshot(path=r"C:\Users\chent\Agentic_Workflows_2026\oracle-job-search\outputs\2026-06-12-feed-first\applications\twitch_culture_people_pm\screenshots\current_state.png")
    print("\nScreenshot: current_state.png")

    time.sleep(3)
    ctx.close()
