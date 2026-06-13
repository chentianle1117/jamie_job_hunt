"""Inspect react portal and iti__selected-country button."""
import sys, time, json
from pathlib import Path
sys.path.insert(0, str(Path(r"C:\Users\chent\Agentic_Workflows_2026\jamie-autopilot\lib")))
from patchright.sync_api import sync_playwright

URL = "https://job-boards.greenhouse.io/twitch/jobs/8582338002"
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
    page.goto(URL, wait_until="domcontentloaded", timeout=40000)
    time.sleep(5)

    # 1. Check the portal mount point
    portal_info = page.evaluate('''() => {
        const portal = document.getElementById("react-portal-mount-point");
        if (!portal) return {err: "no portal"};
        return {
            tag: portal.tagName,
            children: portal.children.length,
            innerHTML_before_open: portal.innerHTML.substring(0, 200)
        };
    }''')
    print("Portal before open:", json.dumps(portal_info))

    # 2. Scroll to phone, click iti__selected-country button
    page.evaluate("() => { document.getElementById('phone')?.scrollIntoView({block:'center'}); }")
    time.sleep(1.0)

    iti_btn_info = page.evaluate('''() => {
        const btn = document.querySelector(".iti__selected-country");
        if (!btn) return {err: "no .iti__selected-country"};
        const r = btn.getBoundingClientRect();
        const cls = Array.from(btn.classList).join(" ");
        return {tag: btn.tagName, cls, x:Math.round(r.x), y:Math.round(r.y), w:Math.round(r.width), h:Math.round(r.height)};
    }''')
    print("ITI button (.iti__selected-country):", json.dumps(iti_btn_info))

    # Click it
    page.locator(".iti__selected-country").click(force=True)
    time.sleep(1.0)

    iti_after = page.evaluate('''() => {
        const dropdown = document.getElementById("iti-0__dropdown-content");
        const hidden = dropdown ? Array.from(dropdown.classList).includes("iti__hide") : null;
        const search = document.getElementById("iti-0__search-input");
        const r = search ? search.getBoundingClientRect() : null;
        return {
            dropdown_exists: !!dropdown,
            dropdown_hidden: hidden,
            search_visible: search ? r.width > 0 : null,
            search_x: r ? Math.round(r.x) : null,
            search_y: r ? Math.round(r.y) : null,
        };
    }''')
    print("ITI after click:", json.dumps(iti_after))

    page.screenshot(path=r"C:\Users\chent\Agentic_Workflows_2026\oracle-job-search\outputs\2026-06-12-feed-first\applications\twitch_culture_people_pm\screenshots\inspect_iti_btn.png")
    print("Screenshot: inspect_iti_btn.png")

    # If dropdown opened, search for US
    if not iti_after.get('dropdown_hidden', True):
        print("ITI: dropdown OPEN! Searching...")
        page.fill("#iti-0__search-input", "United States")
        time.sleep(1.0)
        items = page.locator(".iti__country")
        n = items.count()
        print(f"ITI countries found: {n}")
        for i in range(min(n, 20)):
            try:
                txt = items.nth(i).inner_text().strip()
                if "united states" in txt.lower() and "territories" not in txt.lower() and "island" not in txt.lower() and "samoa" not in txt.lower():
                    items.nth(i).click()
                    time.sleep(0.5)
                    print(f"ITI: selected {txt!r}")
                    break
            except: continue

    # 3. Now open q894 and inspect the portal
    print("\nOpening q894...")
    page.evaluate("() => { document.getElementById('question_36848894002')?.scrollIntoView({block:'center'}); }")
    time.sleep(0.5)
    page.evaluate('''() => {
        const inp = document.getElementById("question_36848894002");
        if (!inp) return;
        let el = inp;
        for (let i=0; i<12; i++) {
            el = el.parentElement; if(!el) return;
            const ctrl = el.querySelector(".select__control");
            if (ctrl) { ctrl.dispatchEvent(new MouseEvent("mousedown",{bubbles:true})); ctrl.click(); return; }
        }
    }''')
    time.sleep(2.0)

    portal_after = page.evaluate('''() => {
        const portal = document.getElementById("react-portal-mount-point");
        if (!portal) return {err: "no portal"};
        const allChildren = [...portal.querySelectorAll("*")];
        const interesting = allChildren.filter(e => e.children.length > 0 || (e.innerText||"").trim().length > 0);
        const summary = interesting.slice(0, 20).map(el => {
            const cls = Array.from(el.classList).join(" ");
            const r = el.getBoundingClientRect();
            return {tag: el.tagName, cls: cls.substring(0,80), id: el.id, text: (el.innerText||"").trim().substring(0,60), x:Math.round(r.x), y:Math.round(r.y), w:Math.round(r.width), h:Math.round(r.height)};
        });
        return {
            portal_html_len: portal.innerHTML.length,
            portal_children: portal.children.length,
            interesting_count: interesting.length,
            first_interesting: summary
        };
    }''')
    print("\nPortal after opening q894:")
    print(json.dumps(portal_after, indent=2))

    # Check for any options in the portal
    opts_in_portal = page.evaluate('''() => {
        const portal = document.getElementById("react-portal-mount-point");
        if (!portal) return [];
        // Look for all divs/spans with role="option" or class containing "option"
        const opts = portal.querySelectorAll('[role="option"], [class*="option"], li');
        return [...opts].slice(0, 20).map(el => {
            const cls = Array.from(el.classList).join(" ");
            return {tag: el.tagName, cls: cls.substring(0,60), text: (el.innerText||"").trim().substring(0,60)};
        });
    }''')
    print("\nOptions in portal:", json.dumps(opts_in_portal[:10], indent=2))

    page.screenshot(path=r"C:\Users\chent\Agentic_Workflows_2026\oracle-job-search\outputs\2026-06-12-feed-first\applications\twitch_culture_people_pm\screenshots\inspect_portal_q894.png")
    print("Screenshot: inspect_portal_q894.png")

    time.sleep(3)
    ctx.close()
