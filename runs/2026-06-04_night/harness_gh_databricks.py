#!/usr/bin/env python3
"""Diagnostic harness for Databricks (Greenhouse, captcha-free). Reuses the REAL submitter's fill
helpers, clears the cookie overlay, clicks Submit ONCE, then KEEPS THE TAB OPEN and captures the
exact post-submit state (errors, required-empty, success text, url). Does NOT close the page so we
can read what actually happened. Safe: Jamie's inbox confirmed no prior Databricks submission."""
import os, sys, json, time
sys.path.insert(0, r"C:\Users\chent\Agentic_Workflows_2026\jamie-autopilot\lib")
import submit_llm_generic as S
from patchright.sync_api import sync_playwright

ROLE = r"C:\Users\chent\Agentic_Workflows_2026\oracle-job-search\runs\2026-06-04_night\discovered\databricks_customer_enablement"
OUT  = r"C:\Users\chent\Agentic_Workflows_2026\oracle-job-search\runs\2026-06-04_night"
from pathlib import Path
FF = json.load(open(Path(ROLE)/"form_fields.json", encoding="utf-8"))
URL = FF["meta"]["url"]
P = FF["personal"]; FIRST, LAST = P.get("first_name","Yi-Chieh"), P.get("last_name","Cheng")
EMAIL, PHONE = P.get("email"), P.get("phone")
LINKEDIN = FF.get("links",{}).get("linkedin","https://www.linkedin.com/in/jamieyccheng/")

def grab_state(page, tag):
    st = page.evaluate(r'''() => {
        const errs=[...document.querySelectorAll('.error,[aria-invalid="true"],.field_with_errors,[class*="error" i],[role="alert"],label.error')]
            .map(n=>(n.innerText||'').trim()).filter(t=>t&&t.length<160);
        const reqEmpty=[...document.querySelectorAll('input[required],select[required],textarea[required],[aria-required="true"]')]
            .filter(e=>!(e.value||'').trim())
            .map(e=>{const l=document.querySelector('label[for="'+e.id+'"]');return (l?l.innerText:e.name||e.id||'?').trim().slice(0,45);});
        const body=document.body.innerText.slice(0,2500);
        return {errors:[...new Set(errs)].slice(0,15), reqEmpty:[...new Set(reqEmpty)].slice(0,15),
                success:/thank you|submitted|received|application has been|thanks for applying/i.test(body),
                url:location.href};
    }''')
    print(f"[{tag}] success={st['success']} | errors={json.dumps(st['errors'])} | reqEmpty={json.dumps(st['reqEmpty'])}")
    return st

with sync_playwright() as p:
    b = p.chromium.connect_over_cdp("http://127.0.0.1:9333")
    ctx = b.contexts[0]
    page = ctx.new_page()
    print("Nav:", URL)
    page.goto(URL, wait_until="domcontentloaded", timeout=60000); page.wait_for_timeout(3500)

    # standard fields (same as submitter)
    for qid,val in [("first_name",FIRST),("last_name",LAST),("email",EMAIL),("phone",PHONE)]:
        S.fill_text(page, qid, val)
    try:
        cl = page.locator("#candidate-location")
        if cl.count(): cl.click(); time.sleep(0.4); page.keyboard.type("Seattle, WA"); time.sleep(0.4); page.wait_for_timeout(900); page.keyboard.press("Enter")
    except: pass
    # resume + cover upload
    try:
        for fid in ["#resume","input[type=file]"]:
            f=page.locator(fid)
            if f.count(): f.first.set_input_files(str(Path(ROLE)/"resume.pdf")); page.wait_for_timeout(1500); break
    except Exception as e: print("upload err", e)

    # the 5 questions via the real extractor+brain
    try:
        qs = S.extract_questions(page)
        print(f"extracted {len(qs)} questions")
        ans = S.ask_gemini(qs) if qs else {}
        for q in qs:
            qid=q.get("id"); a=ans.get(qid) or ans.get(q.get("label","")) or ""
            t=q.get("type","")
            if not a: continue
            if t in ("text","textarea","email","tel","url"): S.fill_text(page,qid,a)
            elif t=="combo": S.fill_combo(page,qid,a)
            elif t in ("radio","radio-group"):
                try: S.fill_radio_group(page,qid,a)
                except: pass
    except Exception as e:
        print("Q-fill err:", str(e)[:120])

    grab_state(page, "PRE-SUBMIT")
    page.screenshot(path=OUT+r"\harness_pre_submit.png", full_page=True)

    # clear cookie overlay (privacy-preserving hide, no Accept click)
    page.evaluate(r'''() => {['#onetrust-banner-sdk','#onetrust-consent-sdk','#onetrust-pc-sdk','.onetrust-pc-dark-filter','.ot-sdk-container','#onetrust-group-container'].forEach(s=>document.querySelectorAll(s).forEach(n=>{n.style.setProperty('display','none','important');n.style.setProperty('pointer-events','none','important');}));document.body.style.removeProperty('overflow');}''')
    page.wait_for_timeout(500)
    page.evaluate("window.scrollTo(0,document.body.scrollHeight)"); page.wait_for_timeout(800)

    # click submit ONCE
    clicked=False
    for nm in ["Submit application","Submit Application","Submit"]:
        try:
            bt=page.get_by_role("button",name=nm).first
            if bt.count(): bt.scroll_into_view_if_needed(); time.sleep(0.4); bt.click(timeout=8000); clicked=True; print("clicked:",nm); break
        except Exception as e: print("click",nm,"->",str(e)[:60])
    page.wait_for_timeout(6000)
    grab_state(page, "POST-SUBMIT")
    page.screenshot(path=OUT+r"\harness_post_submit.png", full_page=True)
    print(">>> TAB LEFT OPEN for inspection. Not closing.")
