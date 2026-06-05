#!/usr/bin/env python3
"""Test the hypothesis: hiding the OneTrust dark-filter overlay (NOT accepting cookies) unblocks
the Greenhouse submit button. Read-only proof: hide overlay, then check if the embed-frame submit
button is hit-testable (elementFromPoint returns the button, not the overlay). Does NOT submit."""
import json
from patchright.sync_api import sync_playwright

URL = "https://boards.greenhouse.io/databricks/jobs/8431927002"
with sync_playwright() as p:
    b = p.chromium.connect_over_cdp("http://127.0.0.1:9333")
    ctx = b.contexts[0]
    page = ctx.new_page()
    page.goto(URL, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(4000)

    before = page.evaluate(r'''() => {
        const df=document.querySelector('.onetrust-pc-dark-filter, #onetrust-consent-sdk');
        return {darkFilterVisible: df ? df.offsetParent!==null : false};
    }''')
    print("BEFORE hide:", json.dumps(before))

    # PRIVACY-PRESERVING: hide the consent overlay + dark filter via CSS. This does NOT click
    # "Accept" — no consent is given; it just removes the click-blocking layer. (Global rule:
    # prefer the most privacy-preserving option; we are NOT accepting non-essential cookies.)
    page.evaluate(r'''() => {
        ['#onetrust-banner-sdk','#onetrust-consent-sdk','#onetrust-pc-sdk','.onetrust-pc-dark-filter',
         '.ot-sdk-container','#onetrust-group-container'].forEach(sel=>{
            document.querySelectorAll(sel).forEach(n=>{ n.style.setProperty('display','none','important');
                                                        n.style.setProperty('pointer-events','none','important'); });
        });
        document.body.style.removeProperty('overflow');
        return true;
    }''')
    page.wait_for_timeout(600)

    after = page.evaluate(r'''() => {
        const df=document.querySelector('.onetrust-pc-dark-filter');
        return {darkFilterVisible: df ? df.offsetParent!==null : false};
    }''')
    print("AFTER hide:", json.dumps(after))

    # Now check the embed frame's submit button hit-testability
    for fr in page.frames:
        if "embed/job_app" in fr.url:
            info = fr.evaluate(r'''() => {
                const btns=[...document.querySelectorAll('button, input[type=submit]')].filter(b=>/submit/i.test((b.innerText||b.value||'')));
                if(!btns.length) return {found:false};
                const b=btns[btns.length-1]; const r=b.getBoundingClientRect();
                const topEl=document.elementFromPoint(r.left+r.width/2, r.top+r.height/2);
                return {found:true, text:(b.innerText||b.value||'').slice(0,25), disabled:b.disabled,
                        topElIsButton: topEl===b || (topEl && b.contains(topEl)),
                        topElTag: topEl? topEl.tagName : null};
            }''')
            print("EMBED-FRAME SUBMIT (within-frame hit-test):", json.dumps(info))
    page.close()
