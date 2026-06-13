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
SHOT     = ROLE_DIR + r"\screenshots\v13"
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
    v13: Navigate the date picker calendar to Sep 2026.
    New strategies:
    1. Direct text input: type '01 Sep 2026' directly into the input field
    2. Click a DIFFERENT day first (Sep 15), then click Sep 1 — forces React selection event
    3. PointerEvent dispatch (React 17+ primary event path, different from MouseEvent)
    4. Keep the proven calendar navigation (works) + enhanced cell-click approaches
    """
    if not alive(page): return False
    log(f"  [date] v13 Opening date picker...")

    import re

    try:
        el = page.locator(f"#{field_id}").first
        el.wait_for(state="visible", timeout=8000)
        el.scroll_into_view_if_needed()

        # Check current value
        cur_val = el.input_value()
        log(f"  [date] Current value: '{cur_val}'")

        # ── Strategy A: Direct keyboard input ─────────────────────────────────
        # Some Phenom date fields accept direct text. Try typing the date directly
        # and pressing Tab/Enter to commit. This bypasses the calendar entirely.
        log(f"  [date] [A] Trying direct keyboard input...")
        el.click(timeout=5000); time.sleep(0.5)
        page.keyboard.press("Control+a"); page.keyboard.press("Delete")
        time.sleep(0.3)
        page.keyboard.type("01 Sep 2026", delay=60)
        time.sleep(0.8)
        page.keyboard.press("Tab")   # Tab often commits a date input
        time.sleep(0.8)
        val_a = el.input_value()
        log(f"  [date] [A] After type+Tab: '{val_a}'")
        if "sep" in val_a.lower() and "2026" in val_a:
            log(f"  [date] [A] Direct input succeeded!")
            esc(page); time.sleep(0.5); ss(page, "v13_date_direct")
            return True
        # Tab may have moved focus away; click back
        el.click(timeout=5000); time.sleep(0.5)
        page.keyboard.press("Control+a"); page.keyboard.press("Delete")
        time.sleep(0.2)
        page.keyboard.type("01 Sep 2026", delay=60)
        time.sleep(0.8)
        page.keyboard.press("Enter")
        time.sleep(0.8)
        val_a2 = el.input_value()
        log(f"  [date] [A2] After type+Enter: '{val_a2}'")
        if "sep" in val_a2.lower() and "2026" in val_a2:
            log(f"  [date] [A2] Direct input+Enter succeeded!")
            esc(page); time.sleep(0.5); ss(page, "v13_date_direct2")
            return True

        # Clear and open calendar
        el.click(timeout=5000); time.sleep(0.5)
        page.keyboard.press("Control+a"); page.keyboard.press("Delete")
        page.keyboard.press("Backspace"); time.sleep(0.3)
        el.click(timeout=5000)
        time.sleep(2.0)
        ss(page, "v13_date_open")

        # ── Calendar navigation helpers ────────────────────────────────────────
        month_map = {
            'jan':1,'feb':2,'mar':3,'apr':4,'may':5,'jun':6,
            'jul':7,'aug':8,'sep':9,'oct':10,'nov':11,'dec':12,
            'january':1,'february':2,'march':3,'april':4,'june':6,
            'july':7,'august':8,'september':9,'october':10,'november':11,'december':12
        }
        target_month, target_year = 9, 2026

        def get_header():
            return page.evaluate("""() => {
                let candidates = document.querySelectorAll('*');
                for (let el of candidates) {
                    if (el.children.length > 0) continue;
                    let t = el.textContent.trim();
                    let months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec',
                                  'January','February','March','April','May','June','July','August',
                                  'September','October','November','December'];
                    let hasMonth = months.some(m => t.startsWith(m) || t.endsWith(m));
                    if (hasMonth && t.length < 25) return t;
                }
                let sels = ['[class*="calendar"] [class*="title"]','[class*="datepicker"] [class*="title"]',
                    '[class*="month-title"]','[class*="monthTitle"]','[aria-live="polite"]'];
                for (let s of sels) {
                    let e = document.querySelector(s);
                    if (e && e.textContent.trim()) return e.textContent.trim();
                }
                return '';
            }""")

        def click_nav_btn(direction="next"):
            kw = "next" if direction == "next" else "prev"
            pwright_sels = (
                ['button[aria-label*="Next month" i]','button[aria-label*="next" i]','[class*="nextMonth"]']
                if direction == "next" else
                ['button[aria-label*="Previous month" i]','button[aria-label*="previous" i]','[class*="prevMonth"]']
            )
            for sel in pwright_sels:
                try:
                    loc = page.locator(sel).first
                    if loc.count() > 0 and loc.is_visible(timeout=1500):
                        lbl = loc.get_attribute("aria-label") or sel
                        loc.click(timeout=3000)
                        return lbl[:50]
                except: pass
            return page.evaluate("""({kw}) => {
                let btns = document.querySelectorAll('button');
                for (let btn of btns) {
                    let lbl = (btn.getAttribute('aria-label') || '').toLowerCase();
                    let cls = (btn.className || '').toLowerCase();
                    if ((lbl.includes(kw) || cls.includes(kw)) && btn.offsetParent !== null && !btn.disabled) {
                        btn.click(); return 'js-fallback: ' + lbl.substring(0,40);
                    }
                }
                return null;
            }""", {"kw": kw})

        # Navigate to Sep 2026
        initial_header = get_header()
        log(f"  [date] Initial header: '{initial_header}'")
        h0 = initial_header.lower()
        start_m = None
        for name, num in month_map.items():
            if name in h0: start_m = num; break
        yr_m = re.search(r'\b(202[0-9])\b', h0)
        start_y = int(yr_m.group(1)) if yr_m else None

        if start_y is None and start_m is not None:
            day_text = page.evaluate("""() => {
                let d = document.querySelector('[class*="ocpicker"],[class*="calendar"],[class*="datepicker"]');
                return d ? d.textContent.trim().replace(/\\s+/g,' ').substring(0,200) : '';
            }""")
            log(f"  [date] Calendar text: '{day_text[:100]}'")
            yr2 = re.search(r'\b(202[0-9])\b', day_text)
            if yr2: start_y = int(yr2.group(1))
            else:
                if start_m == 1: start_y = 2025
                elif start_m == 6: start_y = 2026
                else: start_y = 2025

        log(f"  [date] Start: month={start_m} year={start_y} → target: Sep 2026")
        if start_m and start_y:
            start_total = start_y * 12 + start_m
            target_total = target_year * 12 + target_month
            steps = target_total - start_total
            log(f"  [date] Steps needed: {steps} ({'next' if steps >= 0 else 'prev'})")
        else:
            steps = 20  # Jan 2025 → Sep 2026

        for attempt in range(abs(steps) + 5):
            if not alive(page): break
            header = get_header()
            h = header.lower().strip()
            cur_m = None
            for name, num in month_map.items():
                if name in h: cur_m = num; break
            yr_m2 = re.search(r'\b(202[0-9])\b', h)
            cur_y = int(yr_m2.group(1)) if yr_m2 else None
            if cur_y is None and start_y is not None and start_m is not None:
                inferred_total = (start_y * 12 + start_m) + (attempt * (1 if steps >= 0 else -1))
                cur_y = inferred_total // 12
                cur_m_inf = inferred_total % 12
                if cur_m_inf == 0: cur_m_inf = 12; cur_y -= 1
                if cur_m is None: cur_m = cur_m_inf
            log(f"    [cal] header='{header}' m={cur_m} y={cur_y}")
            if cur_m == target_month and (cur_y == target_year or cur_y is None):
                log(f"  [date] Reached {target_month}/{target_year}!")
                break
            direction = "next" if steps >= 0 else "prev"
            click_nav_btn(direction); time.sleep(0.7)

        ss(page, "v13_date_calendar")

        # Ensure calendar is open
        cal_open = page.evaluate("""() => {
            let cells = document.querySelectorAll('td[class*="ocpicker"]');
            return cells.length > 0;
        }""")
        log(f"  [date] Calendar cells visible: {cal_open}")
        if not cal_open:
            el.click(timeout=5000); time.sleep(2.0)
            hdr2 = get_header().lower()
            if "sep" not in hdr2:
                for _ in range(25):
                    hdr2 = get_header().lower()
                    if "sep" in hdr2: break
                    click_nav_btn("next"); time.sleep(0.5)
            ss(page, "v13_date_reopened")

        # ── Strategy B: PointerEvent dispatch (React 17+ uses pointer events) ──
        # React's SyntheticEvent system hooks into PointerEvents at the document root.
        # Dispatching PointerEvent on the TD (with bubbles=true) should trigger React.
        log(f"  [date] [B] Trying PointerEvent dispatch on day 1 cell...")
        result_b = page.evaluate("""() => {
            let cells = document.querySelectorAll('td[class*="ocpicker"]');
            let target = null;
            for (let td of cells) {
                if (td.textContent.trim() === '1') { target = td; break; }
            }
            if (!target) return 'no-cell-found';
            let r = target.getBoundingClientRect();
            let cx = r.left + r.width/2, cy = r.top + r.height/2;
            // Fire full pointer+mouse event sequence that React expects
            let events = [
                new PointerEvent('pointerover', {bubbles:true, cancelable:true, clientX:cx, clientY:cy, pointerId:1, isPrimary:true}),
                new PointerEvent('pointerenter', {bubbles:false, cancelable:false, clientX:cx, clientY:cy, pointerId:1, isPrimary:true}),
                new MouseEvent('mouseover', {bubbles:true, cancelable:true, clientX:cx, clientY:cy}),
                new MouseEvent('mouseenter', {bubbles:false, cancelable:false, clientX:cx, clientY:cy}),
                new PointerEvent('pointermove', {bubbles:true, cancelable:true, clientX:cx, clientY:cy, pointerId:1, isPrimary:true}),
                new MouseEvent('mousemove', {bubbles:true, cancelable:true, clientX:cx, clientY:cy}),
                new PointerEvent('pointerdown', {bubbles:true, cancelable:true, clientX:cx, clientY:cy, pointerId:1, isPrimary:true, button:0, buttons:1}),
                new MouseEvent('mousedown', {bubbles:true, cancelable:true, clientX:cx, clientY:cy, button:0, buttons:1}),
                new PointerEvent('pointerup', {bubbles:true, cancelable:true, clientX:cx, clientY:cy, pointerId:1, isPrimary:true, button:0}),
                new MouseEvent('mouseup', {bubbles:true, cancelable:true, clientX:cx, clientY:cy, button:0}),
                new MouseEvent('click', {bubbles:true, cancelable:true, clientX:cx, clientY:cy, button:0}),
            ];
            let dispatched = [];
            for (let ev of events) {
                target.dispatchEvent(ev);
                dispatched.push(ev.type);
            }
            return 'dispatched: ' + dispatched.join(',') + ' on ' + target.className.substring(0,40);
        }""")
        log(f"  [date] [B] PointerEvent result: {result_b}")
        time.sleep(1.0)
        val_b = el.input_value()
        log(f"  [date] [B] Value after PointerEvent: '{val_b}'")
        if "sep" in val_b.lower() and "2026" in val_b:
            log(f"  [date] [B] PointerEvent succeeded!")
            esc(page); ss(page, "v13_date_pointer_ok"); return True

        # ── Strategy C: Click a DIFFERENT day first, then Sep 1 ───────────────
        # The Sep 1 cell has aria-selected="true" as a "start of month" marker,
        # NOT as "currently selected date". Clicking it fires no new selection event.
        # Fix: click Sep 15 first (fires a real new selection), then click Sep 1.
        log(f"  [date] [C] Clicking Sep 15 first (to force new selection event)...")

        # Reopen calendar if needed
        cal_open2 = page.evaluate("""() => document.querySelectorAll('td[class*="ocpicker"]').length > 0""")
        if not cal_open2:
            el.click(timeout=5000); time.sleep(2.0)
            hdr3 = get_header().lower()
            if "sep" not in hdr3:
                for _ in range(25):
                    if "sep" in get_header().lower(): break
                    click_nav_btn("next"); time.sleep(0.5)

        # Find and click day 15 using Patchright native click (real browser event)
        day15_clicked = False
        day15_cells = page.evaluate("""() => {
            let cells = document.querySelectorAll('td[class*="ocpicker"]');
            for (let td of cells) {
                if (td.textContent.trim() === '15') {
                    let r = td.getBoundingClientRect();
                    return {x: r.left+r.width/2, y: r.top+r.height/2, cls: td.className.substring(0,50)};
                }
            }
            return null;
        }""")
        log(f"  [date] [C] Day 15 coord: {day15_cells}")
        if day15_cells:
            page.mouse.click(day15_cells['x'], day15_cells['y'])
            time.sleep(1.0)
            val_15 = el.input_value()
            log(f"  [date] [C] After clicking Sep 15: '{val_15}'")
            if "sep" in val_15.lower() or "15" in val_15:
                day15_clicked = True
                log(f"  [date] [C] Sep 15 registered! Now clicking Sep 1...")
                # Calendar may have closed. Reopen if needed.
                time.sleep(0.5)
                cal_open3 = page.evaluate("""() => document.querySelectorAll('td[class*="ocpicker"]').length > 0""")
                if not cal_open3:
                    el.click(timeout=5000); time.sleep(2.0)
                    hdr4 = get_header().lower()
                    if "sep" not in hdr4:
                        for _ in range(25):
                            if "sep" in get_header().lower(): break
                            click_nav_btn("next"); time.sleep(0.5)
                # Now click Sep 1
                day1_coord = page.evaluate("""() => {
                    let cells = document.querySelectorAll('td[class*="ocpicker"]');
                    for (let td of cells) {
                        if (td.textContent.trim() === '1') {
                            let r = td.getBoundingClientRect();
                            return {x: r.left+r.width/2, y: r.top+r.height/2};
                        }
                    }
                    return null;
                }""")
                if day1_coord:
                    page.mouse.click(day1_coord['x'], day1_coord['y'])
                    time.sleep(1.0)
                    val_c = el.input_value()
                    log(f"  [date] [C] After Sep 1 (2nd click): '{val_c}'")
                    if "sep" in val_c.lower() and "2026" in val_c:
                        log(f"  [date] [C] Two-step click succeeded!")
                        esc(page); ss(page, "v13_date_twostep_ok"); return True

        # If Sep 15 didn't register either, try direct Patchright locator click on cells
        log(f"  [date] [D] Patchright locator click on ocpicker TD day 1...")
        # Try all TD cells in the calendar
        td_locator = page.locator('td[class*="ocpicker"]')
        cnt = td_locator.count()
        log(f"  [date] [D] Found {cnt} ocpicker TDs")
        exact_1 = None
        for i in range(min(cnt, 35)):
            try:
                t = td_locator.nth(i).inner_text(timeout=500).strip()
                if t == "1":
                    exact_1 = td_locator.nth(i)
                    break
            except: pass
        if exact_1:
            try:
                exact_1.scroll_into_view_if_needed()
                exact_1.click(timeout=5000)
                time.sleep(1.0)
                val_d = el.input_value()
                log(f"  [date] [D] After Patchright locator click: '{val_d}'")
                if "sep" in val_d.lower() and "2026" in val_d:
                    log(f"  [date] [D] Patchright locator click succeeded!")
                    esc(page); ss(page, "v13_date_locator_ok"); return True
            except Exception as ex:
                log(f"  [date] [D] locator click failed: {str(ex)[:80]}")

        # ── Strategy E: React fiber internal call ────────────────────────────
        # Access the React fiber node on the TD and trigger its onClick prop directly
        log(f"  [date] [E] React fiber onClick trigger...")
        result_e = page.evaluate("""() => {
            let cells = document.querySelectorAll('td[class*="ocpicker"]');
            let target = null;
            for (let td of cells) {
                if (td.textContent.trim() === '1') { target = td; break; }
            }
            if (!target) return 'no-cell';
            // Find React fiber
            let fiber = null;
            for (let key of Object.keys(target)) {
                if (key.startsWith('__reactFiber') || key.startsWith('__reactInternalInstance')) {
                    fiber = target[key]; break;
                }
            }
            if (!fiber) return 'no-fiber';
            // Walk up to find onClick handler
            let node = fiber;
            for (let i = 0; i < 5; i++) {
                let props = node.memoizedProps || node.pendingProps || {};
                if (props.onClick) {
                    let r = target.getBoundingClientRect();
                    let cx = r.left + r.width/2, cy = r.top + r.height/2;
                    let syntheticEvent = {
                        nativeEvent: new MouseEvent('click', {bubbles:true, clientX:cx, clientY:cy}),
                        target: target, currentTarget: target,
                        type: 'click', bubbles: true,
                        preventDefault: ()=>{}, stopPropagation: ()=>{},
                        persist: ()=>{}, isDefaultPrevented: ()=>false,
                    };
                    try { props.onClick(syntheticEvent); return 'fiber-onClick-called on '+node.type; }
                    catch(ex) { return 'fiber-onClick-err: '+ex.message; }
                }
                if (node.return) node = node.return; else break;
            }
            // Try stateNode props
            if (fiber.stateNode && fiber.stateNode.props && fiber.stateNode.props.onClick) {
                try { fiber.stateNode.props.onClick({}); return 'stateNode-onClick'; }
                catch(ex) { return 'stateNode-err: '+ex.message; }
            }
            return 'fiber-found-no-onClick: fiber.type=' + (fiber.type||'?');
        }""")
        log(f"  [date] [E] Fiber result: {result_e}")
        time.sleep(1.0)
        val_e = el.input_value()
        log(f"  [date] [E] Value after fiber: '{val_e}'")
        if "sep" in val_e.lower() and "2026" in val_e:
            log(f"  [date] [E] Fiber onClick succeeded!")
            esc(page); ss(page, "v13_date_fiber_ok"); return True

        time.sleep(0.5)
        esc(page); time.sleep(0.5)
        ss(page, "v13_date_after_all")
        el.scroll_into_view_if_needed(); time.sleep(0.3)
        ss(page, "v13_date_field_view")
        final_val = el.input_value()
        log(f"  [date] Final value: '{final_val}'")
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
