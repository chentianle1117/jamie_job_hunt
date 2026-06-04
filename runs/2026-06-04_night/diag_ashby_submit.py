#!/usr/bin/env python3
"""DIAGNOSTIC ONLY (no submit): inspect the live Ashby form on CDP 9333 to understand why
submit-through-validation fails. Reports: submit button(s), required-field empties as Ashby sees them,
any aria-invalid / error nodes, and whether values persist after a blur."""
import json
from patchright.sync_api import sync_playwright

CDP = "http://127.0.0.1:9333"
with sync_playwright() as p:
    b = p.chromium.connect_over_cdp(CDP)
    ctx = b.contexts[0]
    page = None
    for pg in ctx.pages:
        if "jobs.ashbyhq.com/openai" in pg.url:
            page = pg; break
    if page is None:
        print("NO ASHBY TAB OPEN"); raise SystemExit(1)
    page.bring_to_front()

    info = page.evaluate(r'''() => {
        const out = {url: location.href, submit_buttons: [], invalid: [], inputs: [], errors: []};
        // submit buttons
        document.querySelectorAll('button').forEach(btn => {
            const t = (btn.innerText||'').trim();
            if (/submit application|submit|apply/i.test(t)) {
                out.submit_buttons.push({text: t, type: btn.type, disabled: btn.disabled,
                    cls: (btn.className||'').slice(0,60)});
            }
        });
        // error / invalid nodes
        document.querySelectorAll('[aria-invalid="true"], [class*="error" i], [class*="_error" i]').forEach(n => {
            const tx = (n.innerText||'').trim().slice(0,80);
            if (tx) out.errors.push(tx);
        });
        // all text/textarea inputs + current value + whether Ashby marks them required-empty
        document.querySelectorAll('input, textarea').forEach(el => {
            if (['hidden','file'].includes(el.type)) return;
            const fe = el.closest('.ashby-application-form-field-entry');
            const titleEl = fe ? fe.querySelector('.ashby-application-form-question-title') : null;
            const title = titleEl ? (titleEl.innerText||'').trim().slice(0,40) : '';
            const reqd = titleEl ? /_required_/.test(titleEl.className||'') : false;
            out.inputs.push({title, type: el.type, value: (el.value||'').slice(0,30),
                             required: reqd, id: (el.id||'').slice(0,40)});
        });
        return out;
    }''')
    print(json.dumps(info, indent=2)[:4000])
