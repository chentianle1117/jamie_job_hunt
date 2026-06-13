#!/usr/bin/env python3
"""
Ripple DEI PM - Greenhouse final submit.
LAUNCH CHROME FRESH (no existing state), use persistent_context (not CDP attach).
This avoids the CDP cross-origin frame issue entirely.
Use launch_persistent_context like the original submit_greenhouse_generic.py does.
"""
import os, time, json, socket, subprocess, random
from datetime import datetime
from pathlib import Path

ROLE_DIR    = Path(r"C:\Users\chent\Agentic_Workflows_2026\oracle-job-search\outputs\2026-06-12-feed-first\applications\ripple_dei_pm")
RESUME      = ROLE_DIR / "resume.pdf"
COVER       = ROLE_DIR / "cover_letter.pdf"
SCREENSHOTS = ROLE_DIR / "screenshots"
SCREENSHOTS.mkdir(exist_ok=True)

USER_DATA   = r"C:\Users\chent\ats_agent_9404"  # dedicated profile
RIPPLE_URL  = "https://ripple.com/careers/all-jobs/job/7951682/?gh_jid=7951682"

FIRST, LAST = "Yi-Chieh", "Cheng"
EMAIL       = "jamiecheng0103@gmail.com"
PHONE       = "2137003831"
COUNTRY     = "United States"
CITY        = "New York, NY"
LINKEDIN    = "https://www.linkedin.com/in/jamieyccheng/"
PREFERRED   = "Jamie"

def pause(lo=0.4, hi=0.9): time.sleep(random.uniform(lo, hi))

def get_gh_frame(page):
    for fr in page.frames:
        if "greenhouse.io" in fr.url and "embed" in fr.url:
            return fr
    return None

def safe_fill(fr, field_id, value, desc=""):
    """Fill using locator.fill() which dispatches React-compatible events."""
    for attempt in range(3):
        try:
            loc = fr.locator(f"#{field_id}").first
            loc.wait_for(state="visible", timeout=8000)
            loc.click(timeout=5000); pause(0.2, 0.3)
            loc.press("Control+a"); pause(0.1, 0.2)
            loc.fill(value, timeout=5000); pause(0.3, 0.5)
            loc.press("Tab"); pause(0.3, 0.5)
            got = loc.input_value(timeout=3000)
            if got:
                print(f"  {desc or field_id} = {value!r}")
                return True
            else:
                print(f"  {desc or field_id}: empty after fill (attempt {attempt+1})")
        except Exception as e:
            print(f"  {desc or field_id} attempt {attempt+1}: {e}")
            time.sleep(0.5)
    return False

def combo_select(fr, field_id, option_text):
    """Drive a react-select combobox."""
    want = option_text.strip().lower()
    try:
        loc = fr.locator(f"#{field_id}").first
        loc.scroll_into_view_if_needed(); pause()
        loc.click(); pause(); time.sleep(0.7)

        opts = fr.locator(".select__option"); n = opts.count()
        for i in range(n):
            t = opts.nth(i).inner_text(timeout=3000).strip().lower()
            if want in t:
                opts.nth(i).click(); pause()
                print(f"  [{field_id}] = {option_text}")
                return True

        loc.press_sequentially(option_text, delay=80); time.sleep(1.2)
        opts = fr.locator(".select__option"); n = opts.count()
        for i in range(n):
            t = opts.nth(i).inner_text(timeout=3000).strip().lower()
            if want in t:
                opts.nth(i).click(); pause()
                print(f"  [{field_id}] = {option_text} (typed)")
                return True

        try:
            fr.select_option(f"#{field_id}", label=option_text)
            print(f"  [{field_id}] = {option_text} (native)"); return True
        except: pass

        print(f"  [{field_id}] '{option_text}' not found in options")
    except Exception as e:
        print(f"  combo {field_id}: {e}")
    return False

def main():
    from patchright.sync_api import sync_playwright
    with sync_playwright() as p:
        # Launch fresh persistent context — same approach as submit_greenhouse_generic.py
        # This avoids CDP cross-origin issues
        print("[launching Chrome via persistent context...]")
        browser = p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA,
            channel="chrome",
            headless=False,
            no_viewport=True,
            args=["--disable-popup-blocking", "--disable-notifications",
                  "--no-first-run", "--no-default-browser-check"],
        )
        page = browser.pages[0] if browser.pages else browser.new_page()
        page.set_default_timeout(25000)

        # ── Navigate ───────────────────────────────────────────────────────
        print(f"\n[nav] {RIPPLE_URL}")
        try:
            page.goto(RIPPLE_URL, wait_until="domcontentloaded", timeout=40000)
        except Exception as e:
            print(f"  {e}")
        time.sleep(6)
        page.screenshot(path=str(SCREENSHOTS / "f2_01_landing.png"), full_page=True)

        # Accept cookies
        try:
            c = page.get_by_text("Accept Cookies", exact=False).first
            if c.is_visible(timeout=2000): c.click(); time.sleep(1)
        except: pass

        # ── Click Application tab ──────────────────────────────────────────
        print("\n[Application tab]")
        try:
            btn = page.get_by_text("Application", exact=True).first
            btn.wait_for(state="visible", timeout=8000)
            btn.click(); print("  clicked")
            # Wait for GH iframe to appear in DOM
            page.locator("#grnhse_iframe").wait_for(state="attached", timeout=20000)
            print("  grnhse_iframe attached in DOM")
            time.sleep(6)
        except Exception as e:
            print(f"  {e}")
        page.screenshot(path=str(SCREENSHOTS / "f2_02_after_tab.png"), full_page=True)

        # ── Find frame ─────────────────────────────────────────────────────
        print("\n[finding frame]")
        gh_fr = None
        for i in range(15):
            time.sleep(2)
            gh_fr = get_gh_frame(page)
            if gh_fr:
                print(f"  found (attempt {i+1}): {gh_fr.url[:80]}")
                break
            # Also try frame_locator
            try:
                fl = page.frame_locator("#grnhse_iframe")
                fn_loc = fl.locator("#first_name")
                fn_loc.wait_for(state="visible", timeout=2000)
                gh_fr = fl
                print(f"  found via frame_locator (attempt {i+1})")
                break
            except: pass
            print(f"  attempt {i+1}: frames={[f.url[:50] for f in page.frames if f.url]}")

        if not gh_fr:
            print("[FATAL] can't find GH frame")
            result = {"company":"Ripple","role":"Program Manager, DEI","ats":"Greenhouse",
                      "status":"FAILED_FRAME_ACCESS","confirmed_at":datetime.now().isoformat(),
                      "screenshot":str(SCREENSHOTS/"f2_02_after_tab.png"),
                      "notes":"GH frame not accessible","job_url":RIPPLE_URL}
            with open(ROLE_DIR/"SUBMITTED.json","w",encoding="utf-8") as f: json.dump(result,f,indent=2)
            time.sleep(5); browser.close(); return

        # Wait for form
        try:
            gh_fr.locator("#first_name").wait_for(state="visible", timeout=15000)
            print("  form ready")
        except Exception as e:
            print(f"  form wait: {e}")

        # Scroll iframe into view
        try:
            page.evaluate("""() => {
                const iframe = document.getElementById('grnhse_iframe');
                if (iframe) iframe.scrollIntoView({behavior:'smooth', block:'center'});
            }"""); time.sleep(2)
        except: pass

        # ── FILL PERSONAL ──────────────────────────────────────────────────
        print("\n[personal]")
        safe_fill(gh_fr, "first_name", FIRST)
        safe_fill(gh_fr, "last_name", LAST)
        safe_fill(gh_fr, "email", EMAIL)
        safe_fill(gh_fr, "phone", PHONE)
        combo_select(gh_fr, "country", COUNTRY)

        # Location
        print("  location...")
        for attempt in range(3):
            try:
                loc_input = gh_fr.locator("#candidate-location").first
                loc_input.wait_for(state="visible", timeout=5000)
                loc_input.click(); pause()
                loc_input.press("Control+a")
                loc_input.fill(CITY); time.sleep(3.0)
                # Try picking autocomplete suggestion
                try:
                    sugg = gh_fr.locator('[role="option"]').first
                    if sugg.count() > 0 and sugg.is_visible(timeout=2500):
                        sugg.click(); pause()
                        print(f"  location via suggestion (attempt {attempt+1})")
                        break
                    else:
                        loc_input.press("ArrowDown"); pause()
                        loc_input.press("Enter"); pause()
                        loc_val = loc_input.input_value(timeout=2000)
                        if loc_val and len(loc_val) > 3:
                            print(f"  location = {loc_val!r}")
                            break
                        print(f"  location empty after ArrowDown+Enter (attempt {attempt+1})")
                except Exception as e2:
                    loc_input.press("Tab"); pause()
                    loc_val = loc_input.input_value(timeout=2000)
                    print(f"  location via Tab: {loc_val!r}")
                    if loc_val and len(loc_val) > 3:
                        break
            except Exception as e:
                print(f"  location attempt {attempt+1}: {e}")
                time.sleep(1)

        page.screenshot(path=str(SCREENSHOTS / "f2_03_personal.png"), full_page=True)

        # ── CUSTOM QUESTIONS ───────────────────────────────────────────────
        print("\n[custom questions]")
        safe_fill(gh_fr, "question_67133066", PREFERRED, "preferred")
        safe_fill(gh_fr, "question_67133067", LINKEDIN, "linkedin")
        combo_select(gh_fr, "question_67133069", "LinkedIn")   # how did you hear
        combo_select(gh_fr, "question_67133070", "Yes")        # authorized
        combo_select(gh_fr, "question_67133071", "Yes")        # sponsorship
        combo_select(gh_fr, "question_67133072", "No")         # prev employed at Ripple

        # ── UPLOADS ────────────────────────────────────────────────────────
        print("\n[uploads]")
        try:
            file_inputs = gh_fr.locator('input[type="file"]')
            n = file_inputs.count()
            print(f"  {n} file inputs")
            if n > 0:
                file_inputs.nth(0).set_input_files(str(RESUME), timeout=12000)
                time.sleep(4); print("  resume OK")
            if n > 1:
                file_inputs.nth(1).set_input_files(str(COVER), timeout=12000)
                time.sleep(3); print("  cover OK")
        except Exception as e:
            print(f"  upload: {e}")

        # ── DEMOGRAPHICS ───────────────────────────────────────────────────
        print("\n[demographics]")
        combo_select(gh_fr, "gender", "Woman")
        combo_select(gh_fr, "hispanic_ethnicity", "No")
        combo_select(gh_fr, "veteran_status", "I am not a protected veteran")
        combo_select(gh_fr, "disability_status", "No, I do not have a disability")

        # ── VERIFY & SCREENSHOT ────────────────────────────────────────────
        print("\n[verify]")
        try:
            rb = gh_fr.evaluate("""() => ({
                first: document.getElementById('first_name')?.value||'',
                last: document.getElementById('last_name')?.value||'',
                email: document.getElementById('email')?.value||'',
                phone: document.getElementById('phone')?.value||'',
                preferred: document.getElementById('question_67133066')?.value||'',
                linkedin: document.getElementById('question_67133067')?.value||'',
                location: document.getElementById('candidate-location')?.value||'',
                country_d: document.querySelector('#country .select__single-value')?.innerText||'',
                auth_d: document.querySelector('#question_67133070 .select__single-value')?.innerText||'',
                sponsor_d: document.querySelector('#question_67133071 .select__single-value')?.innerText||'',
                prev_d: document.querySelector('#question_67133072 .select__single-value')?.innerText||'',
                gender_d: document.querySelector('#gender .select__single-value')?.innerText||'',
                hispanic_d: document.querySelector('#hispanic_ethnicity .select__single-value')?.innerText||'',
                file_count: document.querySelectorAll('input[type="file"]').length,
                resume_ui: document.body.innerText.includes('resume.pdf') ? 'YES' : 'no',
                errors: [...document.querySelectorAll('[class*="error"], [aria-invalid=true]')].map(e=>e.innerText.trim()).filter(Boolean).slice(0,5),
            })""")
            print(f"  {json.dumps(rb, indent=2)}")
            # Check required fields
            required_ok = all([
                rb.get('first'), rb.get('last'), rb.get('email'), rb.get('phone'),
                rb.get('auth_d'), rb.get('sponsor_d')
            ])
            print(f"  required_ok={required_ok}")
            if not required_ok:
                print("  WARNING: some required fields appear empty — may fail validation")
        except Exception as e:
            print(f"  readback: {e}")

        try: page.evaluate("window.scrollTo(0,0)"); time.sleep(1)
        except: pass
        page.screenshot(path=str(SCREENSHOTS / "f2_04_prefill_top.png"), full_page=True)
        try: page.evaluate("window.scrollTo(0, document.body.scrollHeight)"); time.sleep(2)
        except: pass
        page.screenshot(path=str(SCREENSHOTS / "f2_04_prefill_bottom.png"), full_page=True)

        # CAPTCHA check
        body_text = page.inner_text("body").lower()
        if any(c in body_text for c in ["recaptcha","hcaptcha","turnstile","i am not a robot"]):
            print("\n[CAPTCHA] — leaving tab open")
            result = {"company":"Ripple","role":"Program Manager, DEI","ats":"Greenhouse",
                      "status":"CAPTCHA_STAGED","confirmed_at":datetime.now().isoformat(),
                      "screenshot":str(SCREENSHOTS/"f2_04_prefill_bottom.png"),
                      "notes":"CAPTCHA before submit — form filled, awaiting human","job_url":RIPPLE_URL}
            with open(ROLE_DIR/"SUBMITTED.json","w",encoding="utf-8") as f: json.dump(result,f,indent=2)
            time.sleep(30); browser.close(); return

        # ── SUBMIT ─────────────────────────────────────────────────────────
        print("\n[SUBMIT]")
        submitted = False

        # Scroll to bottom of iframe
        try:
            page.evaluate("""() => {
                const iframe = document.getElementById('grnhse_iframe');
                if (iframe) iframe.scrollIntoView({behavior:'smooth', block:'end'});
            }"""); time.sleep(2)
        except: pass

        for btn_name in ["Submit application","Submit Application","Submit"]:
            try:
                btn = gh_fr.get_by_role("button", name=btn_name, exact=False).first
                if btn.count() > 0:
                    btn.wait_for(state="visible", timeout=8000)
                    btn.scroll_into_view_if_needed(); pause()
                    btn.click(timeout=15000)
                    time.sleep(15); submitted = True
                    print(f"  clicked '{btn_name}'")
                    break
            except Exception as e:
                print(f"  btn '{btn_name}': {e}")

        if not submitted:
            try:
                res = gh_fr.evaluate("""() => {
                    const btns = [...document.querySelectorAll('button, input[type=submit]')];
                    const sub = btns.find(b=>(b.textContent||b.value||'').toLowerCase().includes('submit'));
                    if (sub) { sub.scrollIntoView(); sub.click(); return 'clicked: '+(sub.textContent||'').trim(); }
                    return 'not found: '+btns.map(b=>(b.textContent||'').trim().substring(0,20)).join('|');
                }""")
                print(f"  JS: {res}")
                time.sleep(15); submitted = True
            except Exception as e:
                print(f"  JS: {e}")

        page.screenshot(path=str(SCREENSHOTS / "f2_05_after_submit.png"), full_page=True)

        # ── VERIFY RESULT ──────────────────────────────────────────────────
        page_body = page.inner_text("body")
        frame_body = ""
        try: frame_body = gh_fr.inner_text("body")
        except: pass
        combined = page_body + "\n" + frame_body

        safe = combined[:4000].encode("ascii","replace").decode("ascii")
        print(f"\n[result] url={page.url}")
        print(f"[result] body:\n{safe[:3000]}")

        success = any(kw in combined.lower() for kw in [
            "thank you","received","submitted","application received",
            "we got your","successfully submitted","your application has been submitted",
            "application complete"
        ])

        status = "SUBMITTED" if success else ("ATTEMPTED_UNCONFIRMED" if submitted else "FAILED_NO_SUBMIT")
        if success:
            print("\n" + "="*60 + "\n*** RIPPLE SUBMITTED ***\n" + "="*60)
        elif submitted:
            print("\n[WARN] clicked submit but no confirmation keyword")
        else:
            print("\n[ERROR] submit not clicked")

        result_json = {
            "company":"Ripple","role":"Program Manager, DEI","ats":"Greenhouse",
            "status":status,"confirmed_at":datetime.now().isoformat(),
            "screenshot":str(SCREENSHOTS/"f2_05_after_submit.png"),
            "notes":f"submitted={submitted} success={success} url={page.url}",
            "job_url":RIPPLE_URL,"body_preview":combined[:2000]
        }
        with open(ROLE_DIR/"SUBMITTED.json","w",encoding="utf-8") as f:
            json.dump(result_json,f,indent=2)

        time.sleep(20)
        browser.close()

if __name__ == "__main__":
    main()
