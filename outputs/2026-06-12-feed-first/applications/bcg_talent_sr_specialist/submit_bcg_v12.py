# -*- coding: utf-8 -*-
"""
submit_bcg_v12.py -- BCG Phenom ATS (v12)

Key insight from v10:
  - Keyboard type "Unite" → dropdown shows filtered list with United States visible.
    Patchright locator click on the li should work. The JS MouseEvent dispatch was
    used as fallback but doesn't trigger React state → State field stays NOT FOUND.
  - Fix: after typing to filter, use locator("li:has-text('United States')").click()
    with force=True to bypass any intercept. Patchright native click IS a proper
    DOM event that React can capture.
  - Date: header shows only month name, not year. Fix: check 'sep' in header AND
    count backwards correctly (start at current month = Jan 2026 or earlier).
    Actually v10 started at "Jan" which means the date field was already at Jan
    from a prior run. Need to navigate to the CORRECT year too.
    Better: detect year from header by looking at full title text, or just count
    exactly the number of back-clicks needed from current date.

State field: After Country is properly selected (React state committed via true click),
  the State field appears dynamically. We've seen it appear in v8 (profile pre-filled
  Washington). Need to select Oregon.
  But since it takes time to cascade, wait up to 10s.

Also: City field is showing 'Seattle' from profile — this is fine since role is Seattle,
but Country still blank means State cascade never fired.
"""
import os, sys, time, json, subprocess, traceback, datetime
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
SHOT     = ROLE_DIR + r"\screenshots\v12"
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
    for sel in ["button:has-text('Accept All and Close')","button:has-text('Accept All')",
                "#truste-consent-button","#onetrust-accept-btn-handler"]:
        try:
            el = page.locator(sel).first
            if el.count() > 0 and el.is_visible(timeout=2000):
                el.click(force=True); time.sleep(2); return
        except: continue
    try:
        page.evaluate("""()=>{
            document.querySelectorAll('[id*="truste"],[class*="truste"],[id*="trustarc"],'+
                '[class*="trustarc"],#onetrust-banner-sdk').forEach(e=>{e.style.display='none';});
            document.body.style.overflow='auto';
        }""")
    except: pass

def esc(page):
    try: page.keyboard.press("Escape"); time.sleep(0.4)
    except: pass
    try: page.keyboard.press("Escape"); time.sleep(0.3)
    except: pass

def fill_text(page, fid, val, lbl=""):
    if not alive(page): return False
    try:
        el = page.locator(f"#{fid}").first
        el.wait_for(state="visible", timeout=5000)
        el.scroll_into_view_if_needed()
        el.click(timeout=3000); el.fill(""); el.fill(val)
        log(f"  [fill] {lbl or fid} = '{val[:50]}'"); return True
    except Exception as e:
        try:
            page.evaluate("(a)=>{let e=document.getElementById(a[0]);if(e){e.focus();e.value=a[1];"
                "e.dispatchEvent(new Event('input',{bubbles:true}));"
                "e.dispatchEvent(new Event('change',{bubbles:true}));}}", [fid, val])
            log(f"  [fill-js] {lbl or fid} = '{val[:50]}'"); return True
        except: pass
        log(f"  [fill!] {lbl or fid}: {str(e)[:60]}"); return False


def phenom_type_and_click(page, field_id, filter_text, full_text, lbl=""):
    """
    Type filter_text into the combobox to filter options, then click the option
    using Patchright's native locator.click() which properly triggers React events.
    This is the ONLY approach that commits React state (needed for Country→State cascade).
    """
    if not alive(page): return False
    log(f"  [ddtc] {lbl or field_id} → '{full_text}' (filter: '{filter_text}')")
    esc(page)

    try:
        inp = page.locator(f"#{field_id}").first
        inp.wait_for(state="visible", timeout=8000)
        inp.scroll_into_view_if_needed()
        time.sleep(0.3)

        # Click to focus
        inp.click(timeout=5000)
        time.sleep(0.5)

        # Clear and type filter text — this triggers React's onChange
        page.keyboard.press("Control+a")
        page.keyboard.press("Delete")
        time.sleep(0.2)
        page.keyboard.type(filter_text, delay=80)
        time.sleep(1.5)

        ss(page, f"v11_typed_{field_id[:12]}")

        # Now use Patchright locator to find and click the matching option
        # Use filter(has_text=) for a more targeted match
        opt_locator = page.locator(f"[role='listbox'] li:has-text('{full_text}')")
        if opt_locator.count() == 0:
            opt_locator = page.locator(f"[role='option']:has-text('{full_text}')")
        if opt_locator.count() == 0:
            opt_locator = page.locator(f"[role='listbox'] li").filter(has_text=full_text)

        log(f"    option count: {opt_locator.count()}")

        if opt_locator.count() > 0:
            try:
                opt_locator.first.scroll_into_view_if_needed()
                opt_locator.first.click(timeout=5000)
                time.sleep(1.5)
                esc(page)
                log(f"    [ddtc-ok] locator click on '{full_text}'")
                return True
            except Exception as e:
                log(f"    [ddtc-intercept] {str(e)[:100]}")
                # Try with force=True
                try:
                    opt_locator.first.click(force=True, timeout=3000)
                    time.sleep(1.5)
                    esc(page)
                    log(f"    [ddtc-force-ok] forced click on '{full_text}'")
                    return True
                except Exception as e2:
                    log(f"    [ddtc-force!] {str(e2)[:80]}")

        # Fallback: press ArrowDown + Enter
        log(f"    [ddtc-arrow] trying arrow approach...")
        for _ in range(10):
            page.keyboard.press("ArrowDown"); time.sleep(0.15)
            active = page.evaluate("""()=>{
                let a = document.querySelector('[aria-selected="true"],[class*="focused"],[class*="highlight"]');
                return a ? a.textContent.trim() : '';
            }""")
            if full_text.lower() in active.lower():
                page.keyboard.press("Enter"); time.sleep(1.0)
                log(f"    [ddtc-arrow-ok] '{active}'")
                return True

        esc(page)
        log(f"    [ddtc-fail] '{full_text}'")
        return False

    except Exception as e:
        log(f"  [ddtc!] {str(e)[:80]}"); return False


def phenom_click_open(page, field_id, full_text, lbl=""):
    """Pure click approach — click to open, then click option. For EEO fields."""
    if not alive(page): return False
    log(f"  [ddc] {lbl or field_id} → '{full_text}'")
    esc(page)
    try:
        inp = page.locator(f"#{field_id}").first
        inp.wait_for(state="visible", timeout=8000)
        inp.scroll_into_view_if_needed()
        time.sleep(0.5)
        try: inp.click(timeout=5000)
        except: page.evaluate(f"document.getElementById('{field_id}').click()")
        time.sleep(2.0)

        for opt_sel in ["[role='listbox'] li","[role='option']","[class*='listbox'] li"]:
            try:
                opt = page.locator(opt_sel).filter(has_text=full_text).first
                if opt.count() > 0:
                    opt.click(timeout=4000); time.sleep(1.0); esc(page)
                    log(f"    [ddc-ok] '{full_text}'"); return True
            except Exception as e:
                try:
                    r = page.evaluate("""(t)=>{
                        for (let s of ['[role="listbox"] li','[role="option"]','[class*="listbox"] li']) {
                            for (let e of document.querySelectorAll(s)) {
                                if (e.textContent.trim().toLowerCase().includes(t.toLowerCase())) {
                                    e.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true}));
                                    return e.textContent.trim();
                                }
                            }
                        }
                        return null;
                    }""", full_text)
                    if r: time.sleep(1.0); esc(page); log(f"    [ddc-js-ok] '{r}'"); return True
                except: pass
        esc(page); log(f"    [ddc-fail] '{full_text}'"); return False
    except Exception as e:
        log(f"  [ddc!] {str(e)[:80]}"); return False


def fill_date_navigate(page, field_id):
    """
    Navigate the date picker calendar to Sep 2025.
    The calendar header shows only month name (Jan, Feb, ...) without year.
    Strategy: detect starting month, count back to reach Sep 2025.
    Current date: June 2026 = 9 months back to Sep 2025.
    But the date field may already show Jan 2025 from prior run (unclear start month).
    """
    if not alive(page): return False
    log(f"  [date] Opening date picker...")

    try:
        el = page.locator(f"#{field_id}").first
        el.wait_for(state="visible", timeout=8000)
        el.scroll_into_view_if_needed()

        # Check if already has a value
        cur_val = el.input_value()
        log(f"  [date] Current value: '{cur_val}'")

        # First clear any existing value by ctrl+a and delete
        el.click(timeout=5000)
        time.sleep(0.5)
        page.keyboard.press("Control+a")
        page.keyboard.press("Delete")
        page.keyboard.press("Backspace")
        time.sleep(0.5)
        cleared_val = el.input_value()
        log(f"  [date] After clear: '{cleared_val}'")
        # Re-click to open calendar
        el.click(timeout=5000)
        time.sleep(2.0)
        ss(page, "v11_date_open")

        # Get header — look for month YEAR format
        def get_header():
            return page.evaluate("""() => {
                // Find elements that look like month+year headers in a calendar context
                // They typically have text like "January 2025" or just "Jan" or "Jun 2026"
                let candidates = document.querySelectorAll('*');
                for (let el of candidates) {
                    if (el.children.length > 0) continue; // Skip non-leaf
                    let t = el.textContent.trim();
                    // Look for month-like text (short or long month names)
                    let months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec',
                                  'January','February','March','April','May','June','July','August',
                                  'September','October','November','December'];
                    let hasMonth = months.some(m => t.startsWith(m) || t.endsWith(m));
                    if (hasMonth && t.length < 25) return t;
                }
                // Try specific selectors
                let sels = [
                    '[class*="calendar"] [class*="title"]',
                    '[class*="datepicker"] [class*="title"]',
                    '[class*="month-title"]','[class*="monthTitle"]',
                    '[aria-live="polite"]',
                    'h2[class*="cal"]','[class*="header"] h2',
                ];
                for (let s of sels) {
                    let e = document.querySelector(s);
                    if (e && e.textContent.trim()) return e.textContent.trim();
                }
                return '';
            }""")

        def click_nav_btn(direction="next"):
            """Click next or previous month button using Patchright native click to preserve focus."""
            if direction == "next":
                pwright_sels = [
                    'button[aria-label*="Next month" i]',
                    'button[aria-label*="next" i]',
                    '[class*="nextMonth"]',
                    '[class*="next-month"]',
                ]
                kw = "next"
            else:
                pwright_sels = [
                    'button[aria-label*="Previous month" i]',
                    'button[aria-label*="previous" i]',
                    '[class*="prevMonth"]',
                    '[class*="prev-month"]',
                ]
                kw = "prev"

            # Try Patchright native click first (preserves focus in React calendar)
            for sel in pwright_sels:
                try:
                    loc = page.locator(sel).first
                    if loc.count() > 0 and loc.is_visible(timeout=1500):
                        lbl = loc.get_attribute("aria-label") or sel
                        loc.click(timeout=3000)
                        return lbl[:50]
                except: pass

            # Fallback: JS click (may lose focus)
            return page.evaluate("""({kw}) => {
                let sels = [
                    'button[aria-label*="' + kw + ' month" i]',
                ];
                let dialog = document.querySelector('[role="dialog"],[class*="calendar"],[class*="datepicker"]');
                let btns = (dialog || document).querySelectorAll('button');
                for (let btn of btns) {
                    let lbl = (btn.getAttribute('aria-label') || '').toLowerCase();
                    let cls = (btn.className || '').toLowerCase();
                    if ((lbl.includes(kw) || cls.includes(kw)) &&
                        btn.offsetParent !== null && !btn.disabled) {
                        btn.click();
                        return 'js-fallback: ' + lbl.substring(0,40);
                    }
                }
                return null;
            }""", {"kw": kw})

        # Navigate from current displayed month to Sep 2025.
        # Current date field value = "20 Jan 2025" (from prior run) → calendar starts at Jan 2025.
        # But we might start at current month (June 2026) if value was cleared.
        # Strategy: detect start month, then navigate FORWARD if < Sep 2025, or BACKWARD if > Sep 2025.
        month_map = {
            'jan':1,'feb':2,'mar':3,'apr':4,'may':5,'jun':6,
            'jul':7,'aug':8,'sep':9,'oct':10,'nov':11,'dec':12,
            'january':1,'february':2,'march':3,'april':4,'june':6,
            'july':7,'august':8,'september':9,'october':10,'november':11,'december':12
        }
        import re
        # Target: Sep 2026 (future date — BCG may require start date to be in the future)
        # Today is June 2026, so Sep 2026 = 3 months away
        target_month, target_year = 9, 2026

        # Track how many steps we've taken to infer year when header shows no year
        # Start by getting initial header to determine starting month
        initial_header = get_header()
        log(f"  [date] Initial header: '{initial_header}'")
        h0 = initial_header.lower()
        start_m = None
        for name, num in month_map.items():
            if name in h0:
                start_m = num; break
        yr_m = re.search(r'\b(202[0-9])\b', h0)
        start_y = int(yr_m.group(1)) if yr_m else None

        # If we don't know year but know month, guess: if month > 9, likely 2025; if < 9, could be 2026
        if start_y is None and start_m is not None:
            # Most likely: prior value was Jan 2025, calendar shows Jan = 2025
            # OR current date Jun 2026
            # We'll infer by checking the day grid for year clues
            day_text = page.evaluate("""() => {
                let d = document.querySelector('[role="dialog"],[class*="calendar"],[class*="datepicker"]');
                return d ? d.textContent.trim().replace(/\\s+/g,' ').substring(0,200) : '';
            }""")
            log(f"  [date] Calendar text: '{day_text[:100]}'")
            # If calendar shows year in text, extract it
            yr2 = re.search(r'\b(202[0-9])\b', day_text)
            if yr2: start_y = int(yr2.group(1))
            else:
                # Assume: if prior run set Jan, we're at Jan 2025
                # Otherwise assume Jun 2026 (current date)
                if start_m == 1: start_y = 2025
                elif start_m == 6: start_y = 2026
                else: start_y = 2025  # best guess

        log(f"  [date] Start: month={start_m} year={start_y} → target: Sep 2025")

        # Calculate number of steps needed
        if start_m and start_y:
            start_total = start_y * 12 + start_m
            target_total = target_year * 12 + target_month
            steps = target_total - start_total  # positive = forward, negative = backward
            log(f"  [date] Steps needed: {steps} ({'next' if steps > 0 else 'prev'})")
        else:
            steps = 8  # default: assume Jan 2025, need to go forward 8 to Sep 2025

        for attempt in range(abs(steps) + 5):
            if not alive(page): break
            header = get_header()
            log(f"    [cal] header: '{header}'")
            h = header.lower().strip()
            cur_m = None
            for name, num in month_map.items():
                if name in h: cur_m = num; break
            yr_m = re.search(r'\b(202[0-9])\b', h)
            cur_y = int(yr_m.group(1)) if yr_m else None

            # Use running counter to infer year if not in header
            if cur_y is None and start_y is not None and start_m is not None:
                steps_taken = attempt
                inferred_total = (start_y * 12 + start_m) + (steps_taken * (1 if steps >= 0 else -1))
                cur_y = inferred_total // 12
                # recalculate cur_m too
                cur_m_inf = inferred_total % 12
                if cur_m_inf == 0: cur_m_inf = 12; cur_y -= 1
                if cur_m is None: cur_m = cur_m_inf

            log(f"    [cal] parsed: month={cur_m} year={cur_y}")

            log(f"    [cal] check: cur_m={cur_m}=={target_month}? cur_y={cur_y}=={target_year}? None={cur_y is None}")
            if cur_m == target_month and (cur_y == target_year or cur_y is None):
                log(f"  [date] Reached {target_month}/{target_year}!")
                break

            direction = "next" if steps >= 0 else "prev"
            result = click_nav_btn(direction)
            log(f"    [cal] {direction}: {result}")
            time.sleep(0.7)

        ss(page, "v12_date_calendar")

        # Verify calendar is still open after navigation
        cal_still_open = page.evaluate("""() => {
            let d = document.querySelector('[role="dialog"]');
            return d && d.offsetParent !== null;
        }""")
        log(f"  [date] Calendar open after nav: {cal_still_open}")
        if not cal_still_open:
            log(f"  [date] Calendar closed — reopening")
            el.click(timeout=5000); time.sleep(1.5)
            # Quick re-nav: check header, navigate if needed
            hdr2 = get_header().lower()
            if "sep" not in hdr2:
                log(f"  [date] Re-nav from '{hdr2}' to Sep")
                for _ in range(20):
                    hdr2 = get_header().lower()
                    if "sep" in hdr2: break
                    click_nav_btn("next"); time.sleep(0.5)
            log(f"  [date] After re-nav: '{get_header()}'")
            ss(page, "v12_date_reopened")

        # Dump calendar DOM structure to understand clickable elements
        cal_dom = page.evaluate("""() => {
            // Find by gridcells directly (not scoped to dialog)
            let cells = document.querySelectorAll('[role="gridcell"]');
            let info = [];
            for (let el of cells) {
                let t = el.textContent.trim();
                info.push({
                    tag: el.tagName,
                    cls: el.className.substring(0,60),
                    txt: t.substring(0,10),
                    dis: el.getAttribute('aria-disabled'),
                    sel: el.getAttribute('aria-selected'),
                    parent: el.parentElement ? el.parentElement.tagName + '.' + el.parentElement.className.substring(0,30) : '',
                    hasBtn: el.querySelector('button') ? 'yes' : 'no',
                    rect: (() => { let r = el.getBoundingClientRect(); return `${Math.round(r.left)},${Math.round(r.top)},${Math.round(r.width)}x${Math.round(r.height)}`; })()
                });
            }
            // Also check what container has "Sep" in it
            let all = document.querySelectorAll('*');
            let calContainer = null;
            for (let el of all) {
                if (el.children.length === 0 && el.textContent.trim() === 'Sep') {
                    calContainer = el.parentElement ? el.parentElement.outerHTML.substring(0,200) : 'no parent';
                    break;
                }
            }
            return JSON.stringify({cells: info.slice(0,15), calContainer});
        }""")
        log(f"  [date] Calendar DOM: {cal_dom[:800]}")

        # Approach 1: mouse.click() at actual coordinates of the picker-cell-start TD
        # DOM showed: td[class*="picker-cell-start"] text="1" at rect 498,560 size 36x36
        # Use page.mouse.click() for real browser-level pointer event
        log(f"  [date] Clicking day cell via coordinates (real browser mouse event)...")
        day_clicked_native = False

        # Get the actual coordinates of the day "1" cell
        day_coord = page.evaluate("""() => {
            // First try: find cells with specific class that mark start of month
            let cells = document.querySelectorAll('td[class*="ocpicker"]');
            for (let td of cells) {
                if (td.textContent.trim() === '1') {
                    let r = td.getBoundingClientRect();
                    return {x: r.left + r.width/2, y: r.top + r.height/2,
                            cls: td.className.substring(0,80), tag: td.tagName,
                            w: r.width, h: r.height};
                }
            }
            // Also try all TDs
            let all_tds = document.querySelectorAll('td');
            let results = [];
            for (let td of all_tds) {
                let t = td.textContent.trim();
                if (t === '1') {
                    let r = td.getBoundingClientRect();
                    if (r.width > 0) results.push({x: r.left+r.width/2, y: r.top+r.height/2, cls: td.className.substring(0,60)});
                }
            }
            return results.length > 0 ? results[0] : null;
        }""")

        log(f"  [date] Day coord: {day_coord}")
        if day_coord:
            x, y = day_coord['x'], day_coord['y']
            log(f"  [date] Day '1' at ({x}, {y})")
            # Try mouse move + down + up sequence (full pointer event chain)
            page.mouse.move(x, y)
            time.sleep(0.1)
            page.mouse.down()
            time.sleep(0.05)
            page.mouse.up()
            time.sleep(0.5)
            v1 = el.input_value()
            log(f"  [date] After mousedown+up: '{v1}'")
            if "sep" not in v1.lower() or "2026" not in v1:
                # Also try locator.click() on this specific element
                try:
                    loc_cell = page.locator('td[class*="picker-cell-start"]').first
                    if loc_cell.count() > 0:
                        loc_cell.click(timeout=3000)
                        v2 = el.input_value()
                        log(f"  [date] After locator.click on picker-cell-start: '{v2}'")
                except: pass
            day_clicked_native = True

        time.sleep(1.5)
        esc(page); time.sleep(0.5)
        ss(page, "v12_date_after_enter")
        # Scroll to the date field and screenshot its actual rendered value
        el.scroll_into_view_if_needed()
        time.sleep(0.5)
        ss(page, "v12_date_field_view")
        val_after_kbd = el.input_value()
        # Also check the placeholder or displayed value via attribute
        val_placeholder = page.evaluate(f"""() => {{
            let e = document.getElementById('{field_id}');
            if (!e) return 'NOT_FOUND';
            // Try React state injection
            let result = {{
                value: e.value,
                placeholder: e.placeholder,
                readOnly: e.readOnly,
                disabled: e.disabled,
                type: e.type,
                data: e.getAttribute('data-value'),
                aria: e.getAttribute('aria-valuenow') || e.getAttribute('aria-label'),
            }};
            // Try direct React setter injection
            try {{
                let nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                nativeSetter.call(e, '01 Sep 2026');
                e.dispatchEvent(new Event('input', {{bubbles:true}}));
                e.dispatchEvent(new Event('change', {{bubbles:true}}));
                result.afterInject = e.value;
            }} catch(ex) {{
                result.injectErr = ex.message;
            }}
            return result;
        }}""")
        log(f"  [date] Input attributes: {val_placeholder}")
        log(f"  [date] Value after native click: '{val_after_kbd}'")

        if "sep" in val_after_kbd.lower() and "2025" in val_after_kbd:
            log(f"  [date] Native click succeeded: '{val_after_kbd}'")
            esc(page); time.sleep(0.5)
        else:
            log(f"  [date] Keyboard didn't commit; trying locator day click...")
            # Need to reopen calendar if it closed
            cur_v2 = el.input_value()
            # Check if calendar is still open
            cal_open = page.evaluate("""() => {
                let d = document.querySelector('[role="dialog"],[class*="calendar"],[class*="datepicker"]');
                return d && d.offsetParent !== null;
            }""")
            if not cal_open:
                log(f"  [date] Reopening calendar for day click...")
                el.click(timeout=5000); time.sleep(1.5)
                # Re-navigate to Sep if needed
                hdr = get_header().lower()
                if "sep" not in hdr:
                    log(f"  [date] Re-nav needed from '{hdr}'")
                    # Quick re-navigate
                    for _ in range(20):
                        hdr = get_header().lower()
                        if "sep" in hdr: break
                        click_nav_btn("next"); time.sleep(0.5)

            # Click day 1 — use Patchright native locator.click() so React synthetic events fire
            day_clicked = False
            for day_sel in [
                '[role="gridcell"]:not([aria-disabled="true"]) button',
                'td:not([class*="outside"]):not([class*="other"]) button',
                '[role="gridcell"]:not([aria-disabled="true"])',
                'td:not([class*="outside"]):not([class*="other"])',
                'button[class*="day"]:not([disabled])',
            ]:
                try:
                    day_loc = page.locator(day_sel).filter(has_text="1")
                    exact_day = None
                    cnt = day_loc.count()
                    for i in range(min(cnt, 15)):
                        try:
                            txt_i = day_loc.nth(i).inner_text(timeout=1000).strip()
                            if txt_i == "1":
                                exact_day = day_loc.nth(i)
                                break
                        except: pass
                    if exact_day:
                        exact_day.scroll_into_view_if_needed()
                        exact_day.click(timeout=5000)
                        log(f"  [date] Day 1 click via locator: {day_sel}")
                        day_clicked = True
                        break
                except Exception as ex:
                    log(f"  [date-day-try] {day_sel}: {str(ex)[:60]}")

            if not day_clicked:
                # JS fallback — also try clicking the aria-selected or focused cell
                r = page.evaluate("""() => {
                    let sels = [
                        '[role="gridcell"]:not([aria-disabled="true"]) button',
                        '[role="gridcell"]:not([aria-disabled="true"])',
                        'td button:not([disabled])',
                    ];
                    for (let s of sels) {
                        for (let el of document.querySelectorAll(s)) {
                            if (el.textContent.trim() === '1') {
                                el.scrollIntoView({block:'center'});
                                let rc = el.getBoundingClientRect();
                                ['mousedown','mouseup','click'].forEach(ev=>
                                    el.dispatchEvent(new MouseEvent(ev,{bubbles:true,cancelable:true,
                                        clientX:rc.left+rc.width/2,clientY:rc.top+rc.height/2})));
                                return 'js:'+s;
                            }
                        }
                    }
                    return null;
                }""")
                log(f"  [date] Day 1 JS fallback: {r}")

            time.sleep(1.0)
            esc(page); time.sleep(0.5)

        final_val = el.input_value()
        log(f"  [date] Final value: '{final_val}'")
        # If value still old, check if it updated visually
        if "sep" not in final_val.lower() and "2025" not in final_val:
            # Try reading value differently
            alt_val = page.evaluate(f"()=>{{let e=document.getElementById('{field_id}');return e?e.value:'';}}")
            log(f"  [date] Alt value check: '{alt_val}'")
        return True

    except Exception as e:
        log(f"  [date!] {e}"); return False


def check_asian_checkbox(page):
    cb_id = "Voluntary_Self_Identification_race-Asian-2"
    if not alive(page): return False
    try:
        cb = page.locator(f"#{cb_id}").first
        if cb.count() > 0:
            cb.scroll_into_view_if_needed(); time.sleep(0.5)
            if cb.is_checked(): log("  [race-ok] already checked"); return True
            cb.click(force=True, timeout=3000); time.sleep(0.8)
            if cb.is_checked(): log("  [race-ok] force click"); return True
    except: pass
    try:
        r = page.evaluate("""()=>{
            let cb = document.getElementById('Voluntary_Self_Identification_race-Asian-2');
            if (!cb) return 'not found';
            cb.scrollIntoView({block:'center'});
            let rc = cb.getBoundingClientRect();
            let cx = rc.left+rc.width/2, cy = rc.top+rc.height/2;
            ['mousedown','mouseup','click'].forEach(ev=>
                cb.dispatchEvent(new MouseEvent(ev,{bubbles:true,cancelable:true,clientX:cx,clientY:cy}))
            );
            return 'clicked,checked='+cb.checked;
        }""")
        log(f"  [race-js] {r}"); time.sleep(0.5)
        try:
            if page.locator(f"#{cb_id}").first.is_checked():
                log("  [race-ok] JS click"); return True
        except: pass
    except: pass
    try:
        page.evaluate("""()=>{
            let cb=document.getElementById('Voluntary_Self_Identification_race-Asian-2');
            if(cb){let s=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'checked').set;
            s.call(cb,true);cb.dispatchEvent(new Event('change',{bubbles:true}));}
        }""")
        log("  [race-setter] applied"); return True
    except: pass
    log("  [race-fail]"); return False


def is_real_confirmation(body, url=""):
    t = body.lower()
    if "login" in url.lower() or ("sign in" in t and "password" in t and "careerhub" not in url.lower()):
        return False
    return any(p in t for p in [
        "thank you for applying","your application has been submitted",
        "application successfully submitted","we have received your application",
        "you have successfully applied","successfully applied to",
    ])

def save(result):
    path = os.path.join(ROLE_DIR, "SUBMITTED.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    log(f"\n[SAVED] {path}")
    log("="*60); log(f"RESULT: {result['status']}")
    log(f"Notes:  {str(result.get('notes',''))[:600]}"); log("="*60)


def main():
    R = {
        "company": "BCG (Boston Consulting Group)",
        "role": "Talent Senior Specialist - People",
        "ats": "Phenom (experiencedtalent.bcg.com)",
        "status": "in_progress",
        "confirmed_at": None, "screenshot": None,
        "account_email": EMAIL, "notes": "",
        "job_url": JOB_PUBLIC_URL, "apply_url": PHENOM_APPLY,
    }

    log("="*60); log("BCG Phenom v12 -- Talent Senior Specialist - People"); log("="*60)

    subprocess.run(["powershell","-Command",
        f"Get-NetTCPConnection -LocalPort {PORT} -ErrorAction SilentlyContinue | "
        f"Select-Object -ExpandProperty OwningProcess | "
        f"ForEach-Object {{Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue}}"],
        capture_output=True, timeout=10)
    time.sleep(3)

    log(f"\n[1] Chrome on port {PORT}...")
    proc = subprocess.Popen(
        [CHROME, f"--remote-debugging-port={PORT}", f"--user-data-dir={PROFILE}",
         "--no-first-run","--no-default-browser-check",
         "--disable-blink-features=AutomationControlled", PHENOM_LOGIN],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    log(f"  PID {proc.pid}, waiting 15s..."); time.sleep(15)

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(f"http://localhost:{PORT}")
        ctx = browser.contexts[0]
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.set_default_timeout(30000)

        try:
            net(page, 20000); time.sleep(3)
            dismiss_cookie(page); time.sleep(2)
            ss(page, "v11_01_initial")
            log(f"  URL: {page.url}")

            # Login
            log("\n[2] Login...")
            if "login" in page.url.lower():
                for s in ["input[type='email']","input[placeholder*='Email' i]","input[id*='email' i]"]:
                    try:
                        el = page.locator(s).first
                        if el.count()>0 and el.is_visible(timeout=3000):
                            el.click(); el.fill(""); el.fill(EMAIL); log("  [fill] email"); break
                    except: continue
                page.locator("button:has-text('Continue')").first.click()
                time.sleep(7); net(page,15000); dismiss_cookie(page)
                ss(page,"v11_02_email"); body=txt(page)
                if "captcha" in body.lower():
                    R["status"]="captcha-staged"; save(R); return R
                if any(k in body.lower() for k in ["verify your email","check your inbox"]):
                    R["status"]="email-verify-staged"; save(R); return R
                if "password" in body.lower():
                    pws=page.locator("input[type='password']").all()
                    if pws: pws[0].click(); pws[0].fill(PW); log("  [fill] password")
                    page.locator("button:has-text('Submit')").first.click()
                    time.sleep(8); net(page,15000); dismiss_cookie(page)
                    ss(page,"v11_03_signin"); log(f"  URL: {page.url}")
                    if "login" in page.url.lower():
                        try: page.locator("a:has-text('Use a one-time code instead')").first.click()
                        except: pass
                        R["status"]="email-verify-staged"; save(R); return R

            # Form
            log("\n[3] Load form...")
            page.goto(PHENOM_APPLY, timeout=30000, wait_until="domcontentloaded")
            time.sleep(8); net(page,15000); dismiss_cookie(page); time.sleep(2)
            ss(page,"v11_10_form"); log(f"  URL: {page.url}")
            if "login" in page.url.lower():
                R["status"]="email-verify-staged"; save(R); return R

            # Upload resume
            log("\n[4] Upload resume...")
            for s in ["input[type='file'][accept*='pdf' i]","input[type='file']"]:
                try:
                    inputs=page.locator(s).all()
                    if inputs:
                        inputs[0].set_input_files(RESUME); time.sleep(6)
                        log(f"  [upload] {s}")
                        for d in ["No, thanks","Skip","No thanks","Enter Manually"]:
                            try:
                                el=page.get_by_text(d,exact=False).first
                                if el.count()>0 and el.is_visible(timeout=2000):
                                    el.click(); time.sleep(2); break
                            except: pass
                        break
                except Exception as e: log(f"  [upload!] {e}")
            ss(page,"v11_11_resume")

            # Personal info
            log("\n[5] Personal info...")
            for fid,val,lbl in [
                ("Before_applying_email",EMAIL,"email"),
                ("Before_applying_firstname","Yi-Chieh","first"),
                ("Before_applying_lastname","Cheng","last"),
                ("Before_applying_phone","2137003831","phone"),
                ("Before_applying_location","Seattle","city"),
            ]:
                try:
                    el=page.locator(f"#{fid}").first
                    if el.count()>0 and el.is_visible(timeout=1500):
                        cur=el.input_value().strip()
                        if not cur: fill_text(page,fid,val,lbl)
                        else: log(f"  [skip] {lbl}='{cur[:30]}'")
                except: pass
            try:
                el=page.locator("#Before_applying_preferred_first_name").first
                if el.count()>0 and el.is_visible(timeout=1500) and not el.input_value().strip():
                    fill_text(page,"Before_applying_preferred_first_name","Jamie","pref")
            except: pass

            # Country — type+locator click
            log("  [country] Setting United States...")
            country_ok = phenom_type_and_click(page, "input-7", "Unite", "United States", "country")
            log(f"  [country] result: {country_ok}")
            time.sleep(5)  # wait for State cascade

            # Find State field dynamically — ID changes based on how many dynamic fields were added
            # After Country loads, State appears with a new ID (observed: input-31, may vary)
            # Find it by its aria-labelledby attribute containing 'state'
            state_field_id = None
            time.sleep(2)  # extra wait for cascade
            try:
                state_field_id = page.evaluate("""() => {
                    let els = document.querySelectorAll('input[placeholder="Select"]');
                    for (let el of els) {
                        let lbl = (el.getAttribute('aria-labelledby') || '').toLowerCase();
                        if (lbl.includes('state') || lbl.includes('province')) {
                            return el.id;
                        }
                    }
                    // Also check label text nearby
                    let allInputs = document.querySelectorAll('input[placeholder="Select"]');
                    for (let inp of allInputs) {
                        let parent = inp.closest('[class*="field"],[class*="form-group"],[class*="grid"]');
                        if (parent) {
                            let lbl = parent.querySelector('label,span[class*="label"]');
                            if (lbl && lbl.textContent.toLowerCase().includes('state')) {
                                return inp.id;
                            }
                        }
                    }
                    return null;
                }""")
                log(f"  [state] Dynamic field ID: {state_field_id}")
            except Exception as e:
                log(f"  [state!] {e}")

            if state_field_id:
                log(f"  [state] Setting Washington (already pre-filled, verifying)...")
                # Check current value — profile pre-fills Washington, which is fine for Seattle role
                try:
                    cur_state = page.evaluate(f"()=>{{let e=document.getElementById('{state_field_id}');return e?e.value:''}}")
                    log(f"  [state] Current: '{cur_state}'")
                    if not cur_state.strip():
                        # Need to set it — use Washington since role is Seattle
                        phenom_type_and_click(page, state_field_id, "Wash", "Washington", "state")
                        time.sleep(1.5)
                    else:
                        log(f"  [state] Already set to '{cur_state}', keeping")
                except: pass
            else:
                state_info = page.evaluate("""()=>{
                    let els = document.querySelectorAll('input[placeholder="Select"]');
                    let r = [];
                    for (let el of els) {
                        r.push({id:el.id,value:el.value,label:(el.getAttribute('aria-labelledby')||'')});
                    }
                    return JSON.stringify(r);
                }""")
                log(f"  [state] All Select inputs: {state_info[:400]}")

            ss(page,"v11_12_personal")

            # Date
            log("\n[6] Date...")
            if alive(page):
                fill_date_navigate(page, "Available_Start_Date_start_date")
            ss(page,"v11_13_date")

            # Work Auth
            log("\n[7] Work Auth...")
            if alive(page):
                phenom_type_and_click(page,"input-10","Y","Yes","Q1_authorized")
                time.sleep(1.5)
                phenom_type_and_click(page,"input-13","Y","Yes","Q2_sponsor")
                time.sleep(1.5)
            ss(page,"v11_14_workauth")

            # EEO
            log("\n[8] EEO...")
            if alive(page):
                phenom_type_and_click(page,"input-16","Wom","Woman","gender")
                time.sleep(2.0)
                phenom_type_and_click(page,"input-19","Non","Non Hispanic/Latino","ethnicity")
                time.sleep(1.5)
                check_asian_checkbox(page); time.sleep(1.0)
                phenom_click_open(page,"input-22","No, I don't have a disability","disability")
                time.sleep(1.5)
                phenom_type_and_click(page,"input-25","N","No","veteran")
                time.sleep(1.5)
            ss(page,"v11_15_eeo")

            # Pre-submit check
            log("\n[9] Pre-submit check...")
            if alive(page):
                page.evaluate("window.scrollTo(0,0)"); time.sleep(1)
                ss(page,"v11_16_top")
                page.evaluate("window.scrollTo(0,document.body.scrollHeight)"); time.sleep(2)
                ss(page,"v11_16_bottom")
                body=txt(page)
                errors=[l.strip() for l in body.split('\n')
                        if any(w in l.lower() for w in [
                            "error found","error:","cannot be left blank",
                            "select a value","select at least one","select a country",
                        ])]
                log(f"  Errors: {errors[:8]}")
                if errors:
                    # Re-check all + re-apply Country
                    for fid,flt,full,lbl in [
                        ("input-7","Unite","United States","country"),
                        ("input-10","Y","Yes","Q1"),
                        ("input-13","Y","Yes","Q2"),
                        ("input-16","Wom","Woman","gender"),
                        ("input-19","Non","Non Hispanic/Latino","ethnicity"),
                        ("input-25","N","No","veteran"),
                    ]:
                        if not alive(page): break
                        v=page.evaluate(f"()=>{{let e=document.getElementById('{fid}');return e?e.value:'';}}")
                        log(f"  [v] {lbl}='{str(v)[:30]}'")
                        # Refill if blank OR if value doesn't start with expected prefix
                        # e.g. 'Hispanic/Latino' != 'Non Hispanic/Latino' → needs refill
                        v_lower = str(v).strip().lower()
                        full_lower = full.lower()
                        # Match if v starts with full, OR full starts with v (prefix match)
                        # But NOT if they merely share a suffix (Hispanic/Latino vs Non Hispanic/Latino)
                        correct = v_lower and (v_lower.startswith(full_lower[:6]) and full_lower.startswith(v_lower[:6]))
                        needs_refill = not v_lower or not correct
                        if needs_refill:
                            log(f"  [refill] {lbl}: '{str(v)[:25]}' → '{full}'")
                            phenom_type_and_click(page,fid,flt,full,lbl); time.sleep(1.5)
                    try:
                        cb=page.locator("#Voluntary_Self_Identification_race-Asian-2").first
                        if cb.count()>0 and not cb.is_checked(): check_asian_checkbox(page)
                    except: pass
                    # Disability re-check
                    v22=page.evaluate("()=>{let e=document.getElementById('input-22');return e?e.value:''}")
                    if not str(v22).strip():
                        phenom_click_open(page,"input-22","No, I don't have a disability","dis2"); time.sleep(1.5)
                    time.sleep(1); ss(page,"v11_16b_refill")

            # Submit
            if alive(page): page.evaluate("window.scrollTo(0,0)"); time.sleep(1); ss(page,"v11_17_presub")
            log("\n[10] Submit...")
            if not alive(page): R["status"]="error"; R["notes"]="Page closed"; save(R); return R

            sub_clicked=False
            for s in ["button:has-text('Submit Application')","button:has-text('Submit application')",
                      "button:has-text('Submit')"]:
                try:
                    el=page.locator(s).first
                    if el.count()>0 and el.is_visible(timeout=3000):
                        t_v=el.inner_text().strip().lower()
                        if any(b in t_v for b in ["subscribe","newsletter"]): continue
                        el.scroll_into_view_if_needed()
                        ss(page,"v11_18_submit_btn")
                        el.click(timeout=5000); sub_clicked=True
                        log(f"  [submit] {s}"); time.sleep(12); net(page,20000); break
                except Exception as e: log(f"  [submit!] {s}: {e}")

            if not sub_clicked:
                R["status"]="blocked"; R["notes"]=f"No submit btn. URL:{page.url}"
                try: browser.close()
                except: pass
                save(R); return R

            if not alive(page):
                R["status"]="likely-submitted"
                R["confirmed_at"]=time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())
                R["notes"]="Submit clicked, page closed."; save(R); return R

            body=txt(page); ss(page,"v11_19_post"); log(f"  URL: {page.url}"); log(f"  Body: {body[:500]}")

            if is_real_confirmation(body,page.url):
                R["status"]="submitted"
                R["confirmed_at"]=time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())
                R["screenshot"]=os.path.join(SHOT,"v11_19_post.png")
                R["notes"]=f"SUBMITTED. {body[:500]}"
                log("  *** CONFIRMED ***")
                try: browser.close()
                except: pass
                save(R); return R

            errs=[l.strip() for l in body.split('\n')
                  if any(w in l.lower() for w in ["error found","error:","select a","cannot be left blank"])]
            if errs:
                R["status"]="blocked"; R["notes"]=f"Errors: {errs[:5]}. URL:{page.url}. Body:{body[:300]}"
                try: browser.close()
                except: pass
                save(R); return R

            R["status"]="likely-submitted"
            R["confirmed_at"]=time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())
            R["screenshot"]=os.path.join(SHOT,"v11_19_post.png")
            R["notes"]=f"Submit no-error. Body:{body[:500]}"
            try: browser.close()
            except: pass
            save(R); return R

        except Exception as e:
            tb=traceback.format_exc()
            log(f"\n[EX] {e}\n{tb[:800]}")
            R["status"]="error"; R["notes"]=f"{str(e)}\n{tb[:400]}"
            try:
                if alive(page): ss(page,"v11_99_ex")
            except: pass
            try: browser.close()
            except: pass
            save(R); return R


if __name__ == "__main__":
    main()
