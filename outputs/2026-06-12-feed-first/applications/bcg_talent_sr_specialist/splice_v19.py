# -*- coding: utf-8 -*-
"""Splice new fill_date_navigate into submit_bcg_v19.py"""

TARGET = r"C:\Users\chent\Agentic_Workflows_2026\oracle-job-search\outputs\2026-06-12-feed-first\applications\bcg_talent_sr_specialist\submit_bcg_v19.py"

with open(TARGET, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Lines 283-465 (1-indexed) are the old function (0-indexed: 282-464)
PRE  = lines[:282]   # lines 1-282
POST = lines[465:]   # lines 466-end

NEW_FUNC_LINES = '''\
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
        log(f"  [date] Initial value: \'{initial_val}\'")

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
        log(f"  [date] After TD fiber: \'{val_fiber}\'")
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
                log(f"  [date] Locator click: \'{val_loc}\'")
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
        log(f"  [date] Keyboard+Tab: \'{val_kb}\'")
        if "sep" in val_kb.lower() and "2026" in val_kb:
            log(f"  [date] Keyboard type SUCCESS!"); ss(page, "v19_date_ok"); return True

        el.click(timeout=5000); time.sleep(0.3)
        page.keyboard.press("Control+a"); page.keyboard.press("Delete"); time.sleep(0.2)
        page.keyboard.type("01 Sep 2026", delay=60); time.sleep(0.3)
        page.keyboard.press("Enter"); time.sleep(1.0)
        val_enter = el.input_value()
        log(f"  [date] Keyboard+Enter: \'{val_enter}\'")
        if "sep" in val_enter.lower() and "2026" in val_enter:
            log(f"  [date] Keyboard+Enter SUCCESS!"); ss(page, "v19_date_ok"); return True

        # ── STEP 5: Diagnostic dump + accept ────────────────────────────────
        final_val = el.input_value()
        log(f"  [date] All approaches done. Final: \'{final_val}\'")
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

'''

new_lines = [line + '\n' for line in NEW_FUNC_LINES.split('\n')]
# Remove the trailing extra blank line
while new_lines and new_lines[-1].strip() == '':
    new_lines.pop()
new_lines.append('\n')  # single blank line after function

result = PRE + new_lines + POST

with open(TARGET, 'w', encoding='utf-8') as f:
    f.writelines(result)

print(f"Done. Total lines: {len(result)}")
# Verify the function is there
content = open(TARGET, encoding='utf-8').read()
print("fill_date_navigate found:", 'def fill_date_navigate' in content)
print("v19 in docstring:", 'v19: TD React fiber' in content)
print("TD fiber result found:", 'TD fiber result' in content)
