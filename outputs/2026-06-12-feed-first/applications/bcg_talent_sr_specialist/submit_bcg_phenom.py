# -*- coding: utf-8 -*-
"""
submit_bcg_phenom.py
BCG "Talent Senior Specialist - People" application via Phenom ATS
(experiencedtalent.bcg.com/careerhub)

BCG DOES NOT use Workday. They use Phenom (PhW/Eightfold-branded).
Flow: careers.bcg.com JD -> Apply -> Phenom candidate login/signup
      -> Phenom application wizard -> Submit

Persistence rules:
- Dismiss TrustArc cookie banner via JS before any clicks
- Open Apply link in SAME tab (it opens in new tab -- navigate directly instead)
- Account: create with jamiecheng0103@gmail.com + shared password
- CAPTCHA / email-verify gate -> stage + report, detach CDP
"""
import os, sys, time, json, subprocess, traceback
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, r"C:\Users\chent\Agentic_Workflows_2026\jamie-autopilot\lib")
from patchright.sync_api import sync_playwright
from credential_vault import job_password

PORT = 9402
PROFILE = r"C:\Users\chent\ats_agent_9402"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
ROLE_DIR = r"C:\Users\chent\Agentic_Workflows_2026\oracle-job-search\outputs\2026-06-12-feed-first\applications\bcg_talent_sr_specialist"
SHOT = ROLE_DIR + r"\screenshots"
RESUME = ROLE_DIR + r"\resume.pdf"
os.makedirs(SHOT, exist_ok=True)

EMAIL = "jamiecheng0103@gmail.com"
PW = job_password()

JOB_ID = "790315808241"
JOB_URL = "https://careers.bcg.com/global/en/job/57988/Talent-Senior-Specialist-People"
# Direct Phenom apply URL (opens in new tab from JD page)
PHENOM_APPLY_URL = (
    f"https://experiencedtalent.bcg.com/careerhub/explore/jobs/{JOB_ID}"
    f"?post_onboarding_pid={JOB_ID}&show_apply=1&profile_type=candidate&customredirect=1"
)
PHENOM_LOGIN = "https://experiencedtalent.bcg.com/candidate/login?domain=bcg.com&hl=en&microsite=microsite_1"
PHENOM_SIGNUP = "https://experiencedtalent.bcg.com/candidate/signup?domain=bcg.com&hl=en&microsite=microsite_1"

# ── Helpers ────────────────────────────────────────────────────────────────────

def shot(page, name):
    path = os.path.join(SHOT, name + ".png")
    try:
        page.screenshot(path=path, full_page=True)
        print(f"  [ss] {name}.png")
    except Exception as e:
        print(f"  [ss FAIL] {e}")
    return path


def wait_net(page, t=12000):
    try:
        page.wait_for_load_state("networkidle", timeout=t)
    except:
        pass


def dismiss_cookie(page):
    """Dismiss TrustArc / OneTrust / Phenom cookie banners via JS hide + click."""
    try:
        result = page.evaluate("""
        (function() {
            var clicked = [];
            var btns = ['#truste-consent-button', '#onetrust-accept-btn-handler',
                        '[data-testid="cookie-accept"]'];
            for (var sel of btns) {
                var b = document.querySelector(sel);
                if (b) { b.click(); clicked.push(sel); }
            }
            var hidden = 0;
            document.querySelectorAll(
                '[id*="truste"],[class*="truste_overlay"],[class*="truste_box"],' +
                '[id*="onetrust"],[class*="onetrust"],.cc-overlay'
            ).forEach(function(el) {
                el.style.cssText = 'display:none!important;visibility:hidden!important;pointer-events:none!important;';
                hidden++;
            });
            return 'clicked=' + clicked.join(',') + ' hidden=' + hidden;
        })()
        """)
        print(f"  [cookie] {result}")
    except Exception as e:
        print(f"  [cookie err] {e}")
    time.sleep(0.5)


def fill(page, selector, value, label="", timeout=8000):
    """Fill a text input, trying multiple strategies."""
    for strategy in ["fill", "triple_click+fill", "type"]:
        try:
            el = page.locator(selector).first
            el.wait_for(state="visible", timeout=timeout)
            if strategy == "fill":
                el.click(timeout=3000)
                el.fill("", timeout=3000)
                el.fill(value, timeout=5000)
            elif strategy == "triple_click+fill":
                el.triple_click(timeout=3000)
                el.fill(value, timeout=5000)
            else:
                el.click(timeout=3000)
                el.type(value, delay=50)
            print(f"  [fill:{strategy}] {label or selector[:50]} = {value[:50]}")
            return True
        except:
            continue
    print(f"  [fill FAIL] {label or selector[:50]}")
    return False


def click_btn(page, selectors, label="", timeout=8000):
    """Click a button by trying multiple selectors."""
    if isinstance(selectors, str):
        selectors = [selectors]
    for sel in selectors:
        try:
            el = page.locator(sel).first
            if el.count() > 0:
                el.wait_for(state="visible", timeout=timeout)
                el.click(timeout=timeout)
                print(f"  [click] {label or sel[:60]}")
                return True
        except:
            continue
    print(f"  [click FAIL] {label}")
    return False


def detect_captcha(page):
    for sel in ["iframe[src*='recaptcha']", "iframe[src*='hcaptcha']",
                ".g-recaptcha", "[data-sitekey]", ".cf-turnstile",
                "iframe[title*='CAPTCHA' i]"]:
        try:
            if page.locator(sel).count() > 0:
                return True
        except:
            pass
    try:
        txt = page.inner_text("body")[:3000].lower()
        return any(w in txt for w in ["captcha", "i'm not a robot", "human verification"])
    except:
        return False


def detect_email_verify(page):
    try:
        txt = page.inner_text("body")[:3000].lower()
        return any(k in txt for k in [
            "verify your email", "verification email", "check your email",
            "confirm your email", "activate your account",
            "we sent", "sent you an email", "email verification"
        ])
    except:
        return False


def get_text(page):
    try:
        return page.inner_text("body")
    except:
        return ""


def save_result(result):
    path = os.path.join(ROLE_DIR, "SUBMITTED.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"\n[SAVED] {path}")
    print("=" * 60)
    print(f"RESULT: {result['status']}")
    print(f"Notes:  {str(result.get('notes', ''))[:300]}")
    print("=" * 60)


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    result = {
        "company": "BCG (Boston Consulting Group)",
        "role": "Talent Senior Specialist - People",
        "ats": "Phenom (experiencedtalent.bcg.com)",
        "status": "in_progress",
        "confirmed_at": None,
        "screenshot": None,
        "account_email": EMAIL,
        "notes": "",
        "job_url": JOB_URL,
        "apply_url": PHENOM_APPLY_URL
    }

    print("=" * 60)
    print("BCG Phenom Submission -- Talent Senior Specialist")
    print("ATS: Phenom (experiencedtalent.bcg.com)")
    print("=" * 60)

    # Kill stale Chrome on this port
    subprocess.run(
        ["powershell", "-Command",
         f"Get-NetTCPConnection -LocalPort {PORT} -ErrorAction SilentlyContinue | "
         f"Select-Object -ExpandProperty OwningProcess | "
         f"ForEach-Object {{ Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }}"],
        capture_output=True, timeout=10
    )
    time.sleep(2)

    print(f"\n[1] Launching Chrome port {PORT}...")
    proc = subprocess.Popen(
        [CHROME, f"--remote-debugging-port={PORT}", f"--user-data-dir={PROFILE}",
         "--no-first-run", "--no-default-browser-check",
         "--disable-blink-features=AutomationControlled",
         PHENOM_APPLY_URL],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    print(f"  PID: {proc.pid}, waiting 10s...")
    time.sleep(10)

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(f"http://localhost:{PORT}")
        ctx = browser.contexts[0]
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.set_default_timeout(30000)

        try:
            wait_net(page, 20000)
            time.sleep(3)
            print(f"  URL: {page.url}")
            dismiss_cookie(page)
            time.sleep(1)
            shot(page, "p_01_phenom_login")
            page_text = get_text(page)
            print(f"  Page: {page_text[:400]}")

            # ── STEP 2: Account creation / login ──────────────────────────────
            print("\n[2] Phenom account creation / login...")

            # Check for captcha immediately
            if detect_captcha(page):
                result["status"] = "captcha-staged"
                result["notes"] = "CAPTCHA on Phenom login page before any form fill."
                shot(page, "p_99_captcha_login")
                browser.close()
                save_result(result)
                return result

            # Are we on the login page?
            is_login = any(w in page_text.lower() for w in
                           ["sign in", "sign up", "create an account", "email", "login"])

            if is_login:
                # Try to find "Create an account" / "Sign Up" link
                create_clicked = False
                for sel in [
                    "a:has-text('Create an account')",
                    "a:has-text('Create Account')",
                    "a:has-text('Sign Up')",
                    "button:has-text('Sign Up')",
                    "[data-testid='signup-link']",
                    "a[href*='signup']",
                    "a[href*='register']",
                ]:
                    try:
                        el = page.locator(sel).first
                        if el.count() > 0 and el.is_visible(timeout=2000):
                            el.click()
                            time.sleep(3)
                            wait_net(page, 10000)
                            create_clicked = True
                            print(f"  [signup] via: {sel}")
                            break
                    except:
                        continue

                if not create_clicked:
                    # Navigate directly to signup URL
                    print("  Navigating to Phenom signup URL...")
                    page.goto(PHENOM_SIGNUP + f"&next={PHENOM_APPLY_URL}", timeout=20000,
                              wait_until="domcontentloaded")
                    time.sleep(4)
                    wait_net(page, 10000)
                    dismiss_cookie(page)

                time.sleep(2)
                shot(page, "p_02_signup_page")
                page_text = get_text(page)
                print(f"  Signup page: {page_text[:500]}")

                if detect_email_verify(page):
                    result["status"] = "email-verify-staged"
                    result["notes"] = "Phenom sent email verification to jamiecheng0103@gmail.com before signup form. Check inbox."
                    shot(page, "p_99_email_verify_early")
                    browser.close()
                    save_result(result)
                    return result

                # ── Fill signup form ──────────────────────────────────────────
                print("  Filling Phenom signup form...")
                time.sleep(2)

                # Phenom signup typically: First Name, Last Name, Email, Password, Confirm Password
                # Try by placeholder / aria-label / type

                # First name
                for sel in ["input[placeholder*='First' i]", "input[name*='first' i]",
                             "input[id*='first' i]", "input[aria-label*='First' i]",
                             "input[autocomplete='given-name']"]:
                    if fill(page, sel, "Yi-Chieh", "first_name"):
                        break

                # Last name
                for sel in ["input[placeholder*='Last' i]", "input[name*='last' i]",
                             "input[id*='last' i]", "input[aria-label*='Last' i]",
                             "input[autocomplete='family-name']"]:
                    if fill(page, sel, "Cheng", "last_name"):
                        break

                # Email
                for sel in ["input[type='email']", "input[placeholder*='Email' i]",
                             "input[name*='email' i]", "input[id*='email' i]",
                             "input[autocomplete='email']"]:
                    if fill(page, sel, EMAIL, "email"):
                        break

                # Password fields
                pw_inputs = page.locator("input[type='password']").all()
                for i, pw_el in enumerate(pw_inputs[:2]):
                    try:
                        pw_el.click(timeout=3000)
                        pw_el.fill(PW, timeout=5000)
                        print(f"  [fill] password[{i}]")
                    except:
                        pass

                shot(page, "p_03_signup_filled")

                if detect_captcha(page):
                    result["status"] = "captcha-staged"
                    result["notes"] = "CAPTCHA on Phenom signup form. Email/name/password filled. Human: solve CAPTCHA then click Create Account."
                    shot(page, "p_99_captcha_signup")
                    browser.close()
                    save_result(result)
                    return result

                # Submit signup
                print("  Submitting signup...")
                for sel in [
                    "button[type='submit']",
                    "button:has-text('Create Account')",
                    "button:has-text('Sign Up')",
                    "button:has-text('Register')",
                    "button:has-text('Continue')",
                    "[data-testid='submit-btn']",
                ]:
                    try:
                        el = page.locator(sel).first
                        if el.count() > 0 and el.is_visible(timeout=3000):
                            el.click()
                            time.sleep(5)
                            wait_net(page, 15000)
                            print(f"  [signup submit] {sel}")
                            break
                    except:
                        continue

                time.sleep(5)
                shot(page, "p_04_after_signup")
                page_text = get_text(page)
                print(f"  Post-signup URL: {page.url}")
                print(f"  Post-signup text: {page_text[:500]}")

                if detect_email_verify(page):
                    result["status"] = "email-verify-staged"
                    result["notes"] = (
                        "Phenom (BCG careerhub) requires email verification. "
                        "Email sent to jamiecheng0103@gmail.com. "
                        f"Debug port {PORT} / profile {PROFILE}. "
                        "Human: click email link, then application will continue."
                    )
                    shot(page, "p_99_email_verify")
                    browser.close()
                    save_result(result)
                    return result

                if detect_captcha(page):
                    result["status"] = "captcha-staged"
                    result["notes"] = "CAPTCHA after Phenom signup. Human: solve and continue."
                    shot(page, "p_99_captcha_post_signup")
                    browser.close()
                    save_result(result)
                    return result

            # ── STEP 3: Navigate into the application ─────────────────────────
            print("\n[3] Navigating to application flow...")
            time.sleep(2)

            # Check current URL — are we in careerhub/apply yet?
            current_url = page.url
            if "apply" not in current_url.lower() and "application" not in current_url.lower():
                print(f"  Not yet in apply flow. Going to: {PHENOM_APPLY_URL}")
                page.goto(PHENOM_APPLY_URL, timeout=30000, wait_until="domcontentloaded")
                time.sleep(5)
                wait_net(page, 15000)
                dismiss_cookie(page)
                time.sleep(2)

            shot(page, "p_05_apply_flow")
            page_text = get_text(page)
            print(f"  URL: {page.url}")
            print(f"  Text: {page_text[:500]}")

            # ── STEP 4: Walk the application wizard ────────────────────────────
            print("\n[4] Application wizard walk...")
            max_steps = 20

            for step in range(max_steps):
                time.sleep(3)
                page_text = get_text(page)
                current_url = page.url
                shot(page, f"p_wizard_{step:02d}")
                print(f"\n  [Step {step}] URL: {current_url[:80]}")
                print(f"  Text: {page_text[:300]}")

                if detect_captcha(page):
                    result["status"] = "captcha-staged"
                    result["notes"] = f"CAPTCHA at Phenom wizard step {step}. Form filled to this point."
                    shot(page, f"p_99_captcha_{step}")
                    browser.close()
                    save_result(result)
                    return result

                if detect_email_verify(page):
                    result["status"] = "email-verify-staged"
                    result["notes"] = f"Email verify at step {step}. Check jamiecheng0103@gmail.com."
                    browser.close()
                    save_result(result)
                    return result

                # === CONFIRMATION? ===
                if any(k in page_text.lower() for k in [
                    "thank you", "application submitted", "successfully submitted",
                    "application has been received", "we have received",
                    "application complete", "your application", "application number",
                    "application id"
                ]):
                    print(f"  CONFIRMED SUBMISSION!")
                    result["status"] = "submitted"
                    result["confirmed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                    result["screenshot"] = os.path.join(SHOT, f"p_wizard_{step:02d}.png")
                    result["notes"] = f"Submitted! Confirmation: {page_text[:400]}"
                    browser.close()
                    save_result(result)
                    return result

                # === SUBMIT BUTTON? ===
                submit_el = None
                for sel in [
                    "button:has-text('Submit Application')",
                    "button:has-text('Submit')",
                    "button[type='submit']:has-text('Submit')",
                    "[data-testid='submit-application']",
                    "button[aria-label*='Submit' i]",
                ]:
                    try:
                        el = page.locator(sel).first
                        if el.count() > 0 and el.is_visible(timeout=2000):
                            txt = el.inner_text().strip().lower()
                            # Make sure it's the application submit, not "subscribe"
                            if "subscribe" not in txt and "notify" not in txt and "similar" not in txt:
                                submit_el = sel
                                break
                    except:
                        continue

                if submit_el:
                    shot(page, f"p_pre_submit_{step:02d}")
                    print(f"  SUBMIT button: {submit_el}")
                    el = page.locator(submit_el).first
                    el.click()
                    time.sleep(8)
                    wait_net(page, 20000)
                    page_text = get_text(page)
                    shot(page, "p_post_submit")
                    print(f"  Post-submit URL: {page.url}")
                    print(f"  Post-submit text: {page_text[:500]}")

                    if any(k in page_text.lower() for k in [
                        "thank you", "submitted", "received", "confirmation", "complete"
                    ]):
                        result["status"] = "submitted"
                        result["confirmed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                        result["screenshot"] = os.path.join(SHOT, "p_post_submit.png")
                        result["notes"] = f"Submitted. Post-submit: {page_text[:400]}"
                    else:
                        result["status"] = "likely-submitted"
                        result["confirmed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                        result["screenshot"] = os.path.join(SHOT, "p_post_submit.png")
                        result["notes"] = f"Submit clicked, unclear confirmation. URL: {page.url}. Text: {page_text[:300]}"
                    browser.close()
                    save_result(result)
                    return result

                # === FILL CURRENT PAGE FIELDS ===
                # Personal info
                page_text_lower = page_text.lower()

                if any(w in page_text_lower for w in ["first name", "last name", "contact"]):
                    print("  Filling personal info...")
                    for sel, val, lbl in [
                        ("input[placeholder*='First' i]", "Yi-Chieh", "first"),
                        ("input[placeholder*='Last' i]", "Cheng", "last"),
                        ("input[autocomplete='given-name']", "Yi-Chieh", "first"),
                        ("input[autocomplete='family-name']", "Cheng", "last"),
                    ]:
                        try:
                            el = page.locator(sel).first
                            if el.count() > 0 and el.is_visible(timeout=2000):
                                cur = el.input_value()
                                if not cur:
                                    fill(page, sel, val, lbl)
                        except:
                            pass

                    for sel in ["input[type='email']", "input[placeholder*='Email' i]",
                                 "input[name*='email' i]"]:
                        try:
                            el = page.locator(sel).first
                            if el.count() > 0:
                                cur = el.input_value()
                                if not cur:
                                    fill(page, sel, EMAIL, "email")
                                break
                        except:
                            pass

                    for sel in ["input[type='tel']", "input[placeholder*='Phone' i]",
                                 "input[name*='phone' i]", "input[aria-label*='Phone' i]"]:
                        if fill(page, sel, "(213) 700-3831", "phone"):
                            break

                # Address
                if any(w in page_text_lower for w in ["address", "city", "postal", "zip"]):
                    print("  Filling address...")
                    for sel, val, lbl in [
                        ("input[placeholder*='Address' i]", "1784 NW Northrup Street", "address"),
                        ("input[name*='address' i]", "1784 NW Northrup Street", "address"),
                        ("input[placeholder*='City' i]", "Portland", "city"),
                        ("input[name*='city' i]", "Portland", "city"),
                        ("input[placeholder*='Zip' i]", "97209", "zip"),
                        ("input[placeholder*='Postal' i]", "97209", "zip"),
                        ("input[name*='zip' i]", "97209", "zip"),
                    ]:
                        try:
                            el = page.locator(sel).first
                            if el.count() > 0 and el.is_visible(timeout=2000):
                                fill(page, sel, val, lbl)
                        except:
                            pass
                    # State dropdown
                    for sel in ["select[name*='state' i]", "select[aria-label*='state' i]",
                                 "select[placeholder*='State' i]"]:
                        try:
                            page.select_option(sel, label="Oregon", timeout=3000)
                            print(f"  [select] state=Oregon")
                            break
                        except:
                            pass

                # Resume upload
                if any(w in page_text_lower for w in ["resume", "upload", "cv", "attach"]):
                    print("  Resume upload...")
                    uploaded = False
                    for sel in ["input[type='file'][accept*='pdf' i]",
                                 "input[type='file']"]:
                        try:
                            inputs = page.locator(sel).all()
                            if inputs:
                                inputs[0].set_input_files(RESUME)
                                time.sleep(4)
                                uploaded = True
                                print(f"  [upload] resume via {sel}")
                                # Dismiss autofill if shown
                                for no_lbl in ["No, thanks", "Skip", "Manual Entry", "No Thanks"]:
                                    try:
                                        el = page.get_by_text(no_lbl, exact=False).first
                                        if el.count() > 0 and el.is_visible(timeout=2000):
                                            el.click()
                                            time.sleep(2)
                                            break
                                    except:
                                        pass
                                break
                        except:
                            pass

                    if not uploaded:
                        for sel in ["button:has-text('Upload')", "label:has-text('Upload')",
                                     "[data-testid*='upload' i]"]:
                            try:
                                with page.expect_file_chooser(timeout=5000) as fc_info:
                                    page.locator(sel).first.click(timeout=4000)
                                fc_info.value.set_files(RESUME)
                                time.sleep(4)
                                uploaded = True
                                print(f"  [upload-chooser] via {sel}")
                                break
                            except:
                                pass
                    shot(page, f"p_wizard_{step:02d}_resume")

                # Work authorization / sponsorship
                if any(w in page_text_lower for w in ["authorized", "work authorization",
                                                        "sponsorship", "visa", "eligible"]):
                    print("  Work authorization questions...")
                    # Phenom typically uses radio buttons or select dropdowns

                    # "Are you authorized to work in the US?" -> Yes
                    for sel in ["select[id*='authorized' i]", "select[name*='authorized' i]",
                                 "select[aria-label*='authorized' i]"]:
                        try:
                            page.select_option(sel, label="Yes", timeout=3000)
                            print(f"  [workauth] authorized=Yes via {sel}")
                            break
                        except:
                            pass

                    # Radio: authorized -> Yes
                    page.evaluate("""
                    (function() {
                        var radios = Array.from(document.querySelectorAll('input[type="radio"]'));
                        for (var r of radios) {
                            var lbl = r.closest('label') || document.querySelector('label[for="'+r.id+'"]');
                            if (!lbl) continue;
                            var txt = lbl.textContent.trim().toLowerCase();
                            var container = r.closest('[class*="field"], [class*="question"], fieldset, div');
                            var containerTxt = (container ? container.textContent : '').toLowerCase();
                            if (txt === 'yes' && (containerTxt.includes('authorized') || containerTxt.includes('eligible'))) {
                                r.click();
                            }
                        }
                    })()
                    """)

                    # "Will you require sponsorship?" -> Yes
                    for sel in ["select[id*='sponsor' i]", "select[name*='sponsor' i]",
                                 "select[aria-label*='sponsor' i]"]:
                        try:
                            page.select_option(sel, label="Yes", timeout=3000)
                            print(f"  [workauth] sponsor=Yes via {sel}")
                            break
                        except:
                            pass

                    page.evaluate("""
                    (function() {
                        var radios = Array.from(document.querySelectorAll('input[type="radio"]'));
                        for (var r of radios) {
                            var lbl = r.closest('label') || document.querySelector('label[for="'+r.id+'"]');
                            if (!lbl) continue;
                            var txt = lbl.textContent.trim().toLowerCase();
                            var container = r.closest('[class*="field"], [class*="question"], fieldset, div');
                            var containerTxt = (container ? container.textContent : '').toLowerCase();
                            if (txt === 'yes' && containerTxt.includes('sponsor')) {
                                r.click();
                            }
                        }
                    })()
                    """)
                    print("  Work auth JS radios applied")

                # Application questions
                if any(w in page_text_lower for w in ["hear about", "source", "referral",
                                                        "salary", "years of experience"]):
                    print("  Application questions...")

                    # How did you hear about us
                    for sel in ["select[id*='source' i]", "select[name*='source' i]",
                                 "select[id*='hear' i]", "select[aria-label*='hear' i]"]:
                        try:
                            for val in ["LinkedIn", "Social Media", "Job Board", "Online"]:
                                try:
                                    page.select_option(sel, label=val, timeout=2000)
                                    print(f"  [select] how_hear={val}")
                                    break
                                except:
                                    continue
                            break
                        except:
                            pass

                    # Salary
                    for sel in ["input[id*='salary' i]", "input[name*='salary' i]",
                                 "input[aria-label*='salary' i]"]:
                        if fill(page, sel, "115000", "salary"):
                            break

                # Demographics (voluntary)
                if any(w in page_text_lower for w in ["gender", "ethnicity", "race",
                                                        "veteran", "disability", "voluntary"]):
                    print("  Demographics (voluntary)...")

                    for sel in ["select[id*='gender' i]", "select[name*='gender' i]",
                                 "select[aria-label*='gender' i]"]:
                        for val in ["Female", "Woman", "F"]:
                            try:
                                page.select_option(sel, label=val, timeout=2000)
                                print(f"  [demog] gender={val}")
                                break
                            except:
                                continue

                    for sel in ["select[id*='ethnicity' i]", "select[name*='race' i]",
                                 "select[aria-label*='race' i]", "select[aria-label*='ethnicity' i]"]:
                        for val in ["Asian", "Asian (Not Hispanic or Latino)"]:
                            try:
                                page.select_option(sel, label=val, timeout=2000)
                                print(f"  [demog] race={val}")
                                break
                            except:
                                continue

                    for sel in ["select[id*='veteran' i]", "select[name*='veteran' i]"]:
                        for val in ["I am not a protected veteran", "Not a protected veteran", "No"]:
                            try:
                                page.select_option(sel, label=val, timeout=2000)
                                break
                            except:
                                continue

                    for sel in ["select[id*='disability' i]", "select[name*='disability' i]"]:
                        for val in ["No, I Don't Have a Disability", "No disability", "No"]:
                            try:
                                page.select_option(sel, label=val, timeout=2000)
                                break
                            except:
                                continue

                # === ADVANCE: Click Next / Continue / Save ===
                advanced = False
                for sel in [
                    "button:has-text('Next')",
                    "button:has-text('Continue')",
                    "button:has-text('Save and Continue')",
                    "button:has-text('Save & Continue')",
                    "button[type='submit']",
                    "[data-testid='next-btn']",
                    "[data-testid='continue-btn']",
                    "button[aria-label*='Next' i]",
                ]:
                    try:
                        el = page.locator(sel).first
                        if el.count() > 0 and el.is_visible(timeout=2000):
                            txt = el.inner_text().strip().lower()
                            # Skip subscribe/notify buttons
                            if any(bad in txt for bad in ["subscribe", "notify", "similar"]):
                                continue
                            el.click()
                            time.sleep(3)
                            wait_net(page, 10000)
                            advanced = True
                            print(f"  [advance] {sel}")
                            break
                    except:
                        continue

                if not advanced:
                    print(f"  No advance button found at step {step}")
                    if step >= 3:
                        # Check if we're stuck on the same page
                        new_text = get_text(page)
                        if new_text == page_text and step >= 5:
                            print("  Stuck on same page, stopping")
                            break

            # Wizard ended without submission
            result["status"] = "blocked"
            result["notes"] = (
                "Phenom wizard exhausted without reaching Submit. "
                f"Last URL: {page.url}. "
                "Possible email verification step or wizard mismatch."
            )
            shot(page, "p_99_wizard_exhausted")
            browser.close()
            save_result(result)
            return result

        except Exception as e:
            tb = traceback.format_exc()
            print(f"\n[EXCEPTION] {e}\n{tb[:600]}")
            result["status"] = "error"
            result["notes"] = f"Exception: {str(e)}\n{tb[:400]}"
            try:
                shot(page, "p_99_exception")
            except:
                pass
            try:
                browser.close()
            except:
                pass
            save_result(result)
            return result


if __name__ == "__main__":
    main()
