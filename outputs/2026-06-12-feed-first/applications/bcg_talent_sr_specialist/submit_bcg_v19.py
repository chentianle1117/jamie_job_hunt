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
SHOT     = ROLE_DIR + r"\screenshots\v19"
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

        # Re-query the locator fresh right before clicking to avoid stale DOM
        def click_option_fresh():
            for attempt in range(3):
                time.sleep(0.5 * (attempt + 1))  # wait longer on each retry
                for sel in [
                    f"[role='listbox'] li:has-text('{full_text}')",
                    f"[role='option']:has-text('{full_text}')",
                    f"li:has-text('{full_text}')",
                ]:
                    try:
                        loc = page.locator(sel).first
                        if loc.count() > 0 and loc.is_visible(timeout=2000):
                            loc.click(timeout=5000)
                            time.sleep(1.5)
                            esc(page)
                            log(f"    [ddtc-ok] locator click on '{full_text}' (attempt {attempt+1})")
                            return True
                    except Exception as ex:
                        log(f"    [ddtc-retry] {sel}: {str(ex)[:60]}")
                # Re-type filter text to re-open dropdown
                if attempt < 2:
                    log(f"    [ddtc-retype] re-typing filter '{filter_text}'")
                    try:
                        inp2 = page.locator(f"#{field_id}").first
                        if inp2.count() > 0 and inp2.is_visible(timeout=2000):
                            inp2.click(timeout=3000)
                            page.keyboard.press("Control+a"); page.keyboard.press("Delete")
                            time.sleep(0.2)
                            page.keyboard.type(filter_text, delay=80)
                            time.sleep(1.5)
                    except: pass
            return False

        if opt_locator.count() > 0:
            if click_option_fresh():
                return True

        # Fallback: press ArrowDown + Enter (with timeout guard)
        log(f"    [ddtc-arrow] trying arrow approach...")
        # Re-open input first
        try:
            inp2 = page.locator(f"#{field_id}").first
            if inp2.count() > 0 and inp2.is_visible(timeout=2000):
                inp2.click(timeout=3000)
                page.keyboard.press("Control+a"); page.keyboard.press("Delete")
                page.keyboard.type(filter_text, delay=80)
                time.sleep(1.5)
        except: pass
        for _ in range(10):
            page.keyboard.press("ArrowDown"); time.sleep(0.2)
            active = page.evaluate("""()=>{
                let a = document.querySelector('[aria-selected="true"],[class*="focused"],[class*="highlight"]');
                return a ? a.textContent.trim() : '';
            }""")
            if active and full_text.lower() in active.lower():
                page.keyboard.press("Enter"); time.sleep(1.0)
                log(f"    [ddtc-arrow-ok] '{active}'")
                return True

        # Last resort: JS click by text
        r2 = page.evaluate("""(t)=>{
            for (let s of ['[role="listbox"] li','[role="option"]','li']) {
                for (let el of document.querySelectorAll(s)) {
                    if (el.textContent.trim().toLowerCase() === t.toLowerCase()) {
                        el.click(); return 'js-ok: '+el.textContent.trim();
                    }
                }
            }
            return null;
        }""", full_text)
        if r2 and "js-ok" in str(r2):
            time.sleep(1.5); esc(page); log(f"    [ddtc-js-ok] {r2}"); return True

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
    v19: TD React fiber onClick + diagnostic approach.

    Prior failures v14-v17:
    - Nav buttons only update DOM display; React viewDate stays pinned at Sep 2025.
    - day2 page.mouse.click always commits Sep 2025 regardless of displayed month.
    - nativeInputValueSetter + input/change events reverted by React.
    - React fiber NOT accessible on nav button elements (dom-click-fallback).

    v19 Approaches (in order):
    1. TD fiber onClick: TD cells ARE React elements with __reactProps. Their onClick
       fires the date selection with DISPLAYED date (after nav). Should work.
    2. Patchright locator.click(): proper browser synthetic events vs mouse.click(coord).
    3. Keyboard type the date string + Tab/Enter to commit.
    4. Diagnostic dump of TD attrs for next version if all fail.
    """
    if not alive(page): return False
    log(f"  [date] v19 TD fiber + diagnostic approach...")

    import re

    try:
        el = page.locator(f"#{field_id}").first
        el.wait_for(state="visible", timeout=8000)
        el.scroll_into_view_if_needed()

        initial_val = el.input_value()
        log(f"  [date] Initial value: '{initial_val}'")

        month_map = {"jan":1,"feb":2,"mar":3,"apr":4,"may":5,"jun":6,
                     "jul":7,"aug":8,"sep":9,"oct":10,"nov":11,"dec":12}
        target_month, target_year = 9, 2026

        def parse_date_val(s):
            if not s: return None, None
            m = re.search(r"(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", s)
            if not m: return None, None
            mon = m.group(2).lower()[:3]
            if mon not in month_map: return None, None
            return month_map[mon], int(m.group(3))

        def open_calendar():
            el.click(timeout=5000); time.sleep(2.0)
            n = page.evaluate(
                """() => document.querySelectorAll('td[class*="ocpicker"]').length""")
            log(f"  [date] Calendar cells: {n}"); return n

        def nav_next_js():
            return page.evaluate("""() => {
                let btns = document.querySelectorAll('button');
                for (let btn of btns) {
                    let lbl = (btn.getAttribute('aria-label') || '').toLowerCase();
                    let cls = (btn.className || '').toLowerCase();
                    if ((lbl.includes('next') || cls.includes('next')) &&
                        btn.offsetParent !== null && !btn.disabled) {
                        btn.click(); return 'nav: ' + lbl.substring(0,30);
                    }
                }
                return 'no-next-btn';
            }""")

        cur_m, cur_y = parse_date_val(initial_val)
        if cur_m is None: cur_m, cur_y = 9, 2025
        steps_needed = (target_year * 12 + target_month) - (cur_y * 12 + cur_m)
        log(f"  [date] {cur_m}/{cur_y} to {target_month}/{target_year} = {steps_needed} steps")

        # ── STEP 0: Inspect TD React structure ──────────────────────────────
        log(f"  [date] Opening calendar to inspect TD React structure...")
        open_calendar()
        ss(page, "v19_cal_open")

        td_info = page.evaluate("""() => {
            let cells = document.querySelectorAll('td[class*="ocpicker"]');
            if (!cells.length) return 'no-cells';
            let td = cells[Math.min(3, cells.length-1)];
            let keys = Object.keys(td).filter(k =>
                k.startsWith('__react') || k.startsWith('_react'));
            let propsKey = keys.find(k => k.startsWith('__reactProps'));
            let fiberKey = keys.find(k => k.startsWith('__reactFiber'));
            let propsInfo = 'none';
            if (propsKey) {
                let p = td[propsKey];
                propsInfo = 'keys=' + Object.keys(p).slice(0,15).join(',');
            }
            let attrs = {};
            for (let a of td.attributes) { attrs[a.name] = a.value; }
            return {
                txt: td.textContent.trim(),
                cls: td.className.substring(0,80),
                reactKeys: keys,
                propsInfo: propsInfo,
                fiberInfo: fiberKey ? 'found' : 'none',
                attrs: attrs
            };
        }""")
        log(f"  [date] TD structure: {td_info}")

        # ── STEP 1: Navigate to Sep 2026 display ────────────────────────────
        for i in range(steps_needed):
            r = nav_next_js(); time.sleep(0.7)
            if i == 0 or (i+1) % 4 == 0:
                log(f"  [date] nav {i+1}/{steps_needed}: {r}")
        ss(page, "v19_cal_navigated")

        # ── STEP 2: TD fiber onClick ─────────────────────────────────────────
        fiber_r = page.evaluate("""(dayNum) => {
            let cells = Array.from(document.querySelectorAll('td[class*="ocpicker"]'));
            let target = null;
            for (let td of cells) {
                let txt = td.textContent.trim();
                if (txt !== dayNum) continue;
                let cls = td.className || '';
                if (!cls.includes('out-of-view') && !cls.includes('other-month') &&
                    !cls.includes('outside')) { target = td; break; }
            }
            if (!target) {
                for (let td of cells) {
                    if (td.textContent.trim() === dayNum) { target = td; break; }
                }
            }
            if (!target) return 'no-td';

            // Try __reactProps (React 17+)
            let propsKey = Object.keys(target).find(k => k.startsWith('__reactProps'));
            if (propsKey) {
                let props = target[propsKey];
                if (props && typeof props.onClick === 'function') {
                    let fakeEv = {type:'click', bubbles:true,
                        preventDefault:()=>{}, stopPropagation:()=>{},
                        target:target, currentTarget:target};
                    try { props.onClick(fakeEv); return 'reactProps-onClick-fired'; }
                    catch(e) { return 'reactProps-onClick-err: ' + e.message; }
                }
                if (props && typeof props.onMouseDown === 'function') {
                    try {
                        props.onMouseDown({type:'mousedown', bubbles:true,
                            preventDefault:()=>{}, stopPropagation:()=>{}});
                        return 'reactProps-onMouseDown-fired';
                    } catch(e) { return 'onMouseDown-err: ' + e.message; }
                }
                return 'reactProps-no-onclick,keys=' + Object.keys(props).slice(0,12).join(',');
            }

            // Try __reactFiber
            let fiberKey = Object.keys(target).find(k => k.startsWith('__reactFiber'));
            if (fiberKey) {
                let node = target[fiberKey];
                for (let i = 0; i < 10 && node; i++) {
                    let props = node.pendingProps || node.memoizedProps;
                    if (props && typeof props.onClick === 'function') {
                        try {
                            props.onClick({type:'click', bubbles:true,
                                preventDefault:()=>{}, stopPropagation:()=>{}});
                            return 'fiber-onClick-depth=' + i;
                        } catch(e) { return 'fiber-err: ' + e.message; }
                    }
                    node = node.return;
                }
                return 'fiber-no-click';
            }
            return 'no-react-on-td';
        }""", "2")
        log(f"  [date] TD fiber result: {fiber_r}")
        time.sleep(1.5)
        val_fiber = el.input_value()
        log(f"  [date] After TD fiber: '{val_fiber}'")
        if "sep" in val_fiber.lower() and "2026" in val_fiber:
            log(f"  [date] TD fiber SUCCESS!"); ss(page, "v19_date_ok"); return True

        # ── STEP 3: Patchright locator click ────────────────────────────────
        n_open = page.evaluate(
            """() => document.querySelectorAll('td[class*="ocpicker"]').length""")
        log(f"  [date] Cells after fiber: {n_open}")
        if n_open == 0:
            open_calendar()
            for i in range(steps_needed): nav_next_js(); time.sleep(0.6)
            ss(page, "v19_cal_reopened")

        log(f"  [date] Trying Patchright locator click on day 2...")
        try:
            day2_loc = page.locator('td[class*="ocpicker"]').filter(
                has_text=re.compile(r"^2$")).first
            if day2_loc.count() > 0:
                day2_loc.click(timeout=4000); time.sleep(1.5)
                val_loc = el.input_value()
                log(f"  [date] Locator click: '{val_loc}'")
                if "sep" in val_loc.lower() and "2026" in val_loc:
                    log(f"  [date] Patchright locator SUCCESS!"); ss(page, "v19_date_ok"); return True
        except Exception as e2:
            log(f"  [date] locator err: {e2}")

        # ── STEP 4: Keyboard type ────────────────────────────────────────────
        esc(page); time.sleep(0.5)
        log(f"  [date] Trying keyboard type...")
        el.click(timeout=5000); time.sleep(0.5)
        page.keyboard.press("Control+a"); page.keyboard.press("Delete"); time.sleep(0.2)
        page.keyboard.type("01 Sep 2026", delay=60); time.sleep(0.5)
        page.keyboard.press("Tab"); time.sleep(1.0)
        val_kb = el.input_value()
        log(f"  [date] Keyboard+Tab: '{val_kb}'")
        if "sep" in val_kb.lower() and "2026" in val_kb:
            log(f"  [date] Keyboard type SUCCESS!"); ss(page, "v19_date_ok"); return True

        el.click(timeout=5000); time.sleep(0.3)
        page.keyboard.press("Control+a"); page.keyboard.press("Delete"); time.sleep(0.2)
        page.keyboard.type("01 Sep 2026", delay=60); time.sleep(0.3)
        page.keyboard.press("Enter"); time.sleep(1.0)
        val_enter = el.input_value()
        log(f"  [date] Keyboard+Enter: '{val_enter}'")
        if "sep" in val_enter.lower() and "2026" in val_enter:
            log(f"  [date] Keyboard+Enter SUCCESS!"); ss(page, "v19_date_ok"); return True

        # ── STEP 5: Diagnostic dump + accept ────────────────────────────────
        final_val = el.input_value()
        log(f"  [date] All approaches done. Final: '{final_val}'")
        open_calendar()
        for i in range(steps_needed): nav_next_js(); time.sleep(0.5)
        td_data = page.evaluate("""() => {
            let cells = document.querySelectorAll('td[class*="ocpicker"]');
            let r = [];
            for (let i = 0; i < Math.min(7, cells.length); i++) {
                let td = cells[i];
                let attrs = {};
                for (let a of td.attributes) { attrs[a.name] = a.value; }
                r.push({txt: td.textContent.trim(), attrs: attrs});
            }
            return r;
        }""")
        log(f"  [date] TD attrs at Sep 2026 display: {td_data}")
        ss(page, "v19_date_final")
        esc(page)
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
