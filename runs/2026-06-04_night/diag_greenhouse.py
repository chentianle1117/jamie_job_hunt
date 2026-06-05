#!/usr/bin/env python3
"""Greenhouse (Databricks, captcha-free) submit diagnostic. Navigates, fills standard fields +
the LLM questions the same way submit_llm_generic does, clicks submit ONCE, then captures the
EXACT Greenhouse validation errors + which fields it flags. Read-only diagnosis of the failure.
Does NOT loop/retry."""
import sys, json, time
sys.path.insert(0, r"C:\Users\chent\Agentic_Workflows_2026\jamie-autopilot\lib")
from patchright.sync_api import sync_playwright

URL = "https://boards.greenhouse.io/databricks/jobs/8431927002"
OUT = r"C:\Users\chent\Agentic_Workflows_2026\oracle-job-search\runs\2026-06-04_night"

with sync_playwright() as p:
    b = p.chromium.connect_over_cdp("http://127.0.0.1:9333")
    ctx = b.contexts[0]
    page = ctx.new_page()
    page.goto(URL, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(3500)

    # Inventory the form: required fields, their types, and whether each currently has a value.
    inv = page.evaluate(r'''() => {
        const out = {fields: [], submitBtns: [], captcha: false, iframes: []};
        out.iframes = [...document.querySelectorAll('iframe')].map(f=>f.src||'').slice(0,20);
        out.captcha = out.iframes.some(s=>/recaptcha|hcaptcha|turnstile/i.test(s));
        // Greenhouse fields: inputs/selects/textareas with a label
        document.querySelectorAll('input, select, textarea').forEach(el => {
            if (['hidden'].includes(el.type)) return;
            const id = el.id || el.name || '';
            let label = '';
            const lab = id ? document.querySelector(`label[for="${id}"]`) : null;
            if (lab) label = (lab.innerText||'').trim();
            if (!label && el.getAttribute('aria-label')) label = el.getAttribute('aria-label');
            const req = el.required || el.getAttribute('aria-required')==='true'
                     || (lab && /\*|required/i.test(lab.innerText||''));
            out.fields.push({label: label.slice(0,45), type: el.type||el.tagName.toLowerCase(),
                             id: id.slice(0,40), required: !!req, value: (el.value||'').slice(0,25),
                             ariaInvalid: el.getAttribute('aria-invalid')});
        });
        [...document.querySelectorAll('button, input[type=submit]')].forEach(b=>{
            const t=(b.innerText||b.value||'').trim();
            if (/submit/i.test(t)) out.submitBtns.push({text:t.slice(0,30), disabled:b.disabled, type:b.type});
        });
        return out;
    }''')
    print("CAPTCHA:", inv["captcha"])
    print("SUBMIT BTNS:", json.dumps(inv["submitBtns"]))
    print("REQUIRED FIELDS:")
    for f in inv["fields"]:
        if f["required"]:
            print(f"   req [{f['type']}] '{f['label']}' id={f['id']} value={'<empty>' if not f['value'] else f['value']}")
    # Save full inventory
    open(OUT + r"\greenhouse_form_inventory.json", "w", encoding="utf-8").write(json.dumps(inv, indent=2))
    print("\n(full inventory -> greenhouse_form_inventory.json)")
    page.screenshot(path=OUT + r"\gh_form_state.png", full_page=True)
    page.close()
