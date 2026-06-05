#!/usr/bin/env python3
"""DEEP DIAGNOSTIC (fills, clicks submit, then INSPECTS failure — does NOT retry/spam).
Reuses the real Ashby submitter to fill, then captures exactly why submit fails:
 - the validation error text Ashby shows
 - whether each required input's value persists in the DOM after the submit attempt
 - the submit button element + whether it's disabled/native-type
 - whether a captcha/turnstile iframe is present
Run once. CDP_PORT=9333."""
import os, sys, json, time
sys.path.insert(0, r"C:\Users\chent\Agentic_Workflows_2026\jamie-autopilot\lib")
os.environ["CDP_PORT"] = "9333"
os.environ["DRY"] = "1"  # ensures the submitter's own code does NOT click submit; we do it here

from patchright.sync_api import sync_playwright

URL = "https://jobs.ashbyhq.com/openai/1778fbc9-b9c5-4ea5-a1d3-aa7bea0be272/application"
OUT = r"C:\Users\chent\Agentic_Workflows_2026\oracle-job-search\runs\2026-06-04_night"

with sync_playwright() as p:
    b = p.chromium.connect_over_cdp("http://127.0.0.1:9333")
    ctx = b.contexts[0]
    page = ctx.new_page()
    page.goto(URL, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(3500)

    # Minimal manual fill of the 3 historically-stuck fields + a quick scan, then inspect.
    # We fill location + start + office-yesno via native setter + fiber, like the patched submitter.
    def commit(sel_label, value):
        return page.evaluate(r'''([label, value]) => {
            // find field-entry whose title contains label
            const fes = [...document.querySelectorAll('.ashby-application-form-field-entry')];
            const fe = fes.find(fe => (fe.querySelector('.ashby-application-form-question-title')||{}).innerText
                                       ?.toLowerCase().includes(label.toLowerCase()));
            if (!fe) return {label, found:false};
            const el = fe.querySelector('input[type=text],input:not([type]),textarea');
            if (!el) return {label, found:false, note:'no text input (maybe yesno button)'};
            const proto = el.tagName==='TEXTAREA'?HTMLTextAreaElement.prototype:HTMLInputElement.prototype;
            Object.getOwnPropertyDescriptor(proto,'value').set.call(el, value);
            el.dispatchEvent(new Event('input',{bubbles:true}));
            el.dispatchEvent(new Event('change',{bubbles:true}));
            const k = Object.keys(el).find(k=>k.startsWith('__reactProps$'));
            if (k && el[k] && typeof el[k].onChange==='function')
                el[k].onChange({target:el,currentTarget:el,type:'change',bubbles:true,preventDefault(){},stopPropagation(){},persist(){}});
            el.dispatchEvent(new Event('blur',{bubbles:true}));
            return {label, found:true, valueAfter: el.value, isTrusted_supported: true};
        }''', [sel_label, value])

    r1 = commit("located", "Portland, OR, USA")
    r2 = commit("start a new role", "2-4 weeks notice")
    print("FILL location:", json.dumps(r1)); print("FILL start:", json.dumps(r2))
    page.wait_for_timeout(800)

    # Inspect the submit button + captcha BEFORE clicking
    pre = page.evaluate(r'''() => {
        const btns = [...document.querySelectorAll('button')].filter(b=>/submit application|submit/i.test(b.innerText||''));
        const sb = btns[btns.length-1];
        return {
            submitBtn: sb ? {text:(sb.innerText||'').trim(), type:sb.type, disabled:sb.disabled,
                             ariaDisabled: sb.getAttribute('aria-disabled')} : null,
            captcha: !!document.querySelector('iframe[src*="recaptcha"], iframe[src*="hcaptcha"], iframe[src*="turnstile"], .cf-turnstile'),
            form: !!document.querySelector('form'),
        };
    }''')
    print("PRE-SUBMIT:", json.dumps(pre, indent=2))

    # snapshot the 3 fields' DOM values right before clicking
    before = page.evaluate(r'''() => {
        const out = {};
        document.querySelectorAll('.ashby-application-form-field-entry').forEach(fe=>{
            const t=(fe.querySelector('.ashby-application-form-question-title')||{}).innerText||'';
            const el=fe.querySelector('input[type=text],input:not([type]),textarea');
            if(el && /located|start a new role/i.test(t)) out[t.trim().slice(0,30)] = el.value;
        });
        return out;
    }''')
    print("VALUES BEFORE CLICK:", json.dumps(before))

    # SAFETY: we deliberately leave yes/no + acknowledgment checkboxes UNSET so the form is
    # guaranteed-incomplete and CANNOT submit. Clicking Submit will just trigger validation,
    # which is exactly what we want to inspect (do our 2 text values survive a validation pass?).
    print(">>> clicking Submit on an INTENTIONALLY-INCOMPLETE form (cannot submit) to read validation")
    page.evaluate(r'''() => {
        const btns=[...document.querySelectorAll('button')].filter(b=>/submit application|submit/i.test(b.innerText||''));
        const sb=btns[btns.length-1]; if(sb){ sb.scrollIntoView({block:'center'}); }
    }''')
    page.wait_for_timeout(400)
    try:
        page.get_by_role("button", name="Submit Application").click(timeout=4000)
    except Exception as e:
        print("click via role failed:", e)
        page.evaluate('''()=>{const b=[...document.querySelectorAll("button")].filter(b=>/submit application|submit/i.test(b.innerText||"")).pop(); if(b)b.click();}''')
    page.wait_for_timeout(2500)

    post = page.evaluate(r'''() => {
        const errs=[];
        document.querySelectorAll('[class*="error" i],[aria-invalid="true"],[role="alert"]').forEach(n=>{
            const t=(n.innerText||'').trim(); if(t && t.length<200) errs.push(t);
        });
        const vals={};
        document.querySelectorAll('.ashby-application-form-field-entry').forEach(fe=>{
            const t=(fe.querySelector('.ashby-application-form-question-title')||{}).innerText||'';
            const el=fe.querySelector('input[type=text],input:not([type]),textarea');
            if(el && /located|start a new role/i.test(t)) vals[t.trim().slice(0,30)]=el.value;
        });
        return {errors:[...new Set(errs)].slice(0,12), valuesAfterSubmit:vals, url:location.href,
                success: /thank|received|submitted|confirm/i.test(document.body.innerText.slice(0,3000))};
    }''')
    print("POST-SUBMIT:", json.dumps(post, indent=2))
    page.screenshot(path=OUT + r"\diag_post_submit.png")
    page.close()
