# -*- coding: utf-8 -*-
"""
inspect_bcg_phenom.py
Navigate directly to BCG's Phenom careerhub apply URL and inspect the flow.
"""
import os, sys, time, json, subprocess
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, r"C:\Users\chent\Agentic_Workflows_2026\jamie-autopilot\lib")
from patchright.sync_api import sync_playwright

PORT = 9402
PROFILE = r"C:\Users\chent\ats_agent_9402"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
SHOT = r"C:\Users\chent\Agentic_Workflows_2026\oracle-job-search\outputs\2026-06-12-feed-first\applications\bcg_talent_sr_specialist\screenshots"

# BCG uses Phenom (experiencedtalent.bcg.com), not Workday
# Direct apply URL extracted from JD page inspection
PHENOM_APPLY_URL = "https://experiencedtalent.bcg.com/careerhub/explore/jobs/790315808241?post_onboarding_pid=790315808241&show_apply=1&profile_type=candidate&customredirect=1"

def shot(page, name):
    path = os.path.join(SHOT, name + ".png")
    try:
        page.screenshot(path=path, full_page=True)
        print(f"  [ss] {name}.png")
    except Exception as e:
        print(f"  [ss FAIL] {e}")

def wait_net(page, t=12000):
    try: page.wait_for_load_state("networkidle", timeout=t)
    except: pass

def dismiss_cookie(page):
    # Hide TrustArc overlays via JS
    result = page.evaluate("""
    (function() {
        var hidden = 0;
        document.querySelectorAll(
            '[id*="truste"], [class*="truste_overlay"], [class*="truste_box"],
            [id*="onetrust"], .onetrust-pc-dark-filter,
            #teconsent, .cc-overlay, [class*="cookie-overlay"]'
        ).forEach(function(el) {
            el.style.display = 'none';
            el.style.visibility = 'hidden';
            el.style.pointerEvents = 'none';
            hidden++;
        });
        // Also try clicking accept buttons
        var btns = ['#truste-consent-button', '#onetrust-accept-btn-handler',
                    '.truste_acceptAll', 'button[id*="accept"]'];
        for (var sel of btns) {
            var b = document.querySelector(sel);
            if (b) { b.click(); return 'clicked: ' + sel; }
        }
        return 'hidden: ' + hidden;
    })()
    """)
    print(f"  [cookie] {result}")

# Kill stale Chrome
subprocess.run(
    ["powershell", "-Command",
     f"Get-NetTCPConnection -LocalPort {PORT} -ErrorAction SilentlyContinue | "
     f"Select-Object -ExpandProperty OwningProcess | "
     f"ForEach-Object {{ Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }}"],
    capture_output=True, timeout=10
)
time.sleep(2)

proc = subprocess.Popen(
    [CHROME, f"--remote-debugging-port={PORT}", f"--user-data-dir={PROFILE}",
     "--no-first-run", "--no-default-browser-check",
     PHENOM_APPLY_URL],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
)
print(f"Chrome PID: {proc.pid}, waiting 10s...")
time.sleep(10)

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(f"http://localhost:{PORT}")
    ctx = browser.contexts[0]
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    page.set_default_timeout(30000)

    try:
        wait_net(page, 20000)
        time.sleep(3)
        print(f"URL: {page.url}")
        print(f"Title: {page.title()}")
        shot(page, "phenom_01_loaded")

        page_text = page.inner_text("body")
        print(f"Page text (first 500):\n{page_text[:500]}")

        # Dismiss cookie
        dismiss_cookie(page)
        time.sleep(2)

        # Dump all inputs and forms
        inputs = page.evaluate("""
        Array.from(document.querySelectorAll('input, select, textarea, button')).map(el => ({
            tag: el.tagName,
            type: el.type || '',
            id: el.id || '',
            name: el.name || '',
            placeholder: el.placeholder || '',
            ariaLabel: el.getAttribute('aria-label') || '',
            value: el.tagName === 'INPUT' ? el.value : '',
            visible: el.getBoundingClientRect().height > 0,
            text: el.textContent.trim().substring(0, 60)
        })).filter(el => el.visible)
        """)
        print("\n=== VISIBLE INPUTS/BUTTONS ===")
        for inp in inputs:
            print(f"  [{inp.get('tag')}:{inp.get('type')}] id={inp.get('id')[:30]} name={inp.get('name')[:30]} aria={inp.get('ariaLabel')[:50]} text={inp.get('text')[:50]}")

        # Dump all links on this page
        links = page.evaluate("""
        Array.from(document.querySelectorAll('a[href]')).map(el => ({
            text: el.textContent.trim().substring(0, 80),
            href: el.href || '',
        })).filter(el => el.href && el.text)
        """)
        print("\n=== LINKS ===")
        for lnk in links[:30]:
            print(f"  {lnk.get('text')[:60]} | {lnk.get('href')[:100]}")

        shot(page, "phenom_02_after_cookie")

        # Check if there's a sign in / create account option
        page_text2 = page.inner_text("body")
        print(f"\nFull page text:\n{page_text2[:2000]}")

    except Exception as e:
        print(f"Exception: {e}")

    browser.close()

print("\nDone.")
