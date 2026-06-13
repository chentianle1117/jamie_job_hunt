# -*- coding: utf-8 -*-
"""
submit_bcg_v7.py  -- BCG Phenom ATS (v7)

Key insight from v6 field inspection:
  All dropdowns are Phenom custom listbox widgets — input[type='text'][placeholder='Select']
  You CANNOT use page.select_option(). You must:
    1. Click the input (or its parent wrapper)
    2. Wait for the dropdown list to appear
    3. Click the desired option

  Known field IDs (from v6 inspection):
  - Personal: Before_applying_email, Before_applying_firstname,
    Before_applying_preferred_first_name, Before_applying_lastname,
    Before_applying_phone, input-7 (Country), input-28 (State), Before_applying_location (City)
  - Start date: Available_Start_Date_start_date  (placeholder='Select date')
  - Work auth:  input-10 (authorized?), input-13 (sponsorship?)
  - EEO Gender: input-16
  - EEO Ethnicity: input-19  (also checkboxes: Voluntary_Self_Identification_race-Asian-2)
  - EEO Disability: input-22
  - EEO Veteran: input-25

  Phenom listbox pattern:
    - Input is inside a div[class*="listbox"] or div[class*="dropdown"]
    - Click the input → options appear as li elements or div[role="option"]
    - Click the desired option by text
"""
import os, sys, time, json, subprocess, traceback
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, r"C:\Users\chent\Agentic_Workflows_2026\jamie-autopilot\lib")
from patchright.sync_api import sync_playwright
from credential_vault import job_password

PORT     = 9402
PROFILE  = r"C:\Users\chent\ats_agent_9402_v4"
CHROME   = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
ROLE_DIR = (r"C:\Users\chent\Agentic_Workflows_2026\oracle-job-search"
            r"\outputs\2026-06-12-feed-first\applications\bcg_talent_sr_specialist")
SHOT     = ROLE_DIR + r"\screenshots\v7"
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

def ss(page, name):
    path = os.path.join(SHOT, name + ".png")
    try:
        page.screenshot(path=path, full_page=True)
        print(f"  [ss] {name}.png")
    except Exception as e:
        print(f"  [ss!] {name}: {e}")
    return path


def net(page, t=15000):
    try: page.wait_for_load_state("networkidle", timeout=t)
    except: pass


def txt(page):
    try: return page.inner_text("body")
    except: return ""


def dismiss_cookie(page):
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
    try:
        el = page.locator(f"#{field_id}").first
        el.wait_for(state="visible", timeout=5000)
        el.scroll_into_view_if_needed()
        el.click(timeout=3000)
        el.fill("", timeout=2000)
        el.fill(val, timeout=5000)
        print(f"  [fill] {lbl or field_id} = '{val[:50]}'")
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
            print(f"  [fill-js] {lbl or field_id} = '{val[:50]}'")
            return True
        except: pass
        print(f"  [fill!] {lbl or field_id}: {str(e)[:80]}")
        return False


def phenom_dropdown_select(page, field_id, desired_text, lbl=""):
    """
    Select a value from a Phenom custom listbox widget.
    Pattern:
      1. Click the input#<field_id> to open the dropdown
      2. Wait for options to appear (li, div[role='option'], etc.)
      3. Click the option matching desired_text (partial, case-insensitive)
    Returns True if selected, False otherwise.
    """
    print(f"  [dropdown] {lbl or field_id} → '{desired_text}'")
    try:
        inp = page.locator(f"#{field_id}").first
        inp.wait_for(state="visible", timeout=5000)
        inp.scroll_into_view_if_needed()

        # Type desired text to filter options (Phenom listboxes filter on input)
        inp.click(timeout=3000)
        inp.fill("", timeout=2000)
        time.sleep(0.5)

        # Try typing to filter
        inp.fill(desired_text[:10], timeout=3000)
        time.sleep(1.5)  # wait for filter

        ss(page, f"v7_dd_{field_id[:20]}_open")

        # Look for dropdown options in various containers
        option_selectors = [
            f"[id*='{field_id}'] li",
            f"[aria-labelledby='{field_id}'] li",
            "[role='listbox'] li",
            "[role='listbox'] [role='option']",
            "[class*='dropdown'] li",
            "[class*='listbox'] li",
            "[class*='options'] li",
            "[class*='menu'] li",
            "ul[class*='list'] li",
            "div[class*='option']",
            "[data-testid*='option']",
        ]

        for opt_sel in option_selectors:
            try:
                opts = page.locator(opt_sel).all()
                if opts:
                    for opt in opts:
                        try:
                            opt_text = opt.inner_text().strip()
                            if desired_text.lower() in opt_text.lower():
                                opt.scroll_into_view_if_needed()
                                opt.click(timeout=3000)
                                time.sleep(1)
                                # Verify selection
                                val_after = inp.input_value()
                                print(f"    [dropdown-ok] selected '{opt_text}' (sel={opt_sel}), field now='{val_after[:40]}'")
                                return True
                        except: continue
            except: continue

        # Fallback: clear and try without filter text, then pick first partial match
        try:
            inp.fill("", timeout=2000)
            time.sleep(0.5)
            for opt_sel in option_selectors:
                try:
                    opts = page.locator(opt_sel).all()
                    if opts:
                        for opt in opts:
                            try:
                                opt_text = opt.inner_text().strip()
                                if desired_text.lower() in opt_text.lower():
                                    opt.scroll_into_view_if_needed()
                                    opt.click(timeout=3000)
                                    time.sleep(1)
                                    print(f"    [dropdown-ok-fallback] '{opt_text}'")
                                    return True
                            except: continue
                except: continue
        except: pass

        # Last resort: press Escape to close, use JS to set the value directly
        try:
            page.keyboard.press("Escape")
            time.sleep(0.3)
        except: pass

        print(f"    [dropdown!] Could not find option '{desired_text}' in {field_id}")
        return False

    except Exception as e:
        print(f"  [dropdown!] {lbl or field_id}: {str(e)[:80]}")
        return False


def phenom_dropdown_debug(page, field_id):
    """Click the dropdown and print all available options for debugging."""
    print(f"  [dd-debug] Opening {field_id} to inspect options...")
    try:
        inp = page.locator(f"#{field_id}").first
        inp.wait_for(state="visible", timeout=5000)
        inp.scroll_into_view_if_needed()
        inp.click(timeout=3000)
        inp.fill("", timeout=2000)
        time.sleep(1.5)
        ss(page, f"v7_debug_{field_id[:20]}")

        # Try to get all option text
        result = page.evaluate("""(fid) => {
            let opts = [];
            // Common option selectors
            let selectors = [
                '[role="listbox"] li', '[role="listbox"] [role="option"]',
                '[role="option"]', '[class*="option"]', '[class*="dropdown"] li',
                '[class*="listbox"] li', '[class*="menu"] li',
                'ul li[class*="item"]', 'div[class*="item"]'
            ];
            for (let sel of selectors) {
                let els = document.querySelectorAll(sel);
                if (els.length > 0) {
                    opts = Array.from(els).map(e => e.textContent.trim().slice(0,60));
                    if (opts.some(t => t.length > 0)) break;
                }
            }
            return {count: opts.length, options: opts.slice(0,20), selector: 'various'};
        }""", field_id)
        print(f"    Options: {result}")
        # Press escape to close
        page.keyboard.press("Escape")
        time.sleep(0.5)
        return result.get('options', [])
    except Exception as e:
        print(f"    [dd-debug!] {e}")
        return []


def has_captcha(page):
    for sel in ["iframe[src*='recaptcha']", "iframe[src*='hcaptcha']",
                ".g-recaptcha", "[data-sitekey]", ".cf-turnstile"]:
        try:
            if page.locator(sel).count() > 0: return True
        except: pass
    try: return any(w in txt(page)[:2000].lower() for w in ["captcha", "i'm not a robot"])
    except: return False


def has_email_verify(page):
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
    print(f"\n[SAVED] {path}")
    print("=" * 60)
    print(f"RESULT: {result['status']}")
    print(f"Notes:  {str(result.get('notes',''))[:600]}")
    print("=" * 60)


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

    print("=" * 60)
    print("BCG Phenom v7 -- Talent Senior Specialist - People")
    print("=" * 60)

    subprocess.run(
        ["powershell", "-Command",
         f"Get-NetTCPConnection -LocalPort {PORT} -ErrorAction SilentlyContinue | "
         f"Select-Object -ExpandProperty OwningProcess | "
         f"ForEach-Object {{ Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }}"],
        capture_output=True, timeout=10
    )
    time.sleep(2)

    print(f"\n[1] Launching Chrome (port {PORT})...")
    proc = subprocess.Popen(
        [CHROME,
         f"--remote-debugging-port={PORT}",
         f"--user-data-dir={PROFILE}",
         "--no-first-run", "--no-default-browser-check",
         "--disable-blink-features=AutomationControlled",
         PHENOM_LOGIN],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    print(f"  PID {proc.pid}, waiting 15s...")
    time.sleep(15)

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(f"http://localhost:{PORT}")
        ctx = browser.contexts[0]
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.set_default_timeout(30000)

        try:
            net(page, 20000); time.sleep(3)
            dismiss_cookie(page); time.sleep(2)
            ss(page, "v7_01_initial")
            print(f"  URL: {page.url}")

            # ── Login ─────────────────────────────────────────────────────
            print("\n[2] Login...")
            if "login" in page.url.lower():
                # Enter email
                for s in ["input[type='email']", "input[placeholder*='Email' i]",
                           "input[id*='email' i]", "input[autocomplete='email']"]:
                    try:
                        el = page.locator(s).first
                        if el.count() > 0 and el.is_visible(timeout=3000):
                            el.click(); el.fill(""); el.fill(EMAIL)
                            print(f"  [fill] email")
                            break
                    except: continue

                page.locator("button:has-text('Continue')").first.click()
                time.sleep(7); net(page, 15000); dismiss_cookie(page)
                ss(page, "v7_02_after_email")
                body = txt(page)

                if has_captcha(page):
                    R["status"] = "captcha-staged"; R["notes"] = "CAPTCHA after email."
                    browser.close(); save(R); return R
                if has_email_verify(page):
                    R["status"] = "email-verify-staged"; R["notes"] = f"Email verify. Check {EMAIL}."
                    browser.close(); save(R); return R

                if "password" in body.lower():
                    pws = page.locator("input[type='password']").all()
                    if pws:
                        pws[0].click(); pws[0].fill(PW)
                        print("  [fill] password")
                    page.locator("button:has-text('Submit')").first.click()
                    time.sleep(8); net(page, 15000); dismiss_cookie(page)
                    ss(page, "v7_03_after_signin")
                    print(f"  Post-signin URL: {page.url}")

                    if "login" in page.url.lower():
                        # Try OTP
                        try:
                            page.locator("a:has-text('Use a one-time code instead')").first.click()
                            time.sleep(4)
                        except: pass
                        R["status"] = "email-verify-staged"
                        R["notes"] = (
                            f"Password login failed. Clicked OTP link — check {EMAIL}. "
                            f"Chrome on port {PORT}."
                        )
                        ss(page, "v7_99_login_fail"); browser.close(); save(R); return R

                elif any(w in body.lower() for w in ["first name", "create account", "register"]):
                    for s in ["input[placeholder*='First' i]", "input[name*='first' i]"]:
                        try:
                            el = page.locator(s).first
                            if el.count() > 0 and el.is_visible(timeout=2000):
                                el.click(); el.fill("Yi-Chieh"); break
                        except: pass
                    for s in ["input[placeholder*='Last' i]", "input[name*='last' i]"]:
                        try:
                            el = page.locator(s).first
                            if el.count() > 0 and el.is_visible(timeout=2000):
                                el.click(); el.fill("Cheng"); break
                        except: pass
                    for pw_el in page.locator("input[type='password']").all()[:2]:
                        try: pw_el.fill(PW)
                        except: pass
                    if has_captcha(page):
                        R["status"] = "captcha-staged"; R["notes"] = "CAPTCHA on registration."
                        browser.close(); save(R); return R
                    for s in ["button:has-text('Create Account')", "button:has-text('Sign Up')",
                               "button[type='submit']"]:
                        try:
                            el = page.locator(s).first
                            if el.count() > 0 and el.is_visible(timeout=2000):
                                el.click(); break
                        except: pass
                    time.sleep(8); net(page, 15000)
                    if has_email_verify(page):
                        R["status"] = "email-verify-staged"
                        R["notes"] = f"Account created — verify at {EMAIL}."
                        browser.close(); save(R); return R

            # ── Load application form ─────────────────────────────────────
            print("\n[3] Loading application form...")
            page.goto(PHENOM_APPLY, timeout=30000, wait_until="domcontentloaded")
            time.sleep(8); net(page, 15000); dismiss_cookie(page); time.sleep(2)
            ss(page, "v7_10_form")
            print(f"  URL: {page.url}")
            if "login" in page.url.lower():
                R["status"] = "email-verify-staged"
                R["notes"] = f"Redirected to login. Check {EMAIL}."
                browser.close(); save(R); return R

            # ── DEBUG: inspect all dropdown options ───────────────────────
            print("\n[4] Debugging dropdown options...")

            # Start date
            print("  === Available Start Date (Available_Start_Date_start_date) ===")
            date_opts = phenom_dropdown_debug(page, "Available_Start_Date_start_date")

            # Work auth dropdowns
            print("  === Work Auth 1 (input-10) ===")
            auth_opts = phenom_dropdown_debug(page, "input-10")
            print("  === Work Auth 2 (input-13) ===")
            sponsor_opts = phenom_dropdown_debug(page, "input-13")

            # EEO dropdowns
            print("  === Gender (input-16) ===")
            gender_opts = phenom_dropdown_debug(page, "input-16")
            print("  === Ethnicity (input-19) ===")
            ethnicity_opts = phenom_dropdown_debug(page, "input-19")
            print("  === Disability (input-22) ===")
            disability_opts = phenom_dropdown_debug(page, "input-22")
            print("  === Veteran (input-25) ===")
            veteran_opts = phenom_dropdown_debug(page, "input-25")

            ss(page, "v7_11_after_debug")

            # ── Upload resume ─────────────────────────────────────────────
            print("\n[5] Uploading resume...")
            for s in ["input[type='file'][accept*='pdf' i]", "input[type='file']"]:
                try:
                    inputs = page.locator(s).all()
                    if inputs:
                        inputs[0].set_input_files(RESUME)
                        time.sleep(5)
                        print(f"  [upload] resume via {s}")
                        for dismiss in ["No, thanks", "Skip", "No thanks", "Enter Manually"]:
                            try:
                                el = page.get_by_text(dismiss, exact=False).first
                                if el.count() > 0 and el.is_visible(timeout=2000):
                                    el.click(); time.sleep(2); break
                            except: pass
                        break
                except Exception as e:
                    print(f"  [upload!] {e}")
            ss(page, "v7_12_after_resume")

            # ── Fill personal info ────────────────────────────────────────
            print("\n[6] Filling personal info...")

            # Check what's already pre-filled
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
                            print(f"  [skip] {lbl} already = '{cur[:30]}'")
                except: pass

            # Preferred first name
            try:
                el = page.locator("#Before_applying_preferred_first_name").first
                if el.count() > 0 and el.is_visible(timeout=1500):
                    if not el.input_value().strip():
                        fill_text(page, "Before_applying_preferred_first_name", "Jamie", "preferred_first")
            except: pass

            # Country dropdown (input-7)
            print("  [country] Setting United States...")
            phenom_dropdown_select(page, "input-7", "United States", "country")
            time.sleep(1.5)  # wait for state cascade

            # State dropdown (input-28)
            print("  [state] Setting Oregon...")
            phenom_dropdown_select(page, "input-28", "Oregon", "state")
            time.sleep(1)

            ss(page, "v7_13_personal_filled")

            # ── Available Start Date ──────────────────────────────────────
            print("\n[7] Filling Available Start Date...")
            # Phenom date picker: click input, then pick from calendar OR type
            date_fid = "Available_Start_Date_start_date"

            # First try: just open the picker and look for a specific month/date
            # Most Phenom instances accept a text date after clicking
            try:
                el = page.locator(f"#{date_fid}").first
                el.wait_for(state="visible", timeout=5000)
                el.scroll_into_view_if_needed()
                el.click(timeout=3000)
                time.sleep(1.5)
                ss(page, "v7_14a_date_picker_open")

                # Check if a calendar appeared
                cal_body = page.evaluate("""() => {
                    let els = document.querySelectorAll(
                        '[class*="calendar"],[class*="datepicker"],[class*="date-picker"],' +
                        '[role="dialog"],[class*="picker-panel"],[class*="dp__"]'
                    );
                    return Array.from(els).map(e => e.textContent.trim().slice(0,100));
                }""")
                print(f"  [date] Calendar elements: {cal_body[:3]}")

                if cal_body:
                    # It's a calendar — navigate to Sep 2025
                    # Try typing the date directly in the input
                    el.fill("09/01/2025", timeout=3000)
                    time.sleep(1)
                    val = el.input_value()
                    if val:
                        print(f"  [date] Filled via text: '{val}'")
                    else:
                        # Click Sep 1 on the calendar
                        # Navigate months if needed
                        for nav_attempt in range(6):
                            cal_text = page.evaluate("""() => {
                                let h = document.querySelector('[class*="calendar"] [class*="header"],[class*="datepicker"] [class*="month"]');
                                return h ? h.textContent.trim() : '';
                            }""")
                            print(f"    Cal header: {cal_text}")
                            if "sep" in cal_text.lower() or "2025" in cal_text:
                                break
                            # Click next month button
                            for nav_sel in ["button[aria-label*='next' i]", "button[class*='next' i]",
                                             "[class*='next-month']", "[class*='right-arrow']",
                                             "button:has-text('>')", "button:has-text('›')"]:
                                try:
                                    nb = page.locator(nav_sel).first
                                    if nb.count() > 0 and nb.is_visible(timeout=1000):
                                        nb.click(); time.sleep(0.8); break
                                except: pass

                        # Click day 1
                        for day_sel in ["button:has-text('1')", "td:has-text('1')", "[class*='day']:has-text('1')"]:
                            try:
                                days = page.locator(day_sel).all()
                                for d in days:
                                    if d.inner_text().strip() == "1":
                                        d.click(); time.sleep(0.5); break
                            except: pass

                    page.keyboard.press("Escape")
                    time.sleep(0.5)
                else:
                    # No calendar — it's a text input
                    el.fill("09/01/2025", timeout=3000)
                    time.sleep(0.5)
                    page.keyboard.press("Tab")
                    time.sleep(0.5)
                    print(f"  [date] Filled as text")

            except Exception as e:
                print(f"  [date!] {e}")
                # JS fallback
                try:
                    page.evaluate(
                        "(id) => { let el = document.getElementById(id); if(el){"
                        "  el.focus(); el.value='09/01/2025';"
                        "  el.dispatchEvent(new Event('input',{bubbles:true}));"
                        "  el.dispatchEvent(new Event('change',{bubbles:true})); } }",
                        date_fid
                    )
                    print("  [date] JS fallback applied")
                except: pass

            ss(page, "v7_14_date_filled")

            # ── Work Authorization ────────────────────────────────────────
            print("\n[8] Filling Work Authorization Status...")

            # Q1: Legally authorized to work in US? → Yes
            print("  [work_auth] Q1: authorized → selecting from options:", auth_opts)
            auth_selected = False
            for opt in auth_opts:
                if "yes" in opt.lower():
                    auth_selected = phenom_dropdown_select(page, "input-10", opt, "work_auth_Q1")
                    break
            if not auth_selected:
                auth_selected = phenom_dropdown_select(page, "input-10", "Yes", "work_auth_Q1")

            # Q2: Require sponsorship? → Yes (truthful)
            print("  [work_auth] Q2: sponsorship → selecting from options:", sponsor_opts)
            sponsor_selected = False
            for opt in sponsor_opts:
                if "yes" in opt.lower():
                    sponsor_selected = phenom_dropdown_select(page, "input-13", opt, "work_auth_Q2")
                    break
            if not sponsor_selected:
                sponsor_selected = phenom_dropdown_select(page, "input-13", "Yes", "work_auth_Q2")

            ss(page, "v7_15_workauth_filled")

            # ── Voluntary Self-Identification ─────────────────────────────
            print("\n[9] Filling Voluntary Self-Identification...")

            # Gender → Female
            print("  [gender] Options:", gender_opts)
            gender_selected = False
            for opt in gender_opts:
                if any(w in opt.lower() for w in ["female", "woman"]):
                    gender_selected = phenom_dropdown_select(page, "input-16", opt, "gender")
                    break
            if not gender_selected:
                gender_selected = phenom_dropdown_select(page, "input-16", "Female", "gender")

            # Ethnicity → Not Hispanic/Latino  (this is a SEPARATE question from Race)
            print("  [ethnicity] Options:", ethnicity_opts)
            ethnicity_selected = False
            for opt in ethnicity_opts:
                if any(w in opt.lower() for w in ["not hispanic", "no", "non-hispanic"]):
                    ethnicity_selected = phenom_dropdown_select(page, "input-19", opt, "hispanic_Q")
                    break
            if not ethnicity_selected:
                # Try "No" or the negative option
                for opt in ethnicity_opts:
                    if "no" in opt.lower():
                        ethnicity_selected = phenom_dropdown_select(page, "input-19", opt, "hispanic_Q")
                        break
            if not ethnicity_selected:
                phenom_dropdown_select(page, "input-19", "Not Hispanic or Latino", "hispanic_Q")

            # Race checkboxes → check Asian
            print("  [race] Checking Asian checkbox...")
            asian_cb_id = "Voluntary_Self_Identification_race-Asian-2"
            try:
                cb = page.locator(f"#{asian_cb_id}").first
                if cb.count() > 0:
                    cb.scroll_into_view_if_needed()
                    if not cb.is_checked():
                        cb.click(force=True)
                        time.sleep(0.5)
                    print(f"  [checkbox] Asian checked = {cb.is_checked()}")
            except Exception as e:
                print(f"  [checkbox!] Asian: {e}")
                # JS fallback
                page.evaluate("""() => {
                    let cb = document.getElementById('Voluntary_Self_Identification_race-Asian-2');
                    if (cb && !cb.checked) {
                        cb.click(); cb.checked = true;
                        cb.dispatchEvent(new Event('change',{bubbles:true}));
                    }
                }""")

            # Disability → No
            print("  [disability] Options:", disability_opts)
            dis_selected = False
            for opt in disability_opts:
                if any(w in opt.lower() for w in ["no, i don't", "do not have", "no disability",
                                                    "i don't have"]):
                    dis_selected = phenom_dropdown_select(page, "input-22", opt, "disability")
                    break
            if not dis_selected:
                for opt in disability_opts:
                    if opt.lower().startswith("no"):
                        dis_selected = phenom_dropdown_select(page, "input-22", opt, "disability")
                        break
            if not dis_selected:
                phenom_dropdown_select(page, "input-22", "No", "disability")

            # Veteran → Not a protected veteran
            print("  [veteran] Options:", veteran_opts)
            vet_selected = False
            for opt in veteran_opts:
                if any(w in opt.lower() for w in ["not a protected", "am not", "not being"]):
                    vet_selected = phenom_dropdown_select(page, "input-25", opt, "veteran")
                    break
            if not vet_selected:
                for opt in veteran_opts:
                    if "not" in opt.lower() or opt.lower() == "no":
                        vet_selected = phenom_dropdown_select(page, "input-25", opt, "veteran")
                        break
            if not vet_selected:
                phenom_dropdown_select(page, "input-25", "I am not a protected veteran", "veteran")

            time.sleep(1)
            ss(page, "v7_16_eeoc_filled")

            # ── Scroll full page and check errors ─────────────────────────
            print("\n[10] Checking for remaining errors...")
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(2)
            ss(page, "v7_17_full_scroll")
            body = txt(page)
            errors = [l.strip() for l in body.split('\n')
                      if any(w in l.lower() for w in ["error", "required", "cannot be left blank",
                                                        "must be", "select a"])]
            print(f"  Errors found: {errors[:10]}")

            if is_real_confirmation(body, page.url):
                R["status"] = "submitted"
                R["confirmed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                R["screenshot"] = os.path.join(SHOT, "v7_17_full_scroll.png")
                R["notes"] = f"Already submitted. {body[:400]}"
                browser.close(); save(R); return R

            # ── Pre-submit screenshot ─────────────────────────────────────
            page.evaluate("window.scrollTo(0, 0)")
            time.sleep(1)
            ss(page, "v7_18_pre_submit")
            print(f"\n[11] Submitting...")

            # Find Submit Application button
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
                        ss(page, "v7_19_about_to_submit")
                        el.click(timeout=5000)
                        submit_clicked = True
                        print(f"  Clicked: {s}")
                        time.sleep(10); net(page, 20000)
                        break
                except Exception as e:
                    print(f"  [submit!] {s}: {e}")

            if not submit_clicked:
                R["status"] = "blocked"
                R["notes"] = f"No submit button. URL: {page.url}. Body: {txt(page)[:300]}"
                ss(page, "v7_99_no_submit")
                browser.close(); save(R); return R

            # ── Post-submit ───────────────────────────────────────────────
            body = txt(page)
            ss(page, "v7_20_post_submit")
            print(f"\n  Post-submit URL: {page.url}")
            print(f"  Post-submit body: {body[:600]}")

            if has_captcha(page):
                R["status"] = "captcha-staged"
                R["notes"] = f"CAPTCHA after Submit. URL: {page.url}"
                browser.close(); save(R); return R

            if is_real_confirmation(body, page.url):
                R["status"] = "submitted"
                R["confirmed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                R["screenshot"] = os.path.join(SHOT, "v7_20_post_submit.png")
                R["notes"] = f"SUBMITTED. {body[:600]}"
                print("  *** CONFIRMED SUBMISSION! ***")
                browser.close(); save(R); return R

            # Check if still errors
            error_lines = [l.strip() for l in body.split('\n')
                           if any(w in l.lower() for w in ["error found", "error:", "required", "cannot be left blank"])]
            if error_lines:
                print(f"  Errors still present: {error_lines[:5]}")
                R["status"] = "blocked"
                R["notes"] = (
                    f"Submit clicked but form still has errors: {error_lines[:5]}. "
                    f"URL: {page.url}. Body: {body[:400]}"
                )
                browser.close(); save(R); return R

            R["status"] = "likely-submitted"
            R["confirmed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            R["screenshot"] = os.path.join(SHOT, "v7_20_post_submit.png")
            R["notes"] = f"Submit clicked. No errors visible. Body: {body[:600]}"
            browser.close(); save(R); return R

        except Exception as e:
            tb = traceback.format_exc()
            print(f"\n[EXCEPTION] {e}\n{tb[:1000]}")
            R["status"] = "error"
            R["notes"] = f"Exception: {str(e)}\n{tb[:500]}"
            try: ss(page, "v7_99_exception")
            except: pass
            try: browser.close()
            except: pass
            save(R); return R


if __name__ == "__main__":
    main()
