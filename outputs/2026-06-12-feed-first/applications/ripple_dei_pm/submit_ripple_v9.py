#!/usr/bin/env python3
"""
Ripple DEI PM - Greenhouse submit v9.
CRITICAL FIX: The iframe has id='grnhse_iframe' in the DOM.
page.frames shows empty URLs for cross-origin iframes until they finish loading.
We need to use the element handle's content_frame() — OR wait for the frame URL to populate.

Strategy:
1. Use page.locator('#grnhse_iframe') -> .content_frame() to get the frame
2. Wait longer (frame needs to be fully loaded cross-origin)
3. Use locator.fill() which properly dispatches React events in Patchright
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

def get_gh_frame(page, ripple_page=None):
    """Try multiple strategies to get the Greenhouse iframe frame object."""
    pg = ripple_page or page

    # Strategy 1: look for frame by URL
    for fr in pg.frames:
        if "greenhouse.io" in fr.url and "embed" in fr.url:
            return fr

    # Strategy 2: get by element handle content_frame
    try:
        iframe_el = pg.locator("#grnhse_iframe").first
        if iframe_el.count() > 0:
            fr = iframe_el.content_frame()
            if fr:
                print(f"  [frame via #grnhse_iframe content_frame]")
                return fr
    except Exception as e:
        print(f"  content_frame via #grnhse_iframe: {e}")

    # Strategy 3: frame_locator approach
    try:
        fl = pg.frame_locator("#grnhse_iframe")
        # Test if accessible
        fn = fl.locator("#first_name")
        fn.wait_for(state="visible", timeout=5000)
        print("  [frame via frame_locator #grnhse_iframe]")
        return fl
    except Exception as e:
        print(f"  frame_locator: {e}")

    # Strategy 4: frame by index — look at all frames and find the one with GH form
    for fr in pg.frames:
        try:
            if fr.url:  # skip empty
                continue
            # Try to access #first_name in this blank frame
            loc = fr.locator("#first_name")
            if loc.count() > 0 and loc.is_visible(timeout=1000):
                print(f"  [frame by blank-URL scan]")
                return fr
        except: continue

    return None

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

def safe_fill(gh_fr, field_id, value, desc=""):
    """Fill a React input using Patchright locator.fill()."""
    try:
        loc = gh_fr.locator(f"#{field_id}").first
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
            print(f"  {desc or field_id}: filled but empty ({value!r})")
    except Exception as e:
        print(f"  {desc or field_id}: {e}")
    return False

def main():
    launch_chrome()
    time.sleep(2)

    from patchright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(f"http://localhost:{DEBUG_PORT}")
        ctx = browser.contexts[0] if browser.contexts else browser.new_context()

        # Close all existing pages
        for pg in list(ctx.pages):
            try: pg.close()
            except: pass
        time.sleep(1)

        page = ctx.new_page()
        page.set_default_timeout(25000)

        # Navigate
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
        page.screenshot(path=str(SCREENSHOTS / "v9_01_landing.png"), full_page=True)

        # Click Application tab
        print("\n[Application tab]")
        try:
            btn = page.get_by_text("Application", exact=True).first
            btn.wait_for(state="visible", timeout=8000)
            btn.click(); print("  clicked")
            # Wait for iframe to appear in DOM
            page.locator("#grnhse_iframe").wait_for(state="attached", timeout=15000)
            print("  grnhse_iframe attached")
            time.sleep(4)
        except Exception as e:
            print(f"  {e}")
        page.screenshot(path=str(SCREENSHOTS / "v9_02_after_tab.png"), full_page=True)

        # Get the GH frame
        print("\n[getting frame]")
        gh_fr = None
        for i in range(15):
            time.sleep(2)
            # Try strategy 1: content_frame
            try:
                iframe_el = page.locator("#grnhse_iframe").first
                if iframe_el.count() > 0:
                    fr = iframe_el.content_frame()
                    if fr:
                        # Test if accessible
                        try:
                            loc = fr.locator("#first_name")
                            if loc.count() > 0:
                                loc.wait_for(state="visible", timeout=3000)
                                gh_fr = fr
                                print(f"  found via content_frame() (attempt {i+1})")
                                break
                        except: pass
            except: pass

            # Strategy 2: search frames
            for fr in page.frames:
                if "greenhouse.io" in fr.url:
                    try:
                        loc = fr.locator("#first_name")
                        if loc.count() > 0:
                            loc.wait_for(state="visible", timeout=2000)
                            gh_fr = fr
                            print(f"  found by URL (attempt {i+1})")
                            break
                    except: pass

            if gh_fr: break
            # Strategy 3: frame_locator
            try:
                fl = page.frame_locator("#grnhse_iframe")
                fn = fl.locator("#first_name")
                fn.wait_for(state="visible", timeout=2000)
                gh_fr = fl
                print(f"  found via frame_locator (attempt {i+1})")
                break
            except: pass

            print(f"  attempt {i+1}: frames={[f.url[:40] for f in page.frames]}")

        if not gh_fr:
            print("[FATAL] can't access GH frame")
            result = {"company":"Ripple","role":"Program Manager, DEI","ats":"Greenhouse",
                      "status":"FAILED_FRAME_ACCESS","confirmed_at":datetime.now().isoformat(),
                      "screenshot":str(SCREENSHOTS/"v9_02_after_tab.png"),
                      "notes":"content_frame() inaccessible (cross-origin CDP restriction)",
                      "job_url":RIPPLE_URL}
            with open(ROLE_DIR/"SUBMITTED.json","w",encoding="utf-8") as f: json.dump(result,f,indent=2)
            return

        # ── FILL FORM ─────────────────────────────────────────────────────
        # Scroll iframe into view
        try:
            page.evaluate("""() => {
                const iframe = document.getElementById('grnhse_iframe');
                if (iframe) iframe.scrollIntoView({behavior:'smooth', block:'center'});
            }"""); time.sleep(2)
        except: pass

        print("\n[personal]")
        safe_fill(gh_fr, "first_name", FIRST, "first_name")
        safe_fill(gh_fr, "last_name", LAST, "last_name")
        safe_fill(gh_fr, "email", EMAIL, "email")
        safe_fill(gh_fr, "phone", PHONE, "phone")
        combo_select(gh_fr, "country", COUNTRY)

        # Location
        print("  location...")
        try:
            loc_input = gh_fr.locator("#candidate-location").first
            loc_input.wait_for(state="visible", timeout=5000)
            loc_input.click(); pause()
            loc_input.press("Control+a"); loc_input.fill(CITY); time.sleep(2.5)
            try:
                sugg = gh_fr.locator('[role="option"]').first
                if sugg.count() > 0 and sugg.is_visible(timeout=2000):
                    sugg.click(); pause(); print("  location via suggestion")
                else:
                    loc_input.press("ArrowDown"); pause()
                    loc_input.press("Enter"); pause()
                    print("  location via ArrowDown+Enter")
            except:
                loc_input.press("Tab"); pause(); print("  location via Tab")
        except Exception as e:
            print(f"  location: {e}")

        page.screenshot(path=str(SCREENSHOTS / "v9_03_personal.png"), full_page=True)

        print("\n[custom questions]")
        safe_fill(gh_fr, "question_67133066", PREFERRED, "preferred")
        safe_fill(gh_fr, "question_67133067", LINKEDIN, "linkedin")
        combo_select(gh_fr, "question_67133069", "LinkedIn")
        combo_select(gh_fr, "question_67133070", "Yes")
        combo_select(gh_fr, "question_67133071", "Yes")
        combo_select(gh_fr, "question_67133072", "No")

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

        print("\n[demographics]")
        combo_select(gh_fr, "gender", "Woman")
        combo_select(gh_fr, "hispanic_ethnicity", "No")
        combo_select(gh_fr, "veteran_status", "I am not a protected veteran")
        combo_select(gh_fr, "disability_status", "No, I do not have a disability")

        # Screenshots
        try: page.evaluate("window.scrollTo(0,0)"); time.sleep(1)
        except: pass
        page.screenshot(path=str(SCREENSHOTS / "v9_04_prefill_top.png"), full_page=True)
        try: page.evaluate("window.scrollTo(0, document.body.scrollHeight)"); time.sleep(2)
        except: pass
        page.screenshot(path=str(SCREENSHOTS / "v9_04_prefill_bottom.png"), full_page=True)

        # Readback
        try:
            rb = gh_fr.evaluate("""() => ({
                first: document.getElementById('first_name')?.value||'',
                last: document.getElementById('last_name')?.value||'',
                email: document.getElementById('email')?.value||'',
                phone: document.getElementById('phone')?.value||'',
                preferred: document.getElementById('question_67133066')?.value||'',
                linkedin: document.getElementById('question_67133067')?.value||'',
                country_d: document.querySelector('.select__single-value')?.innerText||'',
                auth_d: document.querySelector('#question_67133070 .select__single-value')?.innerText||'',
                sponsor_d: document.querySelector('#question_67133071 .select__single-value')?.innerText||'',
                prev_d: document.querySelector('#question_67133072 .select__single-value')?.innerText||'',
                gender_d: document.querySelector('#gender .select__single-value')?.innerText||'',
                resume_text: document.body.innerText.includes('resume.pdf') ? 'yes' : 'no',
            })""")
            print(f"\n  READBACK: {json.dumps(rb, indent=2)}")
        except Exception as e:
            print(f"  readback: {e}")

        # CAPTCHA
        body_text = page.inner_text("body").lower()
        if any(c in body_text for c in ["recaptcha","hcaptcha","turnstile","i am not a robot"]):
            print("\n[CAPTCHA] — leaving tab open")
            result = {"company":"Ripple","role":"Program Manager, DEI","ats":"Greenhouse",
                      "status":"CAPTCHA_STAGED","confirmed_at":datetime.now().isoformat(),
                      "screenshot":str(SCREENSHOTS/"v9_04_prefill_bottom.png"),
                      "notes":"CAPTCHA before submit","job_url":RIPPLE_URL}
            with open(ROLE_DIR/"SUBMITTED.json","w",encoding="utf-8") as f: json.dump(result,f,indent=2)
            time.sleep(30); return

        # SUBMIT
        print("\n[SUBMIT]")
        submitted = False
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

        page.screenshot(path=str(SCREENSHOTS / "v9_05_after_submit.png"), full_page=True)

        # Verify
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
            "screenshot":str(SCREENSHOTS/"v9_05_after_submit.png"),
            "notes":f"submitted={submitted} success={success}",
            "job_url":RIPPLE_URL,"body_preview":combined[:2000]
        }
        with open(ROLE_DIR/"SUBMITTED.json","w",encoding="utf-8") as f:
            json.dump(result_json,f,indent=2)

        time.sleep(15)

if __name__ == "__main__":
    main()
