"""Inspect the ITI widget and figure out why .iti__selected-flag doesn't exist.
Also check the react-select dropdown isolation issue."""
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

    # 1. Find ALL elements with iti in their class
    iti_info = page.evaluate('''() => {
        const results = [];
        // All elements with 'iti' in className
        document.querySelectorAll('[class*="iti"]').forEach(el => {
            const r = el.getBoundingClientRect();
            results.push({
                tag: el.tagName, id: el.id,
                class: (el.className||"").substring(0,100),
                x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height),
                children: el.children.length
            });
        });
        // Also look for phone-input
        const phone = document.querySelector('.phone-input, fieldset.phone-input');
        return {
            iti_elements: results.slice(0, 30),
            phone_fieldset: phone ? {
                class: phone.className,
                innerHTML_len: phone.innerHTML.length,
                inputs: [...phone.querySelectorAll('input, select, button')].map(e => ({
                    tag: e.tagName, id: e.id, type: e.type, class: (e.className||"").substring(0,60)
                }))
            } : null
        };
    }''')
    print("ITI / phone inspection:")
    print(json.dumps(iti_info, indent=2))

    # 2. Scroll to phone field and inspect again
    page.evaluate("() => { document.getElementById('phone')?.scrollIntoView({block:'center'}); }")
    time.sleep(1.0)

    iti_after_scroll = page.evaluate('''() => {
        const results = [];
        document.querySelectorAll('[class*="iti"]').forEach(el => {
            const r = el.getBoundingClientRect();
            results.push({
                tag: el.tagName, id: el.id,
                class: (el.className||"").substring(0,100),
                x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height),
            });
        });
        return results;
    }''')
    print("\nITI elements after scroll to phone:")
    print(json.dumps(iti_after_scroll[:10], indent=2))

    # 3. Click the phone field itself and check what happens
    page.locator("#phone").click()
    time.sleep(0.5)
    iti_after_click = page.evaluate('''() => {
        const results = [];
        document.querySelectorAll('[class*="iti"]').forEach(el => {
            const r = el.getBoundingClientRect();
            results.push({
                tag: el.tagName, id: el.id,
                class: (el.className||"").substring(0,100),
                x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height),
            });
        });
        return results;
    }''')
    print("\nITI elements after clicking #phone:")
    print(json.dumps(iti_after_click[:10], indent=2))

    # 4. Take a screenshot with annotation
    page.screenshot(path=r"C:\Users\chent\Agentic_Workflows_2026\oracle-job-search\outputs\2026-06-12-feed-first\applications\twitch_culture_people_pm\screenshots\inspect_phone.png")
    print("\nScreenshot saved: inspect_phone.png")

    # 5. Check if q894 options truly appear or not - inspect HTML structure
    print("\nInspecting q894 structure...")
    q894_info = page.evaluate('''() => {
        const inp = document.getElementById("question_36848894002");
        if (!inp) return {error: "no input"};
        let el = inp; let chain = [];
        for (let i=0; i<15; i++) {
            if (!el) break;
            chain.push({tag: el.tagName, class: (el.className||"").substring(0,80), id: el.id});
            el = el.parentElement;
        }
        return {chain};
    }''')
    print(json.dumps(q894_info, indent=2))

    # 6. Open q894 and inspect ALL elements that appear
    print("\nOpening q894 and inspecting...")
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
    time.sleep(2.0)  # Wait 2 seconds

    options_info = page.evaluate('''() => {
        const menu = document.querySelector(".select__menu");
        const opts = [...document.querySelectorAll(".select__option")];
        const menuContent = menu ? menu.innerHTML.substring(0, 500) : null;
        const optsText = opts.map(o => o.innerText||"").slice(0, 15);
        return {
            menu_exists: !!menu,
            menu_class: menu?.className||null,
            menu_content_preview: menuContent,
            opts_count: opts.length,
            opts_text: optsText,
            // Where is the menu relative to q894?
            inp_rect: (() => { const inp = document.getElementById("question_36848894002"); if(!inp) return null; const r = inp.getBoundingClientRect(); return {x:r.x, y:r.y, w:r.width, h:r.height}; })(),
            menu_rect: (() => { const m = document.querySelector(".select__menu"); if(!m) return null; const r = m.getBoundingClientRect(); return {x:r.x, y:r.y, w:r.width, h:r.height}; })(),
        };
    }''')
    print("q894 options after 2s wait:")
    print(json.dumps(options_info, indent=2))

    page.screenshot(path=r"C:\Users\chent\Agentic_Workflows_2026\oracle-job-search\outputs\2026-06-12-feed-first\applications\twitch_culture_people_pm\screenshots\inspect_q894.png")
    print("\nScreenshot saved: inspect_q894.png")

    time.sleep(3)
    ctx.close()
