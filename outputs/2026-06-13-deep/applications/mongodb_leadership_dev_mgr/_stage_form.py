"""
_stage_form.py — Drive MongoDB Greenhouse application to the pre-submit review state.
Fills truthful fields, uploads the TAILORED resume.pdf + cover_letter.pdf via set_input_files,
reads back attached filenames, selects react-select comboboxes truthfully, screenshots the full
page, and LEAVES THE TAB OPEN (never submits, never closes other tabs). reCAPTCHA present → we
stop before submit regardless.

Run: python _stage_form.py
"""
from patchright.sync_api import sync_playwright
import time, json, sys
from pathlib import Path

PKG = Path(r"C:/Users/chent/Agentic_Workflows_2026/oracle-job-search/outputs/2026-06-13-deep/applications/mongodb_leadership_dev_mgr")
RESUME = str(PKG / "resume.pdf")
COVER = str(PKG / "cover_letter.pdf")
URL = "https://boards.greenhouse.io/embed/job_app?for=mongodb&token=7844159"

CONTACT = {
    "first_name": "Jamie",
    "last_name": "Cheng",
    "email": "jamiecheng0103@gmail.com",
    "phone": "(213) 700-3831",
}
PLAIN_TEXT_Q = {
    "question_65939066": "Jamie",                                  # Preferred Name*
    "question_65939068": "https://www.linkedin.com/in/jamieyccheng/",  # LinkedIn Profile
}
# combobox id -> the substring we want to match against the real option labels (truthful)
COMBO_WANT = {
    "question_65939073": ["yes"],                  # sponsorship required -> Yes
    "question_65939074": ["no"],                   # worked at MongoDB before -> No
    "question_65939070": ["linkedin"],             # how did you learn
    "1653": ["female", "woman"],                   # Gender
    "1654": ["woman"],                             # Gender Identity
    "1655": ["asian"],                             # Race
    "1656": ["not hispanic", "no"],                # Hispanic/Latino
    "1657": ["not a protected veteran", "not a veteran", "no"],  # Veteran
    "1658": ["no, i do", "do not have", "no"],     # Disability
}

def sel(qid):
    return f'[id="{qid}"]'

def set_text(page, qid, val):
    el = page.query_selector(sel(qid))
    if not el:
        return f"MISSING:{qid}"
    el.click(); el.fill(""); el.type(val, delay=15)
    return el.input_value()

def fill_location(page, val):
    """candidate-location is a Google-places autocomplete combobox: type, wait, pick first suggestion."""
    el = page.query_selector('#candidate-location')
    if not el:
        return "MISSING:candidate-location"
    el.click(); el.fill(""); el.type(val, delay=40)
    time.sleep(1.8)  # wait for suggestions
    opts = page.query_selector_all('[role=option], .select__option, li[role=option]')
    if opts:
        # pick the first suggestion that contains 'Portland'
        picked = None
        for o in opts:
            t = (o.inner_text() or "")
            if "Portland" in t:
                o.click(); picked = t.strip(); break
        if not picked and opts:
            opts[0].click(); picked = (opts[0].inner_text() or "").strip()
        time.sleep(0.4)
        return f"PICKED:{picked}"
    return f"TYPED_NO_SUGGEST:{el.input_value()}"

def read_attached_filename(page, kind):
    """After Greenhouse processes an upload it REMOVES the <input> and renders a filename chip.
    Scrape the chip text (the true confirmation the file is attached)."""
    return page.evaluate("""(kind) => {
        const want = kind === 'resume' ? 'resume.pdf' : 'cover_letter.pdf';
        let hits = [];
        document.querySelectorAll('*').forEach(el => {
            if (el.children.length === 0) {
                const t = (el.innerText || '').trim();
                if (t.toLowerCase() === want || t.toLowerCase().endsWith('/' + want)) hits.push(t);
            }
        });
        return hits.length ? hits[0] : null;
    }""", kind)

def read_combo_options(page, qid):
    el = page.query_selector(sel(qid))
    if not el:
        return None, []
    el.scroll_into_view_if_needed()
    el.click()
    time.sleep(0.5)
    opts = page.query_selector_all('[role=option], .select__option')
    labels = [(o.inner_text() or "").strip() for o in opts if (o.inner_text() or "").strip()]
    return el, labels

def pick_combo(page, qid, wants):
    el, labels = read_combo_options(page, qid)
    if el is None:
        return {"id": qid, "status": "MISSING"}
    chosen = None
    for w in wants:
        for lb in labels:
            if w.lower() in lb.lower():
                chosen = lb; break
        if chosen:
            break
    if not chosen:
        page.keyboard.press("Escape")
        return {"id": qid, "status": "NO_MATCH", "options": labels}
    # type to filter then Enter — robust react-select select
    el.fill("")
    el.type(chosen[:18], delay=20)
    time.sleep(0.4)
    page.keyboard.press("Enter")
    time.sleep(0.3)
    return {"id": qid, "status": "SET", "chosen": chosen, "options": labels}

def main():
    report = {"contact": {}, "plain_text": {}, "combos": [], "uploads": {}, "checkbox": None, "captcha": None}
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://localhost:9222")
        ctx = browser.contexts[0]
        page = ctx.new_page()
        page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        time.sleep(3)

        # ── Contact fields (plain text) ──
        for qid, val in CONTACT.items():
            report["contact"][qid] = set_text(page, qid, val)
        # location autocomplete (special)
        report["contact"]["candidate-location"] = fill_location(page, "Portland, OR")

        # ── Uploads (THE LINCHPIN) ── Greenhouse removes the <input> after processing and
        # renders a filename chip; we read the chip back as confirmation.
        page.set_input_files("#resume", RESUME)
        time.sleep(2.5)
        page.set_input_files("#cover_letter", COVER)
        time.sleep(2.5)
        report["uploads"] = {
            "resume": read_attached_filename(page, "resume"),
            "cover_letter": read_attached_filename(page, "cover_letter"),
        }

        # ── Plain-text questions ──
        for qid, val in PLAIN_TEXT_Q.items():
            report["plain_text"][qid] = set_text(page, qid, val)

        # ── Comboboxes (truthful) ──
        for qid, wants in COMBO_WANT.items():
            r = pick_combo(page, qid, wants)
            report["combos"].append(r)
            time.sleep(0.2)

        # ── Demographic consent checkbox ──
        cb = page.query_selector('#gdpr_demographic_data_consent_given_1')
        if cb:
            if not cb.is_checked():
                cb.check()
            report["checkbox"] = cb.is_checked()

        # ── reCAPTCHA presence ──
        rc = page.query_selector('textarea[name=g-recaptcha-response], iframe[src*=recaptcha], .g-recaptcha')
        report["captcha"] = bool(rc)

        # ── Screenshot full page ──
        time.sleep(1)
        shot = str(PKG / "_review_fullpage.png")
        page.screenshot(path=shot, full_page=True)
        report["screenshot"] = shot
        report["final_url"] = page.url

        print(json.dumps(report, indent=2, ensure_ascii=False))
        print("TAB LEFT OPEN — not submitting.")
        # DO NOT page.close(); DO NOT browser.close() — leave tab for orchestrator/human.

if __name__ == "__main__":
    main()
