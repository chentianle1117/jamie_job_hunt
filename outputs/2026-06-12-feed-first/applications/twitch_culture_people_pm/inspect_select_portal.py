"""
Test 1: Use ITI JS API (intlTelInputGlobals / window.iti) to set US country.
Test 2: Open q894 select and WATCH what happens in real-time.
"""
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

    # 1. Try ITI JS API
    iti_api = page.evaluate('''() => {
        const phone = document.getElementById("phone");
        if (!phone) return {err: "no phone"};
        // ITI stores instance on the element
        const keys = Object.keys(phone).filter(k => k.includes("iti") || k.includes("Iti") || k.includes("intl"));
        // Also check window for globals
        const winKeys = Object.keys(window).filter(k => k.toLowerCase().includes("iti") || k.toLowerCase().includes("intltel"));
        // Check phone._itiId or similar
        const allKeys = Object.getOwnPropertyNames(phone);
        return {
            phone_keys: keys,
            phone_all_keys_with_iti: allKeys.filter(k => k.toLowerCase().includes("iti")),
            window_iti_keys: winKeys,
        };
    }''')
    print("ITI API keys:", json.dumps(iti_api, indent=2))

    # 2. Try calling setCountry via ITI instance
    set_result = page.evaluate('''() => {
        const phone = document.getElementById("phone");
        if (!phone) return {err: "no phone"};

        // Method 1: intlTelInputGlobals
        if (window.intlTelInputGlobals) {
            try {
                const instances = window.intlTelInputGlobals.getInstance(phone);
                if (instances) {
                    instances.setCountry("us");
                    return {method: "intlTelInputGlobals.getInstance", success: true, dialCode: instances.getSelectedCountryData()?.dialCode};
                }
            } catch(e) {}
        }

        // Method 2: intlTelInput() getter
        if (window.intlTelInput) {
            try {
                const inst = window.intlTelInput(phone);
                inst.setCountry("us");
                return {method: "intlTelInput(phone)", success: true};
            } catch(e) {}
        }

        // Method 3: check if the phone element has a reference to ITI
        const itiProp = Object.getOwnPropertyNames(phone).find(k => phone[k] && phone[k].setCountry);
        if (itiProp) {
            phone[itiProp].setCountry("us");
            return {method: itiProp, success: true};
        }

        // Method 4: check __reactFiber for iti props
        return {err: "no iti API found"};
    }''')
    print("ITI setCountry result:", json.dumps(set_result))

    time.sleep(0.5)
    iti_check = page.evaluate('''() => {
        const dialCode = document.querySelector(".iti__dial-code, .iti__selected-dial-code");
        const flag = document.querySelector(".iti__flag");
        const flagClass = flag ? Array.from(flag.classList).join(" ") : "";
        return {dialCode: dialCode?.innerText||"", flagClass};
    }''')
    print("ITI after setCountry:", json.dumps(iti_check))

    # 3. Open q894 and watch it carefully
    print("\n--- q894 investigation ---")
    page.evaluate("() => { document.getElementById('question_36848894002')?.scrollIntoView({block:'center'}); }")
    time.sleep(0.5)

    # Check q894 container class hierarchy
    q894_container = page.evaluate('''() => {
        const inp = document.getElementById("question_36848894002");
        if (!inp) return {err: "no inp"};
        let el = inp; const chain = [];
        for (let i=0; i<10; i++) {
            if (!el) break;
            const cls = Array.from(el.classList).join(" ");
            chain.push({tag: el.tagName, id: el.id, cls: cls.substring(0,80)});
            el = el.parentElement;
        }
        // Also find the react-select control
        let ctrl = inp;
        for (let i=0; i<10; i++) {
            if (!ctrl) break;
            const c = ctrl.querySelector ? ctrl.querySelector(".select__control") : null;
            if (c) {
                const cls = Array.from(c.classList).join(" ");
                chain.push({CTRL: true, cls});
                break;
            }
            ctrl = ctrl.parentElement;
        }
        return chain;
    }''')
    print("q894 container chain:", json.dumps(q894_container, indent=2))

    # Click via the control
    page.evaluate('''() => {
        const inp = document.getElementById("question_36848894002");
        let el = inp;
        for (let i=0; i<12; i++) {
            if (!el) return;
            const ctrl = el.querySelector(".select__control");
            if (ctrl) {
                console.log("Clicking ctrl", ctrl.className);
                ctrl.dispatchEvent(new MouseEvent("mousedown",{bubbles:true}));
                ctrl.click();
                return;
            }
            el = el.parentElement;
        }
    }''')
    time.sleep(0.3)

    # Check immediately
    state_0 = page.evaluate('''() => {
        const menu = document.querySelector(".select__menu, [class*='select__menu']");
        const portal = document.getElementById("react-portal-mount-point");
        return {
            menu_exists: !!menu,
            portal_html_len: portal?.innerHTML?.length || 0,
            opts: [...document.querySelectorAll(".select__option")].map(o => (o.innerText||"").trim()).slice(0,10)
        };
    }''')
    print(f"After click (0.3s): {json.dumps(state_0)}")

    time.sleep(1.0)
    state_1 = page.evaluate('''() => {
        const menu = document.querySelector(".select__menu, [class*='select__menu']");
        const portal = document.getElementById("react-portal-mount-point");
        // Check if menu-portal class (react-select renders to body with menuPortalTarget)
        const menuPortal = document.querySelector("[class*='menu-portal'], [class*='menuPortal']");
        return {
            menu_exists: !!menu,
            menu_portal_exists: !!menuPortal,
            portal_html_len: portal?.innerHTML?.length || 0,
            opts: [...document.querySelectorAll(".select__option")].map(o => (o.innerText||"").trim()).slice(0,10),
            // Check what's in the portal now
            portal_tags: portal ? [...portal.querySelectorAll("*")].slice(0,5).map(e => {const c=Array.from(e.classList).join(" ");return {tag:e.tagName,cls:c.substring(0,60)};}) : [],
        };
    }''')
    print(f"After click (1.3s): {json.dumps(state_1, indent=2)}")

    # Try using Playwright's built-in click
    page.keyboard.press("Escape")
    time.sleep(0.3)

    # Find the .select__control near q894 and click via Playwright
    ctrl_info = page.evaluate('''() => {
        const inp = document.getElementById("question_36848894002");
        let el = inp;
        for (let i=0; i<12; i++) {
            if (!el) break;
            const ctrl = el.querySelector(".select__control");
            if (ctrl) {
                const r = ctrl.getBoundingClientRect();
                return {x:Math.round(r.x), y:Math.round(r.y), w:Math.round(r.width), h:Math.round(r.height), found: true};
            }
            el = el.parentElement;
        }
        return {found: false};
    }''')
    print(f"\nq894 control coords: {ctrl_info}")

    if ctrl_info.get('found') and ctrl_info['w'] > 0:
        cx = ctrl_info['x'] + ctrl_info['w']//2
        cy = ctrl_info['y'] + ctrl_info['h']//2
        print(f"Clicking at ({cx}, {cy})")
        page.mouse.click(cx, cy)
        time.sleep(1.5)

        state_2 = page.evaluate('''() => {
            const portal = document.getElementById("react-portal-mount-point");
            const menus = [...document.querySelectorAll("[class*='select__menu'], [class*='menu-portal']")];
            const opts = [...document.querySelectorAll("[class*='select__option']")];
            return {
                menus: menus.map(m => {const cls=Array.from(m.classList).join(" "); const r=m.getBoundingClientRect(); return {cls:cls.substring(0,80), x:Math.round(r.x), y:Math.round(r.y), w:Math.round(r.width), h:Math.round(r.height), text:(m.innerText||"").trim().substring(0,200)};}),
                opts: opts.map(o=>(o.innerText||"").trim()).slice(0,10),
                portal_len: portal?.innerHTML?.length||0,
            };
        }''')
        print(f"After mouse click (1.5s): {json.dumps(state_2, indent=2)}")
        page.screenshot(path=r"C:\Users\chent\Agentic_Workflows_2026\oracle-job-search\outputs\2026-06-12-feed-first\applications\twitch_culture_people_pm\screenshots\inspect_q894_click.png")
        print("Screenshot saved: inspect_q894_click.png")

    time.sleep(3)
    ctx.close()
