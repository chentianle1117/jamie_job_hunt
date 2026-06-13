# -*- coding: utf-8 -*-
"""
submit_bcg_phenom_v2.py
BCG Phenom ATS -- corrected account creation flow.

Key learnings from v1:
- "Sign Up" nav link opens a NEW TAB -> page context crash. DON'T click it.
- Correct path: enter email in the Email field on the login page, click Continue
  -> Phenom detects new vs existing account and routes accordingly
- OR: click "Create an account" small link in the form body (same tab)
- Cookie consent modal: dismiss via "Accept All and Close" button or hide via JS
- After email Continue: Phenom may ask for password (existing) or name/pw (new account)
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

PHENOM_APPLY_URL = (
    "https://experiencedtalent.bcg.com/careerhub/explore/jobs/790315808241"
    "?post_onboarding_pid=790315808241&show_apply=1&profile_type=candidate&customredirect=1"
)

# ── Helpers ─────────────────────────────────────────────────────────────────────

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


def get_active_page(ctx):
    """Return the most recently active (focused) page in the context."""
    pages = ctx.pages
    if not pages:
        return None
    # Return last page (most recently opened)
    return pages[-1]


def dismiss_cookie(page):
    """Dismiss TrustArc / Phenom cookie banner. Try click first, then JS hide."""
    # Click "Accept All and Close" if visible
    for sel in [
        "button:has-text('Accept All and Close')",
        "button:has-text('Accept All')",
        "#truste-consent-button",
        "[data-testid='cookie-accept']",
        "button[title*='Accept' i]",
    ]:
        try:
            el = page.locator(sel).first
            if el.count() > 0 and el.is_visible(timeout=2000):
                el.click()
                time.sleep(1.5)
                print(f"  [cookie] clicked: {sel}")
                return
        except:
            continue

    # JS hide fallback
    try:
        result = page.evaluate("""
        (function() {
            var hidden = 0;
            document.querySelectorAll(
                '[id*="truste"],[class*="truste_overlay"],[class*="truste_box"],' +
                '#truste-consent-track, .truste_popframe, [class*="trustarc"]'
            ).forEach(function(el) {
                el.style.cssText = 'display:none!important;';
                hidden++;
            });
            return 'hidden:' + hidden;
        })()
        """)
        print(f"  [cookie] {result}")
    except:
        pass


def fill(page, selector, value, label="", timeout=8000):
    try:
        el = page.locator(selector).first
        el.wait_for(state="visible", timeout=timeout)
        el.click(timeout=3000)
        el.fill("", timeout=3000)
        el.fill(value, timeout=5000)
        print(f"  [fill] {label or selector[:50]} = {value[:50]}")
        return True
    except Exception as e:
        # triple-click fallback
        try:
            el = page.locator(selector).first
            el.triple_click(timeout=3000)
            el.type(value, delay=60)
            print(f"  [fill-type] {label or selector[:50]} = {value[:50]}")
            return True
        except:
            print(f"  [fill FAIL] {label or selector[:50]}: {str(e)[:50]}")
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
            "we sent", "sent you an email", "email verification",
            "verification link"
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
    print(f"Notes:  {str(result.get('notes', ''))[:400]}")
    print("=" * 60)


# ── Main ─────────────────────────────────────────────────────────────────────────

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
        "job_url": "https://careers.bcg.com/global/en/job/57988/Talent-Senior-Specialist-People",
        "apply_url": PHENOM_APPLY_URL,
        "job_id": "790315808241"
    }

    print("=" * 60)
    print("BCG Phenom v2 -- Talent Senior Specialist")
    print("=" * 60)

    # Kill stale Chrome on port
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
    print(f"  PID: {proc.pid}, waiting 12s...")
    time.sleep(12)

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
            shot(page, "pv2_01_login_page")
            page_text = get_text(page)
            print(f"  Page: {page_text[:400]}")

            if detect_captcha(page):
                result["status"] = "captcha-staged"
                result["notes"] = "CAPTCHA on Phenom login page."
                shot(page, "pv2_99_captcha_login")
                browser.close()
                save_result(result)
                return result

            # ── STEP 2: Account entry ─────────────────────────────────────────
            print("\n[2] Entering email to begin account flow...")

            # The login page has: Email input, Continue button, "Create an account" link
            # Strategy: enter email in the email field, click Continue
            # Phenom will detect new account and ask for name/password

            email_filled = False
            for sel in [
                "input[type='email']",
                "input[placeholder*='Email' i]",
                "input[name*='email' i]",
                "input[id*='email' i]",
                "input[autocomplete='email']",
                "input[aria-label*='Email' i]",
            ]:
                if fill(page, sel, EMAIL, "email"):
                    email_filled = True
                    break

            if not email_filled:
                print("  Could not find email field. Trying 'Create an account' link...")
                # Click "Create an account" in the body
                for sel in [
                    "a:has-text('Create an account')",
                    "a:has-text('Create Account')",
                    "[data-testid='create-account-link']",
                ]:
                    try:
                        el = page.locator(sel).first
                        if el.count() > 0 and el.is_visible(timeout=3000):
                            # Check it doesn't open new tab
                            target = el.get_attribute("target")
                            if target == "_blank":
                                # Navigate directly instead
                                href = el.get_attribute("href")
                                if href:
                                    print(f"  New-tab link, navigating directly: {href}")
                                    page.goto(href if href.startswith("http") else
                                              "https://experiencedtalent.bcg.com" + href,
                                              timeout=20000, wait_until="domcontentloaded")
                                    time.sleep(4)
                                    dismiss_cookie(page)
                            else:
                                el.click()
                                time.sleep(3)
                                wait_net(page, 10000)
                                print(f"  Create account clicked: {sel}")
                            break
                    except:
                        continue

                time.sleep(2)
                shot(page, "pv2_02_create_account")
                page_text = get_text(page)
                print(f"  After create-account: {page_text[:400]}")

            else:
                # Email was filled; click Continue
                time.sleep(1)
                shot(page, "pv2_02_email_filled")

                continued = False
                for sel in [
                    "button:has-text('Continue')",
                    "button[type='submit']",
                    "input[type='submit']",
                    "button[aria-label*='Continue' i]",
                ]:
                    try:
                        el = page.locator(sel).first
                        if el.count() > 0 and el.is_visible(timeout=3000):
                            el.click()
                            time.sleep(5)
                            wait_net(page, 15000)
                            continued = True
                            print(f"  Continue clicked: {sel}")
                            break
                    except:
                        continue

                time.sleep(3)
                shot(page, "pv2_03_after_continue")
                page_text = get_text(page)
                print(f"  After Continue URL: {page.url}")
                print(f"  After Continue text: {page_text[:500]}")

                if detect_email_verify(page):
                    result["status"] = "email-verify-staged"
                    result["notes"] = (
                        "Phenom (BCG) sent email verification to jamiecheng0103@gmail.com. "
                        "This is a HARD GATE -- must click the email link first. "
                        f"Chrome on port {PORT}. After verifying, run this script again."
                    )
                    shot(page, "pv2_99_email_verify")
                    browser.close()
                    save_result(result)
                    return result

                if detect_captcha(page):
                    result["status"] = "captcha-staged"
                    result["notes"] = "CAPTCHA after email entry. Human: solve and continue."
                    shot(page, "pv2_99_captcha_email")
                    browser.close()
                    save_result(result)
                    return result

                # Now handle the next step depending on what Phenom shows:
                # A) New account: shows name + password fields
                # B) Existing account: shows password field only
                # C) Email consent/marketing opt-in: shows consent checkboxes

                page_text_lower = page_text.lower()

                # Handle consent page (BCG-specific "I consent to receive electronic communication")
                if "consent" in page_text_lower or "electronic communication" in page_text_lower:
                    print("  Consent/marketing preferences page detected...")
                    # Tick the consent checkbox (optional - not required for application)
                    # Then click Submit/Continue
                    for sel in [
                        "button:has-text('Submit')",
                        "button:has-text('Continue')",
                        "button:has-text('Skip')",
                        "button[type='submit']",
                    ]:
                        try:
                            el = page.locator(sel).first
                            if el.count() > 0 and el.is_visible(timeout=3000):
                                txt = el.inner_text().strip().lower()
                                # Don't confuse with "submit similar jobs" subscribe
                                if "subscribe" not in txt and "notify" not in txt:
                                    el.click()
                                    time.sleep(4)
                                    wait_net(page, 10000)
                                    print(f"  Consent page: clicked {sel}")
                                    break
                        except:
                            continue

                    time.sleep(3)
                    shot(page, "pv2_04_after_consent")
                    page_text = get_text(page)
                    print(f"  After consent URL: {page.url}")
                    print(f"  After consent text: {page_text[:500]}")

                    if detect_email_verify(page):
                        result["status"] = "email-verify-staged"
                        result["notes"] = (
                            "Email verification required after BCG Phenom consent step. "
                            "Check jamiecheng0103@gmail.com for a verification link. "
                            f"Chrome port {PORT} still live. After clicking link, re-run script."
                        )
                        shot(page, "pv2_99_email_verify_consent")
                        browser.close()
                        save_result(result)
                        return result

                # Handle sign-up form with name/password
                page_text_lower = get_text(page).lower()
                if any(w in page_text_lower for w in ["first name", "last name", "password", "create password"]):
                    print("  New account form (name + password)...")

                    for sel, val, lbl in [
                        ("input[placeholder*='First' i]", "Yi-Chieh", "first_name"),
                        ("input[name*='first' i]", "Yi-Chieh", "first_name"),
                        ("input[id*='first' i]", "Yi-Chieh", "first_name"),
                        ("input[autocomplete='given-name']", "Yi-Chieh", "first_name"),
                    ]:
                        if fill(page, sel, val, lbl):
                            break

                    for sel, val, lbl in [
                        ("input[placeholder*='Last' i]", "Cheng", "last_name"),
                        ("input[name*='last' i]", "Cheng", "last_name"),
                        ("input[id*='last' i]", "Cheng", "last_name"),
                        ("input[autocomplete='family-name']", "Cheng", "last_name"),
                    ]:
                        if fill(page, sel, val, lbl):
                            break

                    # Password fields
                    pw_inputs = page.locator("input[type='password']").all()
                    for i, pw_el in enumerate(pw_inputs[:2]):
                        try:
                            pw_el.wait_for(state="visible", timeout=3000)
                            pw_el.click(timeout=3000)
                            pw_el.fill(PW, timeout=5000)
                            print(f"  [fill] password[{i}]")
                        except Exception as e:
                            print(f"  [fill FAIL] password[{i}]: {e}")

                    shot(page, "pv2_05_signup_form_filled")

                    if detect_captcha(page):
                        result["status"] = "captcha-staged"
                        result["notes"] = "CAPTCHA on signup form. Name/email/password filled. Human: solve CAPTCHA and submit."
                        shot(page, "pv2_99_captcha_signup")
                        browser.close()
                        save_result(result)
                        return result

                    # Submit the signup form
                    for sel in [
                        "button[type='submit']",
                        "button:has-text('Create Account')",
                        "button:has-text('Sign Up')",
                        "button:has-text('Register')",
                        "button:has-text('Continue')",
                    ]:
                        try:
                            el = page.locator(sel).first
                            if el.count() > 0 and el.is_visible(timeout=3000):
                                el.click()
                                time.sleep(5)
                                wait_net(page, 15000)
                                print(f"  Signup submitted: {sel}")
                                break
                        except:
                            continue

                    time.sleep(5)
                    shot(page, "pv2_06_after_signup_submit")
                    page_text = get_text(page)
                    print(f"  Post-signup URL: {page.url}")
                    print(f"  Post-signup text: {page_text[:400]}")

                    if detect_email_verify(page):
                        result["status"] = "email-verify-staged"
                        result["notes"] = (
                            "BCG Phenom requires email verification after account creation. "
                            "Email sent to jamiecheng0103@gmail.com. "
                            f"Chrome port {PORT} / profile {PROFILE}. "
                            "Human: click the verification link in the email, "
                            "then the account will be active and you can complete the application."
                        )
                        shot(page, "pv2_99_email_verify_post_signup")
                        browser.close()
                        save_result(result)
                        return result

                elif "password" in page_text_lower and "first name" not in page_text_lower:
                    # Existing account - just password
                    print("  Existing account login (password only)...")
                    pw_inputs = page.locator("input[type='password']").all()
                    if pw_inputs:
                        try:
                            pw_inputs[0].fill(PW)
                            print("  [fill] existing-account password")
                        except Exception as e:
                            print(f"  [fill FAIL] existing password: {e}")

                    for sel in ["button[type='submit']", "button:has-text('Sign In')",
                                 "button:has-text('Log In')", "button:has-text('Continue')"]:
                        try:
                            el = page.locator(sel).first
                            if el.count() > 0 and el.is_visible(timeout=3000):
                                el.click()
                                time.sleep(5)
                                wait_net(page, 15000)
                                print(f"  Signed in via: {sel}")
                                break
                        except:
                            continue

                    time.sleep(3)
                    shot(page, "pv2_06_after_login")
                    page_text = get_text(page)
                    print(f"  Post-login URL: {page.url}")

            # ── STEP 3: Navigate to the application form ──────────────────────
            print("\n[3] Navigating to application form...")
            time.sleep(3)
            current_url = page.url
            page_text = get_text(page)

            # If not yet in the apply flow, navigate there
            if "apply" not in current_url.lower() and "application" not in current_url.lower():
                if "careerhub" not in current_url.lower():
                    print(f"  Not in careerhub yet ({current_url[:60]}), navigating...")
                    page.goto(PHENOM_APPLY_URL, timeout=30000, wait_until="domcontentloaded")
                    time.sleep(5)
                    wait_net(page, 15000)
                    dismiss_cookie(page)
                    time.sleep(3)
                    shot(page, "pv2_07_careerhub_nav")
                    page_text = get_text(page)
                    print(f"  Careerhub URL: {page.url}")
                    print(f"  Careerhub text: {page_text[:400]}")

                # Look for an Apply Now button on the job page
                for sel in [
                    "button:has-text('Apply Now')",
                    "button:has-text('Apply')",
                    "a:has-text('Apply Now')",
                    "[data-testid='apply-button']",
                    "button[aria-label*='Apply' i]",
                ]:
                    try:
                        el = page.locator(sel).first
                        if el.count() > 0 and el.is_visible(timeout=3000):
                            txt = el.inner_text().strip().lower()
                            if "subscribe" not in txt and "similar" not in txt:
                                el.click()
                                time.sleep(5)
                                wait_net(page, 15000)
                                print(f"  Apply clicked: {sel}")
                                break
                    except:
                        continue

                time.sleep(3)
                shot(page, "pv2_08_apply_navigated")
                page_text = get_text(page)
                print(f"  Post-Apply URL: {page.url}")
                print(f"  Post-Apply text: {page_text[:400]}")

            # ── STEP 4: Walk the application wizard ────────────────────────────
            print("\n[4] Application wizard...")
            max_steps = 25

            for step in range(max_steps):
                time.sleep(3)
                page_text = get_text(page)
                current_url = page.url
                shot(page, f"pv2_wizard_{step:02d}")
                print(f"\n  [Step {step}] URL: {current_url[:80]}")
                print(f"  Text: {page_text[:300]}")

                # Check gates
                if detect_captcha(page):
                    result["status"] = "captcha-staged"
                    result["notes"] = f"CAPTCHA at wizard step {step}. Form filled to this point."
                    shot(page, f"pv2_99_captcha_{step}")
                    browser.close()
                    save_result(result)
                    return result

                if detect_email_verify(page):
                    result["status"] = "email-verify-staged"
                    result["notes"] = f"Email verify at step {step}. Check jamiecheng0103@gmail.com."
                    browser.close()
                    save_result(result)
                    return result

                page_text_lower = page_text.lower()

                # === CONFIRMATION ===
                if any(k in page_text_lower for k in [
                    "thank you", "application submitted", "successfully submitted",
                    "application has been received", "we have received", "application complete",
                    "your application", "application number", "application id",
                    "you have applied", "you've applied"
                ]):
                    print("  CONFIRMED SUBMISSION!")
                    result["status"] = "submitted"
                    result["confirmed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                    result["screenshot"] = os.path.join(SHOT, f"pv2_wizard_{step:02d}.png")
                    result["notes"] = f"Submitted! Confirmation text: {page_text[:400]}"
                    browser.close()
                    save_result(result)
                    return result

                # === SUBMIT BUTTON ===
                submit_sel = None
                for sel in [
                    "button:has-text('Submit Application')",
                    "button:has-text('Submit')",
                    "button[data-testid='submit-application']",
                    "button[aria-label='Submit Application' i]",
                ]:
                    try:
                        el = page.locator(sel).first
                        if el.count() > 0 and el.is_visible(timeout=2000):
                            txt = el.inner_text().strip().lower()
                            if not any(bad in txt for bad in ["subscribe", "notify", "similar", "jobs"]):
                                submit_sel = sel
                                break
                    except:
                        continue

                if submit_sel:
                    print(f"  SUBMIT button found: {submit_sel}")
                    shot(page, f"pv2_pre_submit_{step:02d}")
                    el = page.locator(submit_sel).first
                    el.click()
                    time.sleep(8)
                    wait_net(page, 20000)
                    page_text = get_text(page)
                    shot(page, "pv2_post_submit")
                    print(f"  Post-submit URL: {page.url}")
                    print(f"  Post-submit text: {page_text[:500]}")

                    if any(k in page_text.lower() for k in [
                        "thank you", "submitted", "received", "confirmation",
                        "complete", "you have applied"
                    ]):
                        result["status"] = "submitted"
                        result["confirmed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                        result["screenshot"] = os.path.join(SHOT, "pv2_post_submit.png")
                        result["notes"] = f"Submitted. Post-submit: {page_text[:400]}"
                    else:
                        result["status"] = "likely-submitted"
                        result["confirmed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                        result["screenshot"] = os.path.join(SHOT, "pv2_post_submit.png")
                        result["notes"] = f"Submit clicked. Post-submit URL: {current_url}. Text: {page_text[:300]}"
                    browser.close()
                    save_result(result)
                    return result

                # === FILL CURRENT PAGE ===

                # Personal info
                if any(w in page_text_lower for w in ["first name", "last name", "contact info"]):
                    print("  Personal info section...")
                    for sel, val, lbl in [
                        ("input[placeholder*='First' i]", "Yi-Chieh", "first"),
                        ("input[name*='first' i]", "Yi-Chieh", "first"),
                        ("input[autocomplete='given-name']", "Yi-Chieh", "first"),
                        ("input[placeholder*='Last' i]", "Cheng", "last"),
                        ("input[name*='last' i]", "Cheng", "last"),
                        ("input[autocomplete='family-name']", "Cheng", "last"),
                    ]:
                        try:
                            el = page.locator(sel).first
                            if el.count() > 0 and el.is_visible(timeout=2000):
                                cur = el.input_value()
                                if not cur.strip():
                                    fill(page, sel, val, lbl)
                        except:
                            pass

                    for sel in ["input[type='tel']", "input[placeholder*='Phone' i]",
                                 "input[name*='phone' i]"]:
                        try:
                            el = page.locator(sel).first
                            if el.count() > 0 and el.is_visible(timeout=2000):
                                if not el.input_value().strip():
                                    fill(page, sel, "(213) 700-3831", "phone")
                                break
                        except:
                            pass

                # Address
                if any(w in page_text_lower for w in ["address", "city", "postal", "zip", "location"]):
                    print("  Address section...")
                    addr_fills = [
                        (["input[placeholder*='Address Line 1' i]",
                          "input[name*='address1' i]",
                          "input[name*='streetAddress' i]"],
                         "1784 NW Northrup Street", "address"),
                        (["input[placeholder*='City' i]", "input[name*='city' i]"], "Portland", "city"),
                        (["input[placeholder*='Zip' i]", "input[placeholder*='Postal' i]",
                          "input[name*='zip' i]"], "97209", "zip"),
                    ]
                    for sels, val, lbl in addr_fills:
                        for sel in sels:
                            if fill(page, sel, val, lbl):
                                break
                    for sel in ["select[name*='state' i]", "select[aria-label*='state' i]"]:
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
                    for sel in ["input[type='file'][accept*='pdf' i]", "input[type='file']"]:
                        try:
                            inputs = page.locator(sel).all()
                            if inputs:
                                inputs[0].set_input_files(RESUME)
                                time.sleep(5)
                                uploaded = True
                                print(f"  [upload] via {sel}")
                                # Dismiss autofill
                                for no_lbl in ["No, thanks", "Skip", "Manual Entry"]:
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
                        for sel in ["button:has-text('Upload')", "label:has-text('Upload')"]:
                            try:
                                with page.expect_file_chooser(timeout=5000) as fc_info:
                                    page.locator(sel).first.click(timeout=4000)
                                fc_info.value.set_files(RESUME)
                                time.sleep(5)
                                uploaded = True
                                break
                            except:
                                pass

                    shot(page, f"pv2_wizard_{step:02d}_resume")

                # Work authorization
                if any(w in page_text_lower for w in ["authorized", "sponsorship", "work authorization"]):
                    print("  Work auth...")
                    page.evaluate("""
                    (function() {
                        var radios = Array.from(document.querySelectorAll('input[type="radio"]'));
                        for (var r of radios) {
                            var lbl = r.closest('label') || document.querySelector('label[for="'+r.id+'"]');
                            if (!lbl) continue;
                            var txt = lbl.textContent.trim().toLowerCase();
                            var container = r.closest('[class*="field"],[class*="question"],fieldset,div');
                            var ctxt = (container ? container.textContent : '').toLowerCase();
                            if (txt === 'yes' && (ctxt.includes('authorized') || ctxt.includes('sponsor'))) {
                                r.click();
                            }
                        }
                    })()
                    """)
                    for sel in ["select[id*='sponsor' i]", "select[name*='authorized' i]"]:
                        try:
                            page.select_option(sel, label="Yes", timeout=2000)
                        except:
                            pass

                # Application questions
                if any(w in page_text_lower for w in ["hear about", "salary", "years"]):
                    print("  App questions...")
                    for sel in ["select[id*='source' i]", "select[name*='source' i]",
                                 "select[id*='hear' i]"]:
                        for val in ["LinkedIn", "Social Media", "Job Board"]:
                            try:
                                page.select_option(sel, label=val, timeout=2000)
                                print(f"  [hear] {val}")
                                break
                            except:
                                continue

                    for sel in ["input[id*='salary' i]", "input[name*='salary' i]"]:
                        if fill(page, sel, "115000", "salary"):
                            break

                # Demographics
                if any(w in page_text_lower for w in ["gender", "ethnicity", "race", "veteran", "disability"]):
                    print("  Demographics...")
                    for sel in ["select[id*='gender' i]", "select[name*='gender' i]"]:
                        for val in ["Female", "Woman"]:
                            try:
                                page.select_option(sel, label=val, timeout=2000)
                                break
                            except:
                                continue

                    for sel in ["select[id*='ethnicity' i]", "select[name*='race' i]"]:
                        for val in ["Asian", "Asian (Not Hispanic or Latino)"]:
                            try:
                                page.select_option(sel, label=val, timeout=2000)
                                break
                            except:
                                continue

                    for sel in ["select[id*='veteran' i]"]:
                        for val in ["I am not a protected veteran", "No"]:
                            try:
                                page.select_option(sel, label=val, timeout=2000)
                                break
                            except:
                                continue

                    for sel in ["select[id*='disability' i]"]:
                        for val in ["No, I Don't Have a Disability", "No"]:
                            try:
                                page.select_option(sel, label=val, timeout=2000)
                                break
                            except:
                                continue

                # === ADVANCE ===
                advanced = False
                for sel in [
                    "button:has-text('Next')",
                    "button:has-text('Continue')",
                    "button:has-text('Save and Continue')",
                    "button:has-text('Save & Continue')",
                    "button[type='submit']",
                    "[data-testid='next-btn']",
                    "button[aria-label*='Next' i]",
                ]:
                    try:
                        el = page.locator(sel).first
                        if el.count() > 0 and el.is_visible(timeout=2000):
                            txt = el.inner_text().strip().lower()
                            if any(bad in txt for bad in ["subscribe", "notify", "similar"]):
                                continue
                            el.click()
                            time.sleep(3)
                            wait_net(page, 10000)
                            advanced = True
                            print(f"  [next] {sel}")
                            break
                    except:
                        continue

                if not advanced:
                    print(f"  No advance button at step {step}. Checking if stuck...")
                    if step >= 3:
                        new_text = get_text(page)
                        if "thank you" in new_text.lower() or "submitted" in new_text.lower():
                            result["status"] = "submitted"
                            result["confirmed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                            result["screenshot"] = os.path.join(SHOT, f"pv2_wizard_{step:02d}.png")
                            result["notes"] = f"Submitted (detected post-advance). Text: {new_text[:400]}"
                            browser.close()
                            save_result(result)
                            return result
                        if step >= 6:
                            break

            # Wizard ended without submission
            result["status"] = "blocked"
            result["notes"] = (
                "Phenom wizard exhausted without finding Submit or Confirmation. "
                f"Last URL: {page.url}. "
                "Likely cause: email verification gate or unexpected page structure."
            )
            shot(page, "pv2_99_wizard_exhausted")
            browser.close()
            save_result(result)
            return result

        except Exception as e:
            tb = traceback.format_exc()
            print(f"\n[EXCEPTION] {e}")
            print(tb[:800])
            result["status"] = "error"
            result["notes"] = f"Exception: {str(e)}\n{tb[:400]}"
            try:
                shot(page, "pv2_99_exception")
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
