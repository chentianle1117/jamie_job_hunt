"""Inspect how Greenhouse validates react-select and find the true country/location fields."""
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

    # 1. Find the form's actual submission fields (what Greenhouse sends to server)
    form_info = page.evaluate('''() => {
        const form = document.querySelector('form');
        if (!form) return {no_form: true};
        const inputs = [...form.querySelectorAll('input, select, textarea')];
        return inputs.map(el => ({
            id: el.id, name: el.name, type: el.type||el.tagName,
            value: el.value?.substring(0,50),
            required: el.required || el.getAttribute('aria-required') === 'true'
        })).filter(e => e.name || e.id).slice(0, 50);
    }''')
    print("Form inputs with names/ids:")
    print(json.dumps(form_info[:40], indent=2))

    # 2. Try clicking the ACTUAL first question (q894) option and check what changes
    print("\n\nTesting react-select click on question_36848894002...")

    # Open the dropdown
    page.evaluate('''() => {
        const inp = document.getElementById("question_36848894002");
        let el = inp;
        for (let i=0; i<10; i++) {
            el = el.parentElement; if (!el) break;
            const ctrl = el.querySelector(".select__control");
            if (ctrl) { ctrl.dispatchEvent(new MouseEvent("mousedown", {bubbles:true})); ctrl.click(); return; }
        }
    }''')
    time.sleep(0.8)

    opts = page.locator(".select__option").all()
    opts_txt = [o.inner_text().strip() for o in opts[:20]]
    print(f"Options: {opts_txt}")

    if opts:
        # Click first option
        opts[0].click()
        time.sleep(0.5)

    # Check state after selection
    state_after = page.evaluate('''() => {
        const inp = document.getElementById("question_36848894002");
        let sv = null;
        if (inp) {
            let el = inp;
            for (let i=0; i<10; i++) {
                el = el.parentElement; if (!el) break;
                const svEl = el.querySelector(".select__single-value");
                if (svEl) { sv = (svEl.innerText||"").trim(); break; }
            }
        }
        // What is inp.value?
        const inpVal = inp ? inp.value : "N/A";
        // What does the form field for submission look like?
        const formField = document.querySelector('[name^="job_application[answers][36848894002]"]');
        return {
            input_value: inpVal,
            single_value_display: sv,
            form_field: formField ? {name: formField.name, value: formField.value, type: formField.type} : null,
        };
    }''')
    print(f"After click state: {state_after}")

    # 3. Look at what form inputs Greenhouse uses to actually submit answers
    all_form_fields = page.evaluate('''() => {
        const fields = [];
        // Look for hidden inputs that Greenhouse uses
        document.querySelectorAll('input[name*="job_application"], input[name*="application"], input[name*="question"]').forEach(el => {
            fields.push({name: el.name, type: el.type, value: el.value?.substring(0,50), id: el.id});
        });
        // Also look for any input with name
        document.querySelectorAll('input[name]').forEach(el => {
            if (!el.name.startsWith('question_') && el.name !== '')
                fields.push({name: el.name, type: el.type, value: el.value?.substring(0,50), id: el.id});
        });
        return fields.slice(0, 40);
    }''')
    print("\nAll form fields by name:")
    print(json.dumps(all_form_fields, indent=2))

    # 4. The country field: find the actual phone input structure
    phone_info = page.evaluate('''() => {
        const phone = document.querySelector('.phone-input');
        if (!phone) return {no_phone: true};
        // What inputs are inside it?
        const inputs = [...phone.querySelectorAll('input, select')];
        return inputs.map(el => ({id: el.id, name: el.name, type: el.type, value: el.value?.substring(0,30)}));
    }''')
    print("\nPhone field inputs:")
    print(json.dumps(phone_info, indent=2))

    # 5. Where is the actual form country selector (not phone country)?
    # In Greenhouse, the country is often a separate field after phone
    country_form = page.evaluate('''() => {
        // Find all select elements or react-select containers outside of phone-input
        const out = [];
        document.querySelectorAll('.select__control').forEach(ctrl => {
            const isInPhone = ctrl.closest('.phone-input');
            if (!isInPhone) {
                // Find nearby label
                let container = ctrl.closest('[class*="field"], [class*="question"], div[class]') || ctrl.parentElement;
                const lbl = container?.querySelector('label');
                const inp = ctrl.querySelector('input');
                out.push({
                    inPhone: false,
                    labelText: (lbl?.innerText||'').trim().substring(0,80),
                    inputId: inp?.id || '',
                    containerClass: ctrl.parentElement?.className?.substring(0,60)
                });
            }
        });
        return out.slice(0, 30);
    }''')
    print("\nReact-select controls (NOT in phone-input):")
    print(json.dumps(country_form, indent=2))

    time.sleep(3)
    ctx.close()
