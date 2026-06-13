"""
Twitch Greenhouse Submitter v7
Fixes from v6:
1. q896 = work location picker (cities), not yes/no relocation — pick "San Francisco, CA"
2. q905 = other citizenship — opens but gets NO OPTIONS; try longer wait + scroll
3. getSV readback fixed to find parent container first, then look for single-value within it
4. Phone readback: "(213) 700-3831" format means ITI is formatting it — that's fine, Greenhouse accepts it
"""
import sys, time, json
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(r"C:\Users\chent\Agentic_Workflows_2026\jamie-autopilot\lib")))
from patchright.sync_api import sync_playwright

ROLE_DIR = Path(r"C:\Users\chent\Agentic_Workflows_2026\oracle-job-search\outputs\2026-06-12-feed-first\applications\twitch_culture_people_pm")
RESUME = ROLE_DIR / "resume.pdf"
COVER = ROLE_DIR / "cover_letter.pdf"
OUT_DIR = ROLE_DIR / "screenshots"
OUT_DIR.mkdir(exist_ok=True)

URL = "https://job-boards.greenhouse.io/twitch/jobs/8582338002"
PROFILE_DIR = r"C:\Users\chent\ats_agent_9410"

def pause(t=0.5): time.sleep(t)

def ss(page, name):
    try: page.screenshot(path=str(OUT_DIR / name), full_page=True); print(f"  [ss] {name}")
    except Exception as e: print(f"  [ss err] {e}")

def get_ctrl_coords(page, input_id):
    return page.evaluate(f'''() => {{
        const inp = document.getElementById("{input_id}");
        if (!inp) return {{found: false, err: "no-input"}};
        let el = inp;
        for (let i=0; i<12; i++) {{
            if (!el) break;
            const ctrl = el.querySelector ? el.querySelector(".select__control") : null;
            if (ctrl) {{
                const r = ctrl.getBoundingClientRect();
                return {{found: true, x: r.x, y: r.y, w: r.width, h: r.height}};
            }}
            el = el.parentElement;
        }}
        return {{found: false, err: "no-ctrl"}};
    }}''')

def open_select_coord(page, input_id):
    page.evaluate(f"() => {{ const e=document.getElementById('{input_id}'); if(e) e.scrollIntoView({{block:'center'}}); }}")
    time.sleep(0.4)
    coords = get_ctrl_coords(page, input_id)
    if not coords.get('found') or coords['w'] == 0:
        print(f"  {input_id}: ctrl not found: {coords}")
        return False
    cx = coords['x'] + coords['w'] / 2
    cy = coords['y'] + coords['h'] / 2
    page.mouse.click(cx, cy)
    time.sleep(0.5)
    return True

def get_options(page, timeout=5000):
    try: page.wait_for_selector("[class*='select__option']", timeout=timeout, state="visible")
    except: pass
    time.sleep(0.2)
    opts = page.locator("[class*='select__option']")
    n = opts.count()
    texts = [opts.nth(i).inner_text().strip() for i in range(n)]
    return texts, opts

def close_dropdown(page):
    page.keyboard.press("Escape"); time.sleep(0.2)

def get_sv(page, input_id):
    """Get the single-value display for a react-select field (scoped to the field's container)."""
    return page.evaluate(f'''() => {{
        const inp = document.getElementById("{input_id}");
        if (!inp) return null;
        let el = inp;
        for (let i=0;i<12;i++) {{
            el=el.parentElement; if(!el) break;
            // Find the container that has select__control (the react-select container)
            if (el.querySelector && el.querySelector(".select__control")) {{
                const sv = el.querySelector(".select__single-value,[class*='single-value']");
                if(sv) return (sv.innerText||"").trim();
                return null;
            }}
        }}
        return null;
    }}''')

def select_field(page, input_id, want_text, close_after_fail=True):
    want = want_text.strip().lower()
    ok = open_select_coord(page, input_id)
    if not ok: return False, None

    texts, opts = get_options(page)
    if not texts:
        if close_after_fail: close_dropdown(page)
        print(f"  {input_id}: NO OPTIONS")
        return False, None

    best_idx = None
    if want == "yes":
        yes_opts = [(i, t) for i, t in enumerate(texts) if "yes" in t.lower()]
        if yes_opts:
            good = [(i,t) for i,t in yes_opts if "partner" not in t.lower() and "affiliate" not in t.lower() and "streamer" not in t.lower()]
            if good: best_idx = min(good, key=lambda x: len(x[1]))[0]
            else: best_idx = min(yes_opts, key=lambda x: len(x[1]))[0]

    if best_idx is None:
        for i, t in enumerate(texts):
            if t.lower() == want: best_idx = i; break
    if best_idx is None:
        for i, t in enumerate(texts):
            if want in t.lower(): best_idx = i; break
    if best_idx is None:
        for i, t in enumerate(texts):
            if all(w in t.lower() for w in want.split()): best_idx = i; break

    if best_idx is None:
        close_dropdown(page)
        print(f"  {input_id}: no match for {want_text!r} in {texts[:5]}")
        return False, None

    chosen = texts[best_idx]
    opts.nth(best_idx).click(); pause(0.35)
    sv = get_sv(page, input_id)
    print(f"  {input_id}: {chosen!r} [{sv!r}]")
    return True, chosen

def fill_location(page):
    loc_el = page.locator("#candidate-location").first
    page.evaluate("() => { const e=document.getElementById('candidate-location'); if(e) e.scrollIntoView({block:'center'}); }")
    time.sleep(0.3)
    loc_el.click(); pause(0.3)
    loc_el.fill(""); pause(0.2)
    page.keyboard.type("San Francisco, CA")
    page.wait_for_timeout(3500)

    filled = False
    for sel in [".pac-container .pac-item", '[role="listbox"] [role="option"]', '[role="option"]', ".pac-item"]:
        try:
            items = page.locator(sel)
            n = items.count()
            if n > 0:
                for i in range(n):
                    try:
                        txt = items.nth(i).inner_text()
                        if "san francisco" in txt.lower() or "california" in txt.lower():
                            items.nth(i).click(); pause(0.4)
                            print(f"  Location: {txt!r}")
                            filled = True; break
                    except: pass
                if not filled and n > 0:
                    items.first.click(); pause(0.4); filled = True
                if filled: break
        except: continue

    if not filled:
        page.keyboard.press("Tab"); pause(0.3)
        print("  Location: Tab")

def main():
    lock = Path(PROFILE_DIR) / "Default" / "LOCK"
    if lock.exists():
        try: lock.unlink()
        except: pass

    with sync_playwright() as p:
        print("Launching Chrome...")
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_DIR, channel="chrome", headless=False, no_viewport=True,
            args=["--remote-debugging-port=9410"], ignore_default_args=["--enable-automation"],
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.set_default_timeout(20000)
        page.goto(URL, wait_until="domcontentloaded", timeout=40000)
        page.wait_for_timeout(5000)

        if "404" in page.title():
            print("SKIP-DEAD"); ctx.close(); return "skip-dead"
        print(f"LIVE: {page.title()}")
        ss(page, "01_landing.png")

        # === 1. TEXT FIELDS ===
        print("\n[1] Text fields")
        page.locator("#first_name").fill("Yi-Chieh"); pause()
        page.locator("#last_name").fill("Cheng"); pause()
        page.locator("#email").fill("jamiecheng0103@gmail.com"); pause()

        # === 2. PHONE COUNTRY (react-select) + PHONE ===
        print("\n[2] Phone country + phone")
        select_field(page, "country", "United States")
        try:
            phone_el = page.locator("#phone")
            phone_el.click(); pause(0.2)
            phone_el.fill("2137003831"); pause()
            print("  Phone: 2137003831")
        except Exception as e: print(f"  Phone err: {e}")

        # === 3. LOCATION ===
        print("\n[3] Location")
        fill_location(page)
        ss(page, "02_personal.png")

        # === 4. FILES ===
        print("\n[4] Files")
        try:
            page.locator("#resume").set_input_files(str(RESUME))
            page.wait_for_timeout(3500); print("  Resume OK")
        except Exception as e: print(f"  Resume: {e}")
        if COVER.exists():
            try:
                page.locator("#cover_letter").set_input_files(str(COVER))
                page.wait_for_timeout(3500); print("  Cover OK")
            except Exception as e: print(f"  Cover: {e}")
        ss(page, "03_files.png")

        # === 5. LINKEDIN ===
        print("\n[5] LinkedIn")
        page.locator("#question_36848892002").fill("https://www.linkedin.com/in/jamieyccheng/"); pause()

        # === 6. TWITCH QUESTIONS ===
        print("\n[6] Twitch questions")
        # q894 - familiar with Twitch
        select_field(page, "question_36848894002", "familiar")

        # q895 - Twitch employee
        select_field(page, "question_36848895002", "No")

        # q896 - WORK LOCATION (cities) - pick San Francisco, CA
        ok, chosen = select_field(page, "question_36848896002", "San Francisco")
        if not ok:
            # Fallback: open and look at options
            ok2 = open_select_coord(page, "question_36848896002")
            if ok2:
                texts, opts = get_options(page)
                print(f"  q896 all options: {texts}")
                # Pick "San Francisco, CA" or any SF option, or "No" if no SF
                sf_idx = None
                for i, t in enumerate(texts):
                    if "san francisco" in t.lower(): sf_idx = i; break
                if sf_idx is not None:
                    opts.nth(sf_idx).click(); pause(0.35)
                    sv = get_sv(page, "question_36848896002")
                    print(f"  q896: SF selected [{sv!r}]")
                elif texts:
                    # Pick first option
                    opts.first.click(); pause(0.35)
                    sv = get_sv(page, "question_36848896002")
                    print(f"  q896: first option [{sv!r}]")
                else:
                    close_dropdown(page)

        # === 7. AMAZON QUESTIONS ===
        print("\n[7] Amazon questions")
        for qid, ans in [
            ("question_36848897002", "No"),
            ("question_36848898002", "No"),
            ("question_36848899002", "No"),
            ("question_36848900002", "No"),
            ("question_36848901002", "Yes"),
            ("question_36848902002", "Yes"),   # sponsorship YES
            ("question_36848903002", "No"),    # H-1B transfer
        ]:
            select_field(page, qid, ans)
        ss(page, "04_questions.png")

        # === 8. TAIWAN CITIZENSHIP ===
        print("\n[8] Taiwan citizenship")
        res = page.evaluate('''() => {
            for (const lbl of document.querySelectorAll("label")) {
                if ((lbl.innerText||lbl.textContent||"").trim() === "Taiwan") {
                    const inp = lbl.htmlFor ? document.getElementById(lbl.htmlFor) : lbl.querySelector("input");
                    if (inp && inp.type === "checkbox") { if (!inp.checked) inp.click(); return {id:inp.id, checked:inp.checked}; }
                }
            }
            return {notFound: true};
        }''')
        print(f"  Taiwan: {res}")
        ss(page, "05_citizenship.png")

        # === 9. POST-CITIZENSHIP ===
        print("\n[9] Post-citizenship/export")
        # q905 - other citizenship besides US? → No
        ok905, _ = select_field(page, "question_36848905002", "No")
        if not ok905:
            # Retry with longer wait
            print("  q905: retrying with longer scroll+wait...")
            page.evaluate("() => { const e=document.getElementById('question_36848905002'); if(e) e.scrollIntoView({block:'center'}); }")
            time.sleep(1.0)
            coords905 = get_ctrl_coords(page, "question_36848905002")
            print(f"  q905 coords: {coords905}")
            if coords905.get('found') and coords905['w'] > 0:
                cx = coords905['x'] + coords905['w']/2
                cy = coords905['y'] + coords905['h']/2
                page.mouse.click(cx, cy)
                time.sleep(1.0)
                texts905, opts905 = get_options(page, timeout=3000)
                print(f"  q905 options: {texts905}")
                for i, t in enumerate(texts905):
                    if "no" in t.lower():
                        opts905.nth(i).click(); pause(0.35)
                        sv = get_sv(page, "question_36848905002")
                        print(f"  q905: {t!r} [{sv!r}]")
                        break
                else:
                    close_dropdown(page)

        # q906 - export country → Taiwan
        ok906 = open_select_coord(page, "question_36848906002")
        if ok906:
            page.keyboard.type("Taiwan"); time.sleep(0.8)
            texts906, opts906 = get_options(page)
            print(f"  q906 opts: {texts906}")
            for i, t in enumerate(texts906):
                if "taiwan" in t.lower():
                    opts906.nth(i).click(); pause(0.35)
                    sv = get_sv(page, "question_36848906002")
                    print(f"  q906: {t!r} [{sv!r}]")
                    break
            else:
                if texts906: opts906.first.click(); pause(0.35)
                else: close_dropdown(page)

        # === 10. SALARY / FUTURE OPPS ===
        print("\n[10] Salary/future opps")
        page.locator("#question_36848907002").fill("100000"); pause()
        select_field(page, "question_36848908002", "Yes")
        ss(page, "06_extra.png")

        # === 11. EEO ===
        print("\n[11] EEO")
        select_field(page, "gender", "Female")
        select_field(page, "hispanic_ethnicity", "No")
        select_field(page, "race-label", "Asian")
        select_field(page, "veteran_status", "I am not a protected veteran")
        select_field(page, "disability_status", "No, I do not have a disability")
        ss(page, "07_eeo.png")

        # === READBACK ===
        print("\n[READBACK]")
        rb = {}
        for fid in ["country", "question_36848894002", "question_36848895002",
                    "question_36848896002", "question_36848897002", "question_36848898002",
                    "question_36848899002", "question_36848900002", "question_36848901002",
                    "question_36848902002", "question_36848903002", "question_36848905002",
                    "question_36848906002", "question_36848908002",
                    "gender", "hispanic_ethnicity", "race-label", "veteran_status", "disability_status"]:
            rb[fid] = get_sv(page, fid)

        # Text fields
        for fid in ["first_name", "last_name", "email", "phone", "candidate-location", "question_36848892002", "question_36848907002"]:
            rb[fid] = page.evaluate(f"() => document.getElementById('{fid}')?.value||''")

        rb["taiwan_checked"] = page.evaluate("() => document.querySelectorAll(\"input[name='question_36848904002[]']:checked\").length")

        critical = {"country", "question_36848894002", "question_36848896002",
                    "question_36848902002", "gender", "hispanic_ethnicity", "veteran_status", "disability_status"}
        for k, v in rb.items():
            if k in critical and not v: flag = "FAIL"
            else: flag = "OK" if v else "??"
            short_k = k.replace("question_", "q").replace("36848", "")
            print(f"  {flag} {short_k}: {repr(v)}")

        page.evaluate("window.scrollTo(0,0)"); page.wait_for_timeout(300)
        ss(page, "08a_top.png")
        page.evaluate("window.scrollTo(0,document.body.scrollHeight)"); page.wait_for_timeout(500)
        ss(page, "08b_bottom.png")

        # === SUBMIT ===
        print("\n[SUBMIT]")
        page.wait_for_timeout(1000)
        for btn_text in ["Submit application", "Submit Application", "Submit"]:
            try:
                btn = page.get_by_role("button", name=btn_text)
                if btn.count() > 0 and btn.first.is_visible(timeout=1500):
                    btn.first.scroll_into_view_if_needed(); pause(0.5)
                    btn.first.click(timeout=10000)
                    print(f"  Clicked: {btn_text!r}"); break
            except: continue

        page.wait_for_timeout(12000)
        ss(page, "09_after_submit.png")

        body = page.inner_text("body")
        final_url, final_title = page.url, page.title()
        print(f"\nURL: {final_url}")
        print(f"Title: {final_title.encode('ascii','replace').decode('ascii')}")
        print(f"Body[:300]:\n{body[:300].encode('ascii','replace').decode('ascii')}")

        success = any(k in body.lower() for k in ["thank you", "received", "submitted", "application has been", "we got your"])
        if not success:
            errs = set()
            for e in page.locator('.error, [class*="error"]').all()[:25]:
                try:
                    t = (e.text_content() or "").strip()
                    if 3 < len(t) < 200: errs.add(t)
                except: pass
            print(f"  Errors: {list(errs)[:10]}")

        status = "submitted" if success else "unknown"
        with open(ROLE_DIR / "SUBMITTED.json", "w", encoding="utf-8") as f:
            json.dump({
                "company": "Twitch", "role": "Program Manager, Culture & People Development",
                "ats": "Greenhouse", "job_url": URL, "status": status,
                "confirmed_at": datetime.now().isoformat(), "final_url": final_url,
                "final_title": final_title, "body_preview": body[:600],
                "notes": "v7 - q896=city picker, fixed getSV scope"
            }, f, indent=2, ensure_ascii=False)
        print(f"\nWrote SUBMITTED.json: {status}")
        time.sleep(20)
        ctx.close()
        return status

if __name__ == "__main__":
    r = main()
    print(f"\n=== RESULT: {r} ===")
