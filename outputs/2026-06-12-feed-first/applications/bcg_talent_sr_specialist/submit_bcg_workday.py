"""
submit_bcg_workday.py — BCG "Talent Senior Specialist - People" (Seattle, Hybrid)
Workday ATS application driver for Jamie (Yi-Chieh) Cheng.

Pattern: dedicated Chrome (port 9402, own profile), Patchright CDP attach,
drive full Workday wizard → SUBMIT or stage at captcha/email-verify.

CDP detach rule: call browser.close() to detach the connection (Chrome stays alive).
NEVER time.sleep() for tab management after captcha gate.
"""
import os, sys, time, json, subprocess, traceback
sys.path.insert(0, r"C:\Users\chent\Agentic_Workflows_2026\jamie-autopilot\lib")
from patchright.sync_api import sync_playwright
from credential_vault import job_password

# ── CONSTANTS ──────────────────────────────────────────────────────────────────
PORT = 9402
PROFILE = r"C:\Users\chent\ats_agent_9402"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
ROLE_DIR = r"C:\Users\chent\Agentic_Workflows_2026\oracle-job-search\outputs\2026-06-12-feed-first\applications\bcg_talent_sr_specialist"
SHOT = ROLE_DIR + r"\screenshots"
RESUME = ROLE_DIR + r"\resume.pdf"
os.makedirs(SHOT, exist_ok=True)

EMAIL = "jamiecheng0103@gmail.com"
PW = job_password()

# BCG Workday careers URL — search for the role
BCG_CAREERS_SEARCH = "https://careers.bcg.com/jobs?q=Talent+Senior+Specialist+People&location=Seattle"
BCG_CAREERS_BASE = "https://careers.bcg.com"

# ── HELPERS ────────────────────────────────────────────────────────────────────
def shot(page, name):
    path = f"{SHOT}/{name}.png"
    try:
        page.screenshot(path=path, full_page=True)
        print(f"  [screenshot] {name}.png")
    except Exception as e:
        print(f"  [screenshot FAILED] {name}: {e}")
    return path

def wait_for_selector(page, selector, timeout=15000):
    """Wait for selector, return True if found."""
    try:
        page.wait_for_selector(selector, timeout=timeout)
        return True
    except:
        return False

def click_if_visible(page, selector, label="", timeout=5000):
    try:
        el = page.locator(selector).first
        el.wait_for(state="visible", timeout=timeout)
        el.click()
        print(f"  [click] {label or selector}")
        return True
    except Exception as e:
        print(f"  [click MISS] {label or selector}: {str(e)[:60]}")
        return False

def fill_field(page, selector, value, label="", timeout=8000):
    """Clear + fill a text field."""
    try:
        el = page.locator(selector).first
        el.wait_for(state="visible", timeout=timeout)
        el.click(timeout=3000)
        el.fill("", timeout=3000)
        el.fill(value, timeout=5000)
        print(f"  [fill] {label or selector[:50]} = {value[:40]}")
        return True
    except Exception as e:
        # Try triple-click + type as fallback
        try:
            el = page.locator(selector).first
            el.triple_click(timeout=3000)
            el.type(value, delay=50)
            print(f"  [fill-type] {label or selector[:50]} = {value[:40]}")
            return True
        except:
            print(f"  [fill FAIL] {label or selector[:50]}: {str(e)[:60]}")
            return False

def select_option(page, selector, value, label=""):
    """Select a <select> option by value or label text."""
    try:
        page.select_option(selector, label=value, timeout=5000)
        print(f"  [select] {label or selector[:50]} = {value}")
        return True
    except:
        try:
            page.select_option(selector, value=value, timeout=3000)
            print(f"  [select-val] {label or selector[:50]} = {value}")
            return True
        except Exception as e:
            print(f"  [select FAIL] {label or selector[:50]}: {str(e)[:60]}")
            return False

def click_radio_by_label(page, question_text, answer_text):
    """Find a radio group by nearby question text and click the matching label."""
    script = f"""
    (function() {{
        // find all radio inputs
        const radios = Array.from(document.querySelectorAll('input[type="radio"]'));
        // find by label text
        for (const r of radios) {{
            const lbl = r.closest('label') || document.querySelector('label[for="'+r.id+'"]');
            if (lbl && lbl.textContent.trim().toLowerCase().includes('{answer_text.lower()}')) {{
                // check if near question text
                const container = r.closest('[data-automation-id], fieldset, .WGEG, div');
                if (!container) {{ r.click(); return 'clicked-no-container'; }}
                if (container.textContent.toLowerCase().includes('{question_text.lower()}')) {{
                    r.click(); return 'clicked';
                }}
            }}
        }}
        // fallback: just find label containing the answer
        for (const r of radios) {{
            const lbl = r.closest('label') || document.querySelector('label[for="'+r.id+'"]');
            if (lbl && lbl.textContent.trim().toLowerCase() === '{answer_text.lower()}') {{
                r.click(); return 'clicked-fallback';
            }}
        }}
        return null;
    }})()
    """
    result = page.evaluate(script)
    print(f"  [radio] {question_text[:40]} → {answer_text}: {result}")
    return result is not None

def click_wd_button(page, labels, timeout=8000):
    """Click a Workday button/link by text (tries multiple labels)."""
    for lbl in (labels if isinstance(labels, list) else [labels]):
        for sel in [
            f"button:has-text('{lbl}')",
            f"[data-automation-id*='next']:has-text('{lbl}')",
            f"[role='button']:has-text('{lbl}')",
            f"a:has-text('{lbl}')",
        ]:
            try:
                el = page.locator(sel).first
                if el.count() > 0:
                    el.wait_for(state="visible", timeout=timeout)
                    el.click()
                    print(f"  [btn] {lbl}")
                    time.sleep(2)
                    return True
            except:
                continue
    # data-automation-id approach
    for aid in ['bottom-navigation-btn-next', 'bottom-navigation-next', 'next-btn']:
        try:
            el = page.locator(f"[data-automation-id='{aid}']").first
            if el.count() > 0:
                el.click(timeout=timeout)
                print(f"  [btn-aid] {aid}")
                time.sleep(2)
                return True
        except:
            continue
    print(f"  [btn MISS] tried: {labels}")
    return False

def wd_next(page):
    """Click the Workday Next/Save&Continue button."""
    # Try common Workday automation IDs first
    for aid in ['bottom-navigation-btn-next', 'bottom-navigation-btn-saveAndContinue',
                'nextButton', 'saveAndContinue', 'next']:
        try:
            el = page.locator(f"[data-automation-id='{aid}']").first
            if el.count() > 0 and el.is_visible(timeout=2000):
                el.click()
                time.sleep(2.5)
                page.wait_for_load_state("networkidle", timeout=10000)
                print(f"  [wd-next] via aid={aid}")
                return True
        except:
            continue
    # Text-based fallback
    for lbl in ["Save and Continue", "Next", "Continue", "Save"]:
        try:
            el = page.get_by_role("button", name=lbl, exact=False).first
            if el.count() > 0 and el.is_visible(timeout=2000):
                el.click()
                time.sleep(2.5)
                print(f"  [wd-next] via text={lbl}")
                return True
        except:
            continue
    return False

def detect_captcha(page):
    """Return True if a CAPTCHA widget is detected on the page."""
    captcha_sels = [
        "iframe[src*='recaptcha']", "iframe[src*='hcaptcha']",
        ".g-recaptcha", "#hcaptcha", "[data-sitekey]",
        "iframe[title*='CAPTCHA']", "iframe[title*='captcha']",
        ".cf-turnstile"
    ]
    for sel in captcha_sels:
        try:
            if page.locator(sel).count() > 0:
                return True
        except:
            continue
    txt = ""
    try:
        txt = page.inner_text("body")[:3000]
    except:
        pass
    return any(w in txt.lower() for w in ["captcha", "i'm not a robot", "human verification"])

def detect_email_verify(page):
    """Return True if email verification is blocking progress."""
    txt = ""
    try:
        txt = page.inner_text("body")[:3000]
    except:
        pass
    keywords = ["verify your email", "verification email", "check your email",
                "confirm your email", "email confirmation", "activate your account",
                "sent you an email", "check inbox"]
    return any(k.lower() in txt.lower() for k in keywords)

def get_page_text(page):
    try:
        return page.inner_text("body")
    except:
        return ""

# ── MAIN ───────────────────────────────────────────────────────────────────────
def main():
    result = {
        "company": "BCG (Boston Consulting Group)",
        "role": "Talent Senior Specialist - People",
        "ats": "Workday",
        "status": "in_progress",
        "confirmed_at": None,
        "screenshot": None,
        "account_email": EMAIL,
        "notes": "",
        "job_url": None
    }

    print("=" * 70)
    print("BCG Workday Submission Agent")
    print("=" * 70)

    # Step 1: Launch dedicated Chrome
    print("\n[1] Launching dedicated Chrome on port", PORT)
    proc = subprocess.Popen(
        [CHROME, f"--remote-debugging-port={PORT}",
         f"--user-data-dir={PROFILE}",
         "--no-first-run", "--no-default-browser-check",
         "--disable-blink-features=AutomationControlled",
         BCG_CAREERS_SEARCH],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    print(f"  Chrome PID: {proc.pid}, waiting 8s for startup...")
    time.sleep(8)

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(f"http://localhost:{PORT}")
        ctx = browser.contexts[0]
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.set_default_timeout(30000)
        print(f"  Connected to Chrome. URL: {page.url}")

        try:
            # Step 2: Find the BCG job posting
            print("\n[2] Finding BCG Talent Senior Specialist job posting...")
            page.wait_for_load_state("networkidle", timeout=20000)
            time.sleep(3)
            shot(page, "01_careers_search")

            page_text = get_page_text(page)
            job_url = None

            # Look for the role in search results
            for link_text in ["Talent Senior Specialist", "Senior Specialist - People", "People"]:
                try:
                    links = page.locator(f"a:has-text('{link_text}')").all()
                    for link in links:
                        href = link.get_attribute("href") or ""
                        lbl = link.inner_text()
                        if "talent" in lbl.lower() or "specialist" in lbl.lower() or "people" in lbl.lower():
                            if "seattle" in page_text[max(0, page_text.find(lbl)-200):page_text.find(lbl)+200].lower() or True:
                                job_url = href if href.startswith("http") else BCG_CAREERS_BASE + href
                                print(f"  Found job link: {lbl[:80]} → {job_url}")
                                break
                    if job_url:
                        break
                except:
                    continue

            # If not found via link text, try job listing cards
            if not job_url:
                try:
                    # BCG careers typically lists jobs as cards/rows
                    all_links = page.locator("a[href*='/jobs/']").all()
                    for link in all_links:
                        try:
                            txt = link.inner_text()
                            href = link.get_attribute("href") or ""
                            if "talent" in txt.lower() and ("specialist" in txt.lower() or "senior" in txt.lower()):
                                job_url = href if href.startswith("http") else BCG_CAREERS_BASE + href
                                print(f"  Found via /jobs/ link: {txt[:80]} → {job_url}")
                                break
                        except:
                            continue
                except:
                    pass

            if not job_url:
                # Try direct BCG Workday search
                print("  Not found in initial search, trying direct Workday tenant search...")
                # BCG uses wd5.myworkdayjobs.com
                direct_urls = [
                    "https://bcg.wd5.myworkdayjobs.com/BCG_Careers?q=Talent+Senior+Specialist",
                    "https://bcg.wd3.myworkdayjobs.com/BCG_Careers?q=Talent+Senior+Specialist",
                    "https://careers.bcg.com/search?q=Talent+Senior+Specialist+People&location=Seattle%2C+WA"
                ]
                for url in direct_urls:
                    try:
                        page.goto(url, timeout=20000, wait_until="domcontentloaded")
                        time.sleep(4)
                        all_links = page.locator("a[href*='/job/'], a[href*='/apply/'], a[href*='workdayjobs.com']").all()
                        for link in all_links:
                            try:
                                txt = link.inner_text()
                                href = link.get_attribute("href") or ""
                                if "talent" in txt.lower() and ("specialist" in txt.lower() or "people" in txt.lower()):
                                    job_url = href if href.startswith("http") else url + href
                                    print(f"  Found via WD search: {txt[:80]}")
                                    break
                            except:
                                continue
                        if job_url:
                            break
                    except Exception as e:
                        print(f"  Direct URL failed: {url}: {e}")

            if not job_url:
                # Try the most likely BCG Workday URL pattern for this role
                print("  Trying known BCG Workday URL patterns...")
                page.goto("https://bcg.wd5.myworkdayjobs.com/BCG_Careers", timeout=20000, wait_until="domcontentloaded")
                time.sleep(5)
                shot(page, "02_wd_careers_page")
                page_text = get_page_text(page)

                # Search within Workday UI
                search_input_sels = [
                    "[data-automation-id='searchBox'] input",
                    "input[data-automation-id='searchBox']",
                    "input[placeholder*='Search']",
                    "input[placeholder*='search']",
                    "input[aria-label*='Search']",
                    "#searchBox",
                ]
                searched = False
                for sel in search_input_sels:
                    try:
                        if page.locator(sel).count() > 0:
                            page.locator(sel).first.fill("Talent Senior Specialist")
                            time.sleep(1)
                            page.keyboard.press("Enter")
                            time.sleep(4)
                            searched = True
                            print(f"  Searched WD using: {sel}")
                            break
                    except:
                        continue

                if searched:
                    shot(page, "03_wd_search_results")
                    # Look for the role in results
                    all_links = page.locator("a[data-automation-id='jobTitle'], a[href*='apply']").all()
                    for link in all_links:
                        try:
                            txt = link.inner_text()
                            href = link.get_attribute("href") or ""
                            if "talent" in txt.lower() or "specialist" in txt.lower():
                                job_url = href if href.startswith("http") else "https://bcg.wd5.myworkdayjobs.com" + href
                                print(f"  Found in WD search: {txt[:80]}")
                                break
                        except:
                            continue

            if not job_url:
                # Last resort: check current page for the role
                print("  Checking current page for matching job...")
                page_text = get_page_text(page)
                if "talent" in page_text.lower() and "specialist" in page_text.lower():
                    # Try to find any apply link
                    for link in page.locator("a").all():
                        try:
                            href = link.get_attribute("href") or ""
                            txt = link.inner_text()
                            if "talent" in txt.lower() and "specialist" in txt.lower():
                                job_url = href if href.startswith("http") else "https://bcg.wd5.myworkdayjobs.com" + href
                                break
                        except:
                            continue

            if not job_url:
                result["status"] = "blocked"
                result["notes"] = "Could not find the BCG Talent Senior Specialist job posting on careers.bcg.com or BCG Workday. The role may have been filled or the URL structure changed."
                print("\n[BLOCKED] Job posting not found. Saving result.")
                shot(page, "99_job_not_found")
                browser.close()
                _save_result(result)
                return result

            result["job_url"] = job_url
            print(f"\n  Job URL: {job_url}")

            # Step 3: Navigate to the job posting
            print("\n[3] Navigating to job posting...")
            page.goto(job_url, timeout=30000, wait_until="domcontentloaded")
            time.sleep(5)
            shot(page, "04_job_posting")
            page_text = get_page_text(page)
            print(f"  Page title snippet: {page_text[:200]}")

            # Step 4: Click Apply
            print("\n[4] Clicking Apply button...")
            apply_clicked = False
            for sel in [
                "a:has-text('Apply')", "button:has-text('Apply')",
                "[data-automation-id='applyButton']",
                "[data-automation-id='Apply']",
                "button[aria-label*='Apply']",
                "a[href*='apply']",
                ".apply-button", "#apply-button",
            ]:
                try:
                    el = page.locator(sel).first
                    if el.count() > 0 and el.is_visible(timeout=3000):
                        el.click()
                        time.sleep(4)
                        apply_clicked = True
                        print(f"  Apply clicked via: {sel}")
                        break
                except:
                    continue

            if not apply_clicked:
                # Try get_by_role
                try:
                    page.get_by_role("link", name="Apply", exact=False).first.click()
                    time.sleep(4)
                    apply_clicked = True
                    print("  Apply clicked via role=link")
                except:
                    pass

            if not apply_clicked:
                print("  Apply button not found on JD page, checking if already on apply flow...")

            shot(page, "05_after_apply_click")
            page_text = get_page_text(page)

            # Check for "Apply Manually" vs "Use Last Application"
            if "last application" in page_text.lower() or "use my last" in page_text.lower():
                print("  'Use Last Application' dialog detected — clicking Apply Manually...")
                for lbl in ["Apply Manually", "Manual", "Apply manually"]:
                    try:
                        el = page.get_by_text(lbl, exact=False).first
                        if el.count() > 0:
                            el.click()
                            time.sleep(3)
                            print(f"  Clicked: {lbl}")
                            break
                    except:
                        continue
                shot(page, "05b_apply_manually")

            # Step 5: Account creation / login
            print("\n[5] Handling account creation / login...")
            time.sleep(3)
            page_text = get_page_text(page)
            shot(page, "06_account_page")

            # Check if we're on a sign-in/create account page
            is_account_page = any(w in page_text.lower() for w in [
                "sign in", "create account", "email address", "password",
                "log in", "register", "account"
            ])

            if is_account_page:
                # Try to reveal signup form first
                print("  Account page detected. Looking for Create Account option...")
                for sel in [
                    "[data-automation-id='createAccountLink']",
                    "[data-automation-id='createAccount']",
                    "button:has-text('Create Account')",
                    "a:has-text('Create Account')",
                    "button:has-text('Sign Up')",
                    "[data-automation-id='toggleCreateAccount']",
                ]:
                    try:
                        el = page.locator(sel).first
                        if el.count() > 0 and el.is_visible(timeout=3000):
                            el.click()
                            time.sleep(2)
                            print(f"  Clicked create account toggle: {sel}")
                            break
                    except:
                        continue

                time.sleep(2)
                shot(page, "06b_signup_form")
                page_text = get_page_text(page)

                # Check if email verify is blocking
                if detect_email_verify(page):
                    print("  EMAIL-VERIFY gate detected!")
                    result["status"] = "email-verify-staged"
                    result["notes"] = "Workday sent an email verification to jamiecheng0103@gmail.com. Open the email and click the verification link, then complete the application manually on port 9402."
                    shot(page, "99_email_verify_gate")
                    browser.close()
                    _save_result(result)
                    return result

                # Fill signup fields
                print("  Filling signup fields...")

                # Email field
                email_filled = False
                for sel in [
                    "input[data-automation-id='email']",
                    "[data-automation-id='email'] input",
                    "input[type='email']",
                    "input[name='email']",
                    "input[placeholder*='Email']",
                    "input[placeholder*='email']",
                ]:
                    if fill_field(page, sel, EMAIL, "email"):
                        email_filled = True
                        break

                if not email_filled:
                    print("  Warning: could not find email field")

                # Password field
                pw_filled = False
                for sel in [
                    "input[data-automation-id='password']",
                    "[data-automation-id='password'] input",
                    "input[type='password'][data-automation-id*='password']:not([data-automation-id*='verify']):not([data-automation-id*='confirm'])",
                    "input[name='password']",
                    "(//input[@type='password'])[1]",
                ]:
                    if fill_field(page, sel, PW, "password"):
                        pw_filled = True
                        break

                if not pw_filled:
                    # Try by index - first password field
                    try:
                        pw_fields = page.locator("input[type='password']").all()
                        if pw_fields:
                            pw_fields[0].fill(PW)
                            print("  [fill] password via index[0]")
                            pw_filled = True
                    except:
                        pass

                # Verify password field
                verify_filled = False
                for sel in [
                    "input[data-automation-id='verifyPassword']",
                    "[data-automation-id='verifyPassword'] input",
                    "input[data-automation-id='confirmPassword']",
                    "[data-automation-id='confirmPassword'] input",
                ]:
                    if fill_field(page, sel, PW, "verify_password"):
                        verify_filled = True
                        break

                if not verify_filled:
                    # Try second password field
                    try:
                        pw_fields = page.locator("input[type='password']").all()
                        if len(pw_fields) >= 2:
                            pw_fields[1].fill(PW)
                            print("  [fill] verify_password via index[1]")
                            verify_filled = True
                    except:
                        pass

                # Tick "I agree" checkbox if present
                for cb_sel in [
                    "[data-automation-id='createAccountCheckbox']",
                    "input[type='checkbox'][data-automation-id*='account']",
                    "input[type='checkbox'][data-automation-id*='agree']",
                    "input[type='checkbox'][data-automation-id*='terms']",
                ]:
                    try:
                        cb = page.locator(cb_sel).first
                        if cb.count() > 0 and cb.is_visible(timeout=2000) and not cb.is_checked():
                            cb.check()
                            print(f"  [checkbox] checked: {cb_sel}")
                            break
                    except:
                        continue

                shot(page, "06c_signup_filled")

                # Check for captcha before submitting
                if detect_captcha(page):
                    print("  CAPTCHA detected on signup form!")
                    result["status"] = "captcha-staged"
                    result["notes"] = "CAPTCHA on Workday account creation page. Form is filled: email, password, verify. Human: solve CAPTCHA then click Create Account."
                    shot(page, "99_captcha_signup")
                    browser.close()
                    _save_result(result)
                    return result

                # Click Create Account / Submit button
                print("  Submitting account creation...")
                account_submitted = False
                for sel in [
                    "button[data-automation-id='createAccountButton']",
                    "button[data-automation-id='signIn']",
                    "button:has-text('Create Account')",
                    "button:has-text('Sign Up')",
                    "[role='button']:has-text('Create Account')",
                    "button[type='submit']",
                ]:
                    try:
                        el = page.locator(sel).first
                        if el.count() > 0 and el.is_visible(timeout=3000):
                            el.click()
                            time.sleep(4)
                            account_submitted = True
                            print(f"  [submit] account via: {sel}")
                            break
                    except:
                        continue

                time.sleep(5)
                shot(page, "07_after_account_submit")
                page_text = get_page_text(page)

                # Check results
                if detect_email_verify(page):
                    print("  EMAIL-VERIFY required after account creation!")
                    result["status"] = "email-verify-staged"
                    result["notes"] = "Workday account created — email verification sent to jamiecheng0103@gmail.com. Human: click verification link in email, then complete application."
                    browser.close()
                    _save_result(result)
                    return result

                if detect_captcha(page):
                    print("  CAPTCHA after account submit!")
                    result["status"] = "captcha-staged"
                    result["notes"] = "CAPTCHA appeared after account creation form submission. Human: solve CAPTCHA to proceed."
                    shot(page, "99_captcha_post_signup")
                    browser.close()
                    _save_result(result)
                    return result

                print(f"  After account submit — page snippet: {page_text[:300]}")

            else:
                print("  No account page detected — may already be in application flow.")

            # Step 6: Navigate through the Workday wizard
            print("\n[6] Starting Workday application wizard...")
            time.sleep(3)
            page_text = get_page_text(page)
            shot(page, "08_wizard_start")

            # ── MY INFORMATION page ──
            print("\n  [Wizard] My Information page...")
            time.sleep(2)
            page_text = get_page_text(page)

            # Handle "My Information" if present
            if "my information" in page_text.lower() or "personal information" in page_text.lower() or "name" in page_text.lower():
                print("  Filling My Information...")

                # First name
                for sel in [
                    "[data-automation-id='legalNameSection_firstName'] input",
                    "input[data-automation-id='firstName']",
                    "input[aria-label*='First Name']",
                    "input[placeholder*='First']",
                    "input[name='firstName']",
                ]:
                    if fill_field(page, sel, "Yi-Chieh", "first_name"):
                        break

                # Last name
                for sel in [
                    "[data-automation-id='legalNameSection_lastName'] input",
                    "input[data-automation-id='lastName']",
                    "input[aria-label*='Last Name']",
                    "input[placeholder*='Last']",
                    "input[name='lastName']",
                ]:
                    if fill_field(page, sel, "Cheng", "last_name"):
                        break

                # Email
                for sel in [
                    "[data-automation-id='email'] input",
                    "input[data-automation-id='email']",
                    "input[type='email']",
                ]:
                    try:
                        el = page.locator(sel).first
                        if el.count() > 0 and el.is_visible(timeout=2000):
                            current = el.input_value()
                            if current != EMAIL:
                                fill_field(page, sel, EMAIL, "email")
                            else:
                                print(f"  [fill] email already correct")
                            break
                    except:
                        continue

                # Phone
                for sel in [
                    "[data-automation-id='phone-number'] input",
                    "input[data-automation-id='phone']",
                    "input[type='tel']",
                    "input[aria-label*='Phone']",
                    "input[placeholder*='Phone']",
                ]:
                    if fill_field(page, sel, "2137003831", "phone"):
                        break

                # Address
                for sel in [
                    "[data-automation-id='addressSection_addressLine1'] input",
                    "input[data-automation-id='addressLine1']",
                    "input[aria-label*='Address']",
                    "input[placeholder*='Address']",
                ]:
                    if fill_field(page, sel, "1784 NW Northrup Street", "address_line1"):
                        break

                # City
                for sel in [
                    "[data-automation-id='addressSection_city'] input",
                    "input[data-automation-id='city']",
                    "input[aria-label*='City']",
                    "input[placeholder*='City']",
                ]:
                    if fill_field(page, sel, "Portland", "city"):
                        break

                # State / region
                for sel in [
                    "[data-automation-id='addressSection_countryRegion'] input",
                    "input[data-automation-id='stateField']",
                    "select[data-automation-id='addressSection_countryRegion']",
                    "select[data-automation-id='state']",
                ]:
                    try:
                        el = page.locator(sel).first
                        if el.count() > 0:
                            tag = el.evaluate("el => el.tagName.toLowerCase()")
                            if tag == "select":
                                select_option(page, sel, "Oregon", "state")
                            else:
                                fill_field(page, sel, "Oregon", "state")
                            break
                    except:
                        continue

                # Zip
                for sel in [
                    "[data-automation-id='addressSection_postalCode'] input",
                    "input[data-automation-id='postalCode']",
                    "input[aria-label*='Zip']",
                    "input[placeholder*='Zip']",
                    "input[aria-label*='Postal']",
                ]:
                    if fill_field(page, sel, "97209", "zip"):
                        break

                shot(page, "09_my_information_filled")
                wd_next(page)
                time.sleep(3)
                shot(page, "10_after_my_information")

            # ── WORK AUTHORIZATION / SPONSORSHIP ──
            page_text = get_page_text(page)
            if any(w in page_text.lower() for w in ["authorized", "sponsorship", "work authorization", "work auth"]):
                print("\n  [Wizard] Work Authorization page...")

                # Are you currently authorized to work in the US? → Yes
                click_radio_by_label(page, "authorized", "Yes")
                time.sleep(0.5)

                # Will you now or in the future require sponsorship? → Yes
                click_radio_by_label(page, "sponsor", "Yes")
                time.sleep(0.5)

                # Also try by question text
                for q_text in ["authorized to work", "sponsorship"]:
                    for ans in ["Yes"]:
                        try:
                            script = f"""
                            (function() {{
                                const all = document.querySelectorAll('[data-automation-id]');
                                for (const el of all) {{
                                    if (el.textContent.toLowerCase().includes('{q_text}')) {{
                                        const radios = el.querySelectorAll('input[type="radio"]');
                                        for (const r of radios) {{
                                            const lbl = r.closest('label') || document.querySelector('label[for="'+r.id+'"]');
                                            if (lbl && lbl.textContent.trim().toLowerCase() === 'yes') {{
                                                r.click(); return 'clicked:' + '{q_text}';
                                            }}
                                        }}
                                    }}
                                }}
                                return null;
                            }})()
                            """
                            result_val = page.evaluate(script)
                            if result_val:
                                print(f"  [workauth] JS click for '{q_text}': {result_val}")
                        except:
                            pass

                shot(page, "11_work_auth_filled")
                wd_next(page)
                time.sleep(3)
                shot(page, "12_after_work_auth")

            # ── MY EXPERIENCE page ──
            page_text = get_page_text(page)
            if any(w in page_text.lower() for w in ["experience", "resume", "upload", "cv"]):
                print("\n  [Wizard] My Experience / Resume upload page...")

                # Upload resume
                print("  Uploading resume...")
                resume_uploaded = False
                for sel in [
                    "input[type='file'][data-automation-id*='resumeFile']",
                    "input[type='file'][data-automation-id*='resume']",
                    "input[type='file'][data-automation-id*='Resume']",
                    "input[type='file']",
                ]:
                    try:
                        file_inputs = page.locator(sel).all()
                        if file_inputs:
                            file_inputs[0].set_input_files(RESUME)
                            time.sleep(4)
                            resume_uploaded = True
                            print(f"  [upload] resume via: {sel}")
                            break
                    except Exception as e:
                        print(f"  [upload try] {sel}: {str(e)[:50]}")
                        continue

                if resume_uploaded:
                    # Dismiss autofill dialog if it appears
                    time.sleep(3)
                    for no_lbl in ["No, thanks", "No Thanks", "Manual Entry", "Skip", "Dismiss", "Enter Manually"]:
                        try:
                            el = page.get_by_text(no_lbl, exact=False).first
                            if el.count() > 0 and el.is_visible(timeout=2000):
                                el.click()
                                print(f"  [dismiss-autofill] {no_lbl}")
                                time.sleep(2)
                                break
                        except:
                            continue

                    shot(page, "13_resume_uploaded")

                # If resume wasn't uploaded, try the + button or drag-drop area
                if not resume_uploaded:
                    print("  Trying alternative upload methods...")
                    for sel in [
                        "[data-automation-id='file-upload-drop-zone']",
                        ".resume-upload-area",
                        "[data-automation-id='resumeupload']",
                        "button:has-text('Upload')",
                        "label:has-text('Upload')",
                    ]:
                        try:
                            with page.expect_file_chooser() as fc_info:
                                page.locator(sel).first.click(timeout=5000)
                            fc = fc_info.value
                            fc.set_files(RESUME)
                            time.sleep(4)
                            resume_uploaded = True
                            print(f"  [upload-chooser] via: {sel}")
                            break
                        except:
                            continue

                    if resume_uploaded:
                        time.sleep(2)
                        for no_lbl in ["No, thanks", "No Thanks", "Skip", "Manual Entry"]:
                            try:
                                el = page.get_by_text(no_lbl, exact=False).first
                                if el.count() > 0 and el.is_visible(timeout=2000):
                                    el.click()
                                    time.sleep(2)
                                    break
                            except:
                                continue
                        shot(page, "13b_resume_uploaded_alt")

                # Fill/correct experience fields after resume parse
                time.sleep(3)
                page_text = get_page_text(page)

                # Work history corrections
                work_entries = [
                    {
                        "company": "Organization Development Network (ODN) Oregon",
                        "title": "Consultant, Organization & Talent Development",
                        "start": "08/2025",
                        "end": "Present",
                        "current": True,
                    },
                    {
                        "company": "InGenius Prep",
                        "title": "Program Enablement Manager",
                        "start": "09/2023",
                        "end": "Present",
                        "current": True,
                    },
                    {
                        "company": "NextGen Healthcare",
                        "title": "Organizational Development Intern",
                        "start": "01/2023",
                        "end": "05/2023",
                        "current": False,
                    },
                    {
                        "company": "Vestas Wind Systems",
                        "title": "HR Business Partner Assistant",
                        "start": "02/2022",
                        "end": "10/2022",
                        "current": False,
                    },
                    {
                        "company": "Kronos Research",
                        "title": "HR Intern",
                        "start": "01/2021",
                        "end": "08/2021",
                        "current": False,
                    },
                ]

                # Look for parsed job titles that may be wrong and correct them
                parsed_titles = page.locator("[data-automation-id='jobTitle'] input, input[data-automation-id*='title']").all()
                for i, el in enumerate(parsed_titles):
                    try:
                        current_val = el.input_value()
                        if i < len(work_entries):
                            correct = work_entries[i]["title"]
                            if current_val != correct and current_val.strip():
                                print(f"  [correct-title] was: {current_val} → {correct}")
                                el.triple_click()
                                el.fill(correct)
                    except:
                        pass

                shot(page, "14_experience_page")
                wd_next(page)
                time.sleep(3)
                shot(page, "15_after_experience")

            # ── APPLICATION QUESTIONS ──
            print("\n  [Wizard] Application Questions page...")
            time.sleep(3)
            page_text = get_page_text(page)
            shot(page, "16_questions_page")

            if any(w in page_text.lower() for w in ["question", "sponsorship", "salary", "authorized", "hear about"]):

                # Work authorization: authorized in US → Yes
                if "authorized" in page_text.lower():
                    click_radio_by_label(page, "authorized to work", "Yes")
                    time.sleep(0.5)

                # Sponsorship required → Yes
                if "sponsor" in page_text.lower():
                    click_radio_by_label(page, "sponsor", "Yes")
                    time.sleep(0.5)

                    # Also try select dropdowns for sponsorship
                    for sel in [
                        "select[data-automation-id*='sponsor']",
                        "[data-automation-id*='sponsor'] select",
                    ]:
                        try:
                            el = page.locator(sel).first
                            if el.count() > 0:
                                select_option(page, sel, "Yes", "sponsorship_select")
                                break
                        except:
                            pass

                # Salary expectation
                if "salary" in page_text.lower():
                    for sel in [
                        "input[data-automation-id*='salary']",
                        "input[aria-label*='salary' i]",
                        "input[placeholder*='salary' i]",
                        "input[placeholder*='Salary' i]",
                    ]:
                        if fill_field(page, sel, "115000", "salary"):
                            break

                # "How did you hear about us" → LinkedIn
                if "hear" in page_text.lower() or "source" in page_text.lower():
                    for sel in [
                        "select[data-automation-id*='source']",
                        "select[data-automation-id*='hear']",
                        "[data-automation-id*='referral'] select",
                        "select[aria-label*='hear' i]",
                    ]:
                        if select_option(page, sel, "LinkedIn", "how_hear"):
                            break
                        # Try "Social Media" as fallback
                        select_option(page, sel, "Social Media", "how_hear_fallback")

                    # Also try dropdown/typeahead version
                    for sel in [
                        "input[data-automation-id*='source']",
                        "input[data-automation-id*='hear']",
                    ]:
                        try:
                            el = page.locator(sel).first
                            if el.count() > 0:
                                el.fill("LinkedIn")
                                time.sleep(1)
                                # Click the first matching option
                                opt = page.locator("[data-automation-id='promptOption']").first
                                if opt.count() > 0:
                                    opt.click()
                                    print("  [typeahead] hear about: LinkedIn")
                                break
                        except:
                            pass

                # Years of experience (if asked)
                if "years" in page_text.lower() and "experience" in page_text.lower():
                    for sel in [
                        "select[data-automation-id*='years']",
                        "select[aria-label*='years' i]",
                    ]:
                        # Try 3 years or "3-5 years" option
                        for val in ["3", "3-5", "2-4", "3-5 years", "Less than 5"]:
                            try:
                                page.select_option(sel, label=val, timeout=2000)
                                print(f"  [select] YOE = {val}")
                                break
                            except:
                                continue

                shot(page, "17_questions_filled")
                wd_next(page)
                time.sleep(3)
                shot(page, "18_after_questions")

            # ── VOLUNTARY DISCLOSURES / DEMOGRAPHICS ──
            page_text = get_page_text(page)
            if any(w in page_text.lower() for w in ["voluntary", "self-identification", "gender", "ethnicity", "race", "veteran", "disability"]):
                print("\n  [Wizard] Voluntary Disclosures / Demographics page...")

                # Gender → Female / Woman
                for sel in [
                    "select[data-automation-id*='gender']",
                    "select[aria-label*='gender' i]",
                    "[data-automation-id*='gender'] select",
                ]:
                    for val in ["Female", "Woman", "F"]:
                        try:
                            page.select_option(sel, label=val, timeout=2000)
                            print(f"  [demog] gender = {val}")
                            break
                        except:
                            continue
                    # Try radio
                    click_radio_by_label(page, "gender", "Female")

                # Race/Ethnicity → Asian
                for sel in [
                    "select[data-automation-id*='ethnicity']",
                    "select[data-automation-id*='race']",
                    "select[aria-label*='race' i]",
                    "[data-automation-id*='race'] select",
                    "[data-automation-id*='ethnicity'] select",
                ]:
                    for val in ["Asian", "Asian (Not Hispanic or Latino)"]:
                        try:
                            page.select_option(sel, label=val, timeout=2000)
                            print(f"  [demog] race = {val}")
                            break
                        except:
                            continue

                # Hispanic/Latino → No
                for sel in [
                    "select[data-automation-id*='hispanic']",
                    "[data-automation-id*='hispanic'] select",
                    "select[aria-label*='hispanic' i]",
                ]:
                    for val in ["No", "I am not Hispanic or Latino", "Not Hispanic"]:
                        try:
                            page.select_option(sel, label=val, timeout=2000)
                            print(f"  [demog] hispanic = {val}")
                            break
                        except:
                            continue
                    click_radio_by_label(page, "hispanic", "No")

                # Veteran → Not a protected veteran
                for sel in [
                    "select[data-automation-id*='veteran']",
                    "[data-automation-id*='veteran'] select",
                ]:
                    for val in ["I am not a protected veteran", "Not a protected veteran", "No", "I Don't Wish To Answer"]:
                        try:
                            page.select_option(sel, label=val, timeout=2000)
                            print(f"  [demog] veteran = {val}")
                            break
                        except:
                            continue

                # Disability → No disability
                for sel in [
                    "select[data-automation-id*='disability']",
                    "[data-automation-id*='disability'] select",
                ]:
                    for val in ["No, I Don't Have a Disability", "No disability", "No", "I Don't Wish To Answer"]:
                        try:
                            page.select_option(sel, label=val, timeout=2000)
                            print(f"  [demog] disability = {val}")
                            break
                        except:
                            continue

                shot(page, "19_demographics_filled")
                wd_next(page)
                time.sleep(3)
                shot(page, "20_after_demographics")

            # ── REVIEW PAGE ──
            print("\n  [Wizard] Looking for Review / Submit page...")
            max_steps = 10
            for step in range(max_steps):
                time.sleep(3)
                page_text = get_page_text(page)
                shot(page, f"21_wizard_step_{step}")

                # Check for submit button
                submit_found = False
                for sel in [
                    "[data-automation-id='bottom-navigation-btn-submit']",
                    "button[data-automation-id*='submit']",
                    "button:has-text('Submit')",
                    "[role='button']:has-text('Submit')",
                ]:
                    try:
                        el = page.locator(sel).first
                        if el.count() > 0 and el.is_visible(timeout=3000):
                            submit_found = True
                            print(f"  [SUBMIT] Found submit button: {sel}")

                            # Take final review screenshot
                            shot(page, "22_review_page_final")

                            # Check for CAPTCHA one last time
                            if detect_captcha(page):
                                print("  CAPTCHA on review/submit page!")
                                result["status"] = "captcha-staged"
                                result["notes"] = "CAPTCHA on Workday review/submit page. Everything is filled. Human: solve CAPTCHA then click Submit."
                                shot(page, "99_captcha_submit")
                                browser.close()
                                _save_result(result)
                                return result

                            # SUBMIT
                            print("  Clicking Submit button...")
                            el.click()
                            time.sleep(8)
                            page.wait_for_load_state("networkidle", timeout=20000)

                            # Confirmation page
                            page_text = get_page_text(page)
                            shot(page, "23_confirmation")
                            print(f"  Post-submit page: {page_text[:400]}")

                            # Detect confirmation
                            confirmation_keywords = [
                                "thank you", "application submitted", "successfully submitted",
                                "application has been received", "we have received",
                                "confirmation", "application complete"
                            ]
                            if any(k.lower() in page_text.lower() for k in confirmation_keywords):
                                print("\n  ✓ SUBMISSION CONFIRMED!")
                                result["status"] = "submitted"
                                result["confirmed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                                result["screenshot"] = f"{SHOT}/23_confirmation.png"
                                result["notes"] = f"Successfully submitted. Confirmation page: {page_text[:300]}"
                            else:
                                # May still have submitted but no clear confirmation
                                print("  Submit clicked but no clear confirmation text found.")
                                result["status"] = "likely-submitted"
                                result["confirmed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                                result["screenshot"] = f"{SHOT}/23_confirmation.png"
                                result["notes"] = f"Submit button clicked, page changed but confirmation text unclear. Page: {page_text[:300]}"

                            browser.close()
                            _save_result(result)
                            return result
                    except:
                        continue

                if submit_found:
                    break

                # Check for captcha blocking
                if detect_captcha(page):
                    result["status"] = "captcha-staged"
                    result["notes"] = f"CAPTCHA at wizard step {step}. Form is filled up to this point. Human: solve CAPTCHA and continue."
                    shot(page, f"99_captcha_step_{step}")
                    browser.close()
                    _save_result(result)
                    return result

                if detect_email_verify(page):
                    result["status"] = "email-verify-staged"
                    result["notes"] = f"Email verification gate at wizard step {step}."
                    shot(page, f"99_email_verify_step_{step}")
                    browser.close()
                    _save_result(result)
                    return result

                # Try to advance to next page
                advanced = wd_next(page)
                if not advanced:
                    print(f"  No Next button found at step {step}, staying on page")
                    # Check page title to see where we are
                    print(f"  Current page text snippet: {page_text[:200]}")
                    if step > 3:
                        break

            # If we get here, we couldn't find the submit button
            result["status"] = "blocked"
            result["notes"] = "Could not locate Submit button after traversing Workday wizard. Manual intervention needed."
            shot(page, "99_submit_not_found")
            browser.close()
            _save_result(result)
            return result

        except Exception as e:
            tb = traceback.format_exc()
            print(f"\n[EXCEPTION] {e}\n{tb}")
            result["status"] = "error"
            result["notes"] = f"Unhandled exception: {str(e)}\n{tb[:500]}"
            try:
                shot(page, "99_exception")
            except:
                pass
            try:
                browser.close()
            except:
                pass
            _save_result(result)
            return result


def _save_result(result):
    """Save SUBMITTED.json to the BCG role folder."""
    out_path = ROLE_DIR + r"\SUBMITTED.json"
    try:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        print(f"\n[SAVED] {out_path}")
    except Exception as e:
        print(f"[SAVE ERROR] {e}")
    print("\n" + "=" * 70)
    print(f"FINAL RESULT: {result['status']}")
    print(f"Notes: {result.get('notes', '')[:200]}")
    print("=" * 70)


if __name__ == "__main__":
    main()
