# -*- coding: utf-8 -*-
"""
submit_bcg_phenom_v3.py  -- BCG Phenom ATS final drive

Correct flow (learned from v1/v2 inspection):
  1. Load Phenom login page -> dismiss TrustArc cookie banner (CLICK, not JS hide)
  2. Enter email in the Email field -> Click Continue
  3. Consent page (/candidate/register): click "Submit" to consent and advance
  4. Registration form (first/last name + password): fill + submit
  5. If email verification is required: stage (Chrome stays live on port 9402)
  6. Otherwise: navigate to careerhub job -> Apply -> wizard -> Submit

Key fixes from v1/v2:
  - Don't click "Sign Up" nav link (opens new tab -> crashes page context)
  - Use the email input + Continue button, NOT the "Create an account" link
  - The consent page "Submit" button is what advances to registration
  - False-positive confirmation guard: only match isolated confirmation phrases,
    NOT "Track your application" (that's marketing copy on the consent page)
  - Cookie banner: try real click on "Accept All and Close" first, THEN JS hide
"""
import os, sys, time, json, subprocess, traceback
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, r"C:\Users\chent\Agentic_Workflows_2026\jamie-autopilot\lib")
from patchright.sync_api import sync_playwright
from credential_vault import job_password

PORT     = 9402
PROFILE  = r"C:\Users\chent\ats_agent_9402"
CHROME   = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
ROLE_DIR = (r"C:\Users\chent\Agentic_Workflows_2026\oracle-job-search"
            r"\outputs\2026-06-12-feed-first\applications\bcg_talent_sr_specialist")
SHOT     = ROLE_DIR + r"\screenshots"
RESUME   = ROLE_DIR + r"\resume.pdf"
os.makedirs(SHOT, exist_ok=True)

EMAIL = "jamiecheng0103@gmail.com"
PW    = job_password()

PHENOM_LOGIN = (
    "https://experiencedtalent.bcg.com/candidate/login"
    "?domain=bcg.com&hl=en&microsite=microsite_1"
    "&next=http%3A%2F%2Fexperiencedtalent.bcg.com%2Fcareerhub%2Fexplore%2Fjobs"
    "%2F790315808241%3Fpost_onboarding_pid%3D790315808241%26show_apply%3D1"
    "%26profile_type%3Dcandidate%26customredirect%3D1"
)
PHENOM_JOB = (
    "https://experiencedtalent.bcg.com/careerhub/explore/jobs/790315808241"
    "?post_onboarding_pid=790315808241&show_apply=1&profile_type=candidate&customredirect=1"
)
JOB_PUBLIC_URL = "https://careers.bcg.com/global/en/job/57988/Talent-Senior-Specialist-People"

# ── helpers ──────────────────────────────────────────────────────────────────

def ss(page, name):
    path = os.path.join(SHOT, name + ".png")
    try:
        page.screenshot(path=path, full_page=True)
        print(f"  [ss] {name}.png")
    except Exception as e:
        print(f"  [ss!] {name}: {e}")
    return path


def net(page, t=12000):
    try:
        page.wait_for_load_state("networkidle", timeout=t)
    except:
        pass


def txt(page):
    try:
        return page.inner_text("body")
    except:
        return ""


def dismiss_cookie(page):
    """Real click on Accept All, then JS hide as fallback."""
    for sel in [
        "button:has-text('Accept All and Close')",
        "button:has-text('Accept All')",
        "#truste-consent-button",
        "button[id*='accept' i]",
    ]:
        try:
            el = page.locator(sel).first
            if el.count() > 0 and el.is_visible(timeout=2000):
                el.click()
                time.sleep(1.5)
                print(f"  [cookie] click: {sel}")
                return
        except:
            continue
    # JS fallback
    try:
        page.evaluate("""
        document.querySelectorAll(
            '[id*="truste"],[class*="truste_overlay"],[class*="truste_box"],' +
            '#truste-consent-track,.truste_popframe,[class*="trustarc"]'
        ).forEach(e => e.style.cssText = 'display:none!important;');
        """)
        print("  [cookie] JS hidden")
    except:
        pass


def fill(page, sel, val, lbl="", t=8000):
    try:
        el = page.locator(sel).first
        el.wait_for(state="visible", timeout=t)
        el.click(timeout=3000)
        el.fill("", timeout=3000)
        el.fill(val, timeout=5000)
        print(f"  [fill] {lbl or sel[:50]} = {val[:40]}")
        return True
    except:
        try:
            el = page.locator(sel).first
            el.triple_click(timeout=3000)
            el.type(val, delay=60)
            print(f"  [fill-type] {lbl or sel[:50]} = {val[:40]}")
            return True
        except Exception as e:
            print(f"  [fill!] {lbl or sel[:50]}: {str(e)[:50]}")
            return False


def has_captcha(page):
    for sel in ["iframe[src*='recaptcha']", "iframe[src*='hcaptcha']",
                ".g-recaptcha", "[data-sitekey]", ".cf-turnstile",
                "iframe[title*='CAPTCHA' i]"]:
        try:
            if page.locator(sel).count() > 0:
                return True
        except:
            pass
    try:
        t = page.inner_text("body")[:3000].lower()
        return any(w in t for w in ["captcha", "i'm not a robot"])
    except:
        return False


def has_email_verify(page):
    """Strict check - only phrases that mean an email was sent for verification."""
    try:
        t = page.inner_text("body")[:3000].lower()
        return any(k in t for k in [
            "verification email sent", "verify your email",
            "we sent an email", "check your inbox",
            "email to confirm", "confirm your email address",
            "click the link in", "activation link",
        ])
    except:
        return False


def is_real_confirmation(page_text):
    """
    True only if page contains genuine application confirmation language.
    Guards against false positives from Phenom's consent/register pages which contain
    'Submit', 'Track your application', 'your application' as marketing copy.
    """
    t = page_text.lower()
    # Must have at least one strong confirmation phrase
    strong = [
        "thank you for applying",
        "your application has been submitted",
        "application successfully submitted",
        "we have received your application",
        "application received",
        "application number",
        "application id:",
        "you have successfully applied",
        "you've applied",
    ]
    return any(p in t for p in strong)


def save(result):
    path = os.path.join(ROLE_DIR, "SUBMITTED.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"\n[SAVED] {path}")
    print("=" * 60)
    print(f"RESULT: {result['status']}")
    print(f"Notes:  {str(result.get('notes', ''))[:400]}")
    print("=" * 60)


# ── main ─────────────────────────────────────────────────────────────────────

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
        "apply_url": PHENOM_JOB,
        "job_id": "790315808241",
    }

    print("=" * 60)
    print("BCG Phenom v3 -- Talent Senior Specialist - People")
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

    print(f"\n[1] Chrome on port {PORT}...")
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
    print(f"  PID {proc.pid}, waiting 12s...")
    time.sleep(12)

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(f"http://localhost:{PORT}")
        ctx = browser.contexts[0]
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.set_default_timeout(30000)

        try:
            net(page, 20000)
            time.sleep(3)
            dismiss_cookie(page)
            time.sleep(1)
            ss(page, "v3_01_login")
            body = txt(page)
            print(f"  URL: {page.url}")
            print(f"  Page: {body[:300]}")

            # ── 2. Enter email, click Continue ────────────────────────────────
            print("\n[2] Enter email + Continue...")

            email_sel = None
            for s in [
                "input[type='email']",
                "input[placeholder*='Email' i]",
                "input[name*='email' i]",
                "input[id*='email' i]",
                "input[autocomplete='email']",
            ]:
                try:
                    el = page.locator(s).first
                    if el.count() > 0 and el.is_visible(timeout=2000):
                        email_sel = s
                        break
                except:
                    continue

            if not email_sel:
                R["status"] = "blocked"
                R["notes"] = "Could not find email input on Phenom login page."
                ss(page, "v3_99_no_email_field")
                browser.close()
                save(R)
                return R

            fill(page, email_sel, EMAIL, "email")
            time.sleep(0.5)
            ss(page, "v3_02_email_filled")

            # Click Continue
            cont_clicked = False
            for s in [
                "button:has-text('Continue')",
                "button[type='submit']",
                "input[type='submit']",
                "button[aria-label*='Continue' i]",
            ]:
                try:
                    el = page.locator(s).first
                    if el.count() > 0 and el.is_visible(timeout=3000):
                        el.click()
                        cont_clicked = True
                        time.sleep(5)
                        net(page, 15000)
                        print(f"  Continue: {s}")
                        break
                except:
                    continue

            if not cont_clicked:
                # Try pressing Enter in the email field
                page.locator(email_sel).first.press("Enter")
                time.sleep(5)
                net(page, 15000)
                print("  Continue: Enter key")

            time.sleep(2)
            ss(page, "v3_03_after_email_continue")
            body = txt(page)
            print(f"  URL: {page.url}")
            print(f"  Page: {body[:400]}")

            # Gate checks
            if has_captcha(page):
                R["status"] = "captcha-staged"
                R["notes"] = "CAPTCHA after email entry on Phenom login."
                ss(page, "v3_99_captcha_email")
                browser.close(); save(R); return R

            if has_email_verify(page):
                R["status"] = "email-verify-staged"
                R["notes"] = (
                    "Phenom (BCG) sent email verification to jamiecheng0103@gmail.com "
                    "after email entry. Check inbox, click verification link, then re-run."
                )
                ss(page, "v3_99_email_verify_post_email")
                browser.close(); save(R); return R

            # ── 3. Handle consent page (/candidate/register) ─────────────────
            print("\n[3] Consent / registration gate...")
            body_lower = body.lower()

            # BCG Phenom shows a consent page after email Continue.
            # It says "Please review before continuing" with a checkbox + Submit button.
            # This is a marketing-comms opt-in, NOT application submission.
            if "please review before continuing" in body_lower or "consent" in body_lower:
                print("  Consent page detected -- clicking Submit to advance...")

                # Optionally tick the consent checkbox (not required by law, optional)
                for cb_sel in [
                    "input[type='checkbox']",
                    "[data-testid='consent-checkbox']",
                ]:
                    try:
                        cb = page.locator(cb_sel).first
                        if cb.count() > 0 and cb.is_visible(timeout=2000) and not cb.is_checked():
                            cb.check()
                            print(f"  [checkbox] consent ticked")
                            break
                    except:
                        pass

                # Click Submit on the consent page
                consent_submitted = False
                for s in [
                    "button:has-text('Submit')",
                    "button[type='submit']",
                    "input[type='submit'][value*='Submit' i]",
                ]:
                    try:
                        el = page.locator(s).first
                        if el.count() > 0 and el.is_visible(timeout=3000):
                            el.click()
                            consent_submitted = True
                            time.sleep(5)
                            net(page, 15000)
                            print(f"  Consent Submit: {s}")
                            break
                    except:
                        continue

                time.sleep(3)
                ss(page, "v3_04_after_consent")
                body = txt(page)
                print(f"  URL after consent: {page.url}")
                print(f"  Page: {body[:400]}")

                if has_email_verify(page):
                    R["status"] = "email-verify-staged"
                    R["notes"] = (
                        "BCG Phenom sent email verification to jamiecheng0103@gmail.com "
                        "after consent step. Human: click the link in the email, "
                        f"then re-run this script. Chrome stays live on port {PORT}."
                    )
                    ss(page, "v3_99_email_verify_post_consent")
                    browser.close(); save(R); return R

            # ── 4. Registration form (name + password) ────────────────────────
            body = txt(page)
            body_lower = body.lower()
            print(f"\n[4] Registration form check. URL: {page.url}")
            print(f"  Page: {body[:400]}")

            if any(w in body_lower for w in ["first name", "create password", "password"]):
                print("  Registration form -- filling name + password...")

                # First name
                for s in ["input[placeholder*='First' i]", "input[name*='first' i]",
                           "input[id*='first' i]", "input[autocomplete='given-name']"]:
                    if fill(page, s, "Yi-Chieh", "first_name"):
                        break

                # Last name
                for s in ["input[placeholder*='Last' i]", "input[name*='last' i]",
                           "input[id*='last' i]", "input[autocomplete='family-name']"]:
                    if fill(page, s, "Cheng", "last_name"):
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
                        print(f"  [fill!] pw[{i}]: {e}")

                ss(page, "v3_05_reg_form_filled")

                if has_captcha(page):
                    R["status"] = "captcha-staged"
                    R["notes"] = "CAPTCHA on Phenom registration form. Name/pw filled. Human: solve + Create Account."
                    ss(page, "v3_99_captcha_reg")
                    browser.close(); save(R); return R

                # Submit registration
                for s in ["button[type='submit']", "button:has-text('Create Account')",
                           "button:has-text('Sign Up')", "button:has-text('Register')",
                           "button:has-text('Continue')"]:
                    try:
                        el = page.locator(s).first
                        if el.count() > 0 and el.is_visible(timeout=3000):
                            el.click()
                            time.sleep(5)
                            net(page, 15000)
                            print(f"  Reg submit: {s}")
                            break
                    except:
                        continue

                time.sleep(5)
                ss(page, "v3_06_after_reg_submit")
                body = txt(page)
                print(f"  Post-reg URL: {page.url}")
                print(f"  Post-reg: {body[:400]}")

                if has_email_verify(page):
                    R["status"] = "email-verify-staged"
                    R["notes"] = (
                        "BCG Phenom account created -- email verification sent to "
                        "jamiecheng0103@gmail.com. Human: click the verification link, "
                        "then the application form will be accessible. "
                        f"Chrome on port {PORT} / profile {PROFILE}."
                    )
                    ss(page, "v3_99_email_verify_post_reg")
                    browser.close(); save(R); return R

                if has_captcha(page):
                    R["status"] = "captcha-staged"
                    R["notes"] = "CAPTCHA post-registration. Human: solve and continue."
                    ss(page, "v3_99_captcha_post_reg")
                    browser.close(); save(R); return R

            # ── 5. Navigate to the application form ───────────────────────────
            print("\n[5] Navigating to job application form...")
            time.sleep(2)
            cur = page.url
            body = txt(page)

            # Navigate to job if not already in careerhub/apply flow
            if "careerhub" not in cur or "apply" not in cur:
                print(f"  Navigating to Phenom job URL...")
                page.goto(PHENOM_JOB, timeout=30000, wait_until="domcontentloaded")
                time.sleep(5)
                net(page, 15000)
                dismiss_cookie(page)
                time.sleep(2)
                ss(page, "v3_07_phenom_job")
                body = txt(page)
                print(f"  Job page URL: {page.url}")
                print(f"  Job page: {body[:400]}")

                # Click Apply Now / Apply button on the job page
                for s in [
                    "button:has-text('Apply Now')",
                    "button:has-text('Apply')",
                    "a:has-text('Apply Now')",
                    "[data-testid='apply-button']",
                ]:
                    try:
                        el = page.locator(s).first
                        if el.count() > 0 and el.is_visible(timeout=3000):
                            t_val = el.inner_text().strip().lower()
                            if not any(bad in t_val for bad in ["subscribe", "similar", "notify"]):
                                el.click()
                                time.sleep(5)
                                net(page, 15000)
                                print(f"  Apply: {s}")
                                break
                    except:
                        continue

                time.sleep(3)
                ss(page, "v3_08_after_apply_click")
                body = txt(page)
                print(f"  After Apply URL: {page.url}")
                print(f"  After Apply: {body[:400]}")

            # ── 6. Walk the application wizard ────────────────────────────────
            print("\n[6] Application wizard walk...")

            for step in range(25):
                time.sleep(3)
                body = txt(page)
                cur = page.url
                ss(page, f"v3_wiz_{step:02d}")
                print(f"\n  [step {step}] {cur[:80]}")
                print(f"  {body[:250]}")

                # Gates
                if has_captcha(page):
                    R["status"] = "captcha-staged"
                    R["notes"] = f"CAPTCHA at wizard step {step}."
                    ss(page, f"v3_99_captcha_wiz{step}")
                    browser.close(); save(R); return R

                if has_email_verify(page):
                    R["status"] = "email-verify-staged"
                    R["notes"] = f"Email verify at wiz step {step}. Check jamiecheng0103@gmail.com."
                    browser.close(); save(R); return R

                # Confirmation (strict)
                if is_real_confirmation(body):
                    print("  CONFIRMED SUBMISSION!")
                    R["status"] = "submitted"
                    R["confirmed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                    R["screenshot"] = os.path.join(SHOT, f"v3_wiz_{step:02d}.png")
                    R["notes"] = f"Submitted. Confirmation: {body[:400]}"
                    browser.close(); save(R); return R

                # Submit button (strict -- not subscribe/notify)
                for s in [
                    "button:has-text('Submit Application')",
                    "button[data-testid='submit-application']",
                ]:
                    try:
                        el = page.locator(s).first
                        if el.count() > 0 and el.is_visible(timeout=2000):
                            print(f"  SUBMIT: {s}")
                            ss(page, f"v3_pre_submit_{step:02d}")
                            el.click()
                            time.sleep(8)
                            net(page, 20000)
                            body = txt(page)
                            ss(page, "v3_post_submit")
                            print(f"  Post-submit URL: {page.url}")
                            print(f"  Post-submit: {body[:400]}")
                            if is_real_confirmation(body):
                                R["status"] = "submitted"
                            else:
                                R["status"] = "likely-submitted"
                            R["confirmed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                            R["screenshot"] = os.path.join(SHOT, "v3_post_submit.png")
                            R["notes"] = f"Submit clicked. Post: {body[:400]}"
                            browser.close(); save(R); return R
                    except:
                        continue

                body_lower = body.lower()

                # Personal info
                if any(w in body_lower for w in ["first name", "last name", "contact"]):
                    print("  Personal info...")
                    for s, v, l in [
                        ("input[placeholder*='First' i]", "Yi-Chieh", "first"),
                        ("input[name*='first' i]", "Yi-Chieh", "first"),
                        ("input[autocomplete='given-name']", "Yi-Chieh", "first"),
                        ("input[placeholder*='Last' i]", "Cheng", "last"),
                        ("input[name*='last' i]", "Cheng", "last"),
                        ("input[autocomplete='family-name']", "Cheng", "last"),
                    ]:
                        try:
                            el = page.locator(s).first
                            if el.count() > 0 and el.is_visible(timeout=2000):
                                if not el.input_value().strip():
                                    fill(page, s, v, l)
                        except:
                            pass
                    for s in ["input[type='tel']", "input[placeholder*='Phone' i]"]:
                        try:
                            el = page.locator(s).first
                            if el.count() > 0 and el.is_visible(timeout=2000):
                                if not el.input_value().strip():
                                    fill(page, s, "(213) 700-3831", "phone")
                                break
                        except:
                            pass

                # Resume upload
                if any(w in body_lower for w in ["resume", "upload", "cv", "attach"]):
                    print("  Resume upload...")
                    uploaded = False
                    for s in ["input[type='file'][accept*='pdf' i]", "input[type='file']"]:
                        try:
                            inputs = page.locator(s).all()
                            if inputs:
                                inputs[0].set_input_files(RESUME)
                                time.sleep(5)
                                uploaded = True
                                print(f"  [upload] {s}")
                                for no in ["No, thanks", "Skip", "Manual Entry"]:
                                    try:
                                        el = page.get_by_text(no, exact=False).first
                                        if el.count() > 0 and el.is_visible(timeout=2000):
                                            el.click(); time.sleep(2); break
                                    except:
                                        pass
                                break
                        except:
                            pass
                    if not uploaded:
                        for s in ["button:has-text('Upload')", "label:has-text('Upload')"]:
                            try:
                                with page.expect_file_chooser(timeout=5000) as fc:
                                    page.locator(s).first.click(timeout=4000)
                                fc.value.set_files(RESUME)
                                time.sleep(5)
                                uploaded = True
                                break
                            except:
                                pass
                    ss(page, f"v3_wiz_{step:02d}_resume")

                # Work auth / sponsorship
                if any(w in body_lower for w in ["authorized", "sponsorship", "work authorization"]):
                    print("  Work auth...")
                    page.evaluate("""
                    Array.from(document.querySelectorAll('input[type="radio"]')).forEach(r => {
                        var lbl = r.closest('label') || document.querySelector('label[for="'+r.id+'"]');
                        if (!lbl) return;
                        var txt = lbl.textContent.trim().toLowerCase();
                        var ctr = r.closest('[class*="field"],[class*="question"],fieldset,div');
                        var ctxt = (ctr ? ctr.textContent : '').toLowerCase();
                        if (txt === 'yes' && (ctxt.includes('authorized') || ctxt.includes('sponsor')))
                            r.click();
                    });
                    """)
                    for s in ["select[id*='sponsor' i]", "select[name*='authorized' i]"]:
                        try:
                            page.select_option(s, label="Yes", timeout=2000)
                        except:
                            pass

                # App questions (hear about, salary)
                if any(w in body_lower for w in ["hear about", "salary"]):
                    for s in ["select[id*='source' i]", "select[name*='source' i]"]:
                        for v in ["LinkedIn", "Social Media", "Job Board"]:
                            try:
                                page.select_option(s, label=v, timeout=2000)
                                print(f"  [hear] {v}")
                                break
                            except:
                                continue
                    for s in ["input[id*='salary' i]", "input[name*='salary' i]"]:
                        if fill(page, s, "115000", "salary"):
                            break

                # Demographics
                if any(w in body_lower for w in ["gender", "ethnicity", "race", "veteran"]):
                    print("  Demographics...")
                    for s in ["select[id*='gender' i]", "select[name*='gender' i]"]:
                        for v in ["Female", "Woman"]:
                            try:
                                page.select_option(s, label=v, timeout=2000)
                                break
                            except:
                                continue
                    for s in ["select[id*='ethnicity' i]", "select[name*='race' i]"]:
                        for v in ["Asian", "Asian (Not Hispanic or Latino)"]:
                            try:
                                page.select_option(s, label=v, timeout=2000)
                                break
                            except:
                                continue
                    for s in ["select[id*='veteran' i]"]:
                        for v in ["I am not a protected veteran", "No"]:
                            try:
                                page.select_option(s, label=v, timeout=2000)
                                break
                            except:
                                continue
                    for s in ["select[id*='disability' i]"]:
                        for v in ["No, I Don't Have a Disability", "No"]:
                            try:
                                page.select_option(s, label=v, timeout=2000)
                                break
                            except:
                                continue

                # Advance -- skip subscribe/notify buttons
                advanced = False
                for s in [
                    "button:has-text('Next')",
                    "button:has-text('Continue')",
                    "button:has-text('Save and Continue')",
                    "button:has-text('Save & Continue')",
                    "[data-testid='next-btn']",
                ]:
                    try:
                        el = page.locator(s).first
                        if el.count() > 0 and el.is_visible(timeout=2000):
                            t_val = el.inner_text().strip().lower()
                            if any(bad in t_val for bad in ["subscribe", "notify", "similar"]):
                                continue
                            el.click()
                            time.sleep(3)
                            net(page, 10000)
                            advanced = True
                            print(f"  [next] {s}")
                            break
                    except:
                        continue

                if not advanced:
                    print(f"  No next button at step {step}")
                    if step >= 4:
                        new_body = txt(page)
                        if is_real_confirmation(new_body):
                            R["status"] = "submitted"
                            R["confirmed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                            R["screenshot"] = os.path.join(SHOT, f"v3_wiz_{step:02d}.png")
                            R["notes"] = f"Submitted (post-no-next). {new_body[:400]}"
                            browser.close(); save(R); return R
                        if step >= 7:
                            print("  Wizard stalled -- stopping.")
                            break

            R["status"] = "blocked"
            R["notes"] = (
                f"Phenom wizard exhausted. Last URL: {page.url}. "
                "Likely hit email-verification gate or unexpected page structure."
            )
            ss(page, "v3_99_wizard_done")
            browser.close(); save(R); return R

        except Exception as e:
            tb = traceback.format_exc()
            print(f"\n[EXCEPTION] {e}\n{tb[:800]}")
            R["status"] = "error"
            R["notes"] = f"Exception: {str(e)}\n{tb[:400]}"
            try:
                ss(page, "v3_99_exception")
            except:
                pass
            try:
                browser.close()
            except:
                pass
            save(R)
            return R


if __name__ == "__main__":
    main()
