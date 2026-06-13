# -*- coding: utf-8 -*-
"""
inspect_bcg_apply.py
Inspect the BCG JD page: dump the Apply button href, cookie overlay details,
and all Workday-related links. Helps build the v3 script.
"""
import os, sys, time, json, subprocess
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, r"C:\Users\chent\Agentic_Workflows_2026\jamie-autopilot\lib")
from patchright.sync_api import sync_playwright

PORT = 9402
PROFILE = r"C:\Users\chent\ats_agent_9402"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
JOB_URL = "https://careers.bcg.com/global/en/job/57988/Talent-Senior-Specialist-People"
SHOT = r"C:\Users\chent\Agentic_Workflows_2026\oracle-job-search\outputs\2026-06-12-feed-first\applications\bcg_talent_sr_specialist\screenshots"

def shot(page, name):
    path = os.path.join(SHOT, name + ".png")
    try:
        page.screenshot(path=path, full_page=True)
        print(f"  [ss] {name}.png")
    except Exception as e:
        print(f"  [ss FAIL] {e}")

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
     "--no-first-run", "--no-default-browser-check", JOB_URL],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
)
time.sleep(8)

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(f"http://localhost:{PORT}")
    ctx = browser.contexts[0]
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    page.set_default_timeout(20000)

    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except:
        pass
    time.sleep(3)
    shot(page, "inspect_01_loaded")

    # 1. Dump all buttons
    buttons = page.evaluate("""
    Array.from(document.querySelectorAll('button, a[role="button"], [role="button"]')).map(el => ({
        tag: el.tagName,
        text: el.textContent.trim().substring(0, 80),
        href: el.href || el.getAttribute('href') || '',
        ariaLabel: el.getAttribute('aria-label') || '',
        dataAttr: el.getAttribute('data-automation-id') || el.getAttribute('data-ph-at-id') || '',
        visible: el.getBoundingClientRect().height > 0,
        id: el.id || ''
    }))
    """)
    print("\n=== ALL BUTTONS/LINKS ===")
    for b in buttons:
        if b.get('visible') or b.get('text'):
            print(f"  [{b.get('tag')}] text={b.get('text')[:60]} | href={b.get('href')[:80]} | aria={b.get('ariaLabel')[:60]} | data={b.get('dataAttr')}")

    # 2. Specifically find Apply buttons
    apply_links = page.evaluate("""
    Array.from(document.querySelectorAll('a, button')).filter(el =>
        /apply/i.test(el.textContent) || /apply/i.test(el.getAttribute('aria-label') || '')
        || /apply/i.test(el.getAttribute('href') || '')
    ).map(el => ({
        tag: el.tagName,
        text: el.textContent.trim().substring(0, 80),
        href: el.href || el.getAttribute('href') || '',
        ariaLabel: el.getAttribute('aria-label') || '',
        outerHTML: el.outerHTML.substring(0, 300)
    }))
    """)
    print("\n=== APPLY LINKS ===")
    for a in apply_links:
        print(f"  [{a.get('tag')}] {a.get('text')[:50]} | {a.get('href')[:100]}")
        print(f"    HTML: {a.get('outerHTML')[:200]}")

    # 3. Cookie overlays
    overlays = page.evaluate("""
    Array.from(document.querySelectorAll('[id*="truste"], [id*="cookie"], [class*="truste"], [class*="cookie"], [class*="overlay"]')).map(el => ({
        id: el.id,
        class: el.className.toString().substring(0, 80),
        display: window.getComputedStyle(el).display,
        visibility: window.getComputedStyle(el).visibility,
        pointerEvents: window.getComputedStyle(el).pointerEvents,
        zIndex: window.getComputedStyle(el).zIndex
    }))
    """)
    print("\n=== COOKIE/OVERLAY ELEMENTS ===")
    for o in overlays:
        print(f"  id={o.get('id')} | class={o.get('class')[:50]} | display={o.get('display')} | pe={o.get('pointerEvents')} | z={o.get('zIndex')}")

    # 4. Dismiss cookie and try Apply via JS
    print("\n=== DISMISSING COOKIE BANNER ===")
    dismiss_result = page.evaluate("""
    (function() {
        // Try clicking any accept/close button in cookie banners
        var sels = [
            '#truste-consent-button', '#truste-agree-btn',
            '.truste_acceptAll', '[id*="accept"]',
            'button[title*="Accept"]', 'button[title*="accept"]',
            '#onetrust-accept-btn-handler',
        ];
        for (var sel of sels) {
            var el = document.querySelector(sel);
            if (el) { el.click(); return 'clicked: ' + sel; }
        }
        // Hide overlays
        var overlays = document.querySelectorAll('[id*="truste"], [class*="truste_overlay"]');
        overlays.forEach(function(o) { o.style.display = 'none'; });
        return 'hidden: ' + overlays.length + ' overlays';
    })()
    """)
    print(f"  Cookie dismiss: {dismiss_result}")
    time.sleep(2)
    shot(page, "inspect_02_after_dismiss")

    # 5. Get the Apply button href via JS
    apply_href = page.evaluate("""
    (function() {
        var candidates = Array.from(document.querySelectorAll('a, button'));
        for (var el of candidates) {
            var txt = el.textContent.trim();
            var label = el.getAttribute('aria-label') || '';
            if ((txt === 'APPLY' || txt === 'Apply' || txt === 'Apply Now' ||
                 label.toLowerCase().includes('apply')) &&
                !label.toLowerCase().includes('similar') &&
                !label.toLowerCase().includes('notify') &&
                !label.toLowerCase().includes('subscribe')) {
                return {
                    tag: el.tagName,
                    text: txt,
                    href: el.href || el.getAttribute('href') || '',
                    outerHTML: el.outerHTML.substring(0, 400)
                };
            }
        }
        return null;
    })()
    """)
    print(f"\n=== PRIMARY APPLY BUTTON ===")
    print(json.dumps(apply_href, indent=2, ensure_ascii=False))

    # 6. Try clicking the Apply button after cookie dismiss
    print("\n=== ATTEMPTING APPLY CLICK ===")
    try:
        # Force-click via JS (bypasses overlay)
        clicked = page.evaluate("""
        (function() {
            var candidates = Array.from(document.querySelectorAll('a, button'));
            for (var el of candidates) {
                var txt = el.textContent.trim();
                var label = el.getAttribute('aria-label') || '';
                if ((txt === 'APPLY' || txt === 'Apply' || txt === 'Apply Now' ||
                     label.toLowerCase() === 'apply') &&
                    !label.toLowerCase().includes('similar') &&
                    !label.toLowerCase().includes('subscribe')) {
                    el.click();
                    return 'js-clicked: ' + txt + ' | href=' + (el.href || el.getAttribute('href') || 'none');
                }
            }
            return null;
        })()
        """)
        print(f"  JS click result: {clicked}")
        time.sleep(5)
        try:
            page.wait_for_load_state("networkidle", timeout=10000)
        except:
            pass
        print(f"  URL after click: {page.url}")
        shot(page, "inspect_03_after_apply_click")
        print(f"  Page text: {page.inner_text('body')[:400]}")
    except Exception as e:
        print(f"  Click error: {e}")

    browser.close()

print("\nDone. Check screenshots.")
