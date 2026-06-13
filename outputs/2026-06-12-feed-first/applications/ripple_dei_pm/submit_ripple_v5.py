#!/usr/bin/env python3
"""
Ripple DEI PM - Greenhouse submit v5.
Fixed issues from v4/final:
1. File upload: use file input within the frame (query_selector approach)
2. "Previously employed by Ripple?" -> "No"
3. Demographics: use react-select patterns correctly
4. Submit: use the frame's submit button properly (not JS click on parent page)
5. Wait properly for each action
"""
import os, time, json, socket, subprocess, random
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
    for fr in page.frames:
        if "greenhouse.io" in fr.url and "embed" in fr.url:
            return fr
    return None

def combo_select(fr, page, field_id, option_text):
    """Drive a Greenhouse react-select combobox by field ID."""
    want = option_text.strip().lower()
    try:
        # The visible input for react-select has the field_id; the actual select has a different ID
        # Click the container div (the react-select wrapper)
        container = fr.locator(f"#{field_id}").first
        container.scroll_into_view_if_needed(); pause()
        container.click(); pause(); time.sleep(0.7)

        # Check for pre-rendered options
        opts = fr.locator(".select__option"); n = opts.count()
        for i in range(n):
            t = opts.nth(i).inner_text(timeout=3000).strip().lower()
            if want in t:
                opts.nth(i).click(); pause()
                print(f"  [{field_id}] = {option_text}")
                return True

        # Type to filter
        container.type(option_text, delay=60); time.sleep(1.0)
        opts = fr.locator(".select__option"); n = opts.count()
        for i in range(n):
            t = opts.nth(i).inner_text(timeout=3000).strip().lower()
            if want in t:
                opts.nth(i).click(); pause()
                print(f"  [{field_id}] = {option_text} (typed)")
                return True

        # Try native select element (for demographics which might not be react-select)
        try:
            fr.select_option(f"#{field_id}", label=option_text)
            print(f"  [{field_id}] = {option_text} (native)"); return True
        except: pass

        page.keyboard.press("Escape"); pause()
    except Exception as e:
        print(f"  combo_select {field_id}: {e}")
    return False

def upload_file_to_frame_input(fr, input_id, file_path):
    """Upload file to a file input inside a frame."""
    try:
        # Try direct set_input_files
        fr.locator(f"#{input_id}").set_input_files(str(file_path), timeout=10000)
        time.sleep(3)
        print(f"  upload #{input_id} OK (direct)")
        return True
    except Exception as e:
        print(f"  upload #{input_id} direct err: {e}")

    # Try query_selector approach via evaluate
    try:
        fr.evaluate(f"""() => {{
            const inp = document.getElementById('{input_id}');
            if (!inp) return 'not found';
            return 'found: type=' + inp.type;
        }}""")
    except: pass

    # Try via page locator with iframe context
    try:
        # Use set_input_files on the frame directly
        file_input = fr.locator(f'input[type="file"]').first
        file_input.set_input_files(str(file_path), timeout=10000)
        time.sleep(3)
        print(f"  upload file[0] in frame OK")
        return True
    except Exception as e2:
        print(f"  upload file[0] in frame err: {e2}")

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

        # ── 1. Navigate ────────────────────────────────────────────────────
        print(f"\n[1] nav to Ripple careers page")
        try:
            page.goto(RIPPLE_URL, wait_until="domcontentloaded", timeout=40000)
        except Exception as e:
            print(f"  nav: {e}")
        time.sleep(5)

        # Accept cookies
        try:
            c = page.get_by_text("Accept Cookies", exact=False).first
            if c.is_visible(timeout=2000): c.click(); time.sleep(1)
        except: pass

        page.screenshot(path=str(SCREENSHOTS / "01_landing.png"), full_page=True)

        # ── 2. Click Application tab ───────────────────────────────────────
        print("\n[2] clicking Application tab...")
        try:
            app_tab = page.get_by_text("Application", exact=True).first
            app_tab.wait_for(state="visible", timeout=5000)
            app_tab.click(); time.sleep(5)
            print("  clicked Application tab")
        except Exception as e:
            print(f"  Application tab err: {e}")
            # Try scrolling to application section
            page.evaluate("window.scrollTo(0, 1000)"); time.sleep(2)

        page.screenshot(path=str(SCREENSHOTS / "02_after_app_tab.png"), full_page=True)

        # ── 3. Find Greenhouse frame ───────────────────────────────────────
        print("\n[3] finding Greenhouse frame...")
        gh_fr = None
        for attempt in range(8):
            time.sleep(2)
            gh_fr = get_gh_frame(page)
            if gh_fr:
                print(f"  found frame (attempt {attempt+1}): {gh_fr.url[:80]}")
                break
            print(f"  not found (attempt {attempt+1}), frames: {[f.url[:50] for f in page.frames if f.url]}")

        if not gh_fr:
            print("[FATAL] no Greenhouse frame")
            result = {"company":"Ripple","role":"Program Manager, DEI","ats":"Greenhouse",
                      "status":"FAILED_FRAME_ACCESS","confirmed_at":datetime.now().isoformat(),
                      "screenshot":str(SCREENSHOTS/"02_after_app_tab.png"),
                      "notes":"Greenhouse iframe not found after Application tab click","job_url":RIPPLE_URL}
            with open(ROLE_DIR/"SUBMITTED.json","w",encoding="utf-8") as f: json.dump(result,f,indent=2)
            time.sleep(5); return

        # ── 4. Wait for form ───────────────────────────────────────────────
        print("\n[4] waiting for form...")
        try:
            gh_fr.locator("#first_name").wait_for(state="visible", timeout=20000)
            print("  form ready")
        except Exception as e:
            print(f"  form wait err: {e}")

        # Scroll the frame to make it visible
        try:
            page.evaluate("""() => {
                const iframe = document.querySelector('iframe[src*="greenhouse"]');
                if (iframe) iframe.scrollIntoView({behavior:'smooth', block:'center'});
            }"""); time.sleep(2)
        except: pass

        # ── 5. Fill personal ───────────────────────────────────────────────
        print("\n[5] personal fields...")
        for fid, val in [("first_name", FIRST), ("last_name", LAST), ("email", EMAIL), ("phone", PHONE)]:
            try:
                loc = gh_fr.locator(f"#{fid}")
                loc.wait_for(state="visible", timeout=8000)
                loc.triple_click(); loc.fill(val); pause()
                print(f"  {fid} = {val}")
            except Exception as e:
                print(f"  {fid} err: {e}")

        # Country
        try:
            combo_select(gh_fr, page, "country", COUNTRY)
        except Exception as e: print(f"  country err: {e}")

        # Location
        try:
            loc = gh_fr.locator("#candidate-location").first
            loc.wait_for(state="visible", timeout=5000)
            loc.click(); pause(); time.sleep(0.5)
            loc.triple_click(); loc.type("New York, NY", delay=60); time.sleep(2.5)
            # Try to pick suggestion
            try:
                sugg = gh_fr.locator('[role="option"], .pac-item').first
                if sugg.is_visible(timeout=2000):
                    sugg.click(); pause(); print("  location via suggestion")
                else:
                    page.keyboard.press("ArrowDown"); pause()
                    page.keyboard.press("Enter"); pause()
                    print("  location via ArrowDown+Enter")
            except:
                page.keyboard.press("Tab"); pause()
                print("  location via Tab")
        except Exception as e:
            print(f"  location err: {e}")

        # ── 6. Custom questions (now we know the exact IDs) ───────────────
        print("\n[6] custom questions...")

        # q67133066: Preferred First Name
        try:
            gh_fr.locator("#question_67133066").fill(PREFERRED, timeout=5000); pause()
            print(f"  preferred = {PREFERRED}")
        except Exception as e: print(f"  preferred err: {e}")

        # q67133067: LinkedIn Profile
        try:
            gh_fr.locator("#question_67133067").fill(LINKEDIN, timeout=5000); pause()
            print(f"  linkedin = {LINKEDIN}")
        except Exception as e: print(f"  linkedin err: {e}")

        # q67133068: Website — skip (no value)
        # q67133069: How did you hear?
        try:
            combo_select(gh_fr, page, "question_67133069", "LinkedIn")
        except Exception as e: print(f"  source err: {e}")

        # q67133070: Are you legally authorized to work in the U.S.? -> Yes
        try:
            combo_select(gh_fr, page, "question_67133070", "Yes")
        except Exception as e: print(f"  authorized err: {e}")

        # q67133071: Will you require visa sponsorship? -> Yes
        try:
            combo_select(gh_fr, page, "question_67133071", "Yes")
        except Exception as e: print(f"  sponsorship err: {e}")

        # q67133072: Have you previously been employed by Ripple? -> No
        try:
            combo_select(gh_fr, page, "question_67133072", "No")
        except Exception as e: print(f"  prev_employed err: {e}")

        # Demographics
        print("\n[7] demographics...")
        # gender
        try:
            combo_select(gh_fr, page, "gender", "Woman")
        except Exception as e:
            try: combo_select(gh_fr, page, "gender", "Female")
            except: print(f"  gender err: {e}")

        # hispanic_ethnicity
        try:
            combo_select(gh_fr, page, "hispanic_ethnicity", "No")
        except Exception as e: print(f"  hispanic err: {e}")

        # race (if present — scan showed no 'race' field, skip)

        # veteran_status
        try:
            combo_select(gh_fr, page, "veteran_status", "I am not a protected veteran")
        except Exception as e:
            try: combo_select(gh_fr, page, "veteran_status", "Not a Protected Veteran")
            except: print(f"  veteran err: {e}")

        # disability_status
        try:
            combo_select(gh_fr, page, "disability_status", "No, I do not have a disability")
        except Exception as e:
            try: combo_select(gh_fr, page, "disability_status", "No")
            except: print(f"  disability err: {e}")

        # ── 8. File uploads ────────────────────────────────────────────────
        print("\n[8] file uploads...")
        # Resume - using set_input_files on the frame's file input
        resume_ok = False
        try:
            # First try #resume in the frame
            file_inputs = gh_fr.locator('input[type="file"]')
            n = file_inputs.count()
            print(f"  found {n} file inputs in frame")
            if n > 0:
                file_inputs.nth(0).set_input_files(str(RESUME), timeout=12000)
                time.sleep(4); resume_ok = True
                print("  resume OK via frame file[0]")
        except Exception as e:
            print(f"  frame file[0] err: {e}")
            # Try the named input
            try:
                gh_fr.locator('#resume, input[name="resume"], input[name="application[resume]"]').first.set_input_files(str(RESUME), timeout=10000)
                time.sleep(3); resume_ok = True
                print("  resume OK via named selector")
            except Exception as e2:
                print(f"  named selector err: {e2}")

        if COVER.exists():
            try:
                file_inputs = gh_fr.locator('input[type="file"]')
                n = file_inputs.count()
                if n > 1:
                    file_inputs.nth(1).set_input_files(str(COVER), timeout=12000)
                    time.sleep(3); print("  cover OK via frame file[1]")
                else:
                    # Try #cover_letter
                    gh_fr.locator('#cover_letter, input[name="cover_letter"]').first.set_input_files(str(COVER), timeout=10000)
                    time.sleep(3); print("  cover OK via named selector")
            except Exception as e:
                print(f"  cover err: {e}")

        page.screenshot(path=str(SCREENSHOTS / "03_before_readback.png"), full_page=True)

        # Readback to verify
        try:
            readback = gh_fr.evaluate("""() => {
                const get = id => document.getElementById(id);
                const fileLabel = id => {
                    const el = get(id);
                    if (!el) return 'no-element';
                    if (el.files && el.files.length > 0) return el.files[0].name;
                    // Check nearby text for filename
                    const p = el.closest('.field');
                    if (p) {
                        const txt = p.innerText || '';
                        const m = txt.match(/([\\w.-]+\\.(pdf|doc|docx))/i);
                        if (m) return m[0];
                    }
                    return 'not-attached';
                };
                const sel_val = id => {
                    const el = get(id);
                    if (!el) return 'no-field';
                    return el.value || '';
                };
                return {
                    first: sel_val('first_name'), last: sel_val('last_name'),
                    email: sel_val('email'), phone: sel_val('phone'),
                    country: sel_val('country'),
                    location: sel_val('candidate-location'),
                    preferred: sel_val('question_67133066'),
                    linkedin: sel_val('question_67133067'),
                    authorized: sel_val('question_67133070'),
                    sponsor: sel_val('question_67133071'),
                    prev_ripple: sel_val('question_67133072'),
                    gender: sel_val('gender'),
                    hispanic: sel_val('hispanic_ethnicity'),
                    veteran: sel_val('veteran_status'),
                    disability: sel_val('disability_status'),
                    resume_files: fileLabel('resume'),
                    cover_files: fileLabel('cover_letter'),
                    num_file_inputs: document.querySelectorAll('input[type="file"]').length,
                };
            }""")
            print(f"\n  READBACK:\n  {json.dumps(readback, indent=2)}")
        except Exception as e:
            print(f"  readback err: {e}")

        page.screenshot(path=str(SCREENSHOTS / "04_prefill_top.png"), full_page=True)
        try: page.evaluate("window.scrollTo(0, document.body.scrollHeight)"); time.sleep(2)
        except: pass
        page.screenshot(path=str(SCREENSHOTS / "04_prefill_bottom.png"), full_page=True)

        # CAPTCHA check
        body_text = page.inner_text("body").lower()
        if any(c in body_text for c in ["recaptcha","hcaptcha","turnstile","i am not a robot","verify you are human"]):
            print("\n[CAPTCHA] detected — tab left open for human")
            result = {"company":"Ripple","role":"Program Manager, DEI","ats":"Greenhouse",
                      "status":"CAPTCHA_STAGED","confirmed_at":datetime.now().isoformat(),
                      "screenshot":str(SCREENSHOTS/"04_prefill_bottom.png"),
                      "notes":"CAPTCHA before submit — form filled","job_url":RIPPLE_URL}
            with open(ROLE_DIR/"SUBMITTED.json","w",encoding="utf-8") as f: json.dump(result,f,indent=2)
            print("[done] leaving tab open — form is filled"); time.sleep(30); return

        # ── 9. SUBMIT ─────────────────────────────────────────────────────
        print("\n[9] SUBMITTING...")
        submitted = False

        # Scroll into the frame to make submit button visible
        try:
            page.evaluate("""() => {
                const iframe = document.querySelector('iframe[src*="greenhouse"]');
                if (iframe) iframe.scrollIntoView({behavior:'smooth', block:'end'});
            }"""); time.sleep(2)
        except: pass

        # Try frame submit button
        for btn_name in ["Submit application","Submit Application","Submit"]:
            try:
                btn = gh_fr.get_by_role("button", name=btn_name, exact=False).first
                if btn.count() > 0:
                    btn.wait_for(state="visible", timeout=8000)
                    btn.scroll_into_view_if_needed(); pause()
                    btn.click(timeout=15000)
                    time.sleep(12); submitted = True
                    print(f"  clicked '{btn_name}' in frame")
                    break
            except Exception as e:
                print(f"  frame btn '{btn_name}': {e}")

        # Try on parent page
        if not submitted:
            for btn_name in ["Submit application","Submit Application","Submit"]:
                try:
                    btn = page.get_by_role("button", name=btn_name, exact=False).first
                    if btn.count() > 0:
                        btn.wait_for(state="visible", timeout=5000)
                        btn.scroll_into_view_if_needed(); pause()
                        btn.click(timeout=15000)
                        time.sleep(12); submitted = True
                        print(f"  clicked '{btn_name}' on page")
                        break
                except: pass

        # JS click inside frame
        if not submitted:
            try:
                result = gh_fr.evaluate("""() => {
                    const btns = [...document.querySelectorAll('button, input[type=submit]')];
                    const sub = btns.find(b => (b.textContent||b.value||'').toLowerCase().includes('submit'));
                    if (sub) { sub.click(); return 'clicked: ' + (sub.textContent||sub.value); }
                    return 'not found, btns: ' + btns.map(b=>(b.textContent||b.value||'').trim().substring(0,30)).join('|');
                }""")
                print(f"  JS in frame: {result}")
                time.sleep(12); submitted = True
            except Exception as e:
                print(f"  JS frame err: {e}")

        page.screenshot(path=str(SCREENSHOTS / "05_after_submit.png"), full_page=True)

        # ── 10. Verify ────────────────────────────────────────────────────
        final_url = page.url
        title = page.title()
        page_body = page.inner_text("body")
        frame_body = ""
        try:
            frame_body = gh_fr.inner_text("body")
        except: pass

        combined_body = page_body + frame_body
        safe = combined_body[:2500].encode("ascii","replace").decode("ascii")
        print(f"\n[result] url={final_url}")
        print(f"[result] title={title}")
        print(f"[result] body:\n{safe[:1500]}")

        success = any(kw in combined_body.lower() for kw in [
            "thank you","received","submitted","application received",
            "we got your","successfully submitted","your application"
        ])

        status = "SUBMITTED" if success else ("ATTEMPTED_UNCONFIRMED" if submitted else "FAILED_NO_SUBMIT")

        if success: print("\n" + "="*60 + "\n*** RIPPLE SUBMITTED ***\n" + "="*60)
        elif submitted: print("\n[WARN] clicked submit, no confirmation keyword")
        else: print("\n[ERROR] submit never clicked")

        result_json = {
            "company":"Ripple","role":"Program Manager, DEI","ats":"Greenhouse",
            "status":status,"confirmed_at":datetime.now().isoformat(),
            "screenshot":str(SCREENSHOTS/"05_after_submit.png"),
            "notes":f"url={final_url} submitted={submitted} success={success} resume_ok={resume_ok}",
            "job_url":RIPPLE_URL,"body_preview":combined_body[:2000]
        }
        with open(ROLE_DIR/"SUBMITTED.json","w",encoding="utf-8") as f:
            json.dump(result_json,f,indent=2)

        time.sleep(15)

if __name__ == "__main__":
    main()
