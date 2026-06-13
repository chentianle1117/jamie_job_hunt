# -*- coding: utf-8 -*-
"""
submit_bcg_v4.py  -- BCG Phenom ATS final drive (v4)

Key fixes over v3:
  - Cookie modal: try real click, then JS override on ALL matching elements,
    then set localStorage/cookie flags that Phenom/TrustArc checks
  - Use a FRESH chrome profile to avoid stale TrustArc state
  - Login flow: email → password (existing account) OR create new account
  - Robust wizard: scroll each page, look for any input/select/radio/checkbox
  - Full demographics + sponsorship + salary + source handling
  - Strict confirmation guard (is_real_confirmation)
  - Cover letter upload attempted after resume
"""
import os, sys, time, json, subprocess, traceback
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, r"C:\Users\chent\Agentic_Workflows_2026\jamie-autopilot\lib")
from patchright.sync_api import sync_playwright
from credential_vault import job_password

PORT     = 9402
# Use a FRESH profile to avoid any stale TrustArc/cookie state from previous runs
PROFILE  = r"C:\Users\chent\ats_agent_9402_v4"
CHROME   = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
ROLE_DIR = (r"C:\Users\chent\Agentic_Workflows_2026\oracle-job-search"
            r"\outputs\2026-06-12-feed-first\applications\bcg_talent_sr_specialist")
SHOT     = ROLE_DIR + r"\screenshots\v4"
RESUME   = ROLE_DIR + r"\resume.pdf"
COVER    = ROLE_DIR + r"\cover_letter.pdf"
os.makedirs(SHOT, exist_ok=True)

EMAIL = "jamiecheng0103@gmail.com"
PW    = job_password()

# BCG uses Phenom (experiencedtalent.bcg.com) NOT Workday
# The job is: Talent Senior Specialist - People, Seattle, Hybrid
JOB_PUBLIC_URL = "https://careers.bcg.com/global/en/job/57988/Talent-Senior-Specialist-People"
# Direct Phenom apply URL (from previous inspection)
PHENOM_APPLY = (
    "https://experiencedtalent.bcg.com/careerhub/explore/jobs/790315808241"
    "?post_onboarding_pid=790315808241&show_apply=1&profile_type=candidate&customredirect=1"
)
PHENOM_LOGIN = "https://experiencedtalent.bcg.com/candidate/login?domain=bcg.com&hl=en"

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


def dismiss_cookie_aggressive(page):
    """Aggressively dismiss any cookie/privacy modal using multiple strategies."""
    print("  [cookie] Attempting aggressive cookie dismiss...")

    # Strategy 1: Real click on all known BCG/TrustArc/OneTrust selectors
    for sel in [
        "button:has-text('Accept All and Close')",
        "button:has-text('Accept All')",
        "button:has-text('Accept all')",
        "button:has-text('Accept Cookies')",
        "button:has-text('Accept all cookies')",
        "button:has-text('I Accept')",
        "button:has-text('Agree')",
        "#truste-consent-button",
        "#onetrust-accept-btn-handler",
        "button[id*='accept' i]",
        "button[class*='accept' i]",
        ".truste-button1",
        "[data-testid='cookie-accept']",
    ]:
        try:
            el = page.locator(sel).first
            if el.count() > 0:
                el.wait_for(state="visible", timeout=2000)
                el.click(timeout=3000, force=True)
                time.sleep(1.5)
                print(f"  [cookie] clicked: {sel}")
                return True
        except:
            continue

    # Strategy 2: JS to set TrustArc consent flags + remove overlays
    try:
        page.evaluate("""
        () => {
            // Hide all TrustArc overlays
            document.querySelectorAll(
                '[id*="truste"],[class*="truste"],[id*="trustarc"],[class*="trustarc"],' +
                '#onetrust-banner-sdk,.onetrust-pc-dark-filter,.truste_popframe,' +
                '.truste_overlay,.trustarc-banner-overlay,[class*="cookie-banner"],' +
                '[class*="CookieBanner"],[id*="cookie-banner"],[class*="privacy-modal"]'
            ).forEach(e => {
                e.style.cssText = 'display:none!important;visibility:hidden!important;';
            });

            // Set TrustArc consent cookies directly
            const d = new Date();
            d.setFullYear(d.getFullYear() + 1);
            const expires = '; expires=' + d.toUTCString();
            // TrustArc 3-group consent: all accepted
            document.cookie = 'notice_behavior=expressed,eu' + expires + '; path=/';
            document.cookie = 'notice_gdpr_prefs=0,1,2:' + btoa('groups=C0001,C0002,C0003') + expires + '; path=/';
            document.cookie = 'cmapi_cookie_privacy=permit 1,2,3' + expires + '; path=/';
            document.cookie = 'cmapi_gtm_bl=' + expires + '; path=/';
            document.cookie = 'notice_preferences=2:' + expires + '; path=/';

            // OneTrust consent
            try {
                if (window.OneTrust) {
                    window.OneTrust.Accept();
                }
            } catch(e) {}

            // TrustArc
            try {
                if (window.truste && window.truste.eu) {
                    window.truste.eu.clickListener();
                }
            } catch(e) {}

            // Remove body scroll locks
            document.body.style.overflow = 'auto';
            document.documentElement.style.overflow = 'auto';
        }
        """)
        time.sleep(1)
        print("  [cookie] JS consent flags set + overlays hidden")
        return True
    except Exception as e:
        print(f"  [cookie] JS fallback failed: {e}")

    return False


def fill(page, sel, val, lbl="", t=8000):
    """Fill a text input field, trying multiple strategies."""
    try:
        el = page.locator(sel).first
        el.wait_for(state="visible", timeout=t)
        el.scroll_into_view_if_needed()
        el.click(timeout=3000)
        el.fill("", timeout=3000)
        el.fill(val, timeout=5000)
        actual = el.input_value()
        if actual.strip() != val.strip():
            # fallback: type char by char
            el.triple_click()
            el.type(val, delay=40)
        print(f"  [fill] {lbl or sel[:50]} = '{val[:60]}'")
        return True
    except Exception as e:
        print(f"  [fill!] {lbl or sel[:50]}: {str(e)[:80]}")
        return False


def click_btn(page, selectors, label="button", timeout=5000):
    """Try clicking any of the selectors, skip subscribe/notify/similar."""
    for s in selectors:
        try:
            el = page.locator(s).first
            if el.count() > 0 and el.is_visible(timeout=2000):
                t_val = el.inner_text().strip().lower()
                if any(bad in t_val for bad in ["subscribe", "notify", "similar", "alert"]):
                    continue
                el.scroll_into_view_if_needed()
                el.click(timeout=timeout)
                print(f"  [click] {label}: {s} ('{t_val[:40]}')")
                return True
        except:
            continue
    return False


def has_captcha(page):
    for sel in ["iframe[src*='recaptcha']", "iframe[src*='hcaptcha']",
                ".g-recaptcha", "[data-sitekey]", ".cf-turnstile",
                "iframe[title*='CAPTCHA' i]", "iframe[title*='challenge' i]"]:
        try:
            if page.locator(sel).count() > 0:
                return True
        except:
            pass
    try:
        t = page.inner_text("body")[:3000].lower()
        return any(w in t for w in ["captcha", "i'm not a robot", "verify you are human"])
    except:
        return False


def has_email_verify(page):
    """Strict: only phrases that mean a verification email was sent."""
    try:
        t = page.inner_text("body")[:3000].lower()
        return any(k in t for k in [
            "verification email sent", "verify your email",
            "we sent an email", "check your inbox",
            "email to confirm", "confirm your email address",
            "click the link in", "activation link",
            "we've sent a link", "sent a verification",
        ])
    except:
        return False


def is_real_confirmation(page_text):
    """True only on genuine application submission confirmation."""
    t = page_text.lower()
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
        "successfully applied",
        "your submission has been received",
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


# ── Application form filling ──────────────────────────────────────────────────

def fill_personal_info(page, body_lower):
    """Fill personal information fields if present."""
    if not any(w in body_lower for w in ["first name", "last name", "phone", "contact"]):
        return
    print("  [wizard] Personal info fields detected...")

    # First name
    for s in ["input[placeholder*='First' i]", "input[name*='first' i]",
               "input[id*='first' i]", "input[autocomplete='given-name']",
               "input[label*='First' i]"]:
        try:
            el = page.locator(s).first
            if el.count() > 0 and el.is_visible(timeout=2000):
                v = el.input_value().strip()
                if not v or v.lower() in ["", "yi-chieh"]:
                    fill(page, s, "Yi-Chieh", "first_name")
                    break
        except:
            pass

    # Last name
    for s in ["input[placeholder*='Last' i]", "input[name*='last' i]",
               "input[id*='last' i]", "input[autocomplete='family-name']"]:
        try:
            el = page.locator(s).first
            if el.count() > 0 and el.is_visible(timeout=2000):
                v = el.input_value().strip()
                if not v or v.lower() == "cheng":
                    fill(page, s, "Cheng", "last_name")
                    break
        except:
            pass

    # Phone
    for s in ["input[type='tel']", "input[placeholder*='Phone' i]",
               "input[name*='phone' i]", "input[id*='phone' i]"]:
        try:
            el = page.locator(s).first
            if el.count() > 0 and el.is_visible(timeout=2000):
                v = el.input_value().strip()
                if not v:
                    fill(page, s, "2137003831", "phone")
                    break
        except:
            pass

    # Address fields (if present)
    for s_addr, v_addr, lbl in [
        ("input[placeholder*='Address' i]", "1784 NW Northrup Street", "address"),
        ("input[placeholder*='City' i]", "Portland", "city"),
        ("input[placeholder*='Zip' i]", "97209", "zip"),
        ("input[placeholder*='Postal' i]", "97209", "postal"),
    ]:
        try:
            el = page.locator(s_addr).first
            if el.count() > 0 and el.is_visible(timeout=1500):
                if not el.input_value().strip():
                    fill(page, s_addr, v_addr, lbl)
        except:
            pass

    # State/Country dropdowns
    for s in ["select[name*='state' i]", "select[id*='state' i]"]:
        try:
            page.select_option(s, value="OR", timeout=2000)
            print("  [select] state=OR")
        except:
            try:
                page.select_option(s, label="Oregon", timeout=2000)
            except:
                pass

    for s in ["select[name*='country' i]", "select[id*='country' i]"]:
        try:
            page.select_option(s, label="United States", timeout=2000)
            print("  [select] country=US")
        except:
            try:
                page.select_option(s, value="US", timeout=2000)
            except:
                pass


def fill_work_auth(page, body_lower):
    """Fill work authorization and sponsorship fields."""
    if not any(w in body_lower for w in ["authorized", "sponsorship", "work authorization",
                                           "eligible to work", "legally authorized"]):
        return
    print("  [wizard] Work auth fields detected...")

    # JS: click YES on authorization questions, YES on sponsorship questions
    page.evaluate("""
    () => {
        const radios = Array.from(document.querySelectorAll('input[type="radio"]'));
        radios.forEach(r => {
            // Find the label for this radio
            let lbl = r.closest('label') || document.querySelector('label[for="'+r.id+'"]');
            let lblTxt = (lbl ? lbl.textContent : r.value || '').trim().toLowerCase();

            // Find the containing question context
            let ctr = r.closest('[class*="field"],[class*="question"],fieldset,div[class*="form"]') || r.parentElement;
            let ctxt = (ctr ? ctr.textContent : '').toLowerCase();

            // Work authorized: click Yes
            if (lblTxt === 'yes' && ctxt.includes('authorized')) {
                r.click(); r.checked = true;
                r.dispatchEvent(new Event('change', {bubbles: true}));
            }
            // Sponsorship required: ALWAYS YES (truthful)
            if (lblTxt === 'yes' && ctxt.includes('sponsor')) {
                r.click(); r.checked = true;
                r.dispatchEvent(new Event('change', {bubbles: true}));
            }
        });
    }
    """)
    time.sleep(0.5)

    # Also handle select dropdowns for auth questions
    for s in ["select[id*='authorized' i]", "select[name*='authorized' i]",
               "select[id*='workauth' i]"]:
        try:
            page.select_option(s, label="Yes", timeout=2000)
            print(f"  [select] work_auth=Yes ({s})")
        except:
            pass

    for s in ["select[id*='sponsor' i]", "select[name*='sponsor' i]"]:
        try:
            page.select_option(s, label="Yes", timeout=2000)
            print(f"  [select] sponsor=Yes ({s})")
        except:
            pass


def fill_app_questions(page, body_lower):
    """Fill application-specific questions."""
    if not any(w in body_lower for w in ["hear about", "salary", "years of experience",
                                           "how did you", "compensation"]):
        return
    print("  [wizard] Application questions detected...")

    # How did you hear
    for s in ["select[id*='source' i]", "select[name*='source' i]",
               "select[id*='hear' i]", "select[name*='hear' i]",
               "select[id*='referral' i]"]:
        for v in ["LinkedIn", "Social Media", "Online Job Board", "Job Board", "Internet"]:
            try:
                page.select_option(s, label=v, timeout=2000)
                print(f"  [select] source={v}")
                break
            except:
                continue

    # Salary
    for s in ["input[id*='salary' i]", "input[name*='salary' i]",
               "input[placeholder*='salary' i]", "input[placeholder*='Salary' i]"]:
        try:
            el = page.locator(s).first
            if el.count() > 0 and el.is_visible(timeout=2000):
                fill(page, s, "115000", "desired_salary")
                break
        except:
            pass

    # Years of experience (text or select)
    for s in ["select[id*='experience' i]", "select[name*='experience' i]"]:
        for v in ["3", "3-5", "3-4", "2-4", "2-5", "Less than 5"]:
            try:
                page.select_option(s, label=v, timeout=1500)
                print(f"  [select] experience={v}")
                break
            except:
                try:
                    page.select_option(s, value=v, timeout=1500)
                    break
                except:
                    continue

    for s in ["input[id*='experience' i]", "input[name*='experience' i]"]:
        try:
            el = page.locator(s).first
            if el.count() > 0 and el.is_visible(timeout=2000):
                fill(page, s, "3", "years_experience")
                break
        except:
            pass


def fill_demographics(page, body_lower):
    """Fill voluntary demographic disclosures (truthful)."""
    if not any(w in body_lower for w in ["gender", "ethnicity", "race", "veteran",
                                           "disability", "demographic", "voluntary"]):
        return
    print("  [wizard] Demographics fields detected...")

    # Gender: Female/Woman
    for s in ["select[id*='gender' i]", "select[name*='gender' i]",
               "select[id*='sex' i]"]:
        for v in ["Female", "Woman", "Female/Woman", "F"]:
            try:
                page.select_option(s, label=v, timeout=2000)
                print(f"  [select] gender={v}")
                break
            except:
                continue

    # Ethnicity/Race: Asian
    for s in ["select[id*='ethnicity' i]", "select[name*='ethnicity' i]",
               "select[id*='race' i]", "select[name*='race' i]"]:
        for v in ["Asian", "Asian (Not Hispanic or Latino)", "Asian or Pacific Islander"]:
            try:
                page.select_option(s, label=v, timeout=2000)
                print(f"  [select] ethnicity={v}")
                break
            except:
                continue

    # Hispanic/Latino: No
    for s in ["select[id*='hispanic' i]", "select[name*='hispanic' i]",
               "select[id*='latino' i]"]:
        for v in ["No", "Not Hispanic or Latino", "Non-Hispanic or Non-Latino"]:
            try:
                page.select_option(s, label=v, timeout=2000)
                break
            except:
                continue

    # Veteran: Not a veteran
    for s in ["select[id*='veteran' i]", "select[name*='veteran' i]"]:
        for v in ["I am not a protected veteran", "No", "Not a Veteran",
                   "I identify as not being a protected veteran"]:
            try:
                page.select_option(s, label=v, timeout=2000)
                print(f"  [select] veteran={v}")
                break
            except:
                continue

    # Disability: No
    for s in ["select[id*='disability' i]", "select[name*='disability' i]"]:
        for v in ["No, I Don't Have a Disability", "No", "I do not have a disability",
                   "I don't have a disability", "N"]:
            try:
                page.select_option(s, label=v, timeout=2000)
                print(f"  [select] disability={v}")
                break
            except:
                continue

    # Radio buttons for demographics
    page.evaluate("""
    () => {
        const radios = Array.from(document.querySelectorAll('input[type="radio"]'));
        radios.forEach(r => {
            let lbl = r.closest('label') || document.querySelector('label[for="'+r.id+'"]');
            let lblTxt = (lbl ? lbl.textContent : r.value || '').trim().toLowerCase();
            let ctr = r.closest('[class*="field"],[class*="question"],fieldset') || r.parentElement;
            let ctxt = (ctr ? ctr.textContent : '').toLowerCase();

            if ((ctxt.includes('gender') || ctxt.includes('sex')) &&
                (lblTxt.includes('female') || lblTxt.includes('woman'))) {
                r.click(); r.checked = true;
                r.dispatchEvent(new Event('change', {bubbles: true}));
            }
            if ((ctxt.includes('veteran') || ctxt.includes('military')) &&
                (lblTxt.includes('not') || lblTxt.includes('no'))) {
                r.click(); r.checked = true;
                r.dispatchEvent(new Event('change', {bubbles: true}));
            }
            if (ctxt.includes('disability') && (lblTxt.includes('no') || lblTxt.includes('not'))) {
                r.click(); r.checked = true;
                r.dispatchEvent(new Event('change', {bubbles: true}));
            }
        });
    }
    """)
    time.sleep(0.5)


def upload_resume(page, body_lower, step):
    """Upload resume PDF if file input is available."""
    if not any(w in body_lower for w in ["resume", "upload", "cv", "attach", "document"]):
        return False
    print("  [wizard] File upload area detected...")

    # Direct file input
    for s in ["input[type='file'][accept*='pdf' i]",
               "input[type='file'][accept*='.pdf' i]",
               "input[type='file']"]:
        try:
            inputs = page.locator(s).all()
            if inputs:
                # Use the first PDF-accepting input
                inp = inputs[0]
                inp.set_input_files(RESUME)
                time.sleep(4)
                print(f"  [upload] resume via {s}")

                # Dismiss any "parse resume" / "autofill" popup
                for dismiss in ["No, thanks", "Skip", "No thanks", "Manual",
                                  "Enter Manually", "I'll enter manually"]:
                    try:
                        el = page.get_by_text(dismiss, exact=False).first
                        if el.count() > 0 and el.is_visible(timeout=2000):
                            el.click()
                            time.sleep(2)
                            print(f"  [dismiss] '{dismiss}'")
                            break
                    except:
                        pass
                ss(page, f"v4_wiz_{step:02d}_resume")
                return True
        except Exception as e:
            print(f"  [upload!] {s}: {e}")

    # File chooser via click
    for s in ["button:has-text('Upload')", "button:has-text('Choose File')",
               "label:has-text('Upload')", "label[for*='file' i]",
               "[class*='upload' i]", "[class*='dropzone' i]"]:
        try:
            with page.expect_file_chooser(timeout=5000) as fc:
                page.locator(s).first.click(timeout=4000)
            fc.value.set_files(RESUME)
            time.sleep(4)
            print(f"  [upload] resume via file chooser {s}")
            ss(page, f"v4_wiz_{step:02d}_resume_chooser")
            return True
        except:
            pass

    return False


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
    print("BCG Phenom v4 -- Talent Senior Specialist - People")
    print(f"Profile: {PROFILE}")
    print("=" * 60)

    # Kill stale Chrome on port 9402
    subprocess.run(
        ["powershell", "-Command",
         f"Get-NetTCPConnection -LocalPort {PORT} -ErrorAction SilentlyContinue | "
         f"Select-Object -ExpandProperty OwningProcess | "
         f"ForEach-Object {{ Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }}"],
        capture_output=True, timeout=10
    )
    time.sleep(2)

    print(f"\n[1] Launching Chrome on port {PORT} with fresh profile...")
    proc = subprocess.Popen(
        [CHROME,
         f"--remote-debugging-port={PORT}",
         f"--user-data-dir={PROFILE}",
         "--no-first-run",
         "--no-default-browser-check",
         "--disable-blink-features=AutomationControlled",
         "--disable-extensions",
         # Start at Phenom login (bypasses BCG.com cookie modal)
         PHENOM_LOGIN],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    print(f"  PID {proc.pid}, waiting 15s for Chrome to settle...")
    time.sleep(15)

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(f"http://localhost:{PORT}")
        ctx = browser.contexts[0]
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.set_default_timeout(30000)

        try:
            net(page, 20000)
            time.sleep(3)
            ss(page, "v4_01_initial")
            print(f"  URL: {page.url}")
            print(f"  Page text: {txt(page)[:300]}")

            # ── Step 2: Dismiss cookie modal aggressively ─────────────────────
            print("\n[2] Cookie dismiss...")
            dismiss_cookie_aggressive(page)
            time.sleep(2)
            ss(page, "v4_02_after_cookie")
            print(f"  URL after cookie: {page.url}")
            print(f"  Page: {txt(page)[:300]}")

            # ── Step 3: Handle Phenom login ───────────────────────────────────
            print("\n[3] Phenom login flow...")
            body = txt(page)
            body_lower = body.lower()

            # Check if we're already logged in (careerhub page)
            if "careerhub" in page.url.lower() or "logged in" in body_lower:
                print("  Already logged in, skipping login...")
            else:
                # Enter email
                email_filled = False
                for s in [
                    "input[type='email']",
                    "input[placeholder*='Email' i]",
                    "input[name*='email' i]",
                    "input[id*='email' i]",
                    "input[autocomplete='email']",
                    "input[placeholder*='Work email' i]",
                ]:
                    try:
                        el = page.locator(s).first
                        if el.count() > 0 and el.is_visible(timeout=3000):
                            fill(page, s, EMAIL, "email")
                            email_filled = True
                            break
                    except:
                        continue

                ss(page, "v4_03_email_filled")

                if not email_filled:
                    # Maybe cookie is still blocking — try again
                    print("  No email field! Re-attempting cookie dismiss...")
                    dismiss_cookie_aggressive(page)
                    time.sleep(3)
                    ss(page, "v4_03b_cookie_retry")
                    for s in ["input[type='email']", "input[placeholder*='Email' i]"]:
                        try:
                            el = page.locator(s).first
                            if el.count() > 0 and el.is_visible(timeout=3000):
                                fill(page, s, EMAIL, "email")
                                email_filled = True
                                break
                        except:
                            continue

                if not email_filled:
                    R["status"] = "blocked"
                    R["notes"] = f"Cannot find email input on login page. URL: {page.url}. Page: {txt(page)[:200]}"
                    ss(page, "v4_99_no_email")
                    browser.close(); save(R); return R

                # Click Continue
                clicked = click_btn(page, [
                    "button:has-text('Continue')",
                    "button[type='submit']",
                    "input[type='submit']",
                    "button[aria-label*='Continue' i]",
                    "button:has-text('Sign In')",
                    "button:has-text('Next')",
                ], "Continue/Next")

                if not clicked:
                    page.keyboard.press("Enter")
                    print("  Pressed Enter for Continue")

                time.sleep(6)
                net(page, 15000)
                ss(page, "v4_04_after_email_continue")
                body = txt(page)
                print(f"  URL: {page.url}")
                print(f"  Page: {body[:400]}")

                if has_captcha(page):
                    R["status"] = "captcha-staged"
                    R["notes"] = "CAPTCHA after email entry. Human: solve and continue."
                    browser.close(); save(R); return R

                if has_email_verify(page):
                    R["status"] = "email-verify-staged"
                    R["notes"] = f"Email verification sent to {EMAIL}. Human: click link in inbox."
                    browser.close(); save(R); return R

                # Check for password field (existing account) vs registration form (new account)
                body_lower = body.lower()

                if "password" in body_lower and any(w in body_lower for w in ["sign in", "login", "log in"]):
                    print("  Existing account -- entering password...")
                    pw_inputs = page.locator("input[type='password']").all()
                    if pw_inputs:
                        try:
                            pw_inputs[0].fill(PW)
                            print("  [fill] password")
                        except Exception as e:
                            print(f"  [fill!] password: {e}")

                    ss(page, "v4_05_pw_filled")
                    click_btn(page, [
                        "button:has-text('Sign In')",
                        "button:has-text('Log In')",
                        "button[type='submit']",
                        "button:has-text('Continue')",
                    ], "Sign In")
                    time.sleep(6)
                    net(page, 15000)
                    ss(page, "v4_06_after_signin")
                    body = txt(page)
                    print(f"  Post-signin URL: {page.url}")
                    print(f"  Post-signin: {body[:400]}")

                elif any(w in body_lower for w in ["first name", "create", "register", "sign up", "create account"]):
                    print("  New account registration form...")

                    # Check for consent step
                    if "please review before continuing" in body_lower or "i consent" in body_lower:
                        print("  Consent page -- ticking checkbox + clicking Submit...")
                        try:
                            cb = page.locator("input[type='checkbox']").first
                            if cb.count() > 0 and cb.is_visible(timeout=2000) and not cb.is_checked():
                                cb.check()
                        except:
                            pass
                        click_btn(page, ["button:has-text('Submit')", "button[type='submit']"], "consent_submit")
                        time.sleep(5); net(page, 15000)
                        body = txt(page)
                        body_lower = body.lower()
                        ss(page, "v4_consent_done")

                    if has_email_verify(page):
                        R["status"] = "email-verify-staged"
                        R["notes"] = f"Email verification required after consent. Check {EMAIL}."
                        browser.close(); save(R); return R

                    # Registration form: first/last/password
                    for s in ["input[placeholder*='First' i]", "input[name*='first' i]",
                               "input[id*='first' i]", "input[autocomplete='given-name']"]:
                        try:
                            el = page.locator(s).first
                            if el.count() > 0 and el.is_visible(timeout=2000):
                                fill(page, s, "Yi-Chieh", "first_name"); break
                        except: pass

                    for s in ["input[placeholder*='Last' i]", "input[name*='last' i]",
                               "input[id*='last' i]", "input[autocomplete='family-name']"]:
                        try:
                            el = page.locator(s).first
                            if el.count() > 0 and el.is_visible(timeout=2000):
                                fill(page, s, "Cheng", "last_name"); break
                        except: pass

                    pw_inputs = page.locator("input[type='password']").all()
                    for i, pw_el in enumerate(pw_inputs[:2]):
                        try:
                            pw_el.wait_for(state="visible", timeout=3000)
                            pw_el.fill(PW)
                            print(f"  [fill] password[{i}]")
                        except Exception as e:
                            print(f"  [fill!] pw[{i}]: {e}")

                    ss(page, "v4_07_reg_filled")

                    if has_captcha(page):
                        R["status"] = "captcha-staged"
                        R["notes"] = "CAPTCHA on registration form. Name/pw filled. Human: solve + submit."
                        browser.close(); save(R); return R

                    click_btn(page, [
                        "button:has-text('Create Account')", "button:has-text('Sign Up')",
                        "button:has-text('Register')", "button[type='submit']",
                        "button:has-text('Continue')",
                    ], "create_account")
                    time.sleep(8); net(page, 15000)
                    ss(page, "v4_08_after_create")
                    body = txt(page)
                    print(f"  Post-create URL: {page.url}")
                    print(f"  Post-create: {body[:400]}")

                    if has_email_verify(page):
                        R["status"] = "email-verify-staged"
                        R["notes"] = (
                            f"BCG Phenom account created — email verification sent to {EMAIL}. "
                            "Human: click the verification link in the inbox, then re-run to complete application."
                        )
                        browser.close(); save(R); return R

                    if has_captcha(page):
                        R["status"] = "captcha-staged"
                        R["notes"] = "CAPTCHA post-registration. Human: solve and continue."
                        browser.close(); save(R); return R

                elif "please review before continuing" in body_lower or "consent" in body_lower:
                    print("  Standalone consent page -- submitting...")
                    try:
                        cb = page.locator("input[type='checkbox']").first
                        if cb.count() > 0 and cb.is_visible(timeout=2000) and not cb.is_checked():
                            cb.check()
                    except: pass
                    click_btn(page, ["button:has-text('Submit')", "button[type='submit']"], "consent")
                    time.sleep(5); net(page, 15000)
                    body = txt(page)
                    ss(page, "v4_consent_standalone")
                    if has_email_verify(page):
                        R["status"] = "email-verify-staged"
                        R["notes"] = f"Email verification required post-consent. Check {EMAIL}."
                        browser.close(); save(R); return R

            # ── Step 4: Navigate to the Phenom job application ────────────────
            print("\n[4] Navigating to Phenom job application...")
            time.sleep(2)
            cur_url = page.url

            # If not already in the apply flow, navigate there
            if "careerhub" not in cur_url or "790315808241" not in cur_url:
                print(f"  Navigating to job application URL...")
                page.goto(PHENOM_APPLY, timeout=30000, wait_until="domcontentloaded")
                time.sleep(6); net(page, 15000)
                dismiss_cookie_aggressive(page)
                time.sleep(2)
                ss(page, "v4_09_job_page")
                body = txt(page)
                print(f"  Job page URL: {page.url}")
                print(f"  Job page: {body[:400]}")
            else:
                ss(page, "v4_09_already_at_job")
                body = txt(page)

            # Look for Apply button
            body_lower = body.lower()
            if any(w in body_lower for w in ["apply now", "apply", "start application"]):
                for s in [
                    "button:has-text('Apply Now')",
                    "button:has-text('Apply')",
                    "a:has-text('Apply Now')",
                    "a:has-text('Apply')",
                    "[data-testid='apply-button']",
                    "[class*='apply-btn' i]",
                ]:
                    try:
                        el = page.locator(s).first
                        if el.count() > 0 and el.is_visible(timeout=3000):
                            t_val = el.inner_text().strip().lower()
                            if not any(bad in t_val for bad in ["subscribe", "similar", "notify", "alert"]):
                                el.click()
                                time.sleep(5); net(page, 15000)
                                print(f"  [apply] clicked: {s}")
                                break
                    except:
                        continue

            time.sleep(3)
            ss(page, "v4_10_after_apply_click")
            body = txt(page)
            print(f"  URL after apply: {page.url}")
            print(f"  After apply: {body[:400]}")

            # ── Step 5: Walk the application wizard ───────────────────────────
            print("\n[5] Walking application wizard...")

            for step in range(30):
                time.sleep(4)
                body = txt(page)
                cur_url = page.url
                ss(page, f"v4_wiz_{step:02d}")
                print(f"\n  [step {step}] URL: {cur_url[:100]}")
                print(f"  Page: {body[:300]}")

                # Gate checks first
                if has_captcha(page):
                    R["status"] = "captcha-staged"
                    R["notes"] = f"CAPTCHA at wizard step {step}. URL: {cur_url}"
                    browser.close(); save(R); return R

                if has_email_verify(page):
                    R["status"] = "email-verify-staged"
                    R["notes"] = f"Email verify at wizard step {step}. Check {EMAIL}."
                    browser.close(); save(R); return R

                # Real confirmation check
                if is_real_confirmation(body):
                    print("  *** CONFIRMED SUBMISSION! ***")
                    R["status"] = "submitted"
                    R["confirmed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                    R["screenshot"] = os.path.join(SHOT, f"v4_wiz_{step:02d}.png")
                    R["notes"] = f"SUBMITTED. Confirmation: {body[:600]}"
                    browser.close(); save(R); return R

                body_lower = body.lower()

                # Scroll to expose all fields
                try:
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(1)
                    page.evaluate("window.scrollTo(0, 0)")
                    time.sleep(0.5)
                except:
                    pass

                # ── Fill whatever's on this page ──────────────────────────────

                # Cookie modal (in case it reappears)
                if any(w in body_lower for w in ["we value your privacy", "cookie", "consent to"]):
                    dismiss_cookie_aggressive(page)
                    time.sleep(2)
                    continue

                # File upload
                upload_resume(page, body_lower, step)

                # Personal info
                fill_personal_info(page, body_lower)

                # Work authorization + sponsorship
                fill_work_auth(page, body_lower)

                # Application-specific questions
                fill_app_questions(page, body_lower)

                # Demographics
                fill_demographics(page, body_lower)

                # Look for a "Submit Application" button specifically
                for s in [
                    "button:has-text('Submit Application')",
                    "button:has-text('Submit')",
                    "button[data-testid='submit-application']",
                    "input[value='Submit Application']",
                    "input[value='Submit']",
                ]:
                    try:
                        el = page.locator(s).first
                        if el.count() > 0 and el.is_visible(timeout=2000):
                            t_val = el.inner_text().strip().lower() if hasattr(el, 'inner_text') else ""
                            if any(bad in t_val for bad in ["subscribe", "newsletter"]):
                                continue
                            print(f"  [SUBMIT] Found submit button: {s}")
                            ss(page, f"v4_pre_submit_{step:02d}")
                            el.click()
                            time.sleep(8); net(page, 20000)
                            body = txt(page)
                            ss(page, "v4_post_submit")
                            print(f"  Post-submit URL: {page.url}")
                            print(f"  Post-submit: {body[:600]}")

                            if is_real_confirmation(body):
                                R["status"] = "submitted"
                            else:
                                R["status"] = "likely-submitted"
                                R["notes_extra"] = "Submit clicked but confirmation text not matched — verify manually."
                            R["confirmed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                            R["screenshot"] = os.path.join(SHOT, "v4_post_submit.png")
                            R["notes"] = f"Submit clicked. Post-submit page: {body[:600]}"
                            browser.close(); save(R); return R
                    except:
                        continue

                # Advance to next step
                time.sleep(1)
                advanced = click_btn(page, [
                    "button:has-text('Next')",
                    "button:has-text('Continue')",
                    "button:has-text('Save and Continue')",
                    "button:has-text('Save & Continue')",
                    "button:has-text('Proceed')",
                    "[data-testid='next-btn']",
                    "[data-testid='continue-btn']",
                    "button[aria-label*='Next' i]",
                    "button[aria-label*='Continue' i]",
                ], f"next_step_{step}")

                if not advanced:
                    print(f"  No next button at step {step} — checking if done...")
                    if step >= 3:
                        final_body = txt(page)
                        if is_real_confirmation(final_body):
                            R["status"] = "submitted"
                            R["confirmed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                            R["screenshot"] = os.path.join(SHOT, f"v4_wiz_{step:02d}.png")
                            R["notes"] = f"Submitted (post-no-next). {final_body[:600]}"
                            browser.close(); save(R); return R
                        if step >= 10:
                            print("  Wizard appears stalled after 10+ steps. Stopping.")
                            break
                    time.sleep(3)

            # Wizard exhausted
            R["status"] = "blocked"
            R["notes"] = (
                f"Wizard exhausted after steps. Last URL: {page.url}. "
                "Last page text: " + txt(page)[:300]
            )
            ss(page, "v4_99_wizard_done")
            browser.close(); save(R); return R

        except Exception as e:
            tb = traceback.format_exc()
            print(f"\n[EXCEPTION] {e}\n{tb[:1000]}")
            R["status"] = "error"
            R["notes"] = f"Exception: {str(e)}\n{tb[:500]}"
            try: ss(page, "v4_99_exception")
            except: pass
            try: browser.close()
            except: pass
            save(R)
            return R


if __name__ == "__main__":
    main()
