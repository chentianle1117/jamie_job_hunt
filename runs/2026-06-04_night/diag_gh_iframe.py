#!/usr/bin/env python3
"""Inspect the Databricks Greenhouse EMBED IFRAME + cookie-consent overlay. Read-only."""
import sys, json
from patchright.sync_api import sync_playwright

URL = "https://boards.greenhouse.io/databricks/jobs/8431927002"
OUT = r"C:\Users\chent\Agentic_Workflows_2026\oracle-job-search\runs\2026-06-04_night"

with sync_playwright() as p:
    b = p.chromium.connect_over_cdp("http://127.0.0.1:9333")
    ctx = b.contexts[0]
    page = ctx.new_page()
    page.goto(URL, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(4000)

    # 1) Is there a OneTrust cookie overlay blocking clicks?
    overlay = page.evaluate(r'''() => {
        const ot = document.querySelector('#onetrust-banner-sdk, #onetrust-consent-sdk, .onetrust-pc-dark-filter, #onetrust-pc-sdk');
        const accept = document.querySelector('#onetrust-accept-btn-handler, [id*="accept" i].ot-sdk, button[id*="accept" i]');
        return {
            overlayPresent: !!ot,
            overlayVisible: ot ? (ot.offsetParent !== null) : false,
            acceptBtn: accept ? (accept.innerText||accept.id||'').slice(0,40) : null,
            darkFilter: !!document.querySelector('.onetrust-pc-dark-filter')
        };
    }''')
    print("COOKIE OVERLAY:", json.dumps(overlay))

    # 2) Enumerate frames; find the greenhouse embed frame + its submit button + required fields
    frames = page.frames
    print(f"FRAMES: {len(frames)}")
    for fr in frames:
        u = fr.url
        if "embed/job_app" in u or "greenhouse" in u and "embed" in u:
            print(f"  EMBED FRAME: {u[:90]}")
            try:
                info = fr.evaluate(r'''() => {
                    const sub=[...document.querySelectorAll('button, input[type=submit]')].filter(b=>/submit/i.test((b.innerText||b.value||'')));
                    const req=[...document.querySelectorAll('input,select,textarea')].filter(e=>e.required||e.getAttribute('aria-required')==='true');
                    return {
                        submit: sub.map(b=>({t:(b.innerText||b.value||'').slice(0,25), disabled:b.disabled, type:b.type})),
                        requiredCount: req.length,
                        requiredEmpty: req.filter(e=>!(e.value||'').trim()).map(e=>{
                            const l=document.querySelector(`label[for="${e.id}"]`); return (l?l.innerText:e.name||e.id||'?').slice(0,40);
                        }).slice(0,15),
                        errors: [...document.querySelectorAll('.error, [aria-invalid="true"], .field_with_errors, [class*="error" i]')]
                                 .map(n=>(n.innerText||'').trim()).filter(t=>t&&t.length<120).slice(0,10),
                    };
                }''')
                print("    submit btns:", json.dumps(info["submit"]))
                print("    required:", info["requiredCount"], "| empty:", json.dumps(info["requiredEmpty"]))
                print("    errors:", json.dumps(info["errors"]))
            except Exception as e:
                print("    frame eval err:", str(e)[:80])
    page.close()
