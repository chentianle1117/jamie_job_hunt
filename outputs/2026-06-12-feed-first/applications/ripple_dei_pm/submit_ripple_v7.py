#!/usr/bin/env python3
"""
Ripple DEI PM - Greenhouse submit v7.
Key fix: use page.keyboard.type() after clicking into the input (not frame.fill())
because Greenhouse's React form needs native keyboard events to register.
Also: after filling each field, click away (Tab) to trigger onBlur/onChange.
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

def type_into_field(page, gh_fr, field_id, value, desc=""):
    """Click into a field in the GH frame, then type via keyboard."""
    try:
        loc = gh_fr.locator(f"#{field_id}").first
        loc.wait_for(state="visible", timeout=8000)
        loc.click(timeout=6000); pause(0.3, 0.5)
        # Clear existing content
        page.keyboard.key_down("Control")
        page.keyboard.press("a")
        page.keyboard.key_up("Control")
        page.keyboard.press("Backspace")
        pause(0.2, 0.3)
        # Type the value
        page.keyboard.type(value, delay=80)
        pause(0.3, 0.5)
        # Tab to commit (triggers onBlur)
        page.keyboard.press("Tab")
        pause(0.3, 0.5)
        # Verify
        got = loc.input_value(timeout=3000)
        print(f"  {desc or field_id}: typed={value!r} got={got!r}")
        return bool(got)
    except Exception as e:
        print(f"  {desc or field_id} err: {e}")
        return False

def combo_select(page, gh_fr, field_id, option_text):
    """Drive a Greenhouse react-select combobox."""
    want = option_text.strip().lower()
    try:
        loc = gh_fr.locator(f"#{field_id}").first
        loc.scroll_into_view_if_needed(); pause()
        loc.click(); pause(); time.sleep(0.6)

        # Check pre-rendered options
        opts = gh_fr.locator(".select__option"); n = opts.count()
        for i in range(n):
            t = opts.nth(i).inner_text(timeout=3000).strip().lower()
            if want in t:
                opts.nth(i).click(); pause()
                print(f"  [{field_id}] = {option_text}")
                return True

        # Type to filter
        page.keyboard.type(option_text, delay=80); time.sleep(1.2)
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

        print(f"  [{field_id}] option {option_text!r} not found")
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

        # Close all existing ripple/greenhouse pages
        for pg in list(ctx.pages):
            try:
                if "ripple" in pg.url or "greenhouse" in pg.url:
                    pg.close()
            except: pass
        time.sleep(1)

        page = ctx.new_page()
        page.set_default_timeout(20000)

        # ── 1. Navigate ────────────────────────────────────────────────────
        print(f"\n[1] nav to {RIPPLE_URL}")
        try:
            page.goto(RIPPLE_URL, wait_until="domcontentloaded", timeout=40000)
        except Exception as e:
            print(f"  nav: {e}")
        time.sleep(6)
        page.screenshot(path=str(SCREENSHOTS / "v7_01_landing.png"), full_page=True)

        # Accept cookies
        try:
            c = page.get_by_text("Accept Cookies", exact=False).first
            if c.is_visible(timeout=2000): c.click(); time.sleep(1)
        except: pass

        # ── 2. Click Application tab ───────────────────────────────────────
        print("\n[2] clicking Application tab...")
        try:
            btn = page.get_by_text("Application", exact=True).first
            btn.wait_for(state="visible", timeout=8000)
            btn.click(); time.sleep(6)
            print("  clicked")
        except Exception as e:
            print(f"  err: {e}")
        page.screenshot(path=str(SCREENSHOTS / "v7_02_after_tab.png"), full_page=True)

        # ── 3. Find frame ──────────────────────────────────────────────────
        print("\n[3] finding GH frame...")
        gh_fr = None
        for i in range(10):
            time.sleep(2)
            gh_fr = get_gh_frame(page)
            if gh_fr:
                print(f"  found (attempt {i+1})")
                break

        if not gh_fr:
            print("[FATAL] no frame found")
            result = {"company":"Ripple","role":"Program Manager, DEI","ats":"Greenhouse",
                      "status":"FAILED_FRAME_ACCESS","confirmed_at":datetime.now().isoformat(),
                      "screenshot":str(SCREENSHOTS/"v7_02_after_tab.png"),
                      "notes":"GH frame not found","job_url":RIPPLE_URL}
            with open(ROLE_DIR/"SUBMITTED.json","w",encoding="utf-8") as f: json.dump(result,f,indent=2)
            return

        # ── 4. Wait for form ───────────────────────────────────────────────
        try:
            gh_fr.locator("#first_name").wait_for(state="visible", timeout=15000)
            print("  form ready")
        except Exception as e:
            print(f"  form wait: {e}")

        # Scroll iframe into center view
        try:
            page.evaluate("""() => {
                const iframe = document.querySelector('iframe[src*="greenhouse"]');
                if (iframe) iframe.scrollIntoView({behavior:'smooth', block:'center'});
            }"""); time.sleep(2)
        except: pass

        # ── 5. Personal fields (keyboard type) ────────────────────────────
        print("\n[5] personal fields...")
        type_into_field(page, gh_fr, "first_name", FIRST, "first_name")
        type_into_field(page, gh_fr, "last_name", LAST, "last_name")
        type_into_field(page, gh_fr, "email", EMAIL, "email")
        type_into_field(page, gh_fr, "phone", PHONE, "phone")

        # Country combobox
        combo_select(page, gh_fr, "country", COUNTRY)

        # Location
        print("  location...")
        try:
            loc_input = gh_fr.locator("#candidate-location").first
            loc_input.wait_for(state="visible", timeout=5000)
            loc_input.click(); pause(); time.sleep(0.5)
            # Clear and type
            page.keyboard.key_down("Control"); page.keyboard.press("a"); page.keyboard.key_up("Control")
            page.keyboard.press("Backspace"); pause(0.2, 0.3)
            page.keyboard.type(CITY, delay=80); time.sleep(2.5)
            # Try suggestion
            try:
                sugg = gh_fr.locator('[role="option"]').first
                if sugg.count() > 0 and sugg.is_visible(timeout=2000):
                    sugg.click(); pause()
                    print("  location via suggestion")
                else:
                    page.keyboard.press("ArrowDown"); pause()
                    page.keyboard.press("Enter"); pause()
                    print("  location via ArrowDown+Enter")
            except:
                page.keyboard.press("Tab"); pause()
                print("  location via Tab")
        except Exception as e:
            print(f"  location err: {e}")

        page.screenshot(path=str(SCREENSHOTS / "v7_03_personal_done.png"), full_page=True)

        # Verify personal
        try:
            v = gh_fr.evaluate("""() => ({
                first: document.getElementById('first_name')?.value||'EMPTY',
                last: document.getElementById('last_name')?.value||'EMPTY',
                email: document.getElementById('email')?.value||'EMPTY',
                phone: document.getElementById('phone')?.value||'EMPTY',
            })""")
            print(f"  personal verify: {v}")
            all_ok = all(v.get(k) and v[k] != 'EMPTY' for k in ['first','last','email','phone'])
            if not all_ok:
                print("  WARNING: some personal fields empty — attempting JS React setter...")
                for (fid, val) in [("first_name", FIRST), ("last_name", LAST), ("email", EMAIL), ("phone", PHONE)]:
                    gh_fr.evaluate(f"""() => {{
                        const el = document.getElementById('{fid}');
                        if (!el) return;
                        const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;
                        setter.call(el, '{val}');
                        el.dispatchEvent(new Event('input', {{bubbles:true}}));
                        el.dispatchEvent(new Event('change', {{bubbles:true}}));
                        el.dispatchEvent(new Event('blur', {{bubbles:true}}));
                    }}""")
                time.sleep(1)
                v2 = gh_fr.evaluate("""() => ({
                    first: document.getElementById('first_name')?.value||'EMPTY',
                    last: document.getElementById('last_name')?.value||'EMPTY',
                    email: document.getElementById('email')?.value||'EMPTY',
                    phone: document.getElementById('phone')?.value||'EMPTY',
                })""")
                print(f"  after JS setter: {v2}")
        except Exception as e:
            print(f"  verify err: {e}")

        # ── 6. Custom questions ────────────────────────────────────────────
        print("\n[6] custom questions...")
        type_into_field(page, gh_fr, "question_67133066", PREFERRED, "preferred")
        type_into_field(page, gh_fr, "question_67133067", LINKEDIN, "linkedin")

        # How did you hear? (q67133069)
        combo_select(page, gh_fr, "question_67133069", "LinkedIn")

        # Authorized (q67133070)
        combo_select(page, gh_fr, "question_67133070", "Yes")

        # Sponsorship (q67133071)
        combo_select(page, gh_fr, "question_67133071", "Yes")

        # Previously at Ripple? (q67133072)
        combo_select(page, gh_fr, "question_67133072", "No")

        # ── 7. File uploads ────────────────────────────────────────────────
        print("\n[7] file uploads...")
        try:
            file_inputs = gh_fr.locator('input[type="file"]')
            n = file_inputs.count()
            print(f"  {n} file inputs in frame")
            if n > 0:
                file_inputs.nth(0).set_input_files(str(RESUME), timeout=12000)
                time.sleep(4); print("  resume OK")
            if n > 1:
                file_inputs.nth(1).set_input_files(str(COVER), timeout=12000)
                time.sleep(3); print("  cover OK")
            elif n == 1 and COVER.exists():
                # Cover field may be separate
                try:
                    gh_fr.locator("#cover_letter").set_input_files(str(COVER), timeout=8000)
                    time.sleep(3); print("  cover OK via #cover_letter")
                except: print("  no second file input")
        except Exception as e:
            print(f"  upload err: {e}")

        # ── 8. Demographics ────────────────────────────────────────────────
        print("\n[8] demographics...")
        combo_select(page, gh_fr, "gender", "Woman")
        combo_select(page, gh_fr, "hispanic_ethnicity", "No")
        combo_select(page, gh_fr, "veteran_status", "I am not a protected veteran")
        combo_select(page, gh_fr, "disability_status", "No, I do not have a disability")

        # ── 9. Pre-submit screenshots ──────────────────────────────────────
        print("\n[9] pre-submit screenshots...")
        try: page.evaluate("window.scrollTo(0,0)"); time.sleep(1)
        except: pass
        page.screenshot(path=str(SCREENSHOTS / "v7_04_prefill_top.png"), full_page=True)
        try: page.evaluate("window.scrollTo(0, document.body.scrollHeight)"); time.sleep(2)
        except: pass
        page.screenshot(path=str(SCREENSHOTS / "v7_04_prefill_bottom.png"), full_page=True)

        # Final readback
        try:
            rb = gh_fr.evaluate("""() => {
                const g = id => document.getElementById(id)?.value||'';
                const sel = id => {
                    const wrapper = document.getElementById(id)?.closest('.field');
                    return wrapper?.querySelector('.select__single-value')?.innerText || g(id) || '';
                };
                return {
                    first: g('first_name'), last: g('last_name'),
                    email: g('email'), phone: g('phone'),
                    preferred: g('question_67133066'), linkedin: g('question_67133067'),
                    country_shown: document.querySelector('#country .select__single-value')?.innerText || '',
                    auth_shown: document.querySelector('#question_67133070 .select__single-value')?.innerText || '',
                    sponsor_shown: document.querySelector('#question_67133071 .select__single-value')?.innerText || '',
                    prev_shown: document.querySelector('#question_67133072 .select__single-value')?.innerText || '',
                    gender_shown: document.querySelector('#gender .select__single-value')?.innerText || '',
                    location_shown: g('candidate-location'),
                    file0: document.querySelectorAll('input[type="file"]')[0]?.files?.[0]?.name || 'none',
                    // Check for any error messages
                    errors: [...document.querySelectorAll('.error-message, .field-error, [aria-invalid=true]')].map(e=>e.innerText.trim()).filter(Boolean),
                };
            }""")
            print(f"  READBACK: {json.dumps(rb, indent=2)}")
        except Exception as e:
            print(f"  readback err: {e}")

        # CAPTCHA check
        body_text = page.inner_text("body").lower()
        if any(c in body_text for c in ["recaptcha","hcaptcha","turnstile","i am not a robot"]):
            print("\n[CAPTCHA] — leaving tab open")
            result = {"company":"Ripple","role":"Program Manager, DEI","ats":"Greenhouse",
                      "status":"CAPTCHA_STAGED","confirmed_at":datetime.now().isoformat(),
                      "screenshot":str(SCREENSHOTS/"v7_04_prefill_bottom.png"),
                      "notes":"CAPTCHA before submit","job_url":RIPPLE_URL}
            with open(ROLE_DIR/"SUBMITTED.json","w",encoding="utf-8") as f: json.dump(result,f,indent=2)
            time.sleep(30); return

        # ── 10. SUBMIT ────────────────────────────────────────────────────
        print("\n[10] SUBMITTING...")
        submitted = False

        # Scroll to submit button
        try:
            page.evaluate("""() => {
                const iframe = document.querySelector('iframe[src*="greenhouse"]');
                if (iframe) iframe.scrollIntoView({behavior:'smooth', block:'end'});
            }"""); time.sleep(2)
        except: pass

        # Try submit in frame
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

        # JS submit inside frame
        if not submitted:
            try:
                res = gh_fr.evaluate("""() => {
                    const btns = [...document.querySelectorAll('button[type=submit], button:not([type]), input[type=submit]')];
                    const found = btns.filter(b => (b.textContent||b.value||'').toLowerCase().includes('submit'));
                    if (found.length > 0) {
                        found[0].scrollIntoView();
                        found[0].click();
                        return 'clicked: ' + (found[0].textContent||found[0].value||'').trim();
                    }
                    // All buttons
                    return 'no submit found, all btns: ' + btns.map(b=>(b.textContent||b.value||'no-text').trim().substring(0,25)).join('|');
                }""")
                print(f"  JS: {res}")
                time.sleep(15); submitted = True
            except Exception as e:
                print(f"  JS err: {e}")

        page.screenshot(path=str(SCREENSHOTS / "v7_05_after_submit.png"), full_page=True)

        # ── 11. Verify ────────────────────────────────────────────────────
        final_url = page.url
        title = page.title()
        page_body = page.inner_text("body")
        frame_body = ""
        try: frame_body = gh_fr.inner_text("body")
        except: pass

        combined = page_body + "\n" + frame_body
        safe = combined[:3000].encode("ascii","replace").decode("ascii")
        print(f"\n[result] url={final_url}")
        print(f"[result] body:\n{safe[:2000]}")

        success = any(kw in combined.lower() for kw in [
            "thank you","received","submitted","application received",
            "we got your","successfully submitted","your application has been submitted"
        ])

        status = "SUBMITTED" if success else ("ATTEMPTED_UNCONFIRMED" if submitted else "FAILED_NO_SUBMIT")

        if success:
            print("\n" + "="*60 + "\n*** RIPPLE DEI PM SUBMITTED ***\n" + "="*60)
        elif submitted:
            print("\n[WARN] clicked submit but no confirmation keyword found")
        else:
            print("\n[ERROR] submit not clicked")

        result_json = {
            "company":"Ripple","role":"Program Manager, DEI","ats":"Greenhouse",
            "status":status,"confirmed_at":datetime.now().isoformat(),
            "screenshot":str(SCREENSHOTS/"v7_05_after_submit.png"),
            "notes":f"url={final_url} submitted={submitted} success={success}",
            "job_url":RIPPLE_URL,"body_preview":combined[:2000]
        }
        with open(ROLE_DIR/"SUBMITTED.json","w",encoding="utf-8") as f:
            json.dump(result_json,f,indent=2)

        time.sleep(15)

if __name__ == "__main__":
    main()
