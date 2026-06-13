#!/usr/bin/env python3
"""
Ripple DEI PM — Greenhouse iframe submit FINAL.

Key discoveries:
1. boards.greenhouse.io/ripple/jobs/7951682 redirects to ripple.com careers page
2. The form is NOT shown by default — must click the "Application" button/tab first
3. After click, an iframe loads: job-boards.greenhouse.io/embed/job_app?for=ripple&validityToken=...
4. The frame appears in page.frames list as frame [5] after the Application tab click
5. We access it via page.frames iteration (looking for job-boards.greenhouse.io in URL)
6. File uploads must use the frame's locator (not page.locator) to hit the correct input
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
    print("[chrome] launching...")
    subprocess.Popen([CHROME_BIN, f"--remote-debugging-port={DEBUG_PORT}",
                      f"--user-data-dir={USER_DATA}", "--no-first-run",
                      "--no-default-browser-check", "--window-size=1400,960"],
                     creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP)
    for _ in range(15):
        time.sleep(1)
        if is_port_open(DEBUG_PORT): print("[chrome] ready"); return

def get_gh_frame(page):
    """Find the Greenhouse embed frame from page.frames."""
    for fr in page.frames:
        if "greenhouse.io" in fr.url and "embed" in fr.url:
            return fr
    return None

def combo(fr, locator, option_text):
    """Drive a react-select or native select combobox."""
    want = option_text.strip().lower()
    if isinstance(locator, str):
        loc = fr.locator(locator)
    else:
        loc = locator
    try: loc.scroll_into_view_if_needed(); pause()
    except: pass
    loc.click(); pause(); time.sleep(0.7)

    # Pre-rendered options (react-select)
    try:
        opts = fr.locator(".select__option"); n = opts.count()
        for i in range(n):
            t = opts.nth(i).inner_text(timeout=3000).strip().lower()
            if want in t:
                opts.nth(i).click(); pause(); return True
    except: pass

    # Type to filter
    try:
        loc.type(option_text, delay=60); time.sleep(1.0)
        opts = fr.locator(".select__option"); n = opts.count()
        for i in range(n):
            t = opts.nth(i).inner_text(timeout=3000).strip().lower()
            if want in t:
                opts.nth(i).click(); pause(); return True
    except: pass

    # Native select
    try:
        fr.select_option(locator if isinstance(locator, str) else f"#{loc.first.get_attribute('id')}", label=option_text)
        print(f"    native select: {option_text}"); return True
    except: pass

    # Enter
    try:
        loc.press("Enter"); pause()
    except: pass
    return False

def fill_location(fr, page):
    for sel in ["#candidate-location", 'input[name*="location" i]', 'input[placeholder*="city" i]']:
        try:
            loc = fr.locator(sel).first
            if loc.count() > 0:
                loc.wait_for(state="visible", timeout=4000)
                loc.click(); pause(); time.sleep(0.5)
                loc.type("New York, NY", delay=60); time.sleep(2.5)
                # Try dropdown suggestion
                try:
                    sugg = fr.locator('[role="option"], .pac-item, .suggestion').first
                    if sugg.count() > 0 and sugg.is_visible(timeout=2000):
                        sugg.click(); pause(); return True
                except: pass
                page.keyboard.press("ArrowDown"); pause()
                page.keyboard.press("Enter"); pause()
                print(f"  location via {sel}")
                return True
        except: continue
    return False

def fill_demog(fr, qid, candidates):
    for c in candidates:
        want = c.strip().lower()
        try:
            loc = fr.locator(f"#{qid}")
            loc.scroll_into_view_if_needed(); pause()
            loc.click(); pause(); time.sleep(0.5)
            # Pre-rendered options
            opts = fr.locator(".select__option"); n = opts.count()
            found = False
            for i in range(n):
                t = opts.nth(i).inner_text(timeout=2000).strip().lower()
                if want in t:
                    opts.nth(i).click(); pause(); print(f"  demog #{qid}={c}"); return True
            if not found:
                # type
                loc.type(c, delay=60); time.sleep(0.8)
                opts = fr.locator(".select__option"); n = opts.count()
                for i in range(n):
                    t = opts.nth(i).inner_text(timeout=2000).strip().lower()
                    if want in t:
                        opts.nth(i).click(); pause(); print(f"  demog #{qid}={c} (typed)"); return True
        except: pass
    # Try native select
    try:
        fr.select_option(f"#{qid}", label=candidates[0])
        print(f"  demog #{qid}={candidates[0]} (native)"); return True
    except: pass
    print(f"  demog #{qid}: could not fill")
    return False

def main():
    launch_chrome()
    time.sleep(2)

    from patchright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(f"http://localhost:{DEBUG_PORT}")
        print(f"[cdp] {len(browser.contexts)} contexts")
        ctx = browser.contexts[0] if browser.contexts else browser.new_context()
        page = ctx.new_page()
        page.set_default_timeout(20000)

        # ── 1. Navigate ────────────────────────────────────────────────────
        print(f"\n[1] nav to {RIPPLE_URL}")
        try:
            page.goto(RIPPLE_URL, wait_until="domcontentloaded", timeout=40000)
        except Exception as e:
            print(f"  nav err: {e}")
        time.sleep(5)
        page.screenshot(path=str(SCREENSHOTS / "01_landing.png"), full_page=True)

        # Accept cookies
        try:
            c = page.get_by_text("Accept Cookies", exact=False).first
            if c.is_visible(timeout=2000): c.click(); time.sleep(1); print("  cookies accepted")
        except: pass

        # ── 2. Click "Application" tab to reveal the Greenhouse form ──────
        print("\n[2] clicking Application tab...")
        clicked = False
        for try_text in ["Application", "Apply Now"]:
            try:
                btn = page.get_by_text(try_text, exact=True).first
                if btn.count() > 0 and btn.is_visible(timeout=3000):
                    btn.click(); time.sleep(4); clicked = True
                    print(f"  clicked '{try_text}'")
                    break
            except: pass
        if not clicked:
            print("  Application tab not found — trying scroll")
            page.evaluate("window.scrollTo(0, 800)"); time.sleep(2)

        page.screenshot(path=str(SCREENSHOTS / "02_after_app_tab.png"), full_page=True)

        # ── 3. Wait for Greenhouse iframe to appear ────────────────────────
        print("\n[3] waiting for Greenhouse frame...")
        gh_fr = None
        for wait_s in [2, 3, 4, 5]:
            time.sleep(wait_s)
            gh_fr = get_gh_frame(page)
            if gh_fr:
                print(f"  found: {gh_fr.url[:80]}")
                break
            print(f"  not yet ({wait_s}s)... frames: {[f.url[:40] for f in page.frames]}")

        if not gh_fr:
            # One more fallback: get iframe src from DOM and open it in a new tab
            print("  fallback: extracting iframe src from DOM...")
            try:
                iframe_src = page.evaluate("""() => {
                    const iframes = document.querySelectorAll('iframe');
                    for (const f of iframes) {
                        if (f.src && (f.src.includes('greenhouse') || f.src.includes('job-boards'))) return f.src;
                    }
                    return null;
                }""")
                print(f"  iframe_src: {iframe_src!r}")
                if iframe_src:
                    page2 = ctx.new_page()
                    page2.set_default_timeout(20000)
                    try:
                        page2.goto(iframe_src, wait_until="domcontentloaded", timeout=30000)
                    except: pass
                    time.sleep(4)
                    page2.screenshot(path=str(SCREENSHOTS / "03_iframe_direct.png"), full_page=True)
                    print(f"  direct iframe tab: {page2.url}")
                    # Check for form
                    try:
                        page2.locator("#first_name").wait_for(state="visible", timeout=8000)
                        print("  form visible in direct iframe tab!")
                        gh_fr = page2
                        page = page2
                    except Exception as e2:
                        print(f"  form not in direct iframe tab: {e2}")
                        # Scan what's there
                        fields = page2.evaluate('''() => [...document.querySelectorAll("input,textarea,select")].map(e=>({id:e.id,visible:e.getBoundingClientRect().width>0}))''')
                        print(f"  fields: {fields[:20]}")
            except Exception as e:
                print(f"  fallback err: {e}")

        if not gh_fr:
            print("\n[FATAL] Cannot access Greenhouse form")
            result = {"company":"Ripple","role":"Program Manager, DEI","ats":"Greenhouse",
                      "status":"FAILED_FRAME_ACCESS","confirmed_at":datetime.now().isoformat(),
                      "screenshot":str(SCREENSHOTS/"02_after_app_tab.png"),
                      "notes":"Greenhouse iframe not accessible via CDP after Application tab click",
                      "job_url":RIPPLE_URL}
            with open(ROLE_DIR/"SUBMITTED.json","w",encoding="utf-8") as f:
                json.dump(result,f,indent=2)
            time.sleep(10); return

        # ── 4. Wait for form to be ready ──────────────────────────────────
        print("\n[4] waiting for form fields...")
        try:
            gh_fr.locator("#first_name").wait_for(state="visible", timeout=15000)
            print("  form ready")
        except Exception as e:
            print(f"  form not ready: {e}")
            # Scan all fields to understand what's there
            fields = gh_fr.evaluate('''() => [...document.querySelectorAll("input,textarea,select")].map(e=>({id:e.id,visible:e.getBoundingClientRect().width>0}))''')
            print(f"  fields: {fields[:20]}")

        # ── 5. Fill personal fields ────────────────────────────────────────
        print("\n[5] filling personal fields...")

        try: gh_fr.locator("#first_name").fill(FIRST, timeout=10000); pause(); print(f"  first_name={FIRST}")
        except Exception as e: print(f"  first_name err: {e}")

        try: gh_fr.locator("#last_name").fill(LAST, timeout=10000); pause(); print(f"  last_name={LAST}")
        except Exception as e: print(f"  last_name err: {e}")

        try: gh_fr.locator("#email").fill(EMAIL, timeout=10000); pause(); print(f"  email={EMAIL}")
        except Exception as e: print(f"  email err: {e}")

        try: gh_fr.locator("#phone").fill(PHONE, timeout=10000); pause(); print(f"  phone={PHONE}")
        except Exception as e: print(f"  phone err: {e}")

        # Country combobox
        try:
            combo(gh_fr, gh_fr.locator("#country").first, COUNTRY)
            print(f"  country={COUNTRY}")
        except Exception as e: print(f"  country err: {e}")

        # Location
        if not fill_location(gh_fr, page):
            print("  location: not filled")

        # LinkedIn
        for sel in ['input[id*="linkedin" i]', 'input[name*="linkedin" i]']:
            try:
                loc = gh_fr.locator(sel).first
                if loc.count() > 0:
                    loc.fill(LINKEDIN, timeout=5000); pause()
                    print(f"  linkedin via {sel}"); break
            except: continue

        # ── 6. Upload files ────────────────────────────────────────────────
        print("\n[6] uploading files...")
        try:
            gh_fr.locator("#resume").set_input_files(str(RESUME), timeout=12000)
            time.sleep(3); print("  resume OK")
        except Exception as e:
            print(f"  #resume err: {e}")
            # Try via the page (parent frame)
            try:
                page.locator('input[type="file"]').nth(0).set_input_files(str(RESUME))
                time.sleep(3); print("  resume OK via page file[0]")
            except Exception as e2:
                print(f"  file[0] err: {e2}")

        if COVER.exists():
            try:
                gh_fr.locator("#cover_letter").set_input_files(str(COVER), timeout=12000)
                time.sleep(3); print("  cover OK")
            except Exception as e:
                print(f"  #cover_letter err: {e}")
                try:
                    page.locator('input[type="file"]').nth(1).set_input_files(str(COVER))
                    time.sleep(3); print("  cover OK via page file[1]")
                except: pass

        page.screenshot(path=str(SCREENSHOTS / "04_uploads.png"), full_page=True)

        # ── 7. Scan + fill custom questions ───────────────────────────────
        print("\n[7] scanning custom questions...")
        try:
            questions = gh_fr.evaluate('''() => {
                const out=[];
                document.querySelectorAll("input,textarea,select").forEach(el=>{
                    const rect=el.getBoundingClientRect();
                    if(rect.width<=0||rect.height<=0)return;
                    if(el.type==="hidden")return;
                    const id=el.id||""; const type=el.tagName.toLowerCase()+(el.type?":"+el.type:"");
                    let label="";
                    if(id){const lbl=document.querySelector(`label[for="${id}"]`);if(lbl)label=(lbl.innerText||"").trim();}
                    if(!label){let p=el.parentElement;for(let i=0;i<5&&p;i++){const t=(p.innerText||"").trim().split("\\n")[0];if(t&&t.length<300){label=t;break;}p=p.parentElement;}}
                    out.push({id,type,label:label.substring(0,250)});
                });
                return out;
            }''')
            print(f"  {len(questions)} fields found:")
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
                    gh_fr.locator(f"#{qid}").fill(LINKEDIN, timeout=5000); pause()
                    print(f"  [q] LinkedIn #{qid}"); continue

                if "preferred" in label_lower and ("name" in label_lower or "first" in label_lower):
                    gh_fr.locator(f"#{qid}").fill(PREFERRED, timeout=5000); pause()
                    print(f"  [q] Preferred #{qid}"); continue

                if "salary" in label_lower or "compensation" in label_lower:
                    gh_fr.locator(f"#{qid}").fill("116000", timeout=5000); pause()
                    print(f"  [q] Salary #{qid}"); continue

                if "website" in label_lower or "portfolio" in label_lower: continue

                if "legally authorized" in label_lower or "authorized to work" in label_lower:
                    combo(gh_fr, gh_fr.locator(f"#{qid}"), AUTHORIZED)
                    print(f"  [q] Authorized={AUTHORIZED}"); continue

                if "sponsorship" in label_lower or "will you now or in the future" in label_lower or ("visa" in label_lower and "require" in label_lower):
                    combo(gh_fr, gh_fr.locator(f"#{qid}"), SPONSOR)
                    print(f"  [q] Sponsorship={SPONSOR}"); continue

                if "how did you hear" in label_lower or "referral" in label_lower:
                    for v in ["LinkedIn","Job board","Other"]:
                        try: combo(gh_fr, gh_fr.locator(f"#{qid}"), v); print(f"  [q] Source={v}"); break
                        except: continue
                    continue

                if any(k in label_lower for k in ["in office","in-office","hybrid","nyc","new york"]):
                    if "select" in tp: combo(gh_fr, gh_fr.locator(f"#{qid}"), "Yes"); print(f"  [q] Office=Yes")
                    elif "textarea" in tp or "input:text" in tp:
                        gh_fr.locator(f"#{qid}").fill("Yes, available to work in-office in New York.", timeout=5000)
                    continue

                if "us-based" in label_lower or "us based" in label_lower:
                    combo(gh_fr, gh_fr.locator(f"#{qid}"), "Yes"); print(f"  [q] USBased=Yes"); continue

                if "18 years" in label_lower or "at least 18" in label_lower:
                    combo(gh_fr, gh_fr.locator(f"#{qid}"), "Yes"); print(f"  [q] Age18+=Yes"); continue

                if any(k in label_lower for k in ["dei","inclusion","diversity","why ripple","tell us","experience with"]):
                    if "textarea" in tp or "input:text" in tp:
                        gh_fr.locator(f"#{qid}").fill(SCREENING_ANSWER, timeout=5000); pause()
                        print(f"  [q] DEI screen #{qid}")
                    continue

                if any(k in label_lower for k in ["gender","hispanic","race","ethnicity","veteran","disability"]):
                    if "select" in tp:
                        if "gender" in label_lower: cands=["Woman","Female"]
                        elif "hispanic" in label_lower: cands=["No","Not Hispanic or Latino"]
                        elif "race" in label_lower or "ethnicity" in label_lower: cands=["Asian","Asian (Not Hispanic or Latino)"]
                        elif "veteran" in label_lower: cands=["I am not a protected veteran","Not a protected veteran","No"]
                        elif "disability" in label_lower: cands=["No, I do not have a disability","No"]
                        else: cands=[]
                        if cands: fill_demog(gh_fr, qid, cands)
                    continue

                if label_lower: print(f"  [q] UNMAPPED: #{qid} label='{q['label'][:80]}'")
            except Exception as e:
                print(f"  [q] #{qid} err: {e}")

        # ── 8. Pre-submit screenshots (scroll to verify) ───────────────────
        print("\n[8] pre-submit review screenshots...")
        try:
            page.evaluate("window.scrollTo(0,0)"); time.sleep(1)
        except: pass
        page.screenshot(path=str(SCREENSHOTS / "05_prefill_top.png"), full_page=True)
        try:
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)"); time.sleep(2)
        except: pass
        page.screenshot(path=str(SCREENSHOTS / "05_prefill_bottom.png"), full_page=True)

        # Read back key values from the form to confirm (no fabrication check)
        try:
            readback = gh_fr.evaluate("""() => ({
                first: document.getElementById('first_name')?.value || '',
                last: document.getElementById('last_name')?.value || '',
                email: document.getElementById('email')?.value || '',
                phone: document.getElementById('phone')?.value || '',
                resume: (() => { const f=document.getElementById('resume'); return f ? (f.files?.[0]?.name || 'attached') : 'none'; })(),
                cover: (() => { const f=document.getElementById('cover_letter'); return f ? (f.files?.[0]?.name || 'none') : 'no-cover-field'; })(),
            })""")
            print(f"\n  READBACK: {readback}")
        except Exception as e:
            print(f"  readback err: {e}")

        # ── 9. CAPTCHA check ──────────────────────────────────────────────
        body_text = page.inner_text("body").lower()
        if any(c in body_text for c in ["recaptcha","hcaptcha","turnstile","i am not a robot","verify you are human"]):
            print("\n[CAPTCHA] detected — tab left open for human")
            result = {"company":"Ripple","role":"Program Manager, DEI","ats":"Greenhouse",
                      "status":"CAPTCHA_STAGED","confirmed_at":datetime.now().isoformat(),
                      "screenshot":str(SCREENSHOTS/"05_prefill_bottom.png"),
                      "notes":"CAPTCHA detected — form filled, awaiting human submit","job_url":RIPPLE_URL}
            with open(ROLE_DIR/"SUBMITTED.json","w",encoding="utf-8") as f:
                json.dump(result,f,indent=2)
            print("[done] leaving tab open — form is filled")
            time.sleep(30); return

        # ── 10. SUBMIT ────────────────────────────────────────────────────
        print("\n[10] SUBMITTING...")
        submitted = False

        for target in [gh_fr, page]:
            for btn_name in ["Submit application","Submit Application","Submit"]:
                try:
                    btn = target.get_by_role("button", name=btn_name, exact=False).first
                    if btn.count() > 0:
                        btn.wait_for(state="visible", timeout=5000)
                        btn.scroll_into_view_if_needed(); pause()
                        btn.click(timeout=15000)
                        time.sleep(12); submitted = True
                        print(f"  clicked '{btn_name}'")
                        break
                except: pass
            if submitted: break

        if not submitted:
            for target in [gh_fr, page]:
                try:
                    result = target.evaluate("""() => {
                        const btns = [...document.querySelectorAll('button, input[type=submit]')];
                        const sub = btns.find(b => (b.textContent||b.value||'').toLowerCase().includes('submit'));
                        if (sub) { sub.click(); return true; } return false;
                    }""")
                    if result:
                        time.sleep(12); submitted = True
                        print("  JS click succeeded"); break
                except: pass

        page.screenshot(path=str(SCREENSHOTS / "06_after_submit.png"), full_page=True)

        # ── 11. Verify ────────────────────────────────────────────────────
        final_url = page.url
        title = page.title()
        body = page.inner_text("body")
        safe = body[:2500].encode("ascii","replace").decode("ascii")
        print(f"\n[result] url={final_url}")
        print(f"[result] title={title}")
        print(f"[result] body:\n{safe[:1500]}")

        success = any(kw in body.lower() for kw in [
            "thank you","received","submitted","application received",
            "we got your","successfully submitted","your application"
        ])

        # Also check the frame's body
        if not success and gh_fr:
            try:
                fr_body = gh_fr.inner_text("body")
                if any(kw in fr_body.lower() for kw in ["thank you","received","submitted","application received"]):
                    success = True
                    safe_fr = fr_body[:800].encode("ascii","replace").decode("ascii")
                    print(f"\n[frame body confirms success]:\n{safe_fr}")
            except: pass

        if not success and not submitted:
            print("\n[ERROR] submit never clicked")
        elif not success:
            print("\n[WARN] submitted but no confirmation — check screenshot")
            # Show errors
            try:
                errs = page.locator('.error, [class*="error"]').all()
                print(f"  {len(errs)} error elements:")
                for e in errs[:10]:
                    t = (e.text_content() or "").strip()
                    if t: print(f"    - {t[:200]}")
            except: pass

        status = "SUBMITTED" if success else ("ATTEMPTED_UNCONFIRMED" if submitted else "FAILED_NO_SUBMIT")

        result = {
            "company":"Ripple","role":"Program Manager, DEI","ats":"Greenhouse",
            "status":status,"confirmed_at":datetime.now().isoformat(),
            "screenshot":str(SCREENSHOTS/"06_after_submit.png"),
            "notes":f"url={final_url} title={title} submitted={submitted} success={success}",
            "job_url":RIPPLE_URL,"body_preview":body[:2000]
        }
        with open(ROLE_DIR/"SUBMITTED.json","w",encoding="utf-8") as f:
            json.dump(result,f,indent=2)

        if success:
            print("\n" + "="*60 + "\n*** RIPPLE APPLICATION SUBMITTED ***\n" + "="*60)

        time.sleep(15)

if __name__ == "__main__":
    main()
