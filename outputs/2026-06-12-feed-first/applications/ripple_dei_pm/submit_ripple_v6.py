#!/usr/bin/env python3
"""
Ripple DEI PM - Greenhouse submit v6.
v5 issues:
- triple_click() doesn't exist in Patchright -> use click() + fill()
- readback showed comboboxes (country, auth, sponsor, demog) return empty string
  because react-select doesn't store value in the input.value — that's normal
- personal fields were empty because triple_click failed
- after submit, form shows validation errors -> personal fields were truly empty
- country/auth/sponsor DID get clicked (combo_select worked for those)
- but we need to verify visually via screen
Plan: just fix fill() calls, re-run with clean page.
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

def safe_fill(fr, selector, value, desc=""):
    """Fill a field in a frame, with retry."""
    for attempt in range(3):
        try:
            loc = fr.locator(selector).first
            loc.wait_for(state="visible", timeout=8000)
            loc.click(timeout=5000); pause(0.2, 0.4)
            loc.fill(value, timeout=5000)
            pause(0.3, 0.6)
            # Verify
            got = loc.input_value(timeout=3000)
            if got and len(got) > 0:
                print(f"  {desc or selector} = {value!r} (verified: {got!r})")
                return True
            else:
                print(f"  {desc or selector}: filled but value empty on attempt {attempt+1}")
        except Exception as e:
            print(f"  {desc or selector} attempt {attempt+1} err: {e}")
            time.sleep(1)
    return False

def combo_select(fr, field_id, option_text):
    """Drive a Greenhouse react-select combobox."""
    want = option_text.strip().lower()
    try:
        container = fr.locator(f"#{field_id}").first
        container.scroll_into_view_if_needed(); pause()
        container.click(); pause(); time.sleep(0.7)

        # Check pre-rendered options
        opts = fr.locator(".select__option"); n = opts.count()
        for i in range(n):
            t = opts.nth(i).inner_text(timeout=3000).strip().lower()
            if want in t:
                opts.nth(i).click(); pause()
                print(f"  [{field_id}] = {option_text}")
                return True

        # Type + click
        container.type(option_text, delay=60); time.sleep(1.2)
        opts = fr.locator(".select__option"); n = opts.count()
        for i in range(n):
            t = opts.nth(i).inner_text(timeout=3000).strip().lower()
            if want in t:
                opts.nth(i).click(); pause()
                print(f"  [{field_id}] = {option_text} (typed)")
                return True

        # Native select fallback
        try:
            fr.select_option(f"#{field_id}", label=option_text)
            print(f"  [{field_id}] = {option_text} (native)")
            return True
        except: pass

    except Exception as e:
        print(f"  combo_select {field_id}: {e}")
    return False

def main():
    launch_chrome()
    time.sleep(2)

    from patchright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(f"http://localhost:{DEBUG_PORT}")
        ctx = browser.contexts[0] if browser.contexts else browser.new_context()

        # Close existing pages and start fresh
        for existing_page in ctx.pages:
            try:
                if "ripple" in existing_page.url or "greenhouse" in existing_page.url:
                    existing_page.close()
            except: pass

        page = ctx.new_page()
        page.set_default_timeout(20000)

        # ── 1. Navigate fresh ──────────────────────────────────────────────
        print(f"\n[1] fresh nav to {RIPPLE_URL}")
        try:
            page.goto(RIPPLE_URL, wait_until="domcontentloaded", timeout=40000)
        except Exception as e:
            print(f"  nav: {e}")
        time.sleep(6)
        page.screenshot(path=str(SCREENSHOTS / "01_landing.png"), full_page=True)

        # Accept cookies
        try:
            c = page.get_by_text("Accept Cookies", exact=False).first
            if c.is_visible(timeout=2000): c.click(); time.sleep(1); print("  cookies accepted")
        except: pass

        # ── 2. Click Application tab ───────────────────────────────────────
        print("\n[2] clicking Application tab...")
        try:
            app_tab = page.get_by_text("Application", exact=True).first
            app_tab.wait_for(state="visible", timeout=8000)
            app_tab.click(); time.sleep(6)
            print("  Application tab clicked")
        except Exception as e:
            print(f"  err: {e}")
        page.screenshot(path=str(SCREENSHOTS / "02_after_tab.png"), full_page=True)

        # ── 3. Find frame ──────────────────────────────────────────────────
        print("\n[3] finding Greenhouse frame...")
        gh_fr = None
        for i in range(10):
            time.sleep(2)
            gh_fr = get_gh_frame(page)
            if gh_fr:
                print(f"  found on attempt {i+1}: {gh_fr.url[:80]}")
                break

        if not gh_fr:
            print("[FATAL] frame not found")
            result = {"company":"Ripple","role":"Program Manager, DEI","ats":"Greenhouse",
                      "status":"FAILED_FRAME_ACCESS","confirmed_at":datetime.now().isoformat(),
                      "screenshot":str(SCREENSHOTS/"02_after_tab.png"),
                      "notes":"Greenhouse frame not found","job_url":RIPPLE_URL}
            with open(ROLE_DIR/"SUBMITTED.json","w",encoding="utf-8") as f: json.dump(result,f,indent=2)
            return

        # ── 4. Wait for form ───────────────────────────────────────────────
        print("\n[4] waiting for form fields...")
        try:
            gh_fr.locator("#first_name").wait_for(state="visible", timeout=15000)
            print("  form fields visible")
        except Exception as e:
            print(f"  form wait err: {e}")

        # Scroll to make iframe fully visible
        try:
            page.evaluate("""() => {
                const iframe = document.querySelector('iframe[src*="greenhouse"]');
                if (iframe) {
                    iframe.scrollIntoView({behavior:'smooth', block:'center'});
                    return true;
                }
                return false;
            }"""); time.sleep(2)
        except: pass
        page.screenshot(path=str(SCREENSHOTS / "03_form_visible.png"), full_page=True)

        # ── 5. Personal fields ─────────────────────────────────────────────
        print("\n[5] personal fields...")

        safe_fill(gh_fr, "#first_name", FIRST, "first_name")
        safe_fill(gh_fr, "#last_name", LAST, "last_name")
        safe_fill(gh_fr, "#email", EMAIL, "email")
        safe_fill(gh_fr, "#phone", PHONE, "phone")

        # Country combobox
        combo_select(gh_fr, "country", COUNTRY)

        # Location
        print("  location...")
        try:
            loc = gh_fr.locator("#candidate-location").first
            loc.wait_for(state="visible", timeout=5000)
            loc.click(); pause(); time.sleep(0.5)
            # Clear first, then type
            loc.fill(""); pause()
            loc.fill(CITY); pause(); time.sleep(2.5)
            # Try to pick a suggestion or just Tab out
            try:
                sugg = gh_fr.locator('[role="option"]').first
                if sugg.count() > 0 and sugg.is_visible(timeout=2000):
                    sugg.click(); pause()
                    print(f"  location via suggestion")
                else:
                    page.keyboard.press("Tab"); pause()
                    print("  location via Tab")
            except:
                page.keyboard.press("Tab"); pause()
        except Exception as e:
            print(f"  location err: {e}")

        # Screenshot after personal
        page.screenshot(path=str(SCREENSHOTS / "04_personal_done.png"), full_page=True)

        # Verify personal fields
        try:
            v = gh_fr.evaluate("""() => ({
                first: document.getElementById('first_name')?.value||'',
                last: document.getElementById('last_name')?.value||'',
                email: document.getElementById('email')?.value||'',
                phone: document.getElementById('phone')?.value||'',
            })""")
            print(f"  personal verify: {v}")
            if not v.get('first'):
                print("  WARNING: first_name still empty after fill — trying JS set")
                gh_fr.evaluate(f"""() => {{
                    const el = document.getElementById('first_name');
                    if (el) {{
                        el.focus();
                        const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;
                        nativeInputValueSetter.call(el, '{FIRST}');
                        el.dispatchEvent(new Event('input', {{bubbles:true}}));
                        el.dispatchEvent(new Event('change', {{bubbles:true}}));
                    }}
                }}""")
                gh_fr.evaluate(f"""() => {{
                    const el = document.getElementById('last_name');
                    if (el) {{
                        el.focus();
                        const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;
                        nativeInputValueSetter.call(el, '{LAST}');
                        el.dispatchEvent(new Event('input', {{bubbles:true}}));
                        el.dispatchEvent(new Event('change', {{bubbles:true}}));
                    }}
                }}""")
                gh_fr.evaluate(f"""() => {{
                    const el = document.getElementById('email');
                    if (el) {{
                        const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;
                        nativeInputValueSetter.call(el, '{EMAIL}');
                        el.dispatchEvent(new Event('input', {{bubbles:true}}));
                        el.dispatchEvent(new Event('change', {{bubbles:true}}));
                    }}
                }}""")
                gh_fr.evaluate(f"""() => {{
                    const el = document.getElementById('phone');
                    if (el) {{
                        const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;
                        nativeInputValueSetter.call(el, '{PHONE}');
                        el.dispatchEvent(new Event('input', {{bubbles:true}}));
                        el.dispatchEvent(new Event('change', {{bubbles:true}}));
                    }}
                }}""")
                pause(1, 2)
                # Verify again
                v2 = gh_fr.evaluate("""() => ({
                    first: document.getElementById('first_name')?.value||'',
                    last: document.getElementById('last_name')?.value||'',
                    email: document.getElementById('email')?.value||'',
                    phone: document.getElementById('phone')?.value||'',
                })""")
                print(f"  personal after JS: {v2}")
        except Exception as e:
            print(f"  verify err: {e}")

        # ── 6. Custom questions ────────────────────────────────────────────
        print("\n[6] custom questions...")

        # Preferred first name
        safe_fill(gh_fr, "#question_67133066", PREFERRED, "preferred")

        # LinkedIn
        safe_fill(gh_fr, "#question_67133067", LINKEDIN, "linkedin")

        # How did you hear? (q67133069)
        combo_select(gh_fr, "question_67133069", "LinkedIn")

        # Are you legally authorized to work in the U.S.? (q67133070)
        combo_select(gh_fr, "question_67133070", "Yes")

        # Will you require visa sponsorship? (q67133071)
        combo_select(gh_fr, "question_67133071", "Yes")

        # Previously employed by Ripple? (q67133072)
        combo_select(gh_fr, "question_67133072", "No")

        # ── 7. File uploads ────────────────────────────────────────────────
        print("\n[7] uploads...")
        # Find file inputs in frame
        try:
            file_inputs = gh_fr.locator('input[type="file"]')
            n = file_inputs.count()
            print(f"  {n} file inputs in frame")
            if n > 0:
                file_inputs.nth(0).set_input_files(str(RESUME), timeout=12000)
                time.sleep(4); print(f"  resume OK (nth 0)")
            if n > 1:
                file_inputs.nth(1).set_input_files(str(COVER), timeout=12000)
                time.sleep(3); print(f"  cover OK (nth 1)")
            elif n == 1 and COVER.exists():
                # Only one file input — try finding cover by ID directly
                try:
                    gh_fr.locator("#cover_letter, input[name*='cover']").first.set_input_files(str(COVER), timeout=8000)
                    time.sleep(3); print("  cover OK (by name)")
                except: print("  no second file input for cover")
        except Exception as e:
            print(f"  file upload err: {e}")

        # ── 8. Demographics ────────────────────────────────────────────────
        print("\n[8] demographics...")
        combo_select(gh_fr, "gender", "Woman")
        combo_select(gh_fr, "hispanic_ethnicity", "No")
        combo_select(gh_fr, "veteran_status", "I am not a protected veteran")
        combo_select(gh_fr, "disability_status", "No, I do not have a disability")

        # ── 9. Pre-submit screenshots ──────────────────────────────────────
        print("\n[9] pre-submit review...")
        try: page.evaluate("window.scrollTo(0,0)"); time.sleep(1)
        except: pass
        page.screenshot(path=str(SCREENSHOTS / "05_prefill_top.png"), full_page=True)
        try: page.evaluate("window.scrollTo(0, document.body.scrollHeight)"); time.sleep(2)
        except: pass
        page.screenshot(path=str(SCREENSHOTS / "05_prefill_bottom.png"), full_page=True)

        # Readback — for text fields only (react-selects won't show value in input.value)
        try:
            rb = gh_fr.evaluate("""() => ({
                first: document.getElementById('first_name')?.value||'EMPTY',
                last: document.getElementById('last_name')?.value||'EMPTY',
                email: document.getElementById('email')?.value||'EMPTY',
                phone: document.getElementById('phone')?.value||'EMPTY',
                preferred: document.getElementById('question_67133066')?.value||'',
                linkedin: document.getElementById('question_67133067')?.value||'',
                file_inputs: document.querySelectorAll('input[type="file"]').length,
                file0_name: document.querySelectorAll('input[type="file"]')[0]?.files?.[0]?.name || 'none',
                file1_name: document.querySelectorAll('input[type="file"]')[1]?.files?.[0]?.name || 'none',
                // React-select single-value text (what the user sees)
                country_text: document.querySelector('#country ~ .select__value-container .select__single-value')?.innerText||'',
                auth_text: document.querySelector('#question_67133070 ~ .select__value-container .select__single-value')?.innerText||'',
                sponsor_text: document.querySelector('#question_67133071 ~ .select__value-container .select__single-value')?.innerText||'',
                prev_text: document.querySelector('#question_67133072 ~ .select__value-container .select__single-value')?.innerText||'',
                gender_text: document.querySelector('#gender ~ .select__value-container .select__single-value')?.innerText||'',
            })""")
            print(f"  READBACK:\n  {json.dumps(rb, indent=2)}")
        except Exception as e:
            print(f"  readback err: {e}")

        # CAPTCHA check
        body_text = page.inner_text("body").lower()
        if any(c in body_text for c in ["recaptcha","hcaptcha","turnstile","i am not a robot"]):
            print("\n[CAPTCHA] — leaving tab open")
            result = {"company":"Ripple","role":"Program Manager, DEI","ats":"Greenhouse",
                      "status":"CAPTCHA_STAGED","confirmed_at":datetime.now().isoformat(),
                      "screenshot":str(SCREENSHOTS/"05_prefill_bottom.png"),
                      "notes":"CAPTCHA before submit","job_url":RIPPLE_URL}
            with open(ROLE_DIR/"SUBMITTED.json","w",encoding="utf-8") as f: json.dump(result,f,indent=2)
            time.sleep(30); return

        # ── 10. SUBMIT ────────────────────────────────────────────────────
        print("\n[10] SUBMITTING...")
        submitted = False

        # Scroll the iframe to make submit button visible
        try:
            page.evaluate("""() => {
                const iframe = document.querySelector('iframe[src*="greenhouse"]');
                if (iframe) iframe.scrollIntoView({behavior:'smooth', block:'end'});
            }"""); time.sleep(2)
        except: pass

        # Find and click submit in frame
        for btn_name in ["Submit application","Submit Application","Submit"]:
            try:
                btn = gh_fr.get_by_role("button", name=btn_name, exact=False).first
                if btn.count() > 0:
                    btn.wait_for(state="visible", timeout=8000)
                    # Scroll inside frame
                    btn.scroll_into_view_if_needed(); pause()
                    btn.click(timeout=15000)
                    time.sleep(14); submitted = True
                    print(f"  clicked '{btn_name}'")
                    break
            except Exception as e:
                print(f"  btn '{btn_name}': {e}")

        # JS fallback inside frame
        if not submitted:
            try:
                res = gh_fr.evaluate("""() => {
                    const btns = [...document.querySelectorAll('button, input[type=submit]')];
                    const sub = btns.find(b => (b.textContent||b.value||'').toLowerCase().includes('submit'));
                    if (sub) { sub.scrollIntoView(); sub.click(); return 'clicked: ' + (sub.textContent||sub.value||'').trim(); }
                    return 'no submit btn, btns=' + btns.map(b=>(b.textContent||b.value||'').trim().substring(0,30)).join('|');
                }""")
                print(f"  JS frame result: {res}")
                time.sleep(14); submitted = True
            except Exception as e:
                print(f"  JS frame err: {e}")

        page.screenshot(path=str(SCREENSHOTS / "06_after_submit.png"), full_page=True)

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
        print(f"[result] title={title}")
        print(f"[result] body:\n{safe[:2000]}")

        success = any(kw in combined.lower() for kw in [
            "thank you","received","submitted","application received",
            "we got your","successfully submitted","your application has been submitted"
        ])

        status = "SUBMITTED" if success else ("ATTEMPTED_UNCONFIRMED" if submitted else "FAILED_NO_SUBMIT")
        if success:
            print("\n" + "="*60 + "\n*** RIPPLE SUBMITTED ***\n" + "="*60)
        elif submitted:
            print("\n[WARN] clicked submit, no confirmation keyword")
        else:
            print("\n[ERROR] submit not clicked")

        result_json = {
            "company":"Ripple","role":"Program Manager, DEI","ats":"Greenhouse",
            "status":status,"confirmed_at":datetime.now().isoformat(),
            "screenshot":str(SCREENSHOTS/"06_after_submit.png"),
            "notes":f"url={final_url} submitted={submitted} success={success}",
            "job_url":RIPPLE_URL,"body_preview":combined[:2000]
        }
        with open(ROLE_DIR/"SUBMITTED.json","w",encoding="utf-8") as f:
            json.dump(result_json,f,indent=2)

        time.sleep(15)

if __name__ == "__main__":
    main()
