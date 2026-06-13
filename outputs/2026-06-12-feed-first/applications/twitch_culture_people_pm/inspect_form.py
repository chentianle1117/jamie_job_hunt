"""Quick inspector — opens the form and dumps the full HTML structure of key fields."""
import sys, time
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

    # Inspect the country field structure
    info = page.evaluate('''() => {
        const results = {};

        // 1. What is #country?
        const cEl = document.getElementById('country');
        if (cEl) {
            let el = cEl;
            let chain = [];
            for (let i=0; i<10; i++) {
                chain.push({tag: el.tagName, id: el.id, class: (el.className||'').substring(0,60)});
                el = el.parentElement; if (!el) break;
            }
            results.country_chain = chain;
        }

        // 2. What is the actual Country form field? (look for a label 'Country*')
        // Greenhouse's standard country field: div with label "Country*" containing a react-select
        const allLabels = [...document.querySelectorAll('label')];
        const countryLabel = allLabels.find(l => (l.textContent||'').trim().startsWith('Country'));
        if (countryLabel) {
            results.country_label_for = countryLabel.htmlFor;
            // Find the react-select container
            let container = countryLabel.closest('[class*="field"], [class*="question"], [class*="form-group"], .sc-')
                            || countryLabel.parentElement;
            const ctrl = container?.querySelector('.select__control');
            const hiddenInp = container?.querySelector('input[type="hidden"], input[name]');
            results.country_container_class = container?.className?.substring(0,80);
            results.country_has_ctrl = !!ctrl;
            results.country_hidden_input = hiddenInp ? {id: hiddenInp.id, name: hiddenInp.name, value: hiddenInp.value} : null;
        }

        // 3. What are ALL the react-select hidden inputs?
        const reactSelects = [...document.querySelectorAll('[class*="select__input-container"] input')];
        results.react_select_inputs = reactSelects.map(el => ({
            id: el.id, name: el.name, type: el.type, value: el.value,
            ariaRequired: el.getAttribute('aria-required')
        })).slice(0, 30);

        // 4. Check if the form validation is checking the hidden input or the react-select container
        // Find what has aria-required="true" for the country question
        const ariaReq = [...document.querySelectorAll('[aria-required="true"]')];
        results.aria_required_count = ariaReq.length;
        results.aria_required_ids = ariaReq.map(el => el.id).slice(0, 20);

        // 5. What does the phone field look like? Is there an ITI widget?
        results.has_iti = !!document.querySelector('.iti, [class*="intl-tel"]');
        const phoneEl = document.getElementById('phone');
        if (phoneEl) {
            let parent = phoneEl.parentElement;
            results.phone_parent_class = parent?.className?.substring(0,80);
        }

        return results;
    }''')

    print("INSPECTION RESULTS:")
    import json
    print(json.dumps(info, indent=2))

    # Also try opening a react-select and checking what gets set
    print("\n\nOpening country select and checking state...")
    page.evaluate('''() => {
        const inp = document.getElementById("country");
        if (!inp) return;
        let el = inp;
        for (let i=0; i<10; i++) {
            el = el.parentElement; if (!el) break;
            const ctrl = el.querySelector(".select__control");
            if (ctrl) { ctrl.dispatchEvent(new MouseEvent("mousedown", {bubbles:true})); ctrl.click(); return; }
        }
    }''')
    time.sleep(0.8)

    options_and_state = page.evaluate('''() => {
        const opts = [...document.querySelectorAll(".select__option")].map(o => (o.innerText||"").trim()).slice(0, 10);
        return {
            options: opts,
            menu_open: !!document.querySelector(".select__menu"),
        };
    }''')
    print(f"Country dropdown state: {options_and_state}")

    # Type "United" and see what happens
    page.keyboard.type("United States")
    time.sleep(0.8)
    opts = page.locator(".select__option").all()
    opts_txt = [o.inner_text().strip() for o in opts[:10]]
    print(f"After typing 'United States': {opts_txt}")

    # Click the right one (not "+1")
    for o in opts:
        txt = o.inner_text().strip()
        if "United States" in txt and "+1" not in txt:
            o.click()
            break
        elif "United States" in txt:
            o.click()
            break

    time.sleep(0.5)
    state_after = page.evaluate('''() => {
        const cEl = document.getElementById("country");
        let sv = null;
        if (cEl) {
            let el = cEl;
            for (let i=0; i<10; i++) {
                el = el.parentElement; if (!el) break;
                const svEl = el.querySelector(".select__single-value");
                if (svEl) { sv = (svEl.innerText||"").trim(); break; }
            }
        }
        // Also check all hidden inputs nearby
        const hiddenInputs = [...document.querySelectorAll('input[type="hidden"]')].map(el => ({
            name: el.name, value: el.value
        })).filter(e => e.value).slice(0, 15);
        // Check what the #country input value is
        const countryVal = document.getElementById("country")?.value;
        return {country_sv: sv, country_input_val: countryVal, hidden_inputs: hiddenInputs};
    }''')
    print(f"After selecting country: {state_after}")

    time.sleep(3)
    ctx.close()
