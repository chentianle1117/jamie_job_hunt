"""Quick inspection of phone widget and q894 dropdown."""
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

    # 1. All elements whose class contains "iti" — safely
    iti_info = page.evaluate('''() => {
        const results = [];
        document.querySelectorAll('[class*="iti"]').forEach(el => {
            const cls = Array.from(el.classList).join(" ");
            const r = el.getBoundingClientRect();
            results.push({tag: el.tagName, id: el.id, cls: cls.substring(0,100), x:Math.round(r.x), y:Math.round(r.y), w:Math.round(r.width), h:Math.round(r.height)});
        });
        return results;
    }''')
    print("All [class*=iti] elements:")
    print(json.dumps(iti_info, indent=2))

    # 2. Phone field parent structure
    phone_parents = page.evaluate('''() => {
        const phone = document.getElementById("phone");
        if (!phone) return {err: "no #phone"};
        const chain = [];
        let el = phone;
        for (let i = 0; i < 10; i++) {
            const cls = Array.from(el.classList).join(" ");
            chain.push({tag: el.tagName, id: el.id, cls: cls.substring(0,80), children: el.children.length});
            el = el.parentElement; if (!el) break;
        }
        return chain;
    }''')
    print("\n#phone parent chain:")
    print(json.dumps(phone_parents, indent=2))

    # 3. Inside .phone-input fieldset
    phone_fieldset = page.evaluate('''() => {
        const fieldset = document.querySelector(".phone-input, fieldset.phone-input");
        if (!fieldset) return {err: "no .phone-input"};
        const children = [];
        fieldset.querySelectorAll("input, select, button, span[class], div[class]").forEach(el => {
            const cls = Array.from(el.classList).join(" ");
            const r = el.getBoundingClientRect();
            const label = el.getAttribute("aria-label") || el.getAttribute("placeholder") || "";
            children.push({tag: el.tagName, id: el.id, cls: cls.substring(0,80), type: el.type||"", value: (el.value||"").substring(0,30), ariaLabel: label.substring(0,50), x:Math.round(r.x), y:Math.round(r.y), w:Math.round(r.width), h:Math.round(r.height)});
        });
        return children;
    }''')
    print("\n.phone-input fieldset children:")
    print(json.dumps(phone_fieldset, indent=2))

    # 4. Scroll to phone and inspect again
    page.evaluate("() => { document.getElementById('phone')?.scrollIntoView({block:'center'}); }")
    time.sleep(1.0)
    page.screenshot(path=r"C:\Users\chent\Agentic_Workflows_2026\oracle-job-search\outputs\2026-06-12-feed-first\applications\twitch_culture_people_pm\screenshots\inspect_phone2.png")
    print("\nScreenshot saved")

    # 5. Look at react-select portals — when dropdown opens, are options in a portal (body-appended)?
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
    time.sleep(2.5)

    portal_info = page.evaluate('''() => {
        // Check if react-select is using a portal (appended to body)
        const allMenus = document.querySelectorAll("[class*='select__menu'], [class*='menu']");
        const menuInfos = [];
        allMenus.forEach(m => {
            const cls = Array.from(m.classList).join(" ");
            const opts = m.querySelectorAll("[class*='select__option']");
            const optTexts = [...opts].map(o => (o.innerText||"").trim()).slice(0, 10);
            const r = m.getBoundingClientRect();
            menuInfos.push({cls: cls.substring(0,80), x:Math.round(r.x), y:Math.round(r.y), w:Math.round(r.width), h:Math.round(r.height), opts_count: opts.length, opts: optTexts});
        });
        // Also check body direct children
        const bodyDirect = [...document.body.children].map(el => {
            const cls = Array.from(el.classList).join(" ");
            return {tag: el.tagName, cls: cls.substring(0,60), id: el.id};
        }).filter(e => e.cls || e.id);
        return {menus: menuInfos, body_children_with_class: bodyDirect.slice(0,20)};
    }''')
    print("\nAll menu elements + body children:")
    print(json.dumps(portal_info, indent=2))

    page.screenshot(path=r"C:\Users\chent\Agentic_Workflows_2026\oracle-job-search\outputs\2026-06-12-feed-first\applications\twitch_culture_people_pm\screenshots\inspect_q894_menu.png")

    time.sleep(3)
    ctx.close()
