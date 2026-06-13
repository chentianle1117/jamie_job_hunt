# -*- coding: utf-8 -*-
"""
submit_bcg_v10.py  -- BCG Phenom ATS (v10)

Root cause analysis from v9:
  - Country dropdown: clicks fire [dd-ok] but React state doesn't commit.
    Phenom uses React controlled components. After clicking the option, must also
    fire the React synthetic onChange via the fiber's onChangeCapture or props.
    Solution: after the option click, use React fiber trick to call onChange,
    OR use keyboard approach (type to filter, then press Enter/ArrowDown+Enter).
  - Date picker: calendar's "Previous month" button exists but header reads 'resume.pdf'
    because the JS picks up the upload section. The date picker opens but navigates
    incorrectly. Solution: scope all calendar JS to elements that appear AFTER clicking
    the date field (check aria-expanded state), and use a fresh approach.
  - Ethnicity pre-filled to 'Hispanic/Latino' from profile — need to override.
  - Work Auth Q1 shows empty in value check — React fiber issue same as Country.
    But re-fill works (shows Yes in second check). So it IS setting but input.value=''
    because React stores in state not DOM.

STRATEGY CHANGE for Country:
  1. Open dropdown by clicking input
  2. Type "United States" character by character (keyboard type) to filter
  3. Press ArrowDown to select filtered item, then Enter to commit
  This triggers React's onKeyDown/onKeyUp synthetic events which properly update state.

STRATEGY CHANGE for Date:
  1. Click the date input to open the calendar dialog
  2. Use the aria-controls attribute to find the actual dialog element
  3. Navigate by clicking the header title to get to month/year view,
     then click month, then year if needed
  4. OR: after opening, look for input[type=text] or input[type=number] inside dialog
     that accepts direct date entry.

Known working (from v9):
  - Work Auth Q1/Q2: Yes/Yes (both work, re-fill may be needed)
  - Gender: Woman (works)
  - Ethnicity: Non Hispanic/Latino (works via JS fallback)
  - Race: Asian checkbox (works via JS MouseEvent)
  - Disability: No... (works)
  - Veteran: No (works)
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
SHOT     = ROLE_DIR + r"\screenshots\v10"
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


def log(msg): print(msg, flush=True)

def ss(page, name):
    path = os.path.join(SHOT, name + ".png")
    try:
        if not page.is_closed():
            page.screenshot(path=path, full_page=True, timeout=15000)
            log(f"  [ss] {name}.png")
    except Exception as e:
        log(f"  [ss!] {name}: {e}")
    return path

def alive(page):
    try: return not page.is_closed()
    except: return False

def net(page, t=15000):
    try: page.wait_for_load_state("networkidle", timeout=t)
    except: pass

def txt(page):
    try: return page.inner_text("body", timeout=5000)
    except: return ""

def dismiss_cookie(page):
    if not alive(page): return
    for sel in ["button:has-text('Accept All and Close')",
                "button:has-text('Accept All')","#truste-consent-button",
                "#onetrust-accept-btn-handler"]:
        try:
            el = page.locator(sel).first
            if el.count() > 0 and el.is_visible(timeout=2000):
                el.click(force=True); time.sleep(2); return
        except: continue
    try:
        page.evaluate("""() => {
            document.querySelectorAll('[id*="truste"],[class*="truste"],[id*="trustarc"],' +
                '[class*="trustarc"],#onetrust-banner-sdk,.onetrust-pc-dark-filter'
            ).forEach(e => { e.style.cssText='display:none!important;'; });
            document.body.style.overflow='auto';
        }""")
    except: pass

def escape_close(page):
    """Close any open dropdown/dialog by pressing Escape twice."""
    try: page.keyboard.press("Escape"); time.sleep(0.4)
    except: pass
    try: page.keyboard.press("Escape"); time.sleep(0.3)
    except: pass

def fill_text(page, field_id, val, lbl=""):
    if not alive(page): return False
    try:
        el = page.locator(f"#{field_id}").first
        el.wait_for(state="visible", timeout=5000)
        el.scroll_into_view_if_needed()
        el.click(timeout=3000); el.fill("", timeout=2000)
        el.fill(val, timeout=5000)
        log(f"  [fill] {lbl or field_id} = '{val[:50]}'"); return True
    except Exception as e:
        try:
            page.evaluate("(args)=>{let el=document.getElementById(args[0]);if(el){"
                "el.focus();el.value=args[1];"
                "el.dispatchEvent(new Event('input',{bubbles:true}));"
                "el.dispatchEvent(new Event('change',{bubbles:true}));}}",
                [field_id, val])
            log(f"  [fill-js] {lbl or field_id} = '{val[:50]}'"); return True
        except: pass
        log(f"  [fill!] {lbl or field_id}: {str(e)[:80]}"); return False


def phenom_select_keyboard(page, field_id, desired_text, lbl=""):
    """
    Select from Phenom combobox using KEYBOARD approach (type to filter, arrow+enter).
    This properly triggers React synthetic events.
    Steps:
      1. Escape to close anything
      2. Click input to focus
      3. Clear existing value (Ctrl+A + Delete)
      4. Type first few chars of desired text (triggers React onChange → filter)
      5. Wait for filtered option to appear
      6. Click the option OR press ArrowDown + Enter
    """
    if not alive(page): return False
    log(f"  [dd-kb] {lbl or field_id} → '{desired_text}'")
    escape_close(page)

    try:
        inp = page.locator(f"#{field_id}").first
        try:
            inp.wait_for(state="visible", timeout=8000)
        except Exception as e:
            log(f"    [dd-kb-wait!] {e}"); return False

        inp.scroll_into_view_if_needed()
        time.sleep(0.3)

        # Focus and clear
        inp.click(timeout=5000)
        time.sleep(0.5)
        page.keyboard.press("Control+a")
        page.keyboard.press("Delete")
        time.sleep(0.3)

        # Type to filter (use first 5 chars to trigger filtering)
        type_chars = desired_text[:5]
        page.keyboard.type(type_chars, delay=80)
        time.sleep(1.5)

        ss(page, f"v10_dd_kb_{field_id[:15]}_typed")

        # Try to find a matching option and click it
        option_selectors = [
            "[role='listbox'] li",
            "[role='listbox'] [role='option']",
            "[role='option']",
            "[class*='listbox'] li",
            "[class*='dropdown'] li",
        ]

        for opt_sel in option_selectors:
            if not alive(page): return False
            try:
                opts = page.locator(opt_sel).all()
                for opt in opts:
                    try:
                        opt_text = opt.inner_text(timeout=1500).strip()
                        if desired_text.lower() in opt_text.lower():
                            opt.scroll_into_view_if_needed()
                            opt.click(timeout=3000)
                            time.sleep(1.0)
                            escape_close(page)
                            log(f"    [dd-kb-ok] clicked '{opt_text}'")
                            return True
                    except Exception as oe:
                        # Intercept — try JS click
                        try:
                            r = page.evaluate("""(txt)=>{
                                for (let sel of ['[role="listbox"] li','[role="option"]','[class*="listbox"] li']) {
                                    for (let el of document.querySelectorAll(sel)) {
                                        if (el.textContent.trim().toLowerCase().includes(txt.toLowerCase())) {
                                            el.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true}));
                                            return el.textContent.trim();
                                        }
                                    }
                                }
                                return null;
                            }""", desired_text)
                            if r:
                                time.sleep(1.0)
                                escape_close(page)
                                log(f"    [dd-kb-js-ok] '{r}'")
                                return True
                        except: pass
            except: continue

        # Fallback: press ArrowDown until we find the right option, then Enter
        log(f"    [dd-kb-arrow] trying arrow navigation...")
        for _ in range(20):
            page.keyboard.press("ArrowDown")
            time.sleep(0.15)
            # Check if a highlighted option matches
            active_text = page.evaluate("""() => {
                let active = document.querySelector('[aria-selected="true"],[class*="focused"],[class*="active"]');
                return active ? active.textContent.trim() : '';
            }""")
            if desired_text.lower() in active_text.lower():
                page.keyboard.press("Enter")
                time.sleep(1.0)
                log(f"    [dd-kb-arrow-ok] '{active_text}'")
                return True

        escape_close(page)
        log(f"    [dd-kb-fail] '{desired_text}' not found for {field_id}")
        return False

    except Exception as e:
        log(f"  [dd-kb!] {lbl or field_id}: {str(e)[:100]}")
        return False


def phenom_select_click(page, field_id, desired_text, lbl=""):
    """
    Click-based selection for fields where keyboard doesn't work.
    Used for EEO fields which aren't filterable.
    """
    if not alive(page): return False
    log(f"  [dd] {lbl or field_id} → '{desired_text}'")
    escape_close(page)

    try:
        inp = page.locator(f"#{field_id}").first
        try:
            inp.wait_for(state="visible", timeout=8000)
        except Exception as e:
            log(f"    [dd-wait!] {e}"); return False

        inp.scroll_into_view_if_needed()
        time.sleep(0.5)

        try:
            inp.click(timeout=5000)
        except Exception as e:
            log(f"    [dd-click!] JS fallback: {str(e)[:60]}")
            try: page.evaluate(f"document.getElementById('{field_id}').click()")
            except: return False

        time.sleep(2.0)
        ss(page, f"v10_dd_{field_id[:15]}_open")

        option_selectors = [
            "[role='listbox'] li",
            "[role='listbox'] [role='option']",
            "[role='option']",
            "[class*='listbox'] li",
            "[class*='dropdown'] li",
        ]

        for opt_sel in option_selectors:
            if not alive(page): return False
            try:
                opts = page.locator(opt_sel).all()
                for opt in opts:
                    try:
                        opt_text = opt.inner_text(timeout=1500).strip()
                        if desired_text.lower() in opt_text.lower():
                            opt.scroll_into_view_if_needed()
                            opt.click(timeout=4000)
                            time.sleep(1.0)
                            escape_close(page)
                            log(f"    [dd-ok] '{opt_text}'")
                            return True
                    except:
                        try:
                            r = page.evaluate("""(txt)=>{
                                for (let sel of ['[role="listbox"] li','[role="option"]','[class*="listbox"] li']) {
                                    for (let el of document.querySelectorAll(sel)) {
                                        if (el.textContent.trim().toLowerCase().includes(txt.toLowerCase())) {
                                            el.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true}));
                                            return el.textContent.trim();
                                        }
                                    }
                                }
                                return null;
                            }""", desired_text)
                            if r:
                                time.sleep(1.0); escape_close(page)
                                log(f"    [dd-js-ok] '{r}'"); return True
                        except: pass
            except: continue

        escape_close(page)
        log(f"    [dd-fail] '{desired_text}' for {field_id}")
        return False
    except Exception as e:
        log(f"  [dd!] {str(e)[:80]}"); return False


def fill_date_phenom(page, field_id):
    """
    Fill Phenom date picker by:
    1. Click field to open dialog
    2. Find the dialog by aria-controls on the input
    3. Navigate to Sep 2025 (back from current month)
    4. Click day 1
    Falls back to direct value injection if calendar not found.
    """
    if not alive(page): return False
    log(f"  [date] Filling Available Start Date → Sep 2025...")

    try:
        el = page.locator(f"#{field_id}").first
        el.wait_for(state="visible", timeout=8000)
        el.scroll_into_view_if_needed()

        # Get the aria-controls to find the dialog
        controls = page.evaluate(f"""() => {{
            let el = document.getElementById('{field_id}');
            return el ? el.getAttribute('aria-controls') : null;
        }}""")
        log(f"  [date] aria-controls: {controls}")

        el.click(timeout=5000)
        time.sleep(2.0)
        ss(page, "v10_date_open")

        # Find the calendar dialog — use aria-controls ID if available
        if controls:
            dialog_sel = f"#{controls}"
        else:
            # Try to find based on aria-expanded=true on the input
            dialog_sel = None

        # Get month/year info from the dialog
        def get_calendar_header():
            queries = []
            if controls:
                queries.append(f"#{controls} [class*='title']")
                queries.append(f"#{controls} [class*='header']")
                queries.append(f"#{controls} [class*='month']")
            queries += [
                "[class*='dateRangePicker'] [class*='title']",
                "[class*='datePicker'] [class*='title']",
                "[class*='calendar-container'] [class*='title']",
                "[class*='calendar-module'] [class*='title']",
                # Look for any visible calendar-like element near the date field
            ]
            for q in queries:
                try:
                    el = page.locator(q).first
                    if el.count() > 0 and el.is_visible(timeout=500):
                        t = el.inner_text(timeout=500).strip()
                        if t and len(t) < 30: return t
                except: continue

            # JS approach — find element with month name
            return page.evaluate("""() => {
                let monthNames = ['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec'];
                let all = document.querySelectorAll('*');
                for (let el of all) {
                    if (el.children.length === 0) { // leaf node
                        let t = el.textContent.trim().toLowerCase();
                        if (t.length < 25 && monthNames.some(m => t.includes(m))) {
                            return el.textContent.trim();
                        }
                    }
                }
                return '';
            }""")

        def click_prev_month():
            return page.evaluate("""() => {
                // Look for previous month buttons specifically in calendar context
                let triggers = [
                    'button[aria-label*="Previous month" i]',
                    'button[aria-label*="previous" i]',
                    '[class*="prevMonth"]',
                    '[class*="prev-month"]',
                    '[class*="calendar"] button:first-of-type',
                    '[class*="datepicker"] button:first-of-type',
                ];
                for (let sel of triggers) {
                    let btns = document.querySelectorAll(sel);
                    for (let btn of btns) {
                        // Only click if it looks like a navigation button (no text or < icon)
                        let txt = btn.textContent.trim();
                        let lbl = (btn.getAttribute('aria-label') || '').toLowerCase();
                        let cls = (btn.className || '').toLowerCase();
                        if (txt.length < 3 || lbl.includes('prev') || cls.includes('prev')) {
                            if (btn.offsetParent !== null && !btn.disabled) {
                                btn.click();
                                return 'clicked: ' + (lbl || txt || cls);
                            }
                        }
                    }
                }
                return null;
            }""")

        # Navigate to Sep 2025
        max_attempts = 20
        reached_target = False
        for i in range(max_attempts):
            if not alive(page): break
            header = get_calendar_header()
            log(f"    [cal] header: '{header}'")
            h = header.lower()
            if ("sep" in h or "september" in h) and "2025" in h:
                reached_target = True
                break
            if not header:
                log(f"    [cal] no header found at attempt {i}")
                if i > 3: break  # Give up after a few attempts
            result = click_prev_month()
            log(f"    [cal] prev: {result}")
            time.sleep(0.8)

        if reached_target:
            log(f"  [date] At Sep 2025, clicking day 1...")
            day_clicked = page.evaluate("""() => {
                // Find all calendar day cells showing "1" that aren't disabled/outside-month
                let daySelectors = [
                    '[class*="day"]:not([class*="outside"]):not([class*="other"]):not([class*="adjacent"])',
                    '[class*="date"]:not([class*="outside"])',
                    'td:not([class*="outside"]) button',
                    '[role="gridcell"]:not([aria-disabled="true"]) button',
                    '[role="gridcell"]:not([aria-disabled="true"])',
                ];
                for (let sel of daySelectors) {
                    for (let el of document.querySelectorAll(sel)) {
                        let txt = el.textContent.trim();
                        if (txt === '1') {
                            el.click();
                            return sel + ':' + txt;
                        }
                    }
                }
                return null;
            }""")
            log(f"  [date] Day click: {day_clicked}")
            time.sleep(0.5)
            escape_close(page)
        else:
            log(f"  [date] Could not navigate to Sep 2025, using JS injection")
            escape_close(page)
            # JS native value setter approach
            page.evaluate(f"""() => {{
                let el = document.getElementById('{field_id}');
                if (!el) return;
                let nativeSet = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;
                nativeSet.call(el, '01 Sep 2025');
                el.dispatchEvent(new Event('input',{{bubbles:true}}));
                el.dispatchEvent(new Event('change',{{bubbles:true}}));
                el.dispatchEvent(new FocusEvent('blur',{{bubbles:true}}));
            }}""")
            time.sleep(0.3)

        val = ""
        try:
            val = el.input_value(timeout=2000)
        except: pass
        log(f"  [date] Field value: '{val}'")
        return True

    except Exception as e:
        log(f"  [date!] {e}")
        return False


def check_asian_checkbox(page):
    cb_id = "Voluntary_Self_Identification_race-Asian-2"
    if not alive(page): return False
    # Strategy 1: direct click
    try:
        cb = page.locator(f"#{cb_id}").first
        if cb.count() > 0:
            cb.scroll_into_view_if_needed(); time.sleep(0.5)
            if cb.is_checked():
                log("  [race-ok] Asian already checked"); return True
            cb.click(force=True, timeout=3000); time.sleep(0.8)
            if cb.is_checked():
                log("  [race-ok] Asian checked (force)"); return True
    except: pass
    # Strategy 2: JS MouseEvent
    try:
        r = page.evaluate("""() => {
            let cb = document.getElementById('Voluntary_Self_Identification_race-Asian-2');
            if (!cb) return 'not found';
            cb.scrollIntoView({block:'center'});
            let rect = cb.getBoundingClientRect();
            let cx = rect.left + rect.width/2, cy = rect.top + rect.height/2;
            ['mousedown','mouseup','click'].forEach(ev =>
                cb.dispatchEvent(new MouseEvent(ev,{bubbles:true,cancelable:true,clientX:cx,clientY:cy}))
            );
            return 'done,checked='+cb.checked;
        }""")
        log(f"  [race-js] {r}"); time.sleep(0.5)
        try:
            if page.locator(f"#{cb_id}").first.is_checked():
                log("  [race-ok] Asian checked (JS)"); return True
        except: pass
    except: pass
    # Strategy 3: native setter
    try:
        page.evaluate("""() => {
            let cb = document.getElementById('Voluntary_Self_Identification_race-Asian-2');
            if (cb) {
                let s = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'checked').set;
                s.call(cb, true);
                cb.dispatchEvent(new Event('change',{bubbles:true}));
            }
        }""")
        log("  [race-setter] applied"); return True
    except: pass
    log("  [race-fail]"); return False


def has_captcha(page):
    if not alive(page): return False
    for sel in ["iframe[src*='recaptcha']","iframe[src*='hcaptcha']",".g-recaptcha","[data-sitekey]"]:
        try:
            if page.locator(sel).count() > 0: return True
        except: pass
    try: return "captcha" in txt(page)[:2000].lower()
    except: return False

def has_email_verify(page):
    if not alive(page): return False
    try:
        t = txt(page)[:2000].lower()
        return any(k in t for k in ["verify your email","we sent an email","check your inbox","confirm your email"])
    except: return False

def is_real_confirmation(body, url=""):
    t = body.lower()
    if "login" in url.lower() or ("sign in" in t and "password" in t and "careerhub" not in url.lower()):
        return False
    return any(p in t for p in [
        "thank you for applying","your application has been submitted",
        "application successfully submitted","we have received your application",
        "you have successfully applied","successfully applied to",
        "your submission has been received","application submitted successfully",
    ])

def save(result):
    path = os.path.join(ROLE_DIR, "SUBMITTED.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    log(f"\n[SAVED] {path}")
    log("=" * 60)
    log(f"RESULT: {result['status']}")
    log(f"Notes:  {str(result.get('notes',''))[:600]}")
    log("=" * 60)


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
    log("BCG Phenom v10 -- Talent Senior Specialist - People")
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
            ss(page, "v10_01_initial")
            log(f"  URL: {page.url}")

            # ── Login ─────────────────────────────────────────────────────
            log("\n[2] Login...")
            if "login" in page.url.lower():
                for s in ["input[type='email']","input[placeholder*='Email' i]","input[id*='email' i]"]:
                    try:
                        el = page.locator(s).first
                        if el.count() > 0 and el.is_visible(timeout=3000):
                            el.click(); el.fill(""); el.fill(EMAIL)
                            log("  [fill] email"); break
                    except: continue

                page.locator("button:has-text('Continue')").first.click()
                time.sleep(7); net(page, 15000); dismiss_cookie(page)
                ss(page, "v10_02_after_email")
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
                    ss(page, "v10_03_after_signin")
                    log(f"  Post-signin URL: {page.url}")
                    if "login" in page.url.lower():
                        try: page.locator("a:has-text('Use a one-time code instead')").first.click(); time.sleep(4)
                        except: pass
                        R["status"]="email-verify-staged"
                        R["notes"]=f"Login failed. OTP link clicked. Check {EMAIL}."
                        try: browser.close()
                        except: pass
                        save(R); return R

            # ── Load form ─────────────────────────────────────────────────
            log("\n[3] Loading application form...")
            page.goto(PHENOM_APPLY, timeout=30000, wait_until="domcontentloaded")
            time.sleep(8); net(page, 15000); dismiss_cookie(page); time.sleep(2)
            ss(page, "v10_10_form")
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
                        inputs[0].set_input_files(RESUME); time.sleep(6)
                        log(f"  [upload] resume via {s}")
                        for dismiss_txt in ["No, thanks","Skip","No thanks","Enter Manually"]:
                            try:
                                el = page.get_by_text(dismiss_txt, exact=False).first
                                if el.count() > 0 and el.is_visible(timeout=2000):
                                    el.click(); time.sleep(2); break
                            except: pass
                        break
                except Exception as e: log(f"  [upload!] {e}")
            ss(page, "v10_11_after_resume")

            # ── Personal info ─────────────────────────────────────────────
            log("\n[5] Personal info...")
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
                        else: log(f"  [skip] {lbl} = '{cur[:30]}'")
                except: pass
            try:
                el = page.locator("#Before_applying_preferred_first_name").first
                if el.count() > 0 and el.is_visible(timeout=1500):
                    if not el.input_value().strip():
                        fill_text(page, "Before_applying_preferred_first_name", "Jamie", "pref_first")
            except: pass

            # Country — keyboard approach (type "United" → filter → click option)
            log("  [country] Setting United States (keyboard approach)...")
            country_ok = phenom_select_keyboard(page, "input-7", "United States", "country")
            time.sleep(4)  # wait for State cascade

            # Verify State appeared
            state_visible = False
            try:
                st = page.locator("#input-28").first
                # Don't use wait_for — just check if it exists and is enabled
                if st.count() > 0:
                    state_visible = True
                    log("  [state] State field found")
            except: pass

            if not state_visible:
                # Profile pre-fills State=Washington, so State might be showing already
                # Check if State field is already there
                state_html = page.evaluate("""() => {
                    let el = document.getElementById('input-28');
                    if (!el) return 'NOT FOUND';
                    return 'value=' + el.value + ' visible=' + (el.offsetParent !== null);
                }""")
                log(f"  [state] JS check: {state_html}")
                if "NOT FOUND" not in state_html:
                    state_visible = True

            if state_visible:
                log("  [state] Setting Oregon (keyboard)...")
                phenom_select_keyboard(page, "input-28", "Oregon", "state")
                time.sleep(1.5)

            ss(page, "v10_12_personal_filled")

            # ── Available Start Date ──────────────────────────────────────
            log("\n[6] Available Start Date...")
            if alive(page):
                fill_date_phenom(page, "Available_Start_Date_start_date")
            ss(page, "v10_13_date_filled")

            # ── Work Authorization ────────────────────────────────────────
            log("\n[7] Work Authorization...")
            if alive(page):
                # Q1 — keyboard approach (type "Y" to filter "Yes")
                phenom_select_keyboard(page, "input-10", "Yes", "work_auth_Q1")
                time.sleep(1.5)
                phenom_select_keyboard(page, "input-13", "Yes", "work_auth_Q2")
                time.sleep(1.5)
            ss(page, "v10_14_workauth_filled")

            # ── Voluntary Self-Identification ─────────────────────────────
            log("\n[8] EEO fields...")
            if alive(page):
                # Gender — keyboard
                phenom_select_keyboard(page, "input-16", "Woman", "gender")
                time.sleep(2.0)  # extra wait before ethnicity

                # Ethnicity — keyboard (type "Non" to filter)
                phenom_select_keyboard(page, "input-19", "Non Hispanic/Latino", "ethnicity")
                time.sleep(1.5)

                # Race checkbox
                check_asian_checkbox(page)
                time.sleep(1.0)

                # Disability — keyboard (type "No" to filter)
                phenom_select_keyboard(page, "input-22", "No, I don't have a disability", "disability")
                time.sleep(1.5)

                # Veteran — keyboard (type "No" to filter)
                phenom_select_keyboard(page, "input-25", "No", "veteran")
                time.sleep(1.5)

            ss(page, "v10_15_eeoc_filled")

            # ── Pre-submit check ──────────────────────────────────────────
            log("\n[9] Pre-submit check...")
            if alive(page):
                page.evaluate("window.scrollTo(0,0)"); time.sleep(1)
                ss(page, "v10_16_top")
                page.evaluate("window.scrollTo(0,document.body.scrollHeight)"); time.sleep(2)
                ss(page, "v10_16_bottom")

                body = txt(page)
                errors = [l.strip() for l in body.split('\n')
                          if any(w in l.lower() for w in [
                              "error found","error:","cannot be left blank",
                              "select a value","select at least one","select a country",
                              "select a gender","select a ethnicity",
                          ])]
                log(f"  Pre-submit errors: {errors[:8]}")

                if errors:
                    log("  [fix] Re-filling failed fields...")
                    # For each dropdown, try click approach as backup
                    for fid, desired, lbl in [
                        ("input-7", "United States", "country"),
                        ("input-10", "Yes", "work_auth_Q1"),
                        ("input-13", "Yes", "work_auth_Q2"),
                        ("input-16", "Woman", "gender"),
                        ("input-19", "Non Hispanic/Latino", "ethnicity"),
                        ("input-22", "No, I don't have a disability", "disability"),
                        ("input-25", "No", "veteran"),
                    ]:
                        if not alive(page): break
                        try:
                            val_js = page.evaluate(f"()=>{{let e=document.getElementById('{fid}');return e?e.value:''}}")
                            log(f"  [check] {lbl} = '{str(val_js)[:30]}'")
                            if not str(val_js).strip():
                                phenom_select_click(page, fid, desired, lbl)
                                time.sleep(1.5)
                        except: pass

                    # Re-check Asian
                    try:
                        cb = page.locator("#Voluntary_Self_Identification_race-Asian-2").first
                        if cb.count() > 0 and not cb.is_checked():
                            check_asian_checkbox(page)
                    except: pass
                    time.sleep(1)
                    ss(page, "v10_16b_refill")

            # ── Submit ────────────────────────────────────────────────────
            if alive(page):
                page.evaluate("window.scrollTo(0,0)"); time.sleep(1)
                ss(page, "v10_17_pre_submit")

            log("\n[10] Submitting...")
            if not alive(page):
                R["status"]="error"; R["notes"]="Page closed before submit"
                save(R); return R

            submit_clicked = False
            for s in ["button:has-text('Submit Application')","button:has-text('Submit application')",
                      "button:has-text('Submit')"]:
                try:
                    el = page.locator(s).first
                    if el.count() > 0 and el.is_visible(timeout=3000):
                        t_val = el.inner_text().strip().lower()
                        if any(bad in t_val for bad in ["subscribe","newsletter"]): continue
                        el.scroll_into_view_if_needed()
                        ss(page, "v10_18_about_to_submit")
                        el.click(timeout=5000)
                        submit_clicked = True
                        log(f"  [submit] Clicked: {s}")
                        time.sleep(12); net(page, 20000)
                        break
                except Exception as e:
                    log(f"  [submit!] {s}: {e}")

            if not submit_clicked:
                R["status"]="blocked"
                R["notes"]=f"No submit button. URL: {page.url}. Body: {txt(page)[:300]}"
                try: browser.close()
                except: pass
                save(R); return R

            # ── Post-submit ───────────────────────────────────────────────
            if not alive(page):
                R["status"]="likely-submitted"
                R["confirmed_at"]=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                R["notes"]="Submit clicked but page closed."
                save(R); return R

            body = txt(page)
            ss(page, "v10_19_post_submit")
            log(f"  Post-submit URL: {page.url}")
            log(f"  Post-submit body: {body[:600]}")

            if has_captcha(page):
                R["status"]="captcha-staged"; R["notes"]=f"CAPTCHA after Submit. URL: {page.url}"
                try: browser.close()
                except: pass
                save(R); return R

            if is_real_confirmation(body, page.url):
                R["status"]="submitted"
                R["confirmed_at"]=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                R["screenshot"]=os.path.join(SHOT,"v10_19_post_submit.png")
                R["notes"]=f"SUBMITTED. {body[:600]}"
                log("  *** CONFIRMED SUBMISSION! ***")
                try: browser.close()
                except: pass
                save(R); return R

            error_lines = [l.strip() for l in body.split('\n')
                           if any(w in l.lower() for w in [
                               "error found","error:","cannot be left blank",
                               "select a value","select at least one"
                           ])]
            if error_lines:
                log(f"  Still errors: {error_lines[:5]}")
                R["status"]="blocked"
                R["notes"]=(f"Submit but errors: {error_lines[:5]}. URL:{page.url}. Body:{body[:400]}")
                try: browser.close()
                except: pass
                save(R); return R

            R["status"]="likely-submitted"
            R["confirmed_at"]=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            R["screenshot"]=os.path.join(SHOT,"v10_19_post_submit.png")
            R["notes"]=f"Submit clicked. No errors. Body:{body[:600]}"
            try: browser.close()
            except: pass
            save(R); return R

        except Exception as e:
            tb = traceback.format_exc()
            log(f"\n[EXCEPTION] {e}\n{tb[:1000]}")
            R["status"]="error"
            R["notes"]=f"Exception: {str(e)}\n{tb[:500]}"
            try:
                if alive(page): ss(page, "v10_99_exception")
            except: pass
            try: browser.close()
            except: pass
            save(R); return R


if __name__ == "__main__":
    main()
