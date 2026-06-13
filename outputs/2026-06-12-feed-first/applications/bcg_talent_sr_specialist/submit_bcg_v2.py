# -*- coding: utf-8 -*-
"""
submit_bcg_v2.py -- BCG "Talent Senior Specialist - People" Workday submission
v2: fix cookie banner dismiss, correct job URL detection, fix encoding issue.
"""
import os, sys, time, json, subprocess, traceback
# Force UTF-8 stdout on Windows
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

# BCG HR careers page (what loaded successfully) + direct WD search
BCG_HR_CAREERS = "https://careers.bcg.com/global/en/teams/human-resources"
BCG_WD_SEARCH = "https://bcg.wd5.myworkdayjobs.com/BCG_Careers?q=Talent+Senior+Specialist"


def shot(page, name):
    path = os.path.join(SHOT, name + ".png")
    try:
        page.screenshot(path=path, full_page=True)
        print(f"  [screenshot] {name}.png")
    except Exception as e:
        print(f"  [screenshot FAIL] {name}: {str(e)[:60]}")
    return path


def dismiss_cookie_banner(page):
    """Dismiss BCG cookie consent modal if present."""
    for sel in [
        "button:has-text('Accept All and Close')",
        "button:has-text('Accept All')",
        "button:has-text('Use Only Essential Cookies')",
        "button:has-text('Accept')",
        "[aria-label*='cookie'] button",
        ".cookie-banner button",
        "#cookie-banner button",
        "[data-testid='cookie-accept']",
    ]:
        try:
            el = page.locator(sel).first
            if el.count() > 0 and el.is_visible(timeout=2000):
                el.click()
                time.sleep(1)
                print(f"  [cookie] dismissed via: {sel}")
                return True
        except:
            continue
    return False


def wait_net(page, timeout=12000):
    try:
        page.wait_for_load_state("networkidle", timeout=timeout)
    except:
        pass


def fill_field(page, selector, value, label=""):
    try:
        el = page.locator(selector).first
        el.wait_for(state="visible", timeout=6000)
        el.click(timeout=3000)
        el.fill("", timeout=3000)
        el.fill(value, timeout=5000)
        print(f"  [fill] {label or selector[:50]} = {value[:40]}")
        return True
    except Exception as e:
        try:
            el = page.locator(selector).first
            el.triple_click(timeout=3000)
            el.type(value, delay=50)
            print(f"  [fill-type] {label or selector[:50]} = {value[:40]}")
            return True
        except:
            print(f"  [fill FAIL] {label or selector[:50]}: {str(e)[:50]}")
            return False


def select_opt(page, selector, values_to_try, label=""):
    for val in (values_to_try if isinstance(values_to_try, list) else [values_to_try]):
        for method in ["label", "value"]:
            try:
                if method == "label":
                    page.select_option(selector, label=val, timeout=3000)
                else:
                    page.select_option(selector, value=val, timeout=3000)
                print(f"  [select] {label or selector[:40]} = {val}")
                return True
            except:
                continue
    return False


def click_radio(page, question_frag, answer):
    """Click a radio button whose label contains answer, near a question fragment."""
    script = """
    (function(qfrag, ans) {
        var radios = Array.from(document.querySelectorAll('input[type="radio"]'));
        for (var r of radios) {
            var lbl = r.closest('label') || document.querySelector('label[for="'+r.id+'"]');
            if (!lbl) continue;
            if (lbl.textContent.trim().toLowerCase() === ans.toLowerCase()) {
                // check container has question
                var parent = r.closest('[data-automation-id], fieldset, [role="group"]');
                if (!parent || parent.textContent.toLowerCase().includes(qfrag.toLowerCase())) {
                    r.click(); return 'clicked';
                }
            }
        }
        // fallback: any radio whose label = answer
        for (var r of radios) {
            var lbl2 = r.closest('label') || document.querySelector('label[for="'+r.id+'"]');
            if (lbl2 && lbl2.textContent.trim().toLowerCase() === ans.toLowerCase()) {
                r.click(); return 'fallback';
            }
        }
        return null;
    })(arguments[0], arguments[1])
    """
    try:
        result = page.evaluate(script, question_frag, answer)
        print(f"  [radio] {question_frag[:40]} -> {answer}: {result}")
        return result is not None
    except Exception as e:
        print(f"  [radio FAIL] {e}")
        return False


def wd_next(page):
    """Click Next / Save and Continue on a Workday wizard page."""
    for aid in ['bottom-navigation-btn-next', 'bottom-navigation-btn-saveAndContinue',
                'nextButton', 'saveAndContinue']:
        try:
            el = page.locator(f"[data-automation-id='{aid}']").first
            if el.count() > 0 and el.is_visible(timeout=2000):
                el.click()
                time.sleep(3)
                wait_net(page, 10000)
                print(f"  [next] aid={aid}")
                return True
        except:
            continue
    for lbl in ["Save and Continue", "Next", "Continue", "Save"]:
        try:
            el = page.get_by_role("button", name=lbl, exact=False).first
            if el.count() > 0 and el.is_visible(timeout=2000):
                el.click()
                time.sleep(3)
                wait_net(page, 10000)
                print(f"  [next] text={lbl}")
                return True
        except:
            continue
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
        return any(k in txt for k in ["verify your email", "verification email", "check your email",
                                       "confirm your email", "activate your account", "sent you an email"])
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
    print(f"Notes:  {str(result.get('notes',''))[:200]}")
    print("=" * 60)


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

    print("=" * 60)
    print("BCG Workday v2 -- Talent Senior Specialist")
    print("=" * 60)

    # Kill any stale Chrome on port 9402
    try:
        subprocess.run(
            ["powershell", "-Command",
             f"Get-NetTCPConnection -LocalPort {PORT} -ErrorAction SilentlyContinue | "
             f"Select-Object -ExpandProperty OwningProcess | "
             f"ForEach-Object {{ Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }}"],
            capture_output=True, timeout=10
        )
        time.sleep(2)
    except:
        pass

    print(f"\n[1] Launching Chrome on port {PORT}...")
    proc = subprocess.Popen(
        [CHROME, f"--remote-debugging-port={PORT}",
         f"--user-data-dir={PROFILE}",
         "--no-first-run", "--no-default-browser-check",
         "--disable-blink-features=AutomationControlled",
         BCG_WD_SEARCH],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    print(f"  Chrome PID: {proc.pid}, waiting 8s...")
    time.sleep(8)

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(f"http://localhost:{PORT}")
        ctx = browser.contexts[0]
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.set_default_timeout(30000)
        print(f"  Connected. URL: {page.url}")

        try:
            # Wait for page
            wait_net(page, 20000)
            time.sleep(3)
            dismiss_cookie_banner(page)
            time.sleep(2)
            shot(page, "v2_01_wd_search_loaded")
            page_text = get_text(page)
            print(f"  Page text snippet: {page_text[:300]}")

            # Step 2: Find the job
            print("\n[2] Locating job posting...")
            job_url = None

            # Try Workday job listing links
            # Workday job links typically: /BCG_Careers/job/City/Title/Job-ID
            all_links = page.locator("a[href*='/job/']").all()
            print(f"  Found {len(all_links)} /job/ links")
            for lnk in all_links:
                try:
                    txt = lnk.inner_text().strip()
                    href = lnk.get_attribute("href") or ""
                    print(f"    Link: {txt[:80]} | {href[:80]}")
                    if any(w in txt.lower() for w in ["talent", "specialist", "people"]):
                        job_url = href if href.startswith("http") else "https://bcg.wd5.myworkdayjobs.com" + href
                        print(f"  --> Selected job: {txt[:80]}")
                        break
                except:
                    continue

            # Also check data-automation-id='jobTitle' links (Workday standard)
            if not job_url:
                for sel in [
                    "[data-automation-id='jobTitle']",
                    "[data-automation-id='jobTitle'] a",
                    ".css-19uc56f",  # Workday job title class
                ]:
                    try:
                        els = page.locator(sel).all()
                        for el in els:
                            txt = el.inner_text().strip()
                            if any(w in txt.lower() for w in ["talent", "specialist"]):
                                href = el.get_attribute("href") or ""
                                if not href:
                                    # Try parent anchor
                                    href = el.evaluate("el => el.closest('a')?.href || ''")
                                if href:
                                    job_url = href if href.startswith("http") else "https://bcg.wd5.myworkdayjobs.com" + href
                                    print(f"  --> Via {sel}: {txt[:60]}")
                                    break
                        if job_url:
                            break
                    except:
                        continue

            # If still not found, try searching within Workday UI
            if not job_url:
                print("  Trying Workday search box...")
                search_sels = [
                    "input[data-automation-id='searchBox']",
                    "[data-automation-id='searchBox'] input",
                    "input[placeholder*='Job title' i]",
                    "input[placeholder*='keyword' i]",
                    "input[aria-label*='Search' i]",
                ]
                for sel in search_sels:
                    try:
                        el = page.locator(sel).first
                        if el.count() > 0 and el.is_visible(timeout=3000):
                            el.fill("Talent Senior Specialist")
                            time.sleep(1)
                            page.keyboard.press("Enter")
                            time.sleep(5)
                            wait_net(page, 10000)
                            shot(page, "v2_02_wd_searched")

                            # Now look for the role
                            for job_sel in ["[data-automation-id='jobTitle'] a",
                                            "a[href*='/job/']"]:
                                job_els = page.locator(job_sel).all()
                                for je in job_els:
                                    try:
                                        txt = je.inner_text().strip()
                                        href = je.get_attribute("href") or ""
                                        if "talent" in txt.lower() or "specialist" in txt.lower():
                                            job_url = href if href.startswith("http") else "https://bcg.wd5.myworkdayjobs.com" + href
                                            print(f"  --> After search: {txt[:60]}")
                                            break
                                    except:
                                        continue
                                if job_url:
                                    break
                            if job_url:
                                break
                    except Exception as e:
                        print(f"  Search box {sel} failed: {str(e)[:50]}")
                        continue

            # Last resort: check the BCG HR page which showed job listings earlier
            if not job_url:
                print("  Trying BCG HR careers page as fallback...")
                page.goto(BCG_HR_CAREERS, timeout=20000, wait_until="domcontentloaded")
                time.sleep(5)
                dismiss_cookie_banner(page)
                time.sleep(2)
                wait_net(page, 10000)
                shot(page, "v2_03_hr_careers")

                # Look for job cards/links
                for sel in [
                    "a:has-text('Talent')",
                    "a:has-text('Senior Specialist')",
                    "a[href*='specialist' i]",
                    "a[href*='talent' i]",
                ]:
                    try:
                        els = page.locator(sel).all()
                        for el in els:
                            txt = el.inner_text().strip()
                            href = el.get_attribute("href") or ""
                            if href and ("specialist" in href.lower() or "talent" in href.lower()
                                         or "specialist" in txt.lower()):
                                job_url = href if href.startswith("http") else "https://careers.bcg.com" + href
                                print(f"  --> HR page link: {txt[:60]} | {href[:80]}")
                                break
                        if job_url:
                            break
                    except:
                        continue

                # Also look in the search jobs widget on HR page
                if not job_url:
                    all_page_links = page.locator("a").all()
                    for lnk in all_page_links:
                        try:
                            txt = lnk.inner_text().strip()
                            href = lnk.get_attribute("href") or ""
                            if ("talent" in txt.lower() and "specialist" in txt.lower()
                                    and href and "team" not in href.lower()):
                                job_url = href if href.startswith("http") else "https://careers.bcg.com" + href
                                print(f"  --> HR page (all): {txt[:60]} | {href[:80]}")
                                break
                        except:
                            continue

            # If we cannot find the job, log and bail
            if not job_url:
                print("\n  All job search strategies exhausted. Dumping all links found:")
                try:
                    all_links = page.locator("a").all()
                    for lnk in all_links[:50]:
                        try:
                            txt = lnk.inner_text().strip()
                            href = lnk.get_attribute("href") or ""
                            if href and txt:
                                print(f"    {txt[:60]} | {href[:80]}")
                        except:
                            pass
                except:
                    pass
                result["status"] = "blocked"
                result["notes"] = ("Job not found: BCG Talent Senior Specialist People role could not be "
                                   "located on careers.bcg.com or bcg.wd5.myworkdayjobs.com. "
                                   "The posting may be filled, delisted, or under a different title. "
                                   "Manual verification needed.")
                shot(page, "v2_99_job_not_found")
                browser.close()
                save_result(result)
                return result

            result["job_url"] = job_url
            print(f"\n  Job URL confirmed: {job_url}")

            # Step 3: Navigate to job
            print("\n[3] Loading job posting...")
            page.goto(job_url, timeout=30000, wait_until="domcontentloaded")
            time.sleep(5)
            dismiss_cookie_banner(page)
            time.sleep(2)
            wait_net(page, 15000)
            shot(page, "v2_04_job_posting")
            page_text = get_text(page)
            print(f"  Title/text: {page_text[:300]}")

            # Step 4: Click Apply
            print("\n[4] Clicking Apply...")
            apply_clicked = False
            for sel in [
                "[data-automation-id='applyButton']",
                "a[data-automation-id='applyButton']",
                "button[data-automation-id='applyButton']",
                "a:has-text('Apply Now')",
                "a:has-text('Apply')",
                "button:has-text('Apply Now')",
                "button:has-text('Apply')",
            ]:
                try:
                    el = page.locator(sel).first
                    if el.count() > 0 and el.is_visible(timeout=3000):
                        el.click()
                        time.sleep(5)
                        wait_net(page, 15000)
                        apply_clicked = True
                        print(f"  Apply via: {sel}")
                        break
                except:
                    continue

            shot(page, "v2_05_after_apply")
            page_text = get_text(page)

            # Handle "Apply Manually" dialog
            if any(p in page_text.lower() for p in ["last application", "use my last", "apply manually"]):
                print("  'Use Last Application' dialog -- clicking Apply Manually")
                for lbl in ["Apply Manually", "Apply manually", "Start a New Application"]:
                    try:
                        el = page.get_by_text(lbl, exact=False).first
                        if el.count() > 0 and el.is_visible(timeout=3000):
                            el.click()
                            time.sleep(3)
                            wait_net(page, 10000)
                            print(f"  Clicked: {lbl}")
                            break
                    except:
                        continue
                shot(page, "v2_05b_apply_manually")

            # Step 5: Account creation
            print("\n[5] Account creation / login...")
            time.sleep(3)
            page_text = get_text(page)
            shot(page, "v2_06_account_page")
            print(f"  Account page text: {page_text[:400]}")

            is_account_page = any(w in page_text.lower() for w in [
                "sign in", "create account", "create an account", "email", "password",
                "log in", "register"
            ])

            if is_account_page:
                print("  Account page -- revealing signup form...")
                for sel in [
                    "[data-automation-id='createAccountLink']",
                    "[data-automation-id='createAccount']",
                    "button:has-text('Create Account')",
                    "a:has-text('Create Account')",
                    "button:has-text('Sign Up')",
                    "[data-automation-id='toggleCreateAccount']",
                    "a:has-text('Sign Up')",
                ]:
                    try:
                        el = page.locator(sel).first
                        if el.count() > 0 and el.is_visible(timeout=3000):
                            el.click()
                            time.sleep(2)
                            print(f"  Toggle: {sel}")
                            break
                    except:
                        continue

                time.sleep(2)
                shot(page, "v2_06b_signup_form")

                if detect_email_verify(page):
                    result["status"] = "email-verify-staged"
                    result["notes"] = "Email verification gate on BCG Workday. Check jamiecheng0103@gmail.com for the link."
                    shot(page, "v2_99_email_verify")
                    browser.close()
                    save_result(result)
                    return result

                # Fill email
                for sel in ["input[data-automation-id='email']",
                             "[data-automation-id='email'] input",
                             "input[type='email']",
                             "input[name='email']",
                             "input[placeholder*='email' i]"]:
                    if fill_field(page, sel, EMAIL, "email"):
                        break

                # Fill password (first)
                pw_fields = page.locator("input[type='password']").all()
                if len(pw_fields) >= 1:
                    try:
                        pw_fields[0].fill(PW)
                        print("  [fill] password[0]")
                    except:
                        pass
                if len(pw_fields) >= 2:
                    try:
                        pw_fields[1].fill(PW)
                        print("  [fill] password[1] verify")
                    except:
                        pass

                # Also try by data-automation-id
                for sel in ["input[data-automation-id='password']",
                             "[data-automation-id='password'] input"]:
                    try:
                        el = page.locator(sel).first
                        if el.count() > 0 and not el.input_value():
                            el.fill(PW)
                            print(f"  [fill] pw via {sel}")
                    except:
                        pass
                for sel in ["input[data-automation-id='verifyPassword']",
                             "[data-automation-id='verifyPassword'] input"]:
                    try:
                        el = page.locator(sel).first
                        if el.count() > 0 and not el.input_value():
                            el.fill(PW)
                            print(f"  [fill] verify pw via {sel}")
                    except:
                        pass

                # Tick checkbox
                for cb in ["[data-automation-id='createAccountCheckbox']",
                            "input[type='checkbox']"]:
                    try:
                        el = page.locator(cb).first
                        if el.count() > 0 and el.is_visible(timeout=2000) and not el.is_checked():
                            el.check()
                            print(f"  [checkbox] {cb}")
                            break
                    except:
                        pass

                shot(page, "v2_06c_signup_filled")

                if detect_captcha(page):
                    result["status"] = "captcha-staged"
                    result["notes"] = "CAPTCHA on BCG Workday account creation. Form filled (email + password). Human: solve CAPTCHA then Create Account."
                    shot(page, "v2_99_captcha_signup")
                    browser.close()
                    save_result(result)
                    return result

                # Submit account
                print("  Submitting account creation...")
                for sel in ["button[data-automation-id='createAccountButton']",
                             "button:has-text('Create Account')",
                             "button:has-text('Sign Up')",
                             "button[type='submit']"]:
                    try:
                        el = page.locator(sel).first
                        if el.count() > 0 and el.is_visible(timeout=3000):
                            el.click()
                            time.sleep(5)
                            wait_net(page, 15000)
                            print(f"  Account submit: {sel}")
                            break
                    except:
                        continue

                time.sleep(5)
                shot(page, "v2_07_after_account")
                page_text = get_text(page)

                if detect_email_verify(page):
                    result["status"] = "email-verify-staged"
                    result["notes"] = "BCG Workday sent email verification to jamiecheng0103@gmail.com. Click the link in the email, then complete the application."
                    shot(page, "v2_99_email_verify_post")
                    browser.close()
                    save_result(result)
                    return result

                if detect_captcha(page):
                    result["status"] = "captcha-staged"
                    result["notes"] = "CAPTCHA post account creation. Human: solve and continue."
                    shot(page, "v2_99_captcha_post")
                    browser.close()
                    save_result(result)
                    return result

                print(f"  Post-account text: {page_text[:300]}")

            # Step 6: Workday wizard
            print("\n[6] Workday application wizard...")
            time.sleep(3)

            # Walk up to 15 wizard pages
            for wizard_page in range(15):
                time.sleep(3)
                page_text = get_text(page)
                shot(page, f"v2_wizard_{wizard_page:02d}")
                print(f"\n  [Wizard step {wizard_page}] URL: {page.url[:80]}")
                print(f"  Text: {page_text[:200]}")

                # === Check for SUBMIT button first ===
                submit_sel = None
                for sel in [
                    "[data-automation-id='bottom-navigation-btn-submit']",
                    "button[data-automation-id*='submit']",
                    "button:has-text('Submit')",
                ]:
                    try:
                        el = page.locator(sel).first
                        if el.count() > 0 and el.is_visible(timeout=3000):
                            submit_sel = sel
                            break
                    except:
                        continue

                if submit_sel:
                    print(f"  SUBMIT button found: {submit_sel}")
                    shot(page, "v2_review_page")

                    if detect_captcha(page):
                        result["status"] = "captcha-staged"
                        result["notes"] = "CAPTCHA on BCG Workday review/submit page. All fields filled. Human: solve CAPTCHA and Submit."
                        shot(page, "v2_99_captcha_review")
                        browser.close()
                        save_result(result)
                        return result

                    print("  Clicking Submit...")
                    el = page.locator(submit_sel).first
                    el.click()
                    time.sleep(8)
                    wait_net(page, 20000)
                    page_text = get_text(page)
                    shot(page, "v2_confirmation")
                    print(f"  Post-submit: {page_text[:400]}")

                    if any(k in page_text.lower() for k in ["thank you", "submitted", "received",
                                                              "confirmation", "application complete"]):
                        print("  CONFIRMED SUBMISSION!")
                        result["status"] = "submitted"
                        result["confirmed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                        result["screenshot"] = os.path.join(SHOT, "v2_confirmation.png")
                        result["notes"] = f"Submitted. Confirmation: {page_text[:300]}"
                    else:
                        print("  Submit clicked, unclear confirmation.")
                        result["status"] = "likely-submitted"
                        result["confirmed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                        result["screenshot"] = os.path.join(SHOT, "v2_confirmation.png")
                        result["notes"] = f"Submit clicked, post-submit page: {page_text[:300]}"

                    browser.close()
                    save_result(result)
                    return result

                # === No submit yet. Fill current wizard section. ===

                # --- MY INFORMATION / PERSONAL ---
                if any(w in page_text.lower() for w in
                       ["first name", "last name", "legal name", "my information", "personal information"]):
                    print("  Filling personal info section...")
                    for sel, val, lbl in [
                        ("[data-automation-id='legalNameSection_firstName'] input", "Yi-Chieh", "first_name"),
                        ("input[data-automation-id='firstName']", "Yi-Chieh", "first_name"),
                        ("[data-automation-id='legalNameSection_lastName'] input", "Cheng", "last_name"),
                        ("input[data-automation-id='lastName']", "Cheng", "last_name"),
                    ]:
                        try:
                            el = page.locator(sel).first
                            if el.count() > 0 and el.is_visible(timeout=2000):
                                current = el.input_value()
                                if not current or current.strip() == "":
                                    fill_field(page, sel, val, lbl)
                                else:
                                    print(f"  [skip-fill] {lbl} already = {current}")
                        except:
                            pass

                    # Phone
                    for sel in ["[data-automation-id='phone-number'] input",
                                 "input[data-automation-id='phone']",
                                 "input[type='tel']",
                                 "input[aria-label*='Phone' i]"]:
                        try:
                            el = page.locator(sel).first
                            if el.count() > 0:
                                fill_field(page, sel, "2137003831", "phone")
                                break
                        except:
                            pass

                    # Address
                    for sel in ["[data-automation-id='addressSection_addressLine1'] input",
                                 "input[data-automation-id='addressLine1']",
                                 "input[aria-label*='Address Line 1' i]"]:
                        if fill_field(page, sel, "1784 NW Northrup Street", "address"):
                            break
                    for sel in ["[data-automation-id='addressSection_city'] input",
                                 "input[data-automation-id='city']",
                                 "input[aria-label*='City' i]"]:
                        if fill_field(page, sel, "Portland", "city"):
                            break
                    for sel in ["[data-automation-id='addressSection_postalCode'] input",
                                 "input[aria-label*='Postal' i]",
                                 "input[aria-label*='Zip' i]"]:
                        if fill_field(page, sel, "97209", "zip"):
                            break

                    # State dropdown or typeahead
                    for sel in [
                        "[data-automation-id='addressSection_countryRegion'] select",
                        "select[data-automation-id*='state']",
                    ]:
                        if select_opt(page, sel, ["Oregon", "OR"], "state"):
                            break
                    # State typeahead
                    for sel in [
                        "[data-automation-id='addressSection_countryRegion'] input",
                        "input[data-automation-id*='state']",
                    ]:
                        try:
                            el = page.locator(sel).first
                            if el.count() > 0:
                                el.fill("Oregon")
                                time.sleep(1)
                                opt = page.locator("[data-automation-id='promptOption']").filter(has_text="Oregon").first
                                if opt.count() > 0:
                                    opt.click()
                                    print("  [state-typeahead] Oregon")
                                break
                        except:
                            pass

                # --- WORK AUTHORIZATION ---
                if any(w in page_text.lower() for w in ["authorized", "work authorization", "sponsorship"]):
                    print("  Work authorization section...")
                    click_radio(page, "authorized", "Yes")
                    time.sleep(0.5)
                    click_radio(page, "sponsor", "Yes")
                    time.sleep(0.5)
                    # Also WD-specific selects
                    for sel in ["select[data-automation-id*='sponsor']",
                                 "[data-automation-id*='sponsor'] select"]:
                        select_opt(page, sel, ["Yes"], "sponsorship")

                # --- RESUME UPLOAD ---
                if any(w in page_text.lower() for w in ["resume", "upload", "cv", "my experience"]):
                    print("  Resume / experience section...")
                    resume_uploaded = False

                    # Method 1: direct file input
                    for sel in ["input[type='file'][data-automation-id*='resume' i]",
                                 "input[type='file']"]:
                        try:
                            inputs = page.locator(sel).all()
                            if inputs:
                                inputs[0].set_input_files(RESUME)
                                time.sleep(5)
                                resume_uploaded = True
                                print(f"  [upload] resume via {sel}")
                                break
                        except:
                            pass

                    if not resume_uploaded:
                        # Method 2: file chooser via click
                        for sel in ["[data-automation-id='file-upload-drop-zone']",
                                     "button:has-text('Upload')",
                                     "label:has-text('Upload')"]:
                            try:
                                with page.expect_file_chooser(timeout=5000) as fc_info:
                                    page.locator(sel).first.click(timeout=4000)
                                fc_info.value.set_files(RESUME)
                                time.sleep(5)
                                resume_uploaded = True
                                print(f"  [upload-chooser] via {sel}")
                                break
                            except:
                                pass

                    if resume_uploaded:
                        time.sleep(3)
                        # Dismiss autofill
                        for no_lbl in ["No, thanks", "No Thanks", "Manual Entry", "Skip", "Enter Manually"]:
                            try:
                                el = page.get_by_text(no_lbl, exact=False).first
                                if el.count() > 0 and el.is_visible(timeout=2000):
                                    el.click()
                                    time.sleep(2)
                                    print(f"  [dismiss-autofill] {no_lbl}")
                                    break
                            except:
                                pass

                    shot(page, f"v2_wizard_{wizard_page:02d}b_resume")

                # --- APPLICATION QUESTIONS ---
                if any(w in page_text.lower() for w in
                       ["question", "require sponsorship", "years of experience",
                        "how did you hear", "salary expectation", "hear about us"]):
                    print("  Application questions section...")

                    if "authorized" in page_text.lower():
                        click_radio(page, "authorized", "Yes")
                        time.sleep(0.3)
                    if "sponsor" in page_text.lower():
                        click_radio(page, "sponsor", "Yes")
                        time.sleep(0.3)

                    # Salary
                    if "salary" in page_text.lower():
                        for sel in ["input[data-automation-id*='salary']",
                                     "input[aria-label*='salary' i]",
                                     "input[placeholder*='salary' i]"]:
                            if fill_field(page, sel, "115000", "salary"):
                                break

                    # How did you hear
                    if any(w in page_text.lower() for w in ["hear about", "source", "referral"]):
                        for sel in ["select[data-automation-id*='source']",
                                     "select[data-automation-id*='hear']",
                                     "select[aria-label*='hear' i]",
                                     "[data-automation-id*='referral'] select"]:
                            if select_opt(page, sel, ["LinkedIn", "Social Media", "Job Board"], "how_hear"):
                                break

                    # YOE
                    if "years" in page_text.lower() and "experience" in page_text.lower():
                        for sel in ["select[data-automation-id*='years']",
                                     "select[aria-label*='years' i]"]:
                            select_opt(page, sel, ["3", "3-5", "2-4", "1-3"], "yoe")

                # --- VOLUNTARY DEMOGRAPHICS ---
                if any(w in page_text.lower() for w in
                       ["voluntary", "self-identification", "gender", "ethnicity", "race"]):
                    print("  Demographics section...")

                    # Gender
                    for sel in ["select[data-automation-id*='gender']",
                                 "[data-automation-id*='gender'] select",
                                 "select[aria-label*='gender' i]"]:
                        if select_opt(page, sel, ["Female", "Woman", "F"], "gender"):
                            break
                    click_radio(page, "gender", "Female")

                    # Race/Ethnicity
                    for sel in ["select[data-automation-id*='ethnicity']",
                                 "[data-automation-id*='race'] select",
                                 "select[aria-label*='race' i]"]:
                        if select_opt(page, sel,
                                       ["Asian", "Asian (Not Hispanic or Latino)",
                                        "Asian or Pacific Islander"], "race"):
                            break

                    # Hispanic
                    for sel in ["select[data-automation-id*='hispanic']",
                                 "[data-automation-id*='hispanic'] select"]:
                        select_opt(page, sel,
                                   ["No", "I am not Hispanic or Latino", "Not Hispanic"], "hispanic")

                    # Veteran
                    for sel in ["select[data-automation-id*='veteran']",
                                 "[data-automation-id*='veteran'] select"]:
                        select_opt(page, sel,
                                   ["I am not a protected veteran", "Not a protected veteran",
                                    "No", "I Don't Wish To Answer"], "veteran")

                    # Disability
                    for sel in ["select[data-automation-id*='disability']",
                                 "[data-automation-id*='disability'] select"]:
                        select_opt(page, sel,
                                   ["No, I Don't Have a Disability", "No disability",
                                    "No", "I Don't Wish To Answer"], "disability")

                # --- CHECK FOR CAPTCHA / EMAIL VERIFY ---
                if detect_captcha(page):
                    result["status"] = "captcha-staged"
                    result["notes"] = f"CAPTCHA at Workday wizard step {wizard_page}. Fields filled to this point. Human: solve CAPTCHA and continue."
                    shot(page, f"v2_99_captcha_step{wizard_page}")
                    browser.close()
                    save_result(result)
                    return result

                if detect_email_verify(page):
                    result["status"] = "email-verify-staged"
                    result["notes"] = f"Email verify gate at step {wizard_page}. Check jamiecheng0103@gmail.com."
                    shot(page, f"v2_99_email_step{wizard_page}")
                    browser.close()
                    save_result(result)
                    return result

                # Advance
                if not wd_next(page):
                    print(f"  No Next button found at step {wizard_page}")
                    if wizard_page >= 3:
                        print("  Stopping -- no more pages to advance through")
                        break

            # Wizard exhausted without finding Submit
            result["status"] = "blocked"
            result["notes"] = "Completed wizard walk but Submit button never appeared. Manual review required."
            shot(page, "v2_99_no_submit")
            browser.close()
            save_result(result)
            return result

        except Exception as e:
            tb = traceback.format_exc()
            print(f"\n[EXCEPTION] {e}\n{tb}")
            result["status"] = "error"
            result["notes"] = f"Exception: {str(e)}\n{tb[:400]}"
            try:
                shot(page, "v2_99_exception")
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
