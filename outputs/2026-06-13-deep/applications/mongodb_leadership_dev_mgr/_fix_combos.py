"""
_fix_combos.py — Correct the two demographic/screening comboboxes that the first pass mis-set
(WorkedBefore and Hispanic both got 'Lebanon+961' because a substring 'no' matched 'Lebanon' from
a stale phone-country option list). Operate on the ALREADY-OPEN MongoDB tab; re-select with proper
whole-word, scoped option reading; re-screenshot. Do NOT submit, do NOT close other tabs.
"""
from patchright.sync_api import sync_playwright
import time, json, re
from pathlib import Path

PKG = Path(r"C:/Users/chent/Agentic_Workflows_2026/oracle-job-search/outputs/2026-06-13-deep/applications/mongodb_leadership_dev_mgr")

# id -> exact option text we want (read from the field's OWN listbox)
FIX = {
    "question_65939074": "No",                 # Have you ever worked at MongoDB before? -> No
    "1656": "No",                              # Are you Hispanic/Latino? -> No (will fall back to a 'not hispanic' variant)
}
# acceptable exact (lowercased) labels per field, in priority order
WANT = {
    "question_65939074": ["no"],
    "1656": ["no", "not hispanic or latino", "not hispanic/latino", "no, not hispanic or latino"],
}

def sel(qid):
    return f'[id="{qid}"]'

def field_container(page, qid):
    # the react-select container that holds THIS input's own listbox
    return page.evaluate_handle(
        """(qid) => {
            const inp = document.getElementById(qid);
            if (!inp) return null;
            let n = inp;
            for (let d=0; d<6 && n; d++){ if (n.querySelector && n.querySelector('[class*=select__menu], [role=listbox]')) return n; n = n.parentElement; }
            // fallback: nearest container that is a select wrapper
            n = inp;
            for (let d=0; d<6 && n; d++){ if (n.className && /select/i.test(n.className)) return n; n = n.parentElement; }
            return inp.parentElement;
        }""", qid)

def fix_combo(page, qid, wants):
    el = page.query_selector(sel(qid))
    if not el:
        return {"id": qid, "status": "MISSING"}
    el.scroll_into_view_if_needed()
    # clear any current value: open and look for a clear ('x') control, else just re-open and retype
    el.click()
    time.sleep(0.5)
    # read options scoped to THIS field's listbox via aria-controls / nearest menu
    labels = page.evaluate(
        """(qid) => {
            const inp = document.getElementById(qid);
            if (!inp) return [];
            // react-select puts the menu as a sibling within the same container
            let cont = inp;
            for (let d=0; d<6 && cont; d++){ if (cont.querySelector && cont.querySelector('[class*=select__menu]')) break; cont = cont.parentElement; }
            const menu = cont ? cont.querySelector('[class*=select__menu]') : null;
            const scope = menu || document;
            const opts = scope.querySelectorAll('[role=option], [class*=select__option]');
            return [...opts].map(o => (o.innerText||'').trim()).filter(Boolean);
        }""", qid)
    chosen = None
    low = [l.lower() for l in labels]
    for w in wants:
        for i, l in enumerate(low):
            if l == w:                      # EXACT match first (whole option)
                chosen = labels[i]; break
        if chosen: break
    if not chosen:
        # whole-word containment (so 'no' won't match 'Lebanon')
        for w in wants:
            for i, l in enumerate(low):
                if re.search(r'\b' + re.escape(w) + r'\b', l):
                    chosen = labels[i]; break
            if chosen: break
    if not chosen:
        page.keyboard.press("Escape")
        return {"id": qid, "status": "NO_MATCH", "options": labels[:15]}
    # select by typing the chosen text then Enter
    el.fill("")
    el.type(chosen[:20], delay=25)
    time.sleep(0.4)
    page.keyboard.press("Enter")
    time.sleep(0.3)
    # read back the rendered single-value
    val = page.evaluate(
        """(qid) => {
            const inp = document.getElementById(qid);
            let cont = inp;
            for (let d=0; d<6 && cont; d++){ if (cont.querySelector && cont.querySelector('[class*=singleValue]')) break; cont = cont.parentElement; }
            const sv = cont ? cont.querySelector('[class*=singleValue]') : null;
            return sv ? sv.innerText.trim() : null;
        }""", qid)
    return {"id": qid, "status": "SET", "chosen": chosen, "rendered": val, "options": labels[:15]}

def main():
    out = {"fixes": []}
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://localhost:9222")
        ctx = browser.contexts[0]
        page = None
        for pg in ctx.pages:
            try:
                if "greenhouse.io" in pg.url and "7844159" in pg.url:
                    page = pg; break
            except Exception:
                continue
        if page is None:
            print(json.dumps({"error": "no open MongoDB tab found"})); return
        page.bring_to_front()
        for qid, _ in FIX.items():
            out["fixes"].append(fix_combo(page, qid, WANT[qid]))
            time.sleep(0.3)
        # re-screenshot
        time.sleep(0.8)
        shot = str(PKG / "_review_fullpage.png")
        page.screenshot(path=shot, full_page=True)
        out["screenshot"] = shot
        print(json.dumps(out, indent=2, ensure_ascii=False))
        print("TAB LEFT OPEN — not submitting.")

if __name__ == "__main__":
    main()
