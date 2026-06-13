# -*- coding: utf-8 -*-
"""
submit_bcg_v5.py  -- BCG Phenom ATS (v5)

Fixes over v4:
  1. FALSE-POSITIVE guard: "you've applied to a role at BCG before May 28" in the
     welcome banner triggered is_real_confirmation. Fixed: confirmation must be
     followed by a SUBMISSION context (not a login page / "Sign in" text).
  2. LOGIN FAILURE: password Submit button was correctly identified but the page
     didn't change — account may not exist yet or wrong password. Strategy:
       a) Try password login
       b) If page doesn't change after Submit → try "Use a one-time code instead"
          (one-time code = no email verify gate, just a code sent to email)
          → if that also fails, report email-verify-staged
       c) Alternatively: skip login entirely and use the direct PHENOM_APPLY URL
          (Phenom sometimes allows guest apply without account)
  3. POST-LOGIN NAVIGATION: after successful sign-in, explicitly navigate to PHENOM_APPLY
     and wait for the careerhub page to load before starting the wizard.
  4. COOKIE MODAL TIMING: wait for TrustArc iframe to load before clicking.
  5. SESSION PERSISTENCE: use the same page object throughout (no new_page calls).
"""
import os, sys, time, json, subprocess, traceback  # json needed by fill() JS fallback
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, r"C:\Users\chent\Agentic_Workflows_2026\jamie-autopilot\lib")
from patchright.sync_api import sync_playwright
from credential_vault import job_password

PORT     = 9402
PROFILE  = r"C:\Users\chent\ats_agent_9402_v4"   # reuse v4 profile (has cookie consent)
CHROME   = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
ROLE_DIR = (r"C:\Users\chent\Agentic_Workflows_2026\oracle-job-search"
            r"\outputs\2026-06-12-feed-first\applications\bcg_talent_sr_specialist")
SHOT     = ROLE_DIR + r"\screenshots\v5"
RESUME   = ROLE_DIR + r"\resume.pdf"
os.makedirs(SHOT, exist_ok=True)

EMAIL = "jamiecheng0103@gmail.com"
PW    = job_password()

JOB_PUBLIC_URL = "https://careers.bcg.com/global/en/job/57988/Talent-Senior-Specialist-People"
PHENOM_APPLY = (
    "https://experiencedtalent.bcg.com/careerhub/explore/jobs/790315808241"
    "?post_onboarding_pid=790315808241&show_apply=1&profile_type=candidate&customredirect=1"
)
PHENOM_LOGIN = (
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
    try:
        page.wait_for_load_state("networkidle", timeout=t)
    except:
        pass


def txt(page):
    try:
        return page.inner_text("body")
    except:
        return ""


def url(page):
    return page.url


def dismiss_cookie(page):
    """Dismiss BCG/TrustArc/OneTrust cookie modal."""
    for sel in [
        "button:has-text('Accept All and Close')",
        "button:has-text('Accept All')",
        "button:has-text('Accept all')",
        "#truste-consent-button",
        "#onetrust-accept-btn-handler",
        "button[id*='accept' i]",
        ".truste-button1",
    ]:
        try:
            el = page.locator(sel).first
            if el.count() > 0 and el.is_visible(timeout=2000):
                el.click(force=True)
                time.sleep(2)
                print(f"  [cookie] click: {sel}")
                return True
        except:
            continue

    # JS fallback
    try:
        page.evaluate("""() => {
            document.querySelectorAll(
                '[id*="truste"],[class*="truste"],[id*="trustarc"],[class*="trustarc"],' +
                '#onetrust-banner-sdk,.onetrust-pc-dark-filter,.truste_popframe,' +
                '.truste_overlay,.trustarc-banner-overlay,[class*="cookie-banner"],' +
                '[class*="CookieBanner"],[id*="cookie-banner"]'
            ).forEach(e => { e.style.cssText = 'display:none!important;'; });
            document.body.style.overflow = 'auto';

            const d = new Date();
            d.setFullYear(d.getFullYear() + 1);
            const exp = '; expires=' + d.toUTCString() + '; path=/';
            document.cookie = 'notice_behavior=expressed,eu' + exp;
            document.cookie = 'cmapi_cookie_privacy=permit 1,2,3' + exp;
            document.cookie = 'notice_preferences=2:' + exp;
        }""")
        print("  [cookie] JS fallback applied")
    except:
        pass
    return False


def fill(page, sel, val, lbl=""):
    try:
        el = page.locator(sel).first
        el.wait_for(state="visible", timeout=6000)
        el.scroll_into_view_if_needed()
        el.click(timeout=3000)
        el.fill("", timeout=3000)
        el.fill(val, timeout=5000)
        # Verify and fallback to type()
        try:
            actual = el.input_value()
            if actual.strip() != val.strip():
                el.click(timeout=2000)
                el.fill("", timeout=2000)
                el.type(val, delay=40)
        except:
            pass
        print(f"  [fill] {lbl or sel[:60]} = '{val[:50]}'")
        return True
    except Exception as e:
        # Fallback: JS-based value set + dispatch events
        try:
            page.evaluate(
                f"""(sel) => {{
                    let el = document.querySelector(sel);
                    if (el) {{
                        el.focus();
                        el.value = {json.dumps(val)};
                        el.dispatchEvent(new Event('input', {{bubbles:true}}));
                        el.dispatchEvent(new Event('change', {{bubbles:true}}));
                    }}
                }}""",
                sel
            )
            print(f"  [fill-js] {lbl or sel[:60]} = '{val[:50]}'")
            return True
        except:
            pass
        print(f"  [fill!] {lbl or sel[:60]}: {str(e)[:80]}")
        return False


def click_visible(page, selectors, label=""):
    for s in selectors:
        try:
            el = page.locator(s).first
            if el.count() > 0 and el.is_visible(timeout=2000):
                t = el.inner_text().strip().lower()
                if any(bad in t for bad in ["subscribe", "newsletter", "notify", "alert", "similar"]):
                    continue
                el.scroll_into_view_if_needed()
                el.click(timeout=5000)
                print(f"  [click] {label}: {s} = '{t[:40]}'")
                return True
        except:
            continue
    return False


def has_captcha(page):
    for sel in ["iframe[src*='recaptcha']", "iframe[src*='hcaptcha']",
                ".g-recaptcha", "[data-sitekey]", ".cf-turnstile"]:
        try:
            if page.locator(sel).count() > 0:
                return True
        except:
            pass
    try:
        t = txt(page)[:2000].lower()
        return any(w in t for w in ["captcha", "i'm not a robot", "verify you are human"])
    except:
        return False


def has_email_verify(page):
    try:
        t = txt(page)[:2000].lower()
        return any(k in t for k in [
            "verification email sent", "verify your email",
            "we sent an email", "check your inbox",
            "email to confirm", "confirm your email address",
            "click the link in", "activation link",
            "sent a verification", "we've sent a link",
        ])
    except:
        return False


def is_real_confirmation(body_text, page_url=""):
    """
    Strict confirmation check.
    MUST: contain a strong submission phrase
    MUST NOT: be on a login page (contains 'sign in' + 'password')
    """
    t = body_text.lower()

    # Hard exclusion: login/signup page
    if ("sign in" in t or "sign up" in t) and ("password" in t or "email" in t and "continue" in t):
        if "careerhub" not in page_url.lower():
            return False

    strong = [
        "thank you for applying",
        "your application has been submitted",
        "application successfully submitted",
        "we have received your application",
        "application received",
        "application number",
        "application id:",
        "you have successfully applied",
        "successfully applied",
        "your submission has been received",
        "you applied",   # "You applied for..."
    ]
    return any(p in t for p in strong)


def save(result):
    path = os.path.join(ROLE_DIR, "SUBMITTED.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"\n[SAVED] {path}")
    print("=" * 60)
    print(f"RESULT: {result['status']}")
    print(f"Notes:  {str(result.get('notes', ''))[:600]}")
    print("=" * 60)


# ── Wizard filling ────────────────────────────────────────────────────────────

def wizard_fill_page(page, body, step):
    body_lower = body.lower()

    # Scroll to reveal all fields
    try:
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(0.8)
        page.evaluate("window.scrollTo(0, 0)")
        time.sleep(0.3)
    except:
        pass

    # File upload
    if any(w in body_lower for w in ["resume", "upload", "cv", "attach", "document"]):
        for s in ["input[type='file'][accept*='pdf' i]",
                   "input[type='file'][accept*='.pdf' i]",
                   "input[type='file']"]:
            try:
                inputs = page.locator(s).all()
                if inputs:
                    inputs[0].set_input_files(RESUME)
                    time.sleep(4)
                    print(f"  [upload] resume via {s}")
                    for dismiss in ["No, thanks", "Skip", "No thanks", "Enter Manually"]:
                        try:
                            el = page.get_by_text(dismiss, exact=False).first
                            if el.count() > 0 and el.is_visible(timeout=2000):
                                el.click(); time.sleep(2); break
                        except: pass
                    ss(page, f"v5_wiz_{step:02d}_resume")
                    break
            except Exception as e:
                print(f"  [upload!] {s}: {e}")

    # Personal info
    if any(w in body_lower for w in ["first name", "last name", "phone", "contact"]):
        for s, v, l in [
            ("input[placeholder*='First' i]", "Yi-Chieh", "first"),
            ("input[name*='first' i]", "Yi-Chieh", "first"),
            ("input[id*='first' i]", "Yi-Chieh", "first"),
            ("input[autocomplete='given-name']", "Yi-Chieh", "first"),
        ]:
            try:
                el = page.locator(s).first
                if el.count() > 0 and el.is_visible(timeout=1500):
                    if not el.input_value().strip() or el.input_value().strip() == "Yi-Chieh":
                        fill(page, s, v, l); break
            except: pass

        for s, v, l in [
            ("input[placeholder*='Last' i]", "Cheng", "last"),
            ("input[name*='last' i]", "Cheng", "last"),
            ("input[id*='last' i]", "Cheng", "last"),
            ("input[autocomplete='family-name']", "Cheng", "last"),
        ]:
            try:
                el = page.locator(s).first
                if el.count() > 0 and el.is_visible(timeout=1500):
                    if not el.input_value().strip() or el.input_value().strip() == "Cheng":
                        fill(page, s, v, l); break
            except: pass

        for s in ["input[type='tel']", "input[placeholder*='Phone' i]",
                   "input[name*='phone' i]", "input[id*='phone' i]"]:
            try:
                el = page.locator(s).first
                if el.count() > 0 and el.is_visible(timeout=1500):
                    if not el.input_value().strip():
                        fill(page, s, "2137003831", "phone"); break
            except: pass

    # Work auth / sponsorship
    if any(w in body_lower for w in ["authorized", "sponsorship", "work authorization",
                                       "legally authorized"]):
        page.evaluate("""() => {
            Array.from(document.querySelectorAll('input[type="radio"]')).forEach(r => {
                let lbl = r.closest('label') || document.querySelector('label[for="'+r.id+'"]');
                let lt = (lbl ? lbl.textContent : r.value || '').trim().toLowerCase();
                let ctr = r.closest('[class*="field"],[class*="question"],fieldset,div') || r.parentElement;
                let ct = (ctr ? ctr.textContent : '').toLowerCase();
                if (lt === 'yes' && (ct.includes('authorized') || ct.includes('sponsor'))) {
                    r.click(); r.checked = true;
                    r.dispatchEvent(new Event('change', {bubbles:true}));
                }
            });
        }""")
        time.sleep(0.5)
        for s in ["select[id*='sponsor' i]", "select[name*='authorized' i]"]:
            try: page.select_option(s, label="Yes", timeout=2000)
            except: pass

    # Application questions
    if any(w in body_lower for w in ["hear about", "salary", "how did you"]):
        for s in ["select[id*='source' i]", "select[name*='source' i]",
                   "select[id*='hear' i]"]:
            for v in ["LinkedIn", "Social Media", "Online Job Board", "Job Board", "Internet"]:
                try:
                    page.select_option(s, label=v, timeout=2000)
                    print(f"  [select] source={v}"); break
                except: continue
        for s in ["input[id*='salary' i]", "input[name*='salary' i]"]:
            try:
                el = page.locator(s).first
                if el.count() > 0 and el.is_visible(timeout=1500):
                    fill(page, s, "115000", "salary"); break
            except: pass

    # Demographics
    if any(w in body_lower for w in ["gender", "ethnicity", "race", "veteran",
                                       "disability", "demographic"]):
        for s in ["select[id*='gender' i]", "select[name*='gender' i]"]:
            for v in ["Female", "Woman", "Female/Woman"]:
                try: page.select_option(s, label=v, timeout=2000); print(f"  [select] gender={v}"); break
                except: continue
        for s in ["select[id*='ethnicity' i]", "select[name*='ethnicity' i]",
                   "select[id*='race' i]", "select[name*='race' i]"]:
            for v in ["Asian", "Asian (Not Hispanic or Latino)", "Asian or Pacific Islander"]:
                try: page.select_option(s, label=v, timeout=2000); print(f"  [select] ethnicity={v}"); break
                except: continue
        for s in ["select[id*='veteran' i]", "select[name*='veteran' i]"]:
            for v in ["I am not a protected veteran", "No", "Not a Veteran"]:
                try: page.select_option(s, label=v, timeout=2000); print(f"  [select] veteran={v}"); break
                except: continue
        for s in ["select[id*='disability' i]", "select[name*='disability' i]"]:
            for v in ["No, I Don't Have a Disability", "No", "I do not have a disability"]:
                try: page.select_option(s, label=v, timeout=2000); print(f"  [select] disability={v}"); break
                except: continue

        # Radio demographics
        page.evaluate("""() => {
            Array.from(document.querySelectorAll('input[type="radio"]')).forEach(r => {
                let lbl = r.closest('label') || document.querySelector('label[for="'+r.id+'"]');
                let lt = (lbl ? lbl.textContent : r.value || '').trim().toLowerCase();
                let ctr = r.closest('[class*="field"],[class*="question"],fieldset') || r.parentElement;
                let ct = (ctr ? ctr.textContent : '').toLowerCase();
                if ((ct.includes('gender') || ct.includes('sex')) && (lt.includes('female') || lt.includes('woman'))) {
                    r.click(); r.checked = true; r.dispatchEvent(new Event('change', {bubbles:true}));
                }
                if ((ct.includes('veteran') || ct.includes('military')) && (lt.includes('not') || lt === 'no')) {
                    r.click(); r.checked = true; r.dispatchEvent(new Event('change', {bubbles:true}));
                }
                if (ct.includes('disability') && (lt.includes('no') || lt.includes('not'))) {
                    r.click(); r.checked = true; r.dispatchEvent(new Event('change', {bubbles:true}));
                }
            });
        }""")
        time.sleep(0.5)


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
    print("BCG Phenom v5 -- Talent Senior Specialist - People")
    print("=" * 60)

    # Kill stale Chrome
    subprocess.run(
        ["powershell", "-Command",
         f"Get-NetTCPConnection -LocalPort {PORT} -ErrorAction SilentlyContinue | "
         f"Select-Object -ExpandProperty OwningProcess | "
         f"ForEach-Object {{ Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }}"],
        capture_output=True, timeout=10
    )
    time.sleep(2)

    print(f"\n[1] Launching Chrome (port {PORT}, profile: {PROFILE})...")
    proc = subprocess.Popen(
        [CHROME,
         f"--remote-debugging-port={PORT}",
         f"--user-data-dir={PROFILE}",
         "--no-first-run",
         "--no-default-browser-check",
         "--disable-blink-features=AutomationControlled",
         PHENOM_LOGIN],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    print(f"  PID {proc.pid}, waiting 15s...")
    time.sleep(15)

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(f"http://localhost:{PORT}")
        ctx = browser.contexts[0]
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.set_default_timeout(30000)

        try:
            net(page, 20000)
            time.sleep(3)
            dismiss_cookie(page)
            time.sleep(2)
            ss(page, "v5_01_initial")
            cur = url(page)
            body = txt(page)
            print(f"  URL: {cur}")
            print(f"  Body: {body[:300]}")

            # ── Login sequence ──────────────────────────────────────────────
            print("\n[2] Login sequence...")
            body_lower = body.lower()
            already_logged_in = "careerhub" in cur and "login" not in cur

            if not already_logged_in:
                # Step A: Enter email + click Continue
                email_filled = False
                for s in ["input[type='email']", "input[placeholder*='Email' i]",
                           "input[name*='email' i]", "input[id*='email' i]",
                           "input[autocomplete='email']"]:
                    try:
                        el = page.locator(s).first
                        if el.count() > 0 and el.is_visible(timeout=3000):
                            fill(page, s, EMAIL, "email")
                            email_filled = True
                            break
                    except: continue

                if not email_filled:
                    R["status"] = "blocked"
                    R["notes"] = f"No email input on login page. URL:{cur} Body:{body[:200]}"
                    ss(page, "v5_99_no_email"); browser.close(); save(R); return R

                ss(page, "v5_02_email_filled")
                click_visible(page, [
                    "button:has-text('Continue')",
                    "button[type='submit']",
                    "button:has-text('Next')",
                ], "continue_after_email")
                time.sleep(7); net(page, 15000)
                dismiss_cookie(page)
                ss(page, "v5_03_after_email")
                body = txt(page)
                print(f"  URL: {url(page)}")
                print(f"  Body: {body[:400]}")

                if has_captcha(page):
                    R["status"] = "captcha-staged"
                    R["notes"] = "CAPTCHA after email entry."
                    browser.close(); save(R); return R
                if has_email_verify(page):
                    R["status"] = "email-verify-staged"
                    R["notes"] = f"Email verify required. Check {EMAIL}."
                    browser.close(); save(R); return R

                body_lower = body.lower()

                # Step B: Password form vs registration vs consent vs OTP
                if "password" in body_lower and "submit" in body_lower:
                    print("  Password form detected -- filling + submitting...")
                    pw_inputs = page.locator("input[type='password']").all()
                    if pw_inputs:
                        pw_inputs[0].fill(PW)
                        print("  [fill] password")
                    else:
                        print("  [warn] No password inputs found!")

                    ss(page, "v5_04_pw_filled")

                    # Click Submit (the green button on the password step)
                    clicked = click_visible(page, [
                        "button:has-text('Submit')",
                        "button[type='submit']",
                        "button:has-text('Sign In')",
                        "button:has-text('Log In')",
                    ], "password_submit")
                    if not clicked:
                        # Try pressing Enter
                        if pw_inputs:
                            pw_inputs[0].press("Enter")
                            print("  Pressed Enter on password field")

                    time.sleep(8); net(page, 15000)
                    dismiss_cookie(page)
                    ss(page, "v5_05_after_signin")
                    body = txt(page)
                    cur = url(page)
                    print(f"  Post-signin URL: {cur}")
                    print(f"  Post-signin body: {body[:400]}")

                    # Check if login succeeded (URL changed away from /login)
                    if "login" in cur.lower() or "sign" in cur.lower():
                        # Login failed — try "Use a one-time code instead"
                        print("  Login seems failed (still on login page). Trying one-time code...")
                        clicked = click_visible(page, [
                            "a:has-text('Use a one-time code instead')",
                            "button:has-text('one-time code')",
                            "a:has-text('one-time')",
                            "[href*='otp' i]",
                        ], "one_time_code")
                        if clicked:
                            time.sleep(5); net(page, 12000)
                            ss(page, "v5_06_otp_flow")
                            body = txt(page)
                            print(f"  OTP flow URL: {url(page)}")
                            print(f"  OTP body: {body[:400]}")
                            # OTP means an email will be sent
                            if has_email_verify(page) or "code" in body.lower() or "sent" in body.lower():
                                R["status"] = "email-verify-staged"
                                R["notes"] = (
                                    f"BCG Phenom sent a one-time login code to {EMAIL}. "
                                    "Human: check inbox, enter the code in the open Chrome window "
                                    f"(port {PORT}), then re-run submit_bcg_v5.py to complete the application."
                                )
                                browser.close(); save(R); return R
                        else:
                            # Can't proceed — account exists but password wrong and no OTP fallback
                            R["status"] = "email-verify-staged"
                            R["notes"] = (
                                f"Login failed for {EMAIL} — password mismatch. "
                                "Options: (A) Manually reset password via 'Forgot password?' in Chrome "
                                f"(port {PORT}), or (B) use 'Sign in using Google' with jamiecheng0103@gmail.com."
                            )
                            ss(page, "v5_99_login_failed")
                            browser.close(); save(R); return R

                elif any(w in body_lower for w in ["please review", "i consent", "consent to receive"]):
                    print("  Consent page -- submitting...")
                    try:
                        cb = page.locator("input[type='checkbox']").first
                        if cb.count() > 0 and cb.is_visible(timeout=2000) and not cb.is_checked():
                            cb.check()
                    except: pass
                    click_visible(page, ["button:has-text('Submit')", "button[type='submit']"], "consent")
                    time.sleep(5); net(page, 12000)
                    body = txt(page)
                    ss(page, "v5_consent")
                    if has_email_verify(page):
                        R["status"] = "email-verify-staged"
                        R["notes"] = f"Email verify required post-consent. Check {EMAIL}."
                        browser.close(); save(R); return R

                elif any(w in body_lower for w in ["first name", "create account", "register", "create a password"]):
                    print("  New account registration form...")
                    for s in ["input[placeholder*='First' i]", "input[name*='first' i]",
                               "input[id*='first' i]", "input[autocomplete='given-name']"]:
                        try:
                            el = page.locator(s).first
                            if el.count() > 0 and el.is_visible(timeout=2000):
                                fill(page, s, "Yi-Chieh", "first"); break
                        except: pass
                    for s in ["input[placeholder*='Last' i]", "input[name*='last' i]",
                               "input[id*='last' i]", "input[autocomplete='family-name']"]:
                        try:
                            el = page.locator(s).first
                            if el.count() > 0 and el.is_visible(timeout=2000):
                                fill(page, s, "Cheng", "last"); break
                        except: pass
                    for i, pw_el in enumerate(page.locator("input[type='password']").all()[:2]):
                        try:
                            pw_el.fill(PW)
                            print(f"  [fill] password[{i}]")
                        except Exception as e:
                            print(f"  [fill!] pw[{i}]: {e}")

                    ss(page, "v5_reg_filled")
                    if has_captcha(page):
                        R["status"] = "captcha-staged"
                        R["notes"] = "CAPTCHA on registration form."
                        browser.close(); save(R); return R
                    click_visible(page, [
                        "button:has-text('Create Account')", "button:has-text('Sign Up')",
                        "button:has-text('Register')", "button[type='submit']",
                        "button:has-text('Continue')",
                    ], "create_account")
                    time.sleep(8); net(page, 15000)
                    body = txt(page)
                    ss(page, "v5_after_create")
                    if has_email_verify(page):
                        R["status"] = "email-verify-staged"
                        R["notes"] = f"Account created — verify email at {EMAIL}."
                        browser.close(); save(R); return R
                    if has_captcha(page):
                        R["status"] = "captcha-staged"
                        R["notes"] = "CAPTCHA post-registration."
                        browser.close(); save(R); return R

            # ── Navigate to job ───────────────────────────────────────────
            print("\n[3] Navigating to Phenom job page...")
            page.goto(PHENOM_APPLY, timeout=30000, wait_until="domcontentloaded")
            time.sleep(7); net(page, 15000)
            dismiss_cookie(page)
            time.sleep(2)
            ss(page, "v5_10_job_page")
            body = txt(page)
            cur = url(page)
            print(f"  URL: {cur}")
            print(f"  Body: {body[:400]}")

            # Still on login page → re-attempt login
            if "login" in cur.lower():
                print("  Still on login page after navigation. Re-attempting login flow...")
                # Try email entry again
                for s in ["input[type='email']", "input[placeholder*='Email' i]"]:
                    try:
                        el = page.locator(s).first
                        if el.count() > 0 and el.is_visible(timeout=3000):
                            fill(page, s, EMAIL, "email_retry")
                            break
                    except: continue
                ss(page, "v5_10b_email_retry")
                click_visible(page, ["button:has-text('Continue')", "button[type='submit']"], "continue_retry")
                time.sleep(7); net(page, 15000)
                body = txt(page)
                body_lower = body.lower()
                ss(page, "v5_10c_after_retry")
                print(f"  URL after retry: {url(page)}")
                print(f"  Body: {body[:400]}")

                if "password" in body_lower:
                    for pw_el in page.locator("input[type='password']").all()[:1]:
                        try: pw_el.fill(PW)
                        except: pass
                    click_visible(page, ["button:has-text('Submit')", "button[type='submit']"], "submit_pw_retry")
                    time.sleep(8); net(page, 15000)
                    body = txt(page)
                    cur = url(page)
                    ss(page, "v5_10d_after_pw_retry")
                    print(f"  URL after pw retry: {cur}")
                    print(f"  Body: {body[:400]}")

                    if "login" in cur.lower():
                        # Try one-time code
                        click_visible(page, [
                            "a:has-text('Use a one-time code instead')",
                            "a:has-text('one-time code')",
                        ], "otp_retry")
                        time.sleep(4)
                        R["status"] = "email-verify-staged"
                        R["notes"] = (
                            f"Login failed for {EMAIL} (password mismatch). "
                            f"One-time code link clicked (check inbox). "
                            f"Chrome on port {PORT} / profile {PROFILE}. "
                            "Human: enter OTP code in Chrome, then re-run script to drive wizard."
                        )
                        ss(page, "v5_99_otp_staged"); browser.close(); save(R); return R

            # ── Apply button ──────────────────────────────────────────────
            if "careerhub" in url(page).lower():
                print("  On careerhub. Looking for Apply button...")
                body_lower = body.lower()
                if "apply" in body_lower:
                    for s in [
                        "button:has-text('Apply Now')", "button:has-text('Apply')",
                        "a:has-text('Apply Now')", "a:has-text('Apply')",
                        "[data-testid='apply-button']",
                    ]:
                        try:
                            el = page.locator(s).first
                            if el.count() > 0 and el.is_visible(timeout=3000):
                                t = el.inner_text().strip().lower()
                                if not any(bad in t for bad in ["subscribe", "similar", "notify"]):
                                    el.click()
                                    time.sleep(5); net(page, 12000)
                                    print(f"  [apply] {s}")
                                    break
                        except: continue

                time.sleep(3)
                ss(page, "v5_11_after_apply")
                body = txt(page)
                print(f"  URL after apply: {url(page)}")
                print(f"  Body: {body[:400]}")

            # ── Application wizard ────────────────────────────────────────
            print("\n[4] Application wizard...")

            for step in range(35):
                time.sleep(4)
                body = txt(page)
                cur = url(page)
                ss(page, f"v5_wiz_{step:02d}")
                print(f"\n  [step {step}] {cur[:100]}")
                print(f"  Body: {body[:300]}")

                if has_captcha(page):
                    R["status"] = "captcha-staged"
                    R["notes"] = f"CAPTCHA at wizard step {step}. URL: {cur}"
                    browser.close(); save(R); return R
                if has_email_verify(page):
                    R["status"] = "email-verify-staged"
                    R["notes"] = f"Email verify at step {step}. Check {EMAIL}."
                    browser.close(); save(R); return R

                # Confirmation check (with login-page exclusion)
                if is_real_confirmation(body, cur):
                    print("  *** CONFIRMED SUBMISSION! ***")
                    R["status"] = "submitted"
                    R["confirmed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                    R["screenshot"] = os.path.join(SHOT, f"v5_wiz_{step:02d}.png")
                    R["notes"] = f"SUBMITTED. Confirmation text: {body[:600]}"
                    browser.close(); save(R); return R

                body_lower = body.lower()

                # Still on login page?
                if ("login" in cur.lower() or
                        ("sign in" in body_lower and "password" in body_lower and "careerhub" not in cur.lower())):
                    print("  Still on login page in wizard! Attempting OTP...")
                    click_visible(page, [
                        "a:has-text('Use a one-time code instead')",
                        "a:has-text('one-time code')",
                    ], "otp_in_wizard")
                    time.sleep(4)
                    R["status"] = "email-verify-staged"
                    R["notes"] = (
                        f"Stuck on login page at wizard step {step}. "
                        f"Clicked 'one-time code' — check {EMAIL} for OTP. "
                        f"Chrome on port {PORT}."
                    )
                    ss(page, f"v5_99_stuck_login_{step}"); browser.close(); save(R); return R

                # Cookie modal re-appeared?
                if any(w in body_lower for w in ["we value your privacy", "cookie consent",
                                                    "accept all and close"]):
                    dismiss_cookie(page)
                    time.sleep(2); continue

                # Fill this page
                wizard_fill_page(page, body, step)
                time.sleep(1)

                # Look for Submit Application button
                for s in [
                    "button:has-text('Submit Application')",
                    "button:has-text('Submit')",
                    "button[data-testid='submit-application']",
                ]:
                    try:
                        el = page.locator(s).first
                        if el.count() > 0 and el.is_visible(timeout=2000):
                            t = el.inner_text().strip().lower()
                            if any(bad in t for bad in ["subscribe", "newsletter"]):
                                continue
                            print(f"  [SUBMIT] {s}")
                            ss(page, f"v5_pre_submit_{step:02d}")
                            el.click()
                            time.sleep(10); net(page, 20000)
                            body = txt(page)
                            ss(page, "v5_post_submit")
                            print(f"  Post-submit URL: {url(page)}")
                            print(f"  Post-submit: {body[:600]}")
                            if is_real_confirmation(body, url(page)):
                                R["status"] = "submitted"
                            else:
                                R["status"] = "likely-submitted"
                            R["confirmed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                            R["screenshot"] = os.path.join(SHOT, "v5_post_submit.png")
                            R["notes"] = f"Submit clicked. Post: {body[:600]}"
                            browser.close(); save(R); return R
                    except: continue

                # Next step
                advanced = click_visible(page, [
                    "button:has-text('Next')",
                    "button:has-text('Continue')",
                    "button:has-text('Save and Continue')",
                    "button:has-text('Save & Continue')",
                    "button:has-text('Proceed')",
                    "[data-testid='next-btn']",
                    "[data-testid='continue-btn']",
                ], f"next_{step}")

                if not advanced:
                    print(f"  No next button at step {step}")
                    if step >= 3 and is_real_confirmation(txt(page), url(page)):
                        R["status"] = "submitted"
                        R["confirmed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                        R["screenshot"] = os.path.join(SHOT, f"v5_wiz_{step:02d}.png")
                        R["notes"] = f"Submitted. {txt(page)[:600]}"
                        browser.close(); save(R); return R
                    if step >= 8:
                        print("  Wizard stalled. Stopping.")
                        break
                    time.sleep(3)

            R["status"] = "blocked"
            R["notes"] = f"Wizard exhausted. Last URL: {url(page)}. Last body: {txt(page)[:400]}"
            ss(page, "v5_99_done")
            browser.close(); save(R); return R

        except Exception as e:
            tb = traceback.format_exc()
            print(f"\n[EXCEPTION] {e}\n{tb[:1000]}")
            R["status"] = "error"
            R["notes"] = f"Exception: {str(e)}\n{tb[:500]}"
            try: ss(page, "v5_99_exception")
            except: pass
            try: browser.close()
            except: pass
            save(R)
            return R


if __name__ == "__main__":
    main()
