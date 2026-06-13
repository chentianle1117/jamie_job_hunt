# -*- coding: utf-8 -*-
"""
submit_bcg_v9.py  -- BCG Phenom ATS (v9)

Fixes vs v8:
  1. Country/State: After clicking United States, press Tab to commit React state.
     Wait 4s for State cascade. Then retry State with scroll+JS click fallback.
  2. Escape after EVERY dropdown selection to close the listbox before moving on.
  3. Ethnicity: extra 2s delay after Gender closes. Use JS to find option, avoid
     intercept issues.
  4. Race checkbox: JS MouseEvent dispatch at center coords (force+click wasn't enough).
  5. Date picker: Navigate backwards from current month to Sep 2025 using prev-month
     button, then click day 1. No keyboard typing.
  6. Verification: don't use input_value() to check listbox fields (React stores value
     in state, not DOM input.value) — instead read aria-labelledby or check visible text.

Known option texts (from v7 debug, confirmed):
  input-7  Country:    'United States'
  input-28 State:      'Oregon'
  input-10 Work Q1:    'Yes'
  input-13 Work Q2:    'Yes'
  input-16 Gender:     'Woman'
  input-19 Ethnicity:  'Non Hispanic/Latino'
  input-22 Disability: "No, I don't have a disability..."
  input-25 Veteran:    'No'
  Race checkbox: Voluntary_Self_Identification_race-Asian-2
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
SHOT     = ROLE_DIR + r"\screenshots\v9"
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


def close_any_open_dropdown(page):
    """Press Escape + wait to ensure no dropdown is open before next action."""
    try:
        page.keyboard.press("Escape")
        time.sleep(0.5)
        page.keyboard.press("Escape")
        time.sleep(0.5)
    except: pass


def fill_text(page, field_id, val, lbl=""):
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


def phenom_select(page, field_id, desired_text, lbl="", commit_tab=False):
    """
    Select from a Phenom custom listbox.
    1. Close any open dropdown first.
    2. Scroll field into view.
    3. Click the input to open dropdown.
    4. Wait for listbox, click matching option by text.
    5. Press Tab or Escape to commit selection + close.
    6. JS fallback if locator approach fails.
    """
    if not alive(page): return False
    log(f"  [dd] {lbl or field_id} → '{desired_text}'")

    # Always close any open dropdown first
    close_any_open_dropdown(page)

    try:
        inp = page.locator(f"#{field_id}").first

        try:
            inp.wait_for(state="visible", timeout=8000)
        except Exception as e:
            log(f"    [dd-wait!] {e}")
            return False

        inp.scroll_into_view_if_needed()
        time.sleep(0.5)

        # Click to open (no fill/type)
        try:
            inp.click(timeout=5000)
        except Exception as e:
            log(f"    [dd-click!] trying JS: {e}")
            try:
                page.evaluate(f"document.getElementById('{field_id}').click()")
            except: return False

        time.sleep(2.0)  # wait for dropdown animation

        ss(page, f"v9_dd_{field_id[:15]}_open")

        # Strategy 1: Locator-based click on options
        option_selectors = [
            "[role='listbox'] li",
            "[role='listbox'] [role='option']",
            "[role='option']",
            "[class*='listbox'] li",
            "[class*='dropdown'] li",
            "[class*='options'] li",
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
                            opt.click(timeout=4000)
                            time.sleep(1.0)
                            # Commit with Tab if requested (e.g., Country to trigger State cascade)
                            if commit_tab:
                                page.keyboard.press("Tab")
                                time.sleep(0.5)
                            else:
                                close_any_open_dropdown(page)
                            log(f"    [dd-ok] '{opt_text}' via '{opt_sel}'")
                            return True
                    except Exception as oe:
                        # If pointer intercept, try JS click
                        try:
                            clicked = page.evaluate("""(txt) => {
                                let sels = ['[role="listbox"] li','[role="option"]',
                                            '[class*="listbox"] li','[class*="dropdown"] li'];
                                for (let sel of sels) {
                                    for (let el of document.querySelectorAll(sel)) {
                                        if (el.textContent.trim().toLowerCase().includes(txt.toLowerCase())) {
                                            el.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true}));
                                            return el.textContent.trim();
                                        }
                                    }
                                }
                                return null;
                            }""", desired_text)
                            if clicked:
                                time.sleep(1.0)
                                if commit_tab:
                                    page.keyboard.press("Tab")
                                    time.sleep(0.5)
                                else:
                                    close_any_open_dropdown(page)
                                log(f"    [dd-ok-js-intercept] '{clicked}'")
                                return True
                        except: pass
                        continue
            except: continue

        # Strategy 2: Pure JS evaluation
        log(f"    [dd-js] fallback for '{desired_text}'")
        try:
            clicked = page.evaluate("""(desired) => {
                let selectors = [
                    '[role="listbox"] li', '[role="option"]',
                    '[class*="listbox"] li', '[class*="dropdown"] li',
                    '[class*="option"]', 'ul li'
                ];
                for (let sel of selectors) {
                    for (let el of document.querySelectorAll(sel)) {
                        if (el.textContent.trim().toLowerCase().includes(desired.toLowerCase())) {
                            el.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true}));
                            return el.textContent.trim();
                        }
                    }
                }
                return null;
            }""", desired_text)
            if clicked:
                time.sleep(1.0)
                if commit_tab:
                    page.keyboard.press("Tab")
                else:
                    close_any_open_dropdown(page)
                log(f"    [dd-js-ok] '{clicked}'")
                return True
        except Exception as e:
            log(f"    [dd-js!] {e}")

        close_any_open_dropdown(page)
        log(f"    [dd-fail] '{desired_text}' not found for {field_id}")
        return False

    except Exception as e:
        log(f"  [dd!] {lbl or field_id}: {str(e)[:100]}")
        return False


def fill_date_calendar(page, field_id, target_month="September", target_year="2025", target_day="1"):
    """
    Fill a Phenom date picker by navigating the calendar.
    Clicks field, navigates to target month/year, clicks target day.
    """
    if not alive(page): return False
    log(f"  [date] Opening calendar for {target_month} {target_year} day {target_day}...")

    try:
        el = page.locator(f"#{field_id}").first
        el.wait_for(state="visible", timeout=8000)
        el.scroll_into_view_if_needed()
        el.click(timeout=5000)
        time.sleep(2.0)

        ss(page, "v9_date_open")

        # Check if a calendar dialog appeared
        cal_count = page.evaluate("""() => {
            return document.querySelectorAll(
                '[role="dialog"], [class*="calendar"], [class*="datepicker"], [class*="dp__"]'
            ).length;
        }""")
        log(f"  [date] Calendar elements: {cal_count}")

        if cal_count > 0:
            # Navigate back from current month (June 2026) to Sep 2025
            # That's 9 months back
            for nav_attempt in range(15):
                if not alive(page): break
                # Get current header
                header = page.evaluate("""() => {
                    let candidates = [
                        '[role="dialog"] [class*="title"]',
                        '[class*="calendar"] [class*="title"]',
                        '[class*="calendar"] [class*="header"]',
                        '[class*="datepicker"] [class*="title"]',
                        '[class*="month-year"]',
                        '[class*="monthYear"]',
                        '[aria-live="polite"]',
                    ];
                    for (let sel of candidates) {
                        let el = document.querySelector(sel);
                        if (el && el.textContent.trim()) return el.textContent.trim();
                    }
                    // Try any heading text in dialog
                    let dialog = document.querySelector('[role="dialog"]');
                    if (dialog) {
                        let h = dialog.querySelector('h1,h2,h3,[class*="header"]');
                        if (h) return h.textContent.trim();
                    }
                    return '';
                }""")
                log(f"    [cal] header: '{header}'")

                hdr_lower = header.lower()
                if ("sep" in hdr_lower and "2025" in hdr_lower) or \
                   ("september" in hdr_lower and "2025" in hdr_lower):
                    log(f"  [date] At target month!")
                    break

                # Click previous month button
                prev_clicked = page.evaluate("""() => {
                    let prevSels = [
                        'button[aria-label*="Previous month" i]',
                        'button[aria-label*="previous month" i]',
                        'button[aria-label*="prev" i]',
                        '[class*="prev-month"]',
                        '[class*="prevMonth"]',
                        'button[class*="prev"]',
                        'button[class*="back"]',
                        'button[class*="left"]',
                        '[class*="left-arrow"]',
                        'button:has([class*="left"])',
                    ];
                    for (let sel of prevSels) {
                        let btns = document.querySelectorAll(sel);
                        for (let btn of btns) {
                            if (btn.offsetParent !== null && !btn.disabled) {
                                btn.click();
                                return sel;
                            }
                        }
                    }
                    // Try finding buttons near calendar header
                    let dialog = document.querySelector('[role="dialog"],[class*="calendar"],[class*="datepicker"]');
                    if (dialog) {
                        let btns = dialog.querySelectorAll('button');
                        for (let btn of btns) {
                            let txt = btn.textContent.trim();
                            let lbl = (btn.getAttribute('aria-label') || '').toLowerCase();
                            if (txt === '<' || txt === '‹' || txt === '«' ||
                                lbl.includes('prev') || lbl.includes('back') || lbl.includes('left')) {
                                btn.click();
                                return 'dialog-btn:' + txt;
                            }
                        }
                    }
                    return null;
                }""")
                log(f"    [cal] prev button: {prev_clicked}")
                time.sleep(0.8)

            # Now click day 1
            day_clicked = page.evaluate("""(dayNum) => {
                let dialog = document.querySelector('[role="dialog"],[class*="calendar"],[class*="datepicker"]');
                if (!dialog) dialog = document;
                // Look for day cells
                let candidates = [
                    '[class*="day"]', '[class*="date"]',
                    'td button', 'td', 'button[class*="cal"]',
                    '[role="gridcell"] button', '[role="gridcell"]'
                ];
                for (let sel of candidates) {
                    let els = dialog.querySelectorAll(sel);
                    for (let el of els) {
                        let txt = el.textContent.trim();
                        if (txt === dayNum && !el.disabled && el.offsetParent !== null) {
                            // Make sure it's not from prev/next month (usually has a different class)
                            let cls = (el.className || '').toLowerCase();
                            if (cls.includes('other') || cls.includes('outside') || cls.includes('adjacent')) continue;
                            el.click();
                            return txt + ' (' + sel + ')';
                        }
                    }
                }
                return null;
            }""", target_day)
            log(f"  [date] Day clicked: {day_clicked}")
            time.sleep(0.8)
            close_any_open_dropdown(page)
        else:
            # No calendar — try direct input
            log("  [date] No calendar found, trying direct input")
            # Clear and type in MM/DD/YYYY format
            el.fill("", timeout=2000)
            time.sleep(0.3)
            # Use fill (not type) to set value
            page.evaluate("""(id) => {
                let el = document.getElementById(id);
                if (el) {
                    let nativeSet = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;
                    nativeSet.call(el, '09/01/2025');
                    el.dispatchEvent(new Event('input',{bubbles:true}));
                    el.dispatchEvent(new Event('change',{bubbles:true}));
                }
            }""", field_id)
            time.sleep(0.5)

        # Read back value
        try:
            val = el.input_value(timeout=2000)
            log(f"  [date] Field value after: '{val}'")
        except:
            pass

        return True

    except Exception as e:
        log(f"  [date!] {e}")
        return False


def check_asian_checkbox(page):
    """Check Asian race checkbox using multiple strategies."""
    cb_id = "Voluntary_Self_Identification_race-Asian-2"
    if not alive(page): return False

    # Strategy 1: scroll + force click
    try:
        cb = page.locator(f"#{cb_id}").first
        if cb.count() > 0:
            cb.scroll_into_view_if_needed()
            time.sleep(0.5)
            already = cb.is_checked()
            if already:
                log(f"  [race-ok] Asian already checked")
                return True
            cb.click(force=True, timeout=3000)
            time.sleep(0.8)
            if cb.is_checked():
                log(f"  [race-ok] Asian checked via force click")
                return True
    except Exception as e:
        log(f"  [race-click!] {e}")

    # Strategy 2: JS MouseEvent at element coordinates
    try:
        result = page.evaluate("""() => {
            let cb = document.getElementById('Voluntary_Self_Identification_race-Asian-2');
            if (!cb) return 'not found';
            cb.scrollIntoView({block:'center'});
            let rect = cb.getBoundingClientRect();
            let cx = rect.left + rect.width/2;
            let cy = rect.top + rect.height/2;
            cb.dispatchEvent(new MouseEvent('mousedown',{bubbles:true,cancelable:true,clientX:cx,clientY:cy}));
            cb.dispatchEvent(new MouseEvent('mouseup',{bubbles:true,cancelable:true,clientX:cx,clientY:cy}));
            cb.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true,clientX:cx,clientY:cy}));
            return 'dispatched, checked=' + cb.checked;
        }""")
        log(f"  [race-js] {result}")
        time.sleep(0.5)
        try:
            cb = page.locator(f"#{cb_id}").first
            if cb.is_checked():
                log(f"  [race-ok] Asian checked via JS MouseEvent")
                return True
        except: pass
    except Exception as e:
        log(f"  [race-js!] {e}")

    # Strategy 3: Force check via property setter
    try:
        page.evaluate("""() => {
            let cb = document.getElementById('Voluntary_Self_Identification_race-Asian-2');
            if (cb) {
                let nativeSet = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'checked').set;
                nativeSet.call(cb, true);
                cb.dispatchEvent(new Event('change',{bubbles:true}));
                cb.dispatchEvent(new Event('input',{bubbles:true}));
            }
        }""")
        time.sleep(0.3)
        log(f"  [race-setter] applied native checked setter")
        return True
    except Exception as e:
        log(f"  [race-setter!] {e}")

    log(f"  [race-fail] Could not check Asian checkbox")
    return False


def has_captcha(page):
    if not alive(page): return False
    for sel in ["iframe[src*='recaptcha']","iframe[src*='hcaptcha']",
                ".g-recaptcha","[data-sitekey]",".cf-turnstile"]:
        try:
            if page.locator(sel).count() > 0: return True
        except: pass
    try: return any(w in txt(page)[:2000].lower() for w in ["captcha","i'm not a robot"])
    except: return False


def has_email_verify(page):
    if not alive(page): return False
    try:
        t = txt(page)[:2000].lower()
        return any(k in t for k in [
            "verification email sent","verify your email","we sent an email",
            "check your inbox","confirm your email","click the link in",
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
    log("BCG Phenom v9 -- Talent Senior Specialist - People")
    log("=" * 60)

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
            ss(page, "v9_01_initial")
            log(f"  URL: {page.url}")

            # ── Login ─────────────────────────────────────────────────────
            log("\n[2] Login...")
            if "login" in page.url.lower():
                for s in ["input[type='email']","input[placeholder*='Email' i]",
                           "input[id*='email' i]","input[autocomplete='email']"]:
                    try:
                        el = page.locator(s).first
                        if el.count() > 0 and el.is_visible(timeout=3000):
                            el.click(); el.fill(""); el.fill(EMAIL)
                            log(f"  [fill] email"); break
                    except: continue

                page.locator("button:has-text('Continue')").first.click()
                time.sleep(7); net(page, 15000); dismiss_cookie(page)
                ss(page, "v9_02_after_email")
                body = txt(page)

                if has_captcha(page):
                    R["status"]="captcha-staged"; R["notes"]="CAPTCHA after email."
                    try: browser.close()
                    except: pass
                    save(R); return R
                if has_email_verify(page):
                    R["status"]="email-verify-staged"; R["notes"]=f"Email verify. Check {EMAIL}."
                    try: browser.close()
                    except: pass
                    save(R); return R

                if "password" in body.lower():
                    pws = page.locator("input[type='password']").all()
                    if pws: pws[0].click(); pws[0].fill(PW); log("  [fill] password")
                    page.locator("button:has-text('Submit')").first.click()
                    time.sleep(8); net(page, 15000); dismiss_cookie(page)
                    ss(page, "v9_03_after_signin")
                    log(f"  Post-signin URL: {page.url}")
                    if "login" in page.url.lower():
                        try:
                            page.locator("a:has-text('Use a one-time code instead')").first.click()
                            time.sleep(4)
                        except: pass
                        R["status"]="email-verify-staged"
                        R["notes"]=f"Password login failed. OTP link clicked. Check {EMAIL}."
                        ss(page, "v9_99_login_fail")
                        try: browser.close()
                        except: pass
                        save(R); return R

            # ── Load application form ─────────────────────────────────────
            log("\n[3] Loading application form...")
            page.goto(PHENOM_APPLY, timeout=30000, wait_until="domcontentloaded")
            time.sleep(8); net(page, 15000); dismiss_cookie(page); time.sleep(2)
            ss(page, "v9_10_form")
            log(f"  URL: {page.url}")
            if "login" in page.url.lower():
                R["status"]="email-verify-staged"; R["notes"]=f"Redirected to login. Check {EMAIL}."
                try: browser.close()
                except: pass
                save(R); return R

            # ── Upload resume ─────────────────────────────────────────────
            log("\n[4] Uploading resume...")
            for s in ["input[type='file'][accept*='pdf' i]","input[type='file']"]:
                try:
                    inputs = page.locator(s).all()
                    if inputs:
                        inputs[0].set_input_files(RESUME)
                        time.sleep(6)
                        log(f"  [upload] resume via {s}")
                        for dismiss in ["No, thanks","Skip","No thanks","Enter Manually"]:
                            try:
                                el = page.get_by_text(dismiss, exact=False).first
                                if el.count() > 0 and el.is_visible(timeout=2000):
                                    el.click(); time.sleep(2); break
                            except: pass
                        break
                except Exception as e: log(f"  [upload!] {e}")
            ss(page, "v9_11_after_resume")

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
                        if not cur: fill_text(page, fid, val, lbl)
                        else: log(f"  [skip] {lbl} already = '{cur[:30]}'")
                except: pass

            try:
                el = page.locator("#Before_applying_preferred_first_name").first
                if el.count() > 0 and el.is_visible(timeout=1500):
                    if not el.input_value().strip():
                        fill_text(page, "Before_applying_preferred_first_name", "Jamie", "preferred_first")
            except: pass

            # Country — commit_tab=True so React state updates and State cascade loads
            log("  [country] Setting United States...")
            phenom_select(page, "input-7", "United States", "country", commit_tab=True)
            log("  [country] Waiting 5s for State cascade...")
            time.sleep(5)

            # Verify Country was set by checking if State is now visible
            state_visible = False
            try:
                st = page.locator("#input-28").first
                st.wait_for(state="visible", timeout=6000)
                state_visible = True
                log("  [state] State field appeared")
            except:
                log("  [state] State still not visible — trying to re-select Country")
                # Try clicking country again
                phenom_select(page, "input-7", "United States", "country", commit_tab=True)
                time.sleep(5)
                try:
                    st = page.locator("#input-28").first
                    st.wait_for(state="visible", timeout=6000)
                    state_visible = True
                    log("  [state] State field appeared after retry")
                except:
                    log("  [state] State still not visible after 2 attempts")

            if state_visible:
                log("  [state] Setting Oregon...")
                phenom_select(page, "input-28", "Oregon", "state")
                time.sleep(1.5)

            ss(page, "v9_12_personal_filled")

            # ── Available Start Date ──────────────────────────────────────
            log("\n[6] Filling Available Start Date...")
            if alive(page):
                fill_date_calendar(page, "Available_Start_Date_start_date",
                                   target_month="September", target_year="2025", target_day="1")
            ss(page, "v9_13_date_filled")

            # ── Work Authorization ────────────────────────────────────────
            log("\n[7] Work Authorization...")
            if alive(page):
                log("  [work_auth] Q1: authorized → Yes")
                phenom_select(page, "input-10", "Yes", "work_auth_Q1")
                time.sleep(1.5)

                log("  [work_auth] Q2: sponsorship → Yes")
                phenom_select(page, "input-13", "Yes", "work_auth_Q2")
                time.sleep(1.5)

            ss(page, "v9_14_workauth_filled")

            # ── Voluntary Self-Identification ─────────────────────────────
            log("\n[8] Voluntary Self-Identification...")
            if alive(page):

                # Gender → Woman
                log("  [gender] → Woman")
                phenom_select(page, "input-16", "Woman", "gender")
                time.sleep(2.0)  # extra wait — gender dropdown may leave residual overlay

                # Ethnicity → Non Hispanic/Latino
                log("  [ethnicity] → Non Hispanic/Latino")
                phenom_select(page, "input-19", "Non Hispanic/Latino", "hispanic_Q")
                time.sleep(1.5)

                # Race → Asian checkbox
                log("  [race] Checking Asian...")
                check_asian_checkbox(page)
                time.sleep(1.0)

                # Disability → No disability
                log("  [disability] → No disability")
                phenom_select(page, "input-22", "No, I don't have a disability", "disability")
                time.sleep(1.5)

                # Veteran → No
                log("  [veteran] → No")
                phenom_select(page, "input-25", "No", "veteran")
                time.sleep(1.5)

            ss(page, "v9_15_eeoc_filled")

            # ── Full-page screenshot + check errors ───────────────────────
            log("\n[9] Pre-submit check...")
            if alive(page):
                page.evaluate("window.scrollTo(0,0)")
                time.sleep(1)
                ss(page, "v9_16_top")
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(2)
                ss(page, "v9_16_bottom")

                body = txt(page)
                error_lines = [l.strip() for l in body.split('\n')
                               if any(w in l.lower() for w in [
                                   "error found","error:","cannot be left blank",
                                   "select a value","select at least one","select a country",
                                   "select a gender","select a ethnicity",
                               ])]
                log(f"  Pre-submit errors: {error_lines[:8]}")

                # Re-fill any empty dropdowns (check which ones failed)
                if error_lines:
                    log("  [fix] Re-checking all dropdowns...")
                    for fid, desired, lbl in [
                        ("input-10", "Yes", "work_auth_Q1"),
                        ("input-13", "Yes", "work_auth_Q2"),
                        ("input-16", "Woman", "gender"),
                        ("input-19", "Non Hispanic/Latino", "ethnicity"),
                        ("input-22", "No, I don't have a disability", "disability"),
                        ("input-25", "No", "veteran"),
                    ]:
                        if not alive(page): break
                        # Check if field has a selected value via aria attribute
                        try:
                            val_check = page.evaluate(f"""() => {{
                                let el = document.getElementById('{fid}');
                                if (!el) return '';
                                return el.value || el.getAttribute('aria-valuenow') || '';
                            }}""")
                            log(f"  [check-js] {lbl} = '{val_check[:40]}'")
                            if not val_check.strip():
                                log(f"  [re-fill] {lbl} empty, retrying...")
                                phenom_select(page, fid, desired, lbl)
                                time.sleep(1.5)
                        except: pass

                    # Re-check Asian
                    try:
                        cb = page.locator("#Voluntary_Self_Identification_race-Asian-2").first
                        if cb.count() > 0 and not cb.is_checked():
                            log("  [re-check] Asian not checked, retrying...")
                            check_asian_checkbox(page)
                    except: pass

                    time.sleep(1)
                    ss(page, "v9_16b_post_refill")

            # ── Submit ────────────────────────────────────────────────────
            if alive(page):
                page.evaluate("window.scrollTo(0,0)")
                time.sleep(1)
                ss(page, "v9_17_pre_submit")

            log("\n[10] Submitting...")
            if not alive(page):
                R["status"]="error"; R["notes"]="Page closed before submit"
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
                        if any(bad in t_val for bad in ["subscribe","newsletter"]): continue
                        el.scroll_into_view_if_needed()
                        ss(page, "v9_18_about_to_submit")
                        el.click(timeout=5000)
                        submit_clicked = True
                        log(f"  [submit] Clicked: {s}")
                        time.sleep(12); net(page, 20000)
                        break
                except Exception as e:
                    log(f"  [submit!] {s}: {e}")

            if not submit_clicked:
                R["status"]="blocked"
                R["notes"]=f"No submit button found. URL: {page.url}. Body: {txt(page)[:300]}"
                ss(page, "v9_99_no_submit")
                try: browser.close()
                except: pass
                save(R); return R

            # ── Post-submit ───────────────────────────────────────────────
            if not alive(page):
                R["status"]="likely-submitted"
                R["confirmed_at"]=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                R["notes"]="Submit clicked but page closed before confirmation."
                save(R); return R

            body = txt(page)
            ss(page, "v9_19_post_submit")
            log(f"\n  Post-submit URL: {page.url}")
            log(f"  Post-submit body (600): {body[:600]}")

            if has_captcha(page):
                R["status"]="captcha-staged"
                R["notes"]=f"CAPTCHA after Submit. URL: {page.url}"
                try: browser.close()
                except: pass
                save(R); return R

            if is_real_confirmation(body, page.url):
                R["status"]="submitted"
                R["confirmed_at"]=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                R["screenshot"]=os.path.join(SHOT,"v9_19_post_submit.png")
                R["notes"]=f"SUBMITTED. {body[:600]}"
                log("  *** CONFIRMED SUBMISSION! ***")
                try: browser.close()
                except: pass
                save(R); return R

            error_lines=[l.strip() for l in body.split('\n')
                         if any(w in l.lower() for w in [
                             "error found","error:","cannot be left blank",
                             "select a value","select at least one"
                         ])]
            if error_lines:
                log(f"  Still errors: {error_lines[:5]}")
                R["status"]="blocked"
                R["notes"]=(f"Submit clicked but errors remain: {error_lines[:5]}. "
                            f"URL: {page.url}. Body: {body[:400]}")
                try: browser.close()
                except: pass
                save(R); return R

            R["status"]="likely-submitted"
            R["confirmed_at"]=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            R["screenshot"]=os.path.join(SHOT,"v9_19_post_submit.png")
            R["notes"]=f"Submit clicked. No errors. Body: {body[:600]}"
            try: browser.close()
            except: pass
            save(R); return R

        except Exception as e:
            tb = traceback.format_exc()
            log(f"\n[EXCEPTION] {e}\n{tb[:1000]}")
            R["status"]="error"
            R["notes"]=f"Exception: {str(e)}\n{tb[:500]}"
            try:
                if alive(page): ss(page, "v9_99_exception")
            except: pass
            try: browser.close()
            except: pass
            save(R); return R


if __name__ == "__main__":
    main()
