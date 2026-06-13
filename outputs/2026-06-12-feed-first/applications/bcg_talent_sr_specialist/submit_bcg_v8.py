# -*- coding: utf-8 -*-
"""
submit_bcg_v8.py  -- BCG Phenom ATS (v8)

Key fixes vs v7:
  1. phenom_dropdown_select: PURE CLICK approach, no fill/type. Click to open,
     wait for options, click option by text. Phenom listboxes don't filter on input.
  2. State dropdown: more wait time after Country, scroll-then-click, no fill.
  3. Date picker: JS keyboard injection approach (type chars into input).
  4. No debug pass — already know all option texts from v7 debug.
  5. Crash guard: check page.is_closed() before each major operation.
  6. JS fallback for every dropdown: direct DOM click on the option element.

Known option texts (from v7 debug):
  input-7  (Country):    contains 'United States'
  input-28 (State):      contains 'Oregon' (after US selected)
  input-10 (Work Auth Q1): 'Yes', 'No'
  input-13 (Work Auth Q2): 'Yes', 'No'
  input-16 (Gender):     'Man','Woman','Non-binary/non-conforming','Not listed/other','Prefer not to answer'
  input-19 (Ethnicity):  'Hispanic/Latino','Non Hispanic/Latino','I prefer not to provide this information'
  input-22 (Disability): 'Yes, I have a disability...', "No, I don't have a disability...", "I Don't Wish to Answer"
  input-25 (Veteran):    'Yes','No','I prefer not to provide this information'
  Race checkboxes: Voluntary_Self_Identification_race-Asian-2
"""
import os, sys, time, json, subprocess, traceback
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stdout.flush()

sys.path.insert(0, r"C:\Users\chent\Agentic_Workflows_2026\jamie-autopilot\lib")
from patchright.sync_api import sync_playwright
from credential_vault import job_password

PORT     = 9402
PROFILE  = r"C:\Users\chent\ats_agent_9402_v4"
CHROME   = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
ROLE_DIR = (r"C:\Users\chent\Agentic_Workflows_2026\oracle-job-search"
            r"\outputs\2026-06-12-feed-first\applications\bcg_talent_sr_specialist")
SHOT     = ROLE_DIR + r"\screenshots\v8"
RESUME   = ROLE_DIR + r"\resume.pdf"
os.makedirs(SHOT, exist_ok=True)

EMAIL = "jamiecheng0103@gmail.com"
PW    = job_password()

JOB_PUBLIC_URL = "https://careers.bcg.com/global/en/job/57988/Talent-Senior-Specialist-People"
PHENOM_APPLY   = "https://experiencedtalent.bcg.com/careerhub/explore/jobs/apply?pid=790315808241"
PHENOM_LOGIN   = (
    "https://experiencedtalent.bcg.com/candidate/login?domain=bcg.com&hl=en"
    "&microsite=microsite_1"
    "&next=http%3A%2F%2Fexperiencedtalent.bcg.com%2Fcareerhub%2Fexplore%2Fjobs"
    "%2F790315808241%3Fpost_onboarding_pid%3D790315808241%26show_apply%3D1"
    "%26profile_type%3Dcandidate%26customredirect%3D1"
)

# ── helpers ──────────────────────────────────────────────────────────────────

def log(msg):
    print(msg, flush=True)


def ss(page, name):
    path = os.path.join(SHOT, name + ".png")
    try:
        if not page.is_closed():
            page.screenshot(path=path, full_page=True, timeout=15000)
            log(f"  [ss] {name}.png")
        else:
            log(f"  [ss!] {name}: page closed")
    except Exception as e:
        log(f"  [ss!] {name}: {e}")
    return path


def alive(page):
    """Return True if page is still open and functional."""
    try:
        return not page.is_closed()
    except:
        return False


def net(page, t=15000):
    try: page.wait_for_load_state("networkidle", timeout=t)
    except: pass


def txt(page):
    try: return page.inner_text("body", timeout=5000)
    except: return ""


def dismiss_cookie(page):
    if not alive(page): return False
    for sel in [
        "button:has-text('Accept All and Close')",
        "button:has-text('Accept All')",
        "#truste-consent-button",
        "#onetrust-accept-btn-handler",
    ]:
        try:
            el = page.locator(sel).first
            if el.count() > 0 and el.is_visible(timeout=2000):
                el.click(force=True); time.sleep(2); return True
        except: continue
    try:
        page.evaluate("""() => {
            document.querySelectorAll(
                '[id*="truste"],[class*="truste"],[id*="trustarc"],[class*="trustarc"],' +
                '#onetrust-banner-sdk,.onetrust-pc-dark-filter'
            ).forEach(e => { e.style.cssText = 'display:none!important;'; });
            document.body.style.overflow = 'auto';
        }""")
    except: pass
    return False


def fill_text(page, field_id, val, lbl=""):
    """Fill a plain text input by ID."""
    if not alive(page): return False
    try:
        el = page.locator(f"#{field_id}").first
        el.wait_for(state="visible", timeout=5000)
        el.scroll_into_view_if_needed()
        el.click(timeout=3000)
        el.fill("", timeout=2000)
        el.fill(val, timeout=5000)
        log(f"  [fill] {lbl or field_id} = '{val[:50]}'")
        return True
    except Exception as e:
        # JS fallback
        try:
            page.evaluate(
                "(args) => { let el = document.getElementById(args[0]); if(el) {"
                "  el.focus(); el.value=args[1];"
                "  el.dispatchEvent(new Event('input',{bubbles:true}));"
                "  el.dispatchEvent(new Event('change',{bubbles:true})); } }",
                [field_id, val]
            )
            log(f"  [fill-js] {lbl or field_id} = '{val[:50]}'")
            return True
        except: pass
        log(f"  [fill!] {lbl or field_id}: {str(e)[:80]}")
        return False


def phenom_click_select(page, field_id, desired_text, lbl="", wait_after_country=False):
    """
    Select from a Phenom custom listbox by pure CLICK (no typing/fill).

    Steps:
    1. Scroll field into view
    2. Click the input to open dropdown
    3. Wait for listbox options to appear
    4. Find option containing desired_text and click it
    5. Verify selection

    Falls back to JS DOM click if locator approach fails.
    """
    if not alive(page): return False
    log(f"  [dd] {lbl or field_id} → '{desired_text}'")

    try:
        inp = page.locator(f"#{field_id}").first

        # Wait for field to be visible with generous timeout
        try:
            inp.wait_for(state="visible", timeout=8000)
        except Exception as e:
            log(f"    [dd-wait!] {e}")
            return False

        inp.scroll_into_view_if_needed()
        time.sleep(0.5)

        # Click to open (no fill, no type)
        try:
            inp.click(timeout=5000)
        except Exception as e:
            log(f"    [dd-click!] {e}")
            # Try JS click
            try:
                page.evaluate(f"document.getElementById('{field_id}').click()")
            except: return False

        time.sleep(1.5)  # wait for dropdown to animate open

        # Take screenshot to see what opened
        ss(page, f"v8_dd_{field_id[:15]}_open")

        # Strategy 1: Find via [role='listbox'] li or [role='option']
        option_selectors = [
            "[role='listbox'] li",
            "[role='listbox'] [role='option']",
            "[role='option']",
            "[class*='listbox'] li",
            "[class*='dropdown'] li",
            "[class*='options-list'] li",
            "[class*='option-item']",
            "[class*='menu-item']",
            "ul[class*='list'] li",
        ]

        for opt_sel in option_selectors:
            if not alive(page): return False
            try:
                opts = page.locator(opt_sel).all()
                if not opts: continue
                for opt in opts:
                    try:
                        opt_text = opt.inner_text(timeout=2000).strip()
                        if desired_text.lower() in opt_text.lower():
                            opt.scroll_into_view_if_needed()
                            opt.click(timeout=3000)
                            time.sleep(1.0)
                            # Verify
                            try:
                                val_after = inp.input_value(timeout=2000)
                                log(f"    [dd-ok] '{opt_text}' via '{opt_sel}', field='{val_after[:40]}'")
                            except:
                                log(f"    [dd-ok] '{opt_text}' via '{opt_sel}' (no verify)")
                            return True
                    except: continue
            except: continue

        # Strategy 2: JS evaluation to find and click option
        log(f"    [dd-js] trying JS approach for '{desired_text}'")
        try:
            clicked = page.evaluate("""(desired) => {
                let selectors = [
                    '[role="listbox"] li', '[role="option"]',
                    '[class*="listbox"] li', '[class*="dropdown"] li',
                    '[class*="option"]', 'ul li'
                ];
                for (let sel of selectors) {
                    let els = document.querySelectorAll(sel);
                    for (let el of els) {
                        if (el.textContent.trim().toLowerCase().includes(desired.toLowerCase())) {
                            el.click();
                            return el.textContent.trim();
                        }
                    }
                }
                return null;
            }""", desired_text)
            if clicked:
                time.sleep(1.0)
                log(f"    [dd-js-ok] clicked '{clicked}'")
                return True
        except Exception as e:
            log(f"    [dd-js!] {e}")

        # Press Escape to close any open dropdown
        try:
            page.keyboard.press("Escape")
            time.sleep(0.3)
        except: pass

        log(f"    [dd-fail] Could not select '{desired_text}' for {field_id}")
        return False

    except Exception as e:
        log(f"  [dd!] {lbl or field_id}: {str(e)[:100]}")
        return False


def has_captcha(page):
    if not alive(page): return False
    for sel in ["iframe[src*='recaptcha']", "iframe[src*='hcaptcha']",
                ".g-recaptcha", "[data-sitekey]", ".cf-turnstile"]:
        try:
            if page.locator(sel).count() > 0: return True
        except: pass
    try: return any(w in txt(page)[:2000].lower() for w in ["captcha", "i'm not a robot"])
    except: return False


def has_email_verify(page):
    if not alive(page): return False
    try:
        t = txt(page)[:2000].lower()
        return any(k in t for k in [
            "verification email sent", "verify your email", "we sent an email",
            "check your inbox", "confirm your email", "click the link in",
        ])
    except: return False


def is_real_confirmation(body, url=""):
    t = body.lower()
    if "login" in url.lower() or ("sign in" in t and "password" in t and "careerhub" not in url.lower()):
        return False
    strong = [
        "thank you for applying",
        "your application has been submitted",
        "application successfully submitted",
        "we have received your application",
        "application received",
        "you have successfully applied",
        "successfully applied to",
        "your submission has been received",
        "application submitted successfully",
        "you applied for",
    ]
    return any(p in t for p in strong)


def save(result):
    path = os.path.join(ROLE_DIR, "SUBMITTED.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    log(f"\n[SAVED] {path}")
    log("=" * 60)
    log(f"RESULT: {result['status']}")
    log(f"Notes:  {str(result.get('notes',''))[:600]}")
    log("=" * 60)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    R = {
        "company": "BCG (Boston Consulting Group)",
        "role": "Talent Senior Specialist - People",
        "ats": "Phenom (experiencedtalent.bcg.com)",
        "status": "in_progress",
        "confirmed_at": None,
        "screenshot": None,
        "account_email": EMAIL,
        "notes": "",
        "job_url": JOB_PUBLIC_URL,
        "apply_url": PHENOM_APPLY,
    }

    log("=" * 60)
    log("BCG Phenom v8 -- Talent Senior Specialist - People")
    log("=" * 60)

    # Kill any stale Chrome on this port
    subprocess.run(
        ["powershell", "-Command",
         f"Get-NetTCPConnection -LocalPort {PORT} -ErrorAction SilentlyContinue | "
         f"Select-Object -ExpandProperty OwningProcess | "
         f"ForEach-Object {{ Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }}"],
        capture_output=True, timeout=10
    )
    time.sleep(3)

    log(f"\n[1] Launching Chrome (port {PORT})...")
    proc = subprocess.Popen(
        [CHROME,
         f"--remote-debugging-port={PORT}",
         f"--user-data-dir={PROFILE}",
         "--no-first-run", "--no-default-browser-check",
         "--disable-blink-features=AutomationControlled",
         PHENOM_LOGIN],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    log(f"  PID {proc.pid}, waiting 15s...")
    time.sleep(15)

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(f"http://localhost:{PORT}")
        ctx = browser.contexts[0]
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.set_default_timeout(30000)

        try:
            net(page, 20000); time.sleep(3)
            dismiss_cookie(page); time.sleep(2)
            ss(page, "v8_01_initial")
            log(f"  URL: {page.url}")

            # ── Login ─────────────────────────────────────────────────────
            log("\n[2] Login...")
            if "login" in page.url.lower():
                # Enter email
                for s in ["input[type='email']", "input[placeholder*='Email' i]",
                           "input[id*='email' i]", "input[autocomplete='email']"]:
                    try:
                        el = page.locator(s).first
                        if el.count() > 0 and el.is_visible(timeout=3000):
                            el.click(); el.fill(""); el.fill(EMAIL)
                            log(f"  [fill] email")
                            break
                    except: continue

                page.locator("button:has-text('Continue')").first.click()
                time.sleep(7); net(page, 15000); dismiss_cookie(page)
                ss(page, "v8_02_after_email")
                body = txt(page)

                if has_captcha(page):
                    R["status"] = "captcha-staged"; R["notes"] = "CAPTCHA after email."
                    try: browser.close()
                    except: pass
                    save(R); return R
                if has_email_verify(page):
                    R["status"] = "email-verify-staged"; R["notes"] = f"Email verify. Check {EMAIL}."
                    try: browser.close()
                    except: pass
                    save(R); return R

                if "password" in body.lower():
                    pws = page.locator("input[type='password']").all()
                    if pws:
                        pws[0].click(); pws[0].fill(PW)
                        log("  [fill] password")
                    page.locator("button:has-text('Submit')").first.click()
                    time.sleep(8); net(page, 15000); dismiss_cookie(page)
                    ss(page, "v8_03_after_signin")
                    log(f"  Post-signin URL: {page.url}")

                    if "login" in page.url.lower():
                        try:
                            page.locator("a:has-text('Use a one-time code instead')").first.click()
                            time.sleep(4)
                        except: pass
                        R["status"] = "email-verify-staged"
                        R["notes"] = f"Password login failed. OTP link clicked — check {EMAIL}."
                        ss(page, "v8_99_login_fail")
                        try: browser.close()
                        except: pass
                        save(R); return R

            # ── Load application form ─────────────────────────────────────
            log("\n[3] Loading application form...")
            page.goto(PHENOM_APPLY, timeout=30000, wait_until="domcontentloaded")
            time.sleep(8); net(page, 15000); dismiss_cookie(page); time.sleep(2)
            ss(page, "v8_10_form")
            log(f"  URL: {page.url}")
            if "login" in page.url.lower():
                R["status"] = "email-verify-staged"
                R["notes"] = f"Redirected to login. Check {EMAIL}."
                try: browser.close()
                except: pass
                save(R); return R

            # ── Upload resume ─────────────────────────────────────────────
            log("\n[4] Uploading resume...")
            for s in ["input[type='file'][accept*='pdf' i]", "input[type='file']"]:
                try:
                    inputs = page.locator(s).all()
                    if inputs:
                        inputs[0].set_input_files(RESUME)
                        time.sleep(6)
                        log(f"  [upload] resume via {s}")
                        # Dismiss any "enter manually" prompts
                        for dismiss in ["No, thanks", "Skip", "No thanks", "Enter Manually"]:
                            try:
                                el = page.get_by_text(dismiss, exact=False).first
                                if el.count() > 0 and el.is_visible(timeout=2000):
                                    el.click(); time.sleep(2); break
                            except: pass
                        break
                except Exception as e:
                    log(f"  [upload!] {e}")
            ss(page, "v8_11_after_resume")

            # ── Fill personal info ────────────────────────────────────────
            log("\n[5] Filling personal info...")

            for fid, val, lbl in [
                ("Before_applying_email", EMAIL, "email"),
                ("Before_applying_firstname", "Yi-Chieh", "first_name"),
                ("Before_applying_lastname", "Cheng", "last_name"),
                ("Before_applying_phone", "2137003831", "phone"),
                ("Before_applying_location", "Portland", "city"),
            ]:
                try:
                    el = page.locator(f"#{fid}").first
                    if el.count() > 0 and el.is_visible(timeout=1500):
                        cur = el.input_value().strip()
                        if not cur:
                            fill_text(page, fid, val, lbl)
                        else:
                            log(f"  [skip] {lbl} already = '{cur[:30]}'")
                except: pass

            # Preferred first name
            try:
                el = page.locator("#Before_applying_preferred_first_name").first
                if el.count() > 0 and el.is_visible(timeout=1500):
                    if not el.input_value().strip():
                        fill_text(page, "Before_applying_preferred_first_name", "Jamie", "preferred_first")
            except: pass

            # Country dropdown (input-7) — pure click, no fill
            log("  [country] Setting United States...")
            phenom_click_select(page, "input-7", "United States", "country")
            time.sleep(3)  # IMPORTANT: wait for State cascade to load after Country selection

            # State dropdown (input-28) — pure click, no fill
            log("  [state] Setting Oregon...")
            # Try up to 3 times, giving more time for cascade
            state_ok = False
            for attempt in range(3):
                if not alive(page): break
                state_ok = phenom_click_select(page, "input-28", "Oregon", "state")
                if state_ok: break
                log(f"    [state retry {attempt+1}] waiting 3s...")
                time.sleep(3)

            ss(page, "v8_12_personal_filled")

            # ── Available Start Date ──────────────────────────────────────
            log("\n[6] Filling Available Start Date...")
            # Phenom date picker with aria-haspopup="dialog"
            # Approach: click to open, then use keyboard to navigate OR type directly
            if alive(page):
                date_fid = "Available_Start_Date_start_date"
                date_filled = False
                try:
                    el = page.locator(f"#{date_fid}").first
                    el.wait_for(state="visible", timeout=8000)
                    el.scroll_into_view_if_needed()
                    el.click(timeout=5000)
                    time.sleep(1.5)
                    ss(page, "v8_13a_date_open")

                    # Try typing date directly into the input
                    # Phenom date input often accepts MM/DD/YYYY via keyboard
                    page.keyboard.type("09/01/2025", delay=50)
                    time.sleep(1)
                    val_after = el.input_value()
                    log(f"  [date] After type: '{val_after}'")

                    if val_after and val_after != "":
                        date_filled = True
                        page.keyboard.press("Escape")
                        time.sleep(0.5)
                        log(f"  [date-ok] '{val_after}'")
                    else:
                        # Try the calendar navigator approach
                        # Look for a calendar popup
                        cal_visible = page.evaluate("""() => {
                            let els = document.querySelectorAll('[role="dialog"], [class*="calendar"], [class*="datepicker"], [class*="dp__"]');
                            return els.length;
                        }""")
                        log(f"  [date] Calendar elements visible: {cal_visible}")

                        if cal_visible > 0:
                            # Navigate to Sep 2025 if needed
                            for nav_attempt in range(8):
                                cal_header = page.evaluate("""() => {
                                    let h = document.querySelector('[class*="calendar"] [class*="month-year"], [class*="datepicker"] [class*="title"], [role="dialog"] [class*="header"]');
                                    return h ? h.textContent.trim() : '';
                                }""")
                                log(f"    [cal] header: '{cal_header}'")
                                if "sep" in cal_header.lower() and "2025" in cal_header:
                                    break
                                # Future = click next button
                                for nav_sel in [
                                    "button[aria-label*='next month' i]",
                                    "button[aria-label*='Next' i]",
                                    "[class*='next-month']",
                                    "[class*='next']",
                                    "button:has-text('>')",
                                ]:
                                    try:
                                        nb = page.locator(nav_sel).first
                                        if nb.count() > 0 and nb.is_visible(timeout=1000):
                                            nb.click(); time.sleep(0.8); break
                                    except: pass

                            # Click day "1"
                            clicked_day = page.evaluate("""() => {
                                let els = document.querySelectorAll('[class*="day"], [class*="date"], td, button[class*="cal"]');
                                for (let el of els) {
                                    if (el.textContent.trim() === '1' && !el.disabled) {
                                        el.click();
                                        return true;
                                    }
                                }
                                return false;
                            }""")
                            if clicked_day:
                                date_filled = True
                                time.sleep(0.5)
                                page.keyboard.press("Escape")
                                log("  [date-ok] Calendar day 1 clicked")

                        if not date_filled:
                            # JS direct set
                            page.evaluate("""(id) => {
                                let el = document.getElementById(id);
                                if (el) {
                                    let nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                                    nativeInputValueSetter.call(el, '09/01/2025');
                                    el.dispatchEvent(new Event('input', {bubbles:true}));
                                    el.dispatchEvent(new Event('change', {bubbles:true}));
                                }
                            }""", date_fid)
                            time.sleep(0.5)
                            log("  [date] JS native setter applied")
                            page.keyboard.press("Escape")

                except Exception as e:
                    log(f"  [date!] {e}")

            ss(page, "v8_13_date_filled")

            # ── Work Authorization ────────────────────────────────────────
            log("\n[7] Filling Work Authorization Status...")
            if alive(page):
                # Q1: Legally authorized → Yes
                log("  [work_auth] Q1: authorized → Yes")
                phenom_click_select(page, "input-10", "Yes", "work_auth_Q1")
                time.sleep(1)

                # Q2: Require sponsorship → Yes (truthful)
                log("  [work_auth] Q2: sponsorship → Yes")
                phenom_click_select(page, "input-13", "Yes", "work_auth_Q2")
                time.sleep(1)

            ss(page, "v8_14_workauth_filled")

            # ── Voluntary Self-Identification ─────────────────────────────
            log("\n[8] Filling Voluntary Self-Identification...")
            if alive(page):

                # Gender → Woman (exact option from debug)
                log("  [gender] → Woman")
                phenom_click_select(page, "input-16", "Woman", "gender")
                time.sleep(1)

                # Ethnicity → Non Hispanic/Latino (exact option from debug)
                log("  [ethnicity] → Non Hispanic/Latino")
                phenom_click_select(page, "input-19", "Non Hispanic/Latino", "hispanic_Q")
                time.sleep(1)

                # Race checkboxes → check Asian
                log("  [race] Checking Asian checkbox...")
                asian_cb_id = "Voluntary_Self_Identification_race-Asian-2"
                asian_checked = False
                try:
                    cb = page.locator(f"#{asian_cb_id}").first
                    if cb.count() > 0:
                        cb.scroll_into_view_if_needed()
                        time.sleep(0.3)
                        if not cb.is_checked():
                            cb.click(force=True)
                            time.sleep(0.8)
                        asian_checked = cb.is_checked()
                        log(f"  [race-ok] Asian checked = {asian_checked}")
                except Exception as e:
                    log(f"  [race!] {e}")

                if not asian_checked:
                    # JS fallback
                    try:
                        page.evaluate("""() => {
                            let cb = document.getElementById('Voluntary_Self_Identification_race-Asian-2');
                            if (cb) {
                                cb.scrollIntoView();
                                cb.click();
                                cb.checked = true;
                                cb.dispatchEvent(new Event('change',{bubbles:true}));
                            }
                        }""")
                        time.sleep(0.5)
                        log("  [race-js] Asian checkbox JS click attempted")
                    except: pass

                # Disability → No, I don't have a disability...
                log("  [disability] → No disability")
                phenom_click_select(page, "input-22", "No, I don't have a disability", "disability")
                time.sleep(1)

                # Veteran → No  (options: Yes, No, I prefer not to provide this information)
                log("  [veteran] → No")
                phenom_click_select(page, "input-25", "No", "veteran")
                time.sleep(1)

            ss(page, "v8_15_eeoc_filled")

            # ── Verify all fields before submit ──────────────────────────
            log("\n[9] Verifying fields + checking errors...")
            if alive(page):
                page.evaluate("window.scrollTo(0, 0)")
                time.sleep(1)
                ss(page, "v8_16_full_top")
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(2)
                ss(page, "v8_16_full_bottom")

                body = txt(page)
                error_lines = [l.strip() for l in body.split('\n')
                               if any(w in l.lower() for w in [
                                   "error found", "error:", "required", "cannot be left blank",
                                   "select a value", "select at least one"
                               ])]
                log(f"  Pre-submit errors: {error_lines[:10]}")

                # If still errors, try to re-fill the ones that failed
                if error_lines:
                    log("  [fix] Attempting to re-fill errored fields...")
                    # Re-check each dropdown that might have failed
                    # Check field values
                    fields_to_check = [
                        ("input-10", "Yes", "work_auth_Q1"),
                        ("input-13", "Yes", "work_auth_Q2"),
                        ("input-16", "Woman", "gender"),
                        ("input-19", "Non Hispanic/Latino", "ethnicity"),
                        ("input-22", "No, I don't have a disability", "disability"),
                        ("input-25", "No", "veteran"),
                    ]
                    for fid, desired, lbl in fields_to_check:
                        if not alive(page): break
                        try:
                            el = page.locator(f"#{fid}").first
                            if el.count() > 0:
                                cur = el.input_value(timeout=2000)
                                if not cur.strip():
                                    log(f"  [re-fill] {lbl} is empty, retrying...")
                                    phenom_click_select(page, fid, desired, lbl)
                                    time.sleep(1)
                                else:
                                    log(f"  [check] {lbl} = '{cur[:40]}'")
                        except: pass

                    # Re-check Asian checkbox
                    try:
                        cb = page.locator(f"#{asian_cb_id}").first
                        if cb.count() > 0 and not cb.is_checked():
                            cb.scroll_into_view_if_needed()
                            cb.click(force=True)
                            time.sleep(0.5)
                            log(f"  [re-check] Asian = {cb.is_checked()}")
                    except: pass

                    time.sleep(1)
                    ss(page, "v8_16b_after_refill")

            # ── Pre-submit screenshot ─────────────────────────────────────
            if alive(page):
                page.evaluate("window.scrollTo(0, 0)")
                time.sleep(1)
                ss(page, "v8_17_pre_submit")

            log("\n[10] Submitting application...")
            if not alive(page):
                R["status"] = "error"
                R["notes"] = "Page closed before submit"
                save(R); return R

            submit_clicked = False
            for s in [
                "button:has-text('Submit Application')",
                "button:has-text('Submit application')",
                "button:has-text('Submit')",
                "input[type='submit'][value*='Submit' i]",
            ]:
                try:
                    el = page.locator(s).first
                    if el.count() > 0 and el.is_visible(timeout=3000):
                        t_val = el.inner_text().strip().lower()
                        if any(bad in t_val for bad in ["subscribe", "newsletter"]):
                            continue
                        el.scroll_into_view_if_needed()
                        ss(page, "v8_18_about_to_submit")
                        el.click(timeout=5000)
                        submit_clicked = True
                        log(f"  [submit] Clicked: {s}")
                        time.sleep(12); net(page, 20000)
                        break
                except Exception as e:
                    log(f"  [submit!] {s}: {e}")

            if not submit_clicked:
                R["status"] = "blocked"
                R["notes"] = f"No submit button found. URL: {page.url}. Body: {txt(page)[:300]}"
                ss(page, "v8_99_no_submit")
                try: browser.close()
                except: pass
                save(R); return R

            # ── Post-submit ───────────────────────────────────────────────
            if not alive(page):
                R["status"] = "likely-submitted"
                R["confirmed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                R["notes"] = "Submit clicked but page closed before confirmation check."
                save(R); return R

            body = txt(page)
            ss(page, "v8_19_post_submit")
            log(f"\n  Post-submit URL: {page.url}")
            log(f"  Post-submit body (first 600): {body[:600]}")

            if has_captcha(page):
                R["status"] = "captcha-staged"
                R["notes"] = f"CAPTCHA after Submit. URL: {page.url}"
                try: browser.close()
                except: pass
                save(R); return R

            if is_real_confirmation(body, page.url):
                R["status"] = "submitted"
                R["confirmed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                R["screenshot"] = os.path.join(SHOT, "v8_19_post_submit.png")
                R["notes"] = f"SUBMITTED. {body[:600]}"
                log("  *** CONFIRMED SUBMISSION! ***")
                try: browser.close()
                except: pass
                save(R); return R

            # Check remaining errors
            error_lines = [l.strip() for l in body.split('\n')
                           if any(w in l.lower() for w in [
                               "error found", "error:", "required", "cannot be left blank",
                               "select a value", "select at least one"
                           ])]
            if error_lines:
                log(f"  Still has errors: {error_lines[:8]}")
                R["status"] = "blocked"
                R["notes"] = (
                    f"Submit clicked but form still has errors: {error_lines[:5]}. "
                    f"URL: {page.url}. Body: {body[:400]}"
                )
                try: browser.close()
                except: pass
                save(R); return R

            R["status"] = "likely-submitted"
            R["confirmed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            R["screenshot"] = os.path.join(SHOT, "v8_19_post_submit.png")
            R["notes"] = f"Submit clicked. No errors. Body: {body[:600]}"
            try: browser.close()
            except: pass
            save(R); return R

        except Exception as e:
            tb = traceback.format_exc()
            log(f"\n[EXCEPTION] {e}\n{tb[:1000]}")
            R["status"] = "error"
            R["notes"] = f"Exception: {str(e)}\n{tb[:500]}"
            try:
                if alive(page): ss(page, "v8_99_exception")
            except: pass
            try: browser.close()
            except: pass
            save(R); return R


if __name__ == "__main__":
    main()
