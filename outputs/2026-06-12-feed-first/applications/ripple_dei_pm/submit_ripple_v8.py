#!/usr/bin/env python3
"""
Ripple DEI PM - Greenhouse submit v8.
Key insight: Patchright's locator.fill() should work for React inputs.
Previous attempts failed because:
  - triple_click() doesn't exist -> use click(click_count=3) or select_all keyboard
  - key_down() doesn't exist -> use down()
  - The frame locator works fine for standard inputs
  - The issue was that after fill(), React state wasn't updating for SOME fields

Let's try using page.keyboard.press('Control+a') syntax (not key_down/key_up separately).
Also: use locator.press_sequentially() which types char by char.

For text fields: click() -> select_all keyboard -> fill()
This is the proven working pattern for React inputs in Patchright.
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

def pause(lo=0.4, hi=0.9): time.sleep(random.uniform(lo, hi))
def is_port_open(port):
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=2):
            return True
    except: return False

def launch_chrome():
    if is_port_open(DEBUG_PORT):
        print(f"[chrome] already on {DEBUG_PORT}"); return
    subprocess.Popen([CHROME_BIN, f"--remote-debugging-port={DEBUG_PORT}",
                      f"--user-data-dir={USER_DATA}", "--no-first-run",
                      "--no-default-browser-check", "--window-size=1400,960"],
                     creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP)
    for _ in range(15):
        time.sleep(1)
        if is_port_open(DEBUG_PORT): return

def get_gh_frame(page):
    for fr in page.frames:
        if "greenhouse.io" in fr.url and "embed" in fr.url:
            return fr
    return None

def fill_react_input(gh_fr, field_id, value, desc=""):
    """Fill a React-controlled input by clicking + clearing + filling."""
    for attempt in range(3):
        try:
            loc = gh_fr.locator(f"#{field_id}").first
            loc.wait_for(state="visible", timeout=8000)
            # Click to focus
            loc.click(timeout=5000); pause(0.2, 0.4)
            # Select all and delete
            loc.press("Control+a"); pause(0.1, 0.2)
            loc.press("Delete"); pause(0.1, 0.2)
            # Fill using Patchright fill (dispatches input events)
            loc.fill(value, timeout=5000); pause(0.3, 0.5)
            # Press Tab to trigger onBlur
            loc.press("Tab"); pause(0.3, 0.5)
            # Verify
            got = loc.input_value(timeout=3000)
            if got and len(got) > 0:
                print(f"  {desc or field_id} = {value!r}")
                return True
            else:
                print(f"  {desc or field_id}: empty after fill (attempt {attempt+1})")
        except Exception as e:
            print(f"  {desc or field_id} attempt {attempt+1}: {e}")
            time.sleep(1)
    # Final fallback: press_sequentially
    try:
        loc = gh_fr.locator(f"#{field_id}").first
        loc.click(); pause()
        loc.press("Control+a"); pause()
        loc.press_sequentially(value, delay=80); pause()
        loc.press("Tab"); pause()
        got = loc.input_value(timeout=2000)
        print(f"  {desc or field_id} = {value!r} (press_seq, got={got!r})")
        return bool(got)
    except Exception as e:
        print(f"  {desc or field_id} press_sequentially: {e}")
    return False

def combo_select(gh_fr, field_id, option_text):
    """Drive a Greenhouse react-select combobox."""
    want = option_text.strip().lower()
    try:
        loc = gh_fr.locator(f"#{field_id}").first
        loc.scroll_into_view_if_needed(); pause()
        loc.click(); pause(); time.sleep(0.7)

        # Pre-rendered options
        opts = gh_fr.locator(".select__option"); n = opts.count()
        for i in range(n):
            t = opts.nth(i).inner_text(timeout=3000).strip().lower()
            if want in t:
                opts.nth(i).click(); pause()
                print(f"  [{field_id}] = {option_text}")
                return True

        # Type to filter
        loc.press_sequentially(option_text, delay=80); time.sleep(1.2)
        opts = gh_fr.locator(".select__option"); n = opts.count()
        for i in range(n):
            t = opts.nth(i).inner_text(timeout=3000).strip().lower()
            if want in t:
                opts.nth(i).click(); pause()
                print(f"  [{field_id}] = {option_text} (typed)")
                return True

        # Native select
        try:
            gh_fr.select_option(f"#{field_id}", label=option_text)
            print(f"  [{field_id}] = {option_text} (native)"); return True
        except: pass

        print(f"  [{field_id}] option '{option_text}' not found")
    except Exception as e:
        print(f"  combo {field_id}: {e}")
    return False

def main():
    launch_chrome()
    time.sleep(2)

    from patchright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(f"http://localhost:{DEBUG_PORT}")
        ctx = browser.contexts[0] if browser.contexts else browser.new_context()

        # Close existing ripple pages
        for pg in list(ctx.pages):
            try:
                if "ripple" in pg.url or "greenhouse" in pg.url:
                    pg.close()
            except: pass
        time.sleep(1)

        page = ctx.new_page()
        page.set_default_timeout(20000)

        # ── Navigate ───────────────────────────────────────────────────────
        print(f"\n[nav] {RIPPLE_URL}")
        try:
            page.goto(RIPPLE_URL, wait_until="domcontentloaded", timeout=40000)
        except Exception as e:
            print(f"  {e}")
        time.sleep(6)

        # Accept cookies
        try:
            c = page.get_by_text("Accept Cookies", exact=False).first
            if c.is_visible(timeout=2000): c.click(); time.sleep(1)
        except: pass

        page.screenshot(path=str(SCREENSHOTS / "v8_01_landing.png"), full_page=True)

        # ── Click Application tab ──────────────────────────────────────────
        print("\n[click Application tab]")
        try:
            btn = page.get_by_text("Application", exact=True).first
            btn.wait_for(state="visible", timeout=8000)
            btn.click(); time.sleep(6); print("  clicked")
        except Exception as e:
            print(f"  {e}")

        # ── Find frame ─────────────────────────────────────────────────────
        print("\n[finding frame]")
        gh_fr = None
        for i in range(10):
            time.sleep(2)
            gh_fr = get_gh_frame(page)
            if gh_fr: print(f"  found (attempt {i+1})"); break

        if not gh_fr:
            result = {"company":"Ripple","role":"Program Manager, DEI","ats":"Greenhouse",
                      "status":"FAILED_FRAME_ACCESS","confirmed_at":datetime.now().isoformat(),
                      "screenshot":str(SCREENSHOTS/"v8_01_landing.png"),
                      "notes":"GH frame not found","job_url":RIPPLE_URL}
            with open(ROLE_DIR/"SUBMITTED.json","w",encoding="utf-8") as f: json.dump(result,f,indent=2)
            return

        # Wait for form
        try:
            gh_fr.locator("#first_name").wait_for(state="visible", timeout=15000)
            print("  form ready")
        except Exception as e:
            print(f"  {e}")

        # Scroll iframe to center
        try:
            page.evaluate("""() => {
                const iframe = document.querySelector('iframe[src*="greenhouse"]');
                if (iframe) iframe.scrollIntoView({behavior:'smooth', block:'center'});
            }"""); time.sleep(2)
        except: pass

        # ── Personal fields ────────────────────────────────────────────────
        print("\n[personal]")
        fill_react_input(gh_fr, "first_name", FIRST, "first_name")
        fill_react_input(gh_fr, "last_name", LAST, "last_name")
        fill_react_input(gh_fr, "email", EMAIL, "email")
        fill_react_input(gh_fr, "phone", PHONE, "phone")

        # Country combobox
        combo_select(gh_fr, "country", COUNTRY)

        # Location
        print("  location...")
        try:
            loc_input = gh_fr.locator("#candidate-location").first
            loc_input.wait_for(state="visible", timeout=5000)
            loc_input.click(); pause()
            loc_input.press("Control+a"); pause()
            loc_input.fill(CITY); time.sleep(2.5)
            # Suggestion
            try:
                sugg = gh_fr.locator('[role="option"], .pac-container .pac-item').first
                if sugg.count() > 0 and sugg.is_visible(timeout=2000):
                    sugg.click(); pause(); print("  location via suggestion")
                else:
                    loc_input.press("ArrowDown"); pause()
                    loc_input.press("Enter"); pause()
                    print("  location via ArrowDown+Enter")
            except:
                loc_input.press("Tab"); pause()
                print("  location via Tab")
        except Exception as e:
            print(f"  location: {e}")

        page.screenshot(path=str(SCREENSHOTS / "v8_02_personal.png"), full_page=True)

        # ── Custom questions ───────────────────────────────────────────────
        print("\n[custom questions]")
        fill_react_input(gh_fr, "question_67133066", PREFERRED, "preferred")
        fill_react_input(gh_fr, "question_67133067", LINKEDIN, "linkedin")
        combo_select(gh_fr, "question_67133069", "LinkedIn")
        combo_select(gh_fr, "question_67133070", "Yes")
        combo_select(gh_fr, "question_67133071", "Yes")
        combo_select(gh_fr, "question_67133072", "No")

        # ── File uploads ───────────────────────────────────────────────────
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

        # ── Demographics ───────────────────────────────────────────────────
        print("\n[demographics]")
        combo_select(gh_fr, "gender", "Woman")
        combo_select(gh_fr, "hispanic_ethnicity", "No")
        combo_select(gh_fr, "veteran_status", "I am not a protected veteran")
        combo_select(gh_fr, "disability_status", "No, I do not have a disability")

        # ── Verify state ───────────────────────────────────────────────────
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
                num_file_inputs: document.querySelectorAll('input[type="file"]').length,
                file0_files: document.querySelectorAll('input[type="file"]')[0]?.files?.length || 0,
                // check for resume.pdf text in DOM
                resume_text: [...document.querySelectorAll('.resume-name, .file-name, [class*="filename"]')].map(e=>e.innerText).join('|'),
                // react-select displayed values
                country_display: document.querySelector('#country .select__single-value')?.innerText || '',
                auth_display: document.querySelector('#question_67133070 .select__single-value')?.innerText || '',
                sponsor_display: document.querySelector('#question_67133071 .select__single-value')?.innerText || '',
                prev_display: document.querySelector('#question_67133072 .select__single-value')?.innerText || '',
                gender_display: document.querySelector('#gender .select__single-value')?.innerText || '',
                hispanic_display: document.querySelector('#hispanic_ethnicity .select__single-value')?.innerText || '',
                veteran_display: document.querySelector('#veteran_status .select__single-value')?.innerText || '',
                disability_display: document.querySelector('#disability_status .select__single-value')?.innerText || '',
                errors: [...document.querySelectorAll('.error-message, [class*="error"], [aria-invalid=true]')]
                    .map(e=>e.innerText.trim()).filter(Boolean).slice(0,10),
            })""")
            print(f"  {json.dumps(rb, indent=2)}")
        except Exception as e:
            print(f"  readback err: {e}")

        try: page.evaluate("window.scrollTo(0,0)"); time.sleep(1)
        except: pass
        page.screenshot(path=str(SCREENSHOTS / "v8_03_prefill_top.png"), full_page=True)
        try: page.evaluate("window.scrollTo(0, document.body.scrollHeight)"); time.sleep(2)
        except: pass
        page.screenshot(path=str(SCREENSHOTS / "v8_03_prefill_bottom.png"), full_page=True)

        # CAPTCHA check
        body_text = page.inner_text("body").lower()
        if any(c in body_text for c in ["recaptcha","hcaptcha","turnstile","i am not a robot"]):
            print("\n[CAPTCHA] — leaving tab open")
            result = {"company":"Ripple","role":"Program Manager, DEI","ats":"Greenhouse",
                      "status":"CAPTCHA_STAGED","confirmed_at":datetime.now().isoformat(),
                      "screenshot":str(SCREENSHOTS/"v8_03_prefill_bottom.png"),
                      "notes":"CAPTCHA before submit — form filled","job_url":RIPPLE_URL}
            with open(ROLE_DIR/"SUBMITTED.json","w",encoding="utf-8") as f: json.dump(result,f,indent=2)
            time.sleep(30); return

        # ── SUBMIT ─────────────────────────────────────────────────────────
        print("\n[SUBMIT]")
        submitted = False

        try:
            page.evaluate("""() => {
                const iframe = document.querySelector('iframe[src*="greenhouse"]');
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
                    const btns = [...document.querySelectorAll('button[type=submit], button, input[type=submit]')];
                    const sub = btns.find(b => (b.textContent||b.value||'').toLowerCase().includes('submit'));
                    if (sub) { sub.scrollIntoView(); sub.click(); return 'clicked: ' + (sub.textContent||'').trim().substring(0,30); }
                    return 'no submit btn, have: ' + btns.map(b=>(b.textContent||b.value||'').trim().substring(0,20)).join('|');
                }""")
                print(f"  JS: {res}")
                time.sleep(15); submitted = True
            except Exception as e:
                print(f"  JS: {e}")

        page.screenshot(path=str(SCREENSHOTS / "v8_04_after_submit.png"), full_page=True)

        # Verify
        final_url = page.url
        title = page.title()
        page_body = page.inner_text("body")
        frame_body = ""
        try: frame_body = gh_fr.inner_text("body")
        except: pass

        combined = page_body + "\n" + frame_body
        safe = combined[:4000].encode("ascii","replace").decode("ascii")
        print(f"\n[result] url={final_url}")
        print(f"[result] body:\n{safe[:3000]}")

        success = any(kw in combined.lower() for kw in [
            "thank you","received","submitted","application received",
            "we got your","successfully submitted","your application has been submitted"
        ])

        status = "SUBMITTED" if success else ("ATTEMPTED_UNCONFIRMED" if submitted else "FAILED_NO_SUBMIT")
        if success:
            print("\n" + "="*60 + "\n*** RIPPLE SUBMITTED ***\n" + "="*60)
        elif submitted:
            print("\n[WARN] clicked submit but no confirmation")

        result_json = {
            "company":"Ripple","role":"Program Manager, DEI","ats":"Greenhouse",
            "status":status,"confirmed_at":datetime.now().isoformat(),
            "screenshot":str(SCREENSHOTS/"v8_04_after_submit.png"),
            "notes":f"url={final_url} submitted={submitted} success={success}",
            "job_url":RIPPLE_URL,"body_preview":combined[:2000]
        }
        with open(ROLE_DIR/"SUBMITTED.json","w",encoding="utf-8") as f:
            json.dump(result_json,f,indent=2)

        time.sleep(15)

if __name__ == "__main__":
    main()
