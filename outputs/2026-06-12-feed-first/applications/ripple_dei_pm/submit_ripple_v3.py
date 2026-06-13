#!/usr/bin/env python3
"""
Ripple DEI PM — Greenhouse submit v3.
Key findings from inspect:
- boards.greenhouse.io/ripple/jobs/7951682 redirects to ripple.com (careers page)
- ripple.com page has an iframe at job-boards.greenhouse.io/embed/job_app?for=ripple&validityToken=...
- Playwright frame list shows the iframe URLs as empty strings (cross-origin fingerprinting block)
- Must use page.frame_locator('iframe[src*="greenhouse.io"]') with content_frame approach
  OR use the iframe element handle's content_frame
Strategy v3:
1. Load ripple.com careers page
2. Click "Apply Now" button if needed (may show form)
3. Get the iframe element handle -> content_frame -> fill
4. If frame access fails (cross-origin), open the iframe src directly in a new tab
"""
import os, sys, time, json, socket, subprocess, random
from datetime import datetime
from pathlib import Path

ROLE_DIR    = Path(r"C:\Users\chent\Agentic_Workflows_2026\oracle-job-search\outputs\2026-06-12-feed-first\applications\ripple_dei_pm")
RESUME      = ROLE_DIR / "resume.pdf"
COVER       = ROLE_DIR / "cover_letter.pdf"
SCREENSHOTS = ROLE_DIR / "screenshots"
SCREENSHOTS.mkdir(exist_ok=True)

CHROME_BIN  = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
DEBUG_PORT  = 9404
USER_DATA   = r"C:\Users\chent\ats_agent_9404"

RIPPLE_URL  = "https://ripple.com/careers/all-jobs/job/7951682/?gh_jid=7951682"

FIRST, LAST = "Yi-Chieh", "Cheng"
EMAIL       = "jamiecheng0103@gmail.com"
PHONE       = "2137003831"
COUNTRY     = "United States"
CITY        = "New York, NY"
LINKEDIN    = "https://www.linkedin.com/in/jamieyccheng/"
PREFERRED   = "Jamie"
AUTHORIZED  = "Yes"
SPONSOR     = "Yes"

SCREENING_ANSWER = (
    "I have worked on DEI initiatives across multiple organizational contexts. "
    "At Vestas Wind Systems, I developed and scaled an Inclusive Leadership workshop to 23 locations, "
    "co-designed a DEI culture pilot, and partnered with HR to embed inclusion practices into people processes. "
    "At NextGen, I consulted on DEI strategy and inclusive leadership for client organizations. "
    "In my current role at InGenius Prep, I manage 20+ programs and 10+ vendors, including initiatives "
    "with DEI-adjacent impact. My MS in Applied Organizational Psychology from USC grounds this work in "
    "research-backed frameworks. I am drawn to Ripple's mission of enabling economic inclusion globally "
    "and see the DEI PM role as a natural place to bring these skills to scale."
)

def pause(lo=0.5, hi=1.2): time.sleep(random.uniform(lo, hi))

def is_port_open(port):
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=2):
            return True
    except: return False

def launch_chrome():
    if is_port_open(DEBUG_PORT):
        print(f"[chrome] already on {DEBUG_PORT}"); return
    print(f"[chrome] launching...")
    subprocess.Popen([CHROME_BIN, f"--remote-debugging-port={DEBUG_PORT}",
                      f"--user-data-dir={USER_DATA}", "--no-first-run",
                      "--no-default-browser-check", "--window-size=1400,960"],
                     creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP)
    for _ in range(15):
        time.sleep(1)
        if is_port_open(DEBUG_PORT): print("[chrome] ready"); return

def combo(frame, locator, option_text, page_kb=None):
    """Drive a react-select combobox."""
    want = option_text.strip().lower()
    if isinstance(locator, str):
        loc = frame.locator(locator)
    else:
        loc = locator
    try: loc.scroll_into_view_if_needed(); pause()
    except: pass
    loc.click(); pause(); time.sleep(0.7)

    # Pre-rendered options
    try:
        opts = frame.locator(".select__option"); n = opts.count()
        for i in range(n):
            t = opts.nth(i).inner_text(timeout=3000).strip().lower()
            if want in t:
                opts.nth(i).click(); pause(); return True
    except: pass

    # Type + click
    try:
        loc.type(option_text, delay=60); time.sleep(1.0)
        opts = frame.locator(".select__option"); n = opts.count()
        for i in range(n):
            t = opts.nth(i).inner_text(timeout=3000).strip().lower()
            if want in t:
                opts.nth(i).click(); pause(); return True
    except: pass

    # Enter
    if page_kb:
        page_kb.keyboard.press("Enter"); pause()
    return False

def fill_form(frame, page, scan_frame=None):
    """Fill the Greenhouse form using the given frame object."""
    if scan_frame is None:
        scan_frame = frame

    # Personal
    print("  first_name...")
    try: frame.locator("#first_name").fill(FIRST, timeout=10000); pause()
    except Exception as e: print(f"    err: {e}")

    print("  last_name...")
    try: frame.locator("#last_name").fill(LAST, timeout=10000); pause()
    except Exception as e: print(f"    err: {e}")

    print("  email...")
    try: frame.locator("#email").fill(EMAIL, timeout=10000); pause()
    except Exception as e: print(f"    err: {e}")

    print("  phone...")
    try: frame.locator("#phone").fill(PHONE, timeout=10000); pause()
    except Exception as e: print(f"    err: {e}")

    print("  country...")
    try:
        combo(frame, frame.locator("#country").first, COUNTRY, page)
        print(f"  country = {COUNTRY}")
    except Exception as e: print(f"    country err: {e}")

    print("  location...")
    loc_ok = False
    for sel in ["#candidate-location", 'input[name*="location" i]', 'input[placeholder*="city" i]']:
        try:
            loc = frame.locator(sel).first
            if loc.count() > 0:
                loc.wait_for(state="visible", timeout=4000)
                loc.click(); pause(); time.sleep(0.5)
                loc.type("New York, NY", delay=60); time.sleep(2.5)
                page.keyboard.press("ArrowDown"); pause()
                page.keyboard.press("Enter"); pause()
                print(f"  location via {sel}")
                loc_ok = True; break
        except: continue
    if not loc_ok:
        print("  location: could not fill")

    print("  linkedin...")
    for sel in ['input[id*="linkedin" i]', 'input[class*="linkedin" i]']:
        try:
            loc = frame.locator(sel).first
            if loc.count() > 0:
                loc.fill(LINKEDIN, timeout=5000); pause()
                print(f"  linkedin via {sel}"); break
        except: continue

    print("  resume upload...")
    try:
        frame.locator("#resume").set_input_files(str(RESUME), timeout=10000)
        time.sleep(3); print("  resume OK")
    except Exception as e:
        print(f"  #resume err: {e}")
        try:
            # Try via page
            page.locator('input[type="file"]').nth(0).set_input_files(str(RESUME))
            time.sleep(3); print("  resume OK via page file[0]")
        except Exception as e2: print(f"  resume file[0] err: {e2}")

    if COVER.exists():
        print("  cover upload...")
        try:
            frame.locator("#cover_letter").set_input_files(str(COVER), timeout=10000)
            time.sleep(3); print("  cover OK")
        except Exception as e:
            print(f"  cover err: {e}")
            try:
                page.locator('input[type="file"]').nth(1).set_input_files(str(COVER))
                time.sleep(3); print("  cover OK via page file[1]")
            except: pass

    page.screenshot(path=str(SCREENSHOTS / "s1_uploads.png"), full_page=True)

    # Scan custom questions
    print("\n  scanning custom questions via JS...")
    try:
        questions = scan_frame.evaluate('''() => {
            const out=[];
            document.querySelectorAll("input,textarea,select").forEach(el=>{
                const rect=el.getBoundingClientRect();
                if(rect.width<=0||rect.height<=0)return;
                if(el.type==="hidden")return;
                const id=el.id||"";
                const type=el.tagName.toLowerCase()+(el.type?":"+el.type:"");
                let label="";
                if(id){const lbl=document.querySelector(`label[for="${id}"]`);if(lbl)label=(lbl.innerText||"").trim();}
                if(!label){let p=el.parentElement;for(let i=0;i<5&&p;i++){const t=(p.innerText||"").trim().split("\\n")[0];if(t&&t.length<300){label=t;break;}p=p.parentElement;}}
                out.push({id,type,label:label.substring(0,250)});
            });
            return out;
        }''')
        print(f"  {len(questions)} fields:")
        for q in questions:
            print(f"    id={q['id']!r:<40} type={q['type']!r:<25} label={q['label'][:80]!r}")
    except Exception as e:
        print(f"  scan err: {e}"); questions = []

    SKIP = {"first_name","last_name","email","phone","country","candidate-location","resume","cover_letter"}
    for q in questions:
        qid = q.get("id","")
        if qid in SKIP: continue
        label_lower = q.get("label","").lower()
        tp = q.get("type","")
        if not qid and not label_lower: continue

        try:
            if "linkedin" in label_lower or "linkedin" in qid.lower():
                frame.locator(f"#{qid}").fill(LINKEDIN, timeout=5000); pause()
                print(f"  [q] LinkedIn -> #{qid}"); continue
            if "preferred" in label_lower and ("name" in label_lower or "first" in label_lower):
                frame.locator(f"#{qid}").fill(PREFERRED, timeout=5000); pause()
                print(f"  [q] Preferred -> #{qid}"); continue
            if "salary" in label_lower or "compensation" in label_lower:
                frame.locator(f"#{qid}").fill("116000", timeout=5000); pause()
                print(f"  [q] Salary -> #{qid}"); continue
            if "website" in label_lower or "portfolio" in label_lower: continue
            if "legally authorized" in label_lower or "authorized to work" in label_lower:
                combo(frame, frame.locator(f"#{qid}"), AUTHORIZED, page)
                print(f"  [q] Authorized={AUTHORIZED}"); continue
            if "sponsorship" in label_lower or ("visa" in label_lower and "require" in label_lower) or "will you now or in the future" in label_lower:
                combo(frame, frame.locator(f"#{qid}"), SPONSOR, page)
                print(f"  [q] Sponsorship={SPONSOR}"); continue
            if "how did you hear" in label_lower or "referral" in label_lower:
                for v in ["LinkedIn","Job board","Other"]:
                    try: combo(frame, frame.locator(f"#{qid}"), v, page); print(f"  [q] Source={v}"); break
                    except: continue
                continue
            if any(k in label_lower for k in ["in office","in-office","hybrid","nyc","new york"]):
                if "select" in tp: combo(frame, frame.locator(f"#{qid}"), "Yes", page); print(f"  [q] Office=Yes")
                elif "textarea" in tp or "input:text" in tp: frame.locator(f"#{qid}").fill("Yes, available in-office New York.", timeout=5000)
                continue
            if any(k in label_lower for k in ["dei","inclusion","diversity","why ripple","tell us","experience with"]):
                if "textarea" in tp or "input:text" in tp:
                    frame.locator(f"#{qid}").fill(SCREENING_ANSWER, timeout=5000); pause()
                    print(f"  [q] DEI screen -> #{qid}")
                continue
            if any(k in label_lower for k in ["gender","hispanic","race","ethnicity","veteran","disability"]):
                if "select" in tp:
                    if "gender" in label_lower: cands=["Woman","Female"]
                    elif "hispanic" in label_lower: cands=["No","Not Hispanic or Latino"]
                    elif "race" in label_lower or "ethnicity" in label_lower: cands=["Asian","Asian (Not Hispanic or Latino)"]
                    elif "veteran" in label_lower: cands=["I am not a protected veteran","Not a protected veteran","No"]
                    elif "disability" in label_lower: cands=["No, I do not have a disability","No"]
                    else: cands=[]
                    for c in cands:
                        try: combo(frame, frame.locator(f"#{qid}"), c, page); print(f"  [demog] #{qid}={c}"); break
                        except: continue
                continue
            if label_lower: print(f"  [q] UNMAPPED: #{qid} label='{q['label'][:80]}'")
        except Exception as e:
            print(f"  [q] #{qid} err: {e}")

def submit_form(frame, page):
    """Try to find and click the submit button."""
    submitted = False
    for target in [frame, page]:
        for name in ["Submit application","Submit Application","Submit"]:
            try:
                btn = target.get_by_role("button", name=name, exact=False).first
                if btn.count() > 0:
                    btn.wait_for(state="visible", timeout=5000)
                    btn.scroll_into_view_if_needed(); pause()
                    btn.click(timeout=15000)
                    time.sleep(12)
                    submitted = True
                    print(f"  clicked '{name}'")
                    return submitted
            except: pass

    # JS fallback
    for target in [frame, page]:
        try:
            target.evaluate("""() => {
                const btns = [...document.querySelectorAll('button, input[type=submit]')];
                const sub = btns.find(b => (b.textContent||b.value||'').toLowerCase().includes('submit'));
                if (sub) { sub.click(); return true; }
                return false;
            }""")
            time.sleep(12); submitted = True
            print("  submitted via JS click")
            return submitted
        except: pass

    return False

def main():
    launch_chrome()
    time.sleep(2)

    from patchright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(f"http://localhost:{DEBUG_PORT}")
        ctx = browser.contexts[0] if browser.contexts else browser.new_context()
        page = ctx.new_page()
        page.set_default_timeout(20000)

        # ── Navigate to ripple.com ─────────────────────────────────────────
        print(f"[nav] {RIPPLE_URL}")
        try:
            page.goto(RIPPLE_URL, wait_until="networkidle", timeout=45000)
        except Exception as e:
            print(f"  networkidle timeout: {e}")
        time.sleep(5)
        page.screenshot(path=str(SCREENSHOTS / "00_ripple_loaded.png"), full_page=True)
        print(f"  url: {page.url}")
        print(f"  frames: {len(page.frames)}")

        # Accept cookies if present
        try:
            cookie_btn = page.get_by_text("Accept Cookies", exact=False).first
            if cookie_btn.count() > 0 and cookie_btn.is_visible(timeout=3000):
                cookie_btn.click(); time.sleep(1)
                print("  accepted cookies")
        except: pass

        # Click "Apply Now" to reveal the form if it's not already showing
        try:
            apply_now = page.get_by_role("link", name="Apply Now", exact=False).first
            if apply_now.count() > 0 and apply_now.is_visible(timeout=3000):
                apply_now.click(); time.sleep(3)
                print("  clicked Apply Now")
        except: pass

        # Scroll down to show the form
        page.evaluate("window.scrollTo(0, 800)"); time.sleep(2)
        page.screenshot(path=str(SCREENSHOTS / "01_scrolled.png"), full_page=True)

        # Now try to get the Greenhouse iframe element handle
        print("\n[iframe] locating Greenhouse embed...")
        iframe_frame = None

        # Method A: page.frame_locator — use the actual iframe src pattern
        try:
            fl = page.frame_locator("iframe[src*='greenhouse.io']")
            fn = fl.locator("#first_name")
            fn.wait_for(state="visible", timeout=12000)
            print("  Method A (frame_locator) worked!")
            iframe_frame = fl
        except Exception as e:
            print(f"  Method A failed: {e}")

        # Method B: Get iframe element handle -> content_frame()
        if iframe_frame is None:
            try:
                iframe_el = page.locator("iframe[src*='greenhouse.io']").first
                iframe_el.wait_for(state="attached", timeout=5000)
                frame_obj = iframe_el.content_frame()
                if frame_obj:
                    frame_obj.locator("#first_name").wait_for(state="visible", timeout=10000)
                    print("  Method B (content_frame) worked!")
                    iframe_frame = frame_obj
            except Exception as e:
                print(f"  Method B failed: {e}")

        # Method C: Search through all frames by checking for #first_name
        if iframe_frame is None:
            print("  Method C: scanning all frames for #first_name...")
            for fr in page.frames:
                try:
                    loc = fr.locator("#first_name")
                    if loc.count() > 0:
                        loc.wait_for(state="visible", timeout=3000)
                        print(f"  found in frame: {fr.url!r}")
                        iframe_frame = fr
                        break
                except: continue

        # Method D: Extract the iframe src from DOM and open in new tab
        if iframe_frame is None:
            print("  Method D: extracting iframe src and opening in new tab...")
            try:
                iframe_src = page.evaluate("""() => {
                    const iframes = document.querySelectorAll('iframe[src*="greenhouse.io"], iframe[src*="job-boards"]');
                    return iframes.length > 0 ? iframes[0].src : null;
                }""")
                print(f"  iframe src: {iframe_src!r}")
                if iframe_src:
                    new_page = ctx.new_page()
                    new_page.set_default_timeout(20000)
                    new_page.goto(iframe_src, wait_until="networkidle", timeout=40000)
                    time.sleep(4)
                    new_page.screenshot(path=str(SCREENSHOTS / "02_gh_direct.png"), full_page=True)
                    print(f"  direct tab url: {new_page.url}")
                    print(f"  direct tab title: {new_page.title()}")
                    # Check for form fields
                    try:
                        fn = new_page.locator("#first_name")
                        fn.wait_for(state="visible", timeout=10000)
                        print("  Method D worked! #first_name visible in new tab")
                        # Use new_page as our working page
                        page = new_page
                        iframe_frame = new_page
                    except Exception as e2:
                        print(f"  Method D: #first_name not found: {e2}")
                        # Scan what's on the page
                        fields = new_page.evaluate('''() => {
                            return [...document.querySelectorAll("input,textarea")].map(e=>({id:e.id,type:e.type,visible:e.getBoundingClientRect().width>0}))
                        }''')
                        print(f"  fields on direct page: {fields[:20]}")
            except Exception as e:
                print(f"  Method D failed: {e}")

        if iframe_frame is None:
            print("\n[FATAL] Cannot access Greenhouse form frame via any method")
            page.screenshot(path=str(SCREENSHOTS / "ERR_no_frame.png"), full_page=True)
            result = {"company":"Ripple","role":"Program Manager, DEI","ats":"Greenhouse",
                      "status":"FAILED_FRAME_ACCESS","confirmed_at":datetime.now().isoformat(),
                      "screenshot":str(SCREENSHOTS/"ERR_no_frame.png"),
                      "notes":"Cross-origin iframe: cannot access form fields. Need Playwright devtools protocol or alternative.",
                      "job_url":RIPPLE_URL}
            with open(ROLE_DIR/"SUBMITTED.json","w",encoding="utf-8") as f:
                json.dump(result,f,indent=2)
            time.sleep(10); return

        # ── Fill the form ──────────────────────────────────────────────────
        print(f"\n[fill] using frame type={type(iframe_frame).__name__}")
        fill_form(iframe_frame, page)

        # Pre-submit screenshots
        page.evaluate("window.scrollTo(0,0)"); time.sleep(1)
        page.screenshot(path=str(SCREENSHOTS / "s2_prefill_top.png"), full_page=True)
        page.evaluate("window.scrollTo(0,document.body.scrollHeight)"); time.sleep(2)
        page.screenshot(path=str(SCREENSHOTS / "s2_prefill_bottom.png"), full_page=True)

        # CAPTCHA check
        body_text = page.inner_text("body").lower()
        if any(c in body_text for c in ["recaptcha","hcaptcha","turnstile","i am not a robot","verify you are human"]):
            print("[CAPTCHA] detected — tab left open")
            result = {"company":"Ripple","role":"Program Manager, DEI","ats":"Greenhouse",
                      "status":"CAPTCHA_STAGED","confirmed_at":datetime.now().isoformat(),
                      "screenshot":str(SCREENSHOTS/"s2_prefill_bottom.png"),
                      "notes":"CAPTCHA before submit — form filled","job_url":RIPPLE_URL}
            with open(ROLE_DIR/"SUBMITTED.json","w",encoding="utf-8") as f:
                json.dump(result,f,indent=2)
            time.sleep(30); return

        # Submit
        print("\n[submit]")
        submitted = submit_form(iframe_frame, page)
        page.screenshot(path=str(SCREENSHOTS / "s3_after_submit.png"), full_page=True)

        final_url = page.url
        title = page.title()
        body = page.inner_text("body")
        safe = body[:2000].encode("ascii","replace").decode("ascii")
        print(f"\n[result] url={final_url}")
        print(f"[result] title={title}")
        print(f"[result] body:\n{safe[:1200]}")

        success = any(kw in body.lower() for kw in
            ["thank you","received","submitted","application received","we got your","successfully submitted"])

        status = "SUBMITTED" if success else ("ATTEMPTED_UNCONFIRMED" if submitted else "FAILED_NO_SUBMIT")
        result = {
            "company":"Ripple","role":"Program Manager, DEI","ats":"Greenhouse",
            "status":status,"confirmed_at":datetime.now().isoformat(),
            "screenshot":str(SCREENSHOTS/"s3_after_submit.png"),
            "notes":f"url={final_url} submitted={submitted} success={success}",
            "job_url":RIPPLE_URL,"body_preview":body[:2000]
        }
        with open(ROLE_DIR/"SUBMITTED.json","w",encoding="utf-8") as f:
            json.dump(result,f,indent=2)

        if success:
            print("\n" + "="*60 + "\n*** SUBMITTED TO RIPPLE ***\n" + "="*60)
        elif submitted:
            print("\n[WARN] clicked submit but no success confirmation — check screenshot")
        else:
            print("\n[ERROR] submit button never clicked")

        time.sleep(15)

if __name__ == "__main__":
    main()
