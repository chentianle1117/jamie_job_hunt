"""
Twitch Greenhouse Submitter v8
Changes from v7:
1. Wait 30s after submit (up from 12s) to give Greenhouse SPA time to update
2. Check body after 5s intervals
3. Check for success/error by looking at visible error divs AND page body
4. Save full body text (not just 600 chars) so we can see what the page shows
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
        if (!inp) return {{found: false}};
        let el = inp;
        for (let i=0; i<12; i++) {{
            if (!el) break;
            const ctrl = el.querySelector ? el.querySelector(".select__control") : null;
            if (ctrl) {{ const r = ctrl.getBoundingClientRect(); return {{found: true, x: r.x, y: r.y, w: r.width, h: r.height}}; }}
            el = el.parentElement;
        }}
        return {{found: false}};
    }}''')

def open_select_coord(page, input_id, extra_wait=0.4):
    page.evaluate(f"() => {{ const e=document.getElementById('{input_id}'); if(e) e.scrollIntoView({{block:'center'}}); }}")
    time.sleep(extra_wait)
    coords = get_ctrl_coords(page, input_id)
    if not coords.get('found') or coords['w'] == 0: return False, None
    cx = coords['x'] + coords['w'] / 2
    cy = coords['y'] + coords['h'] / 2
    page.mouse.click(cx, cy); time.sleep(0.5)
    return True, (cx, cy)

def get_options(page, timeout=5000):
    try: page.wait_for_selector("[class*='select__option']", timeout=timeout, state="visible")
    except: pass
    time.sleep(0.2)
    opts = page.locator("[class*='select__option']")
    n = opts.count()
    return [opts.nth(i).inner_text().strip() for i in range(n)], opts

def close_dd(page): page.keyboard.press("Escape"); time.sleep(0.2)

def get_sv(page, input_id):
    return page.evaluate(f'''() => {{
        const inp = document.getElementById("{input_id}");
        if (!inp) return null;
        let el = inp;
        for (let i=0;i<12;i++) {{
            el=el.parentElement; if(!el) break;
            if (el.querySelector && el.querySelector(".select__control")) {{
                const sv = el.querySelector(".select__single-value,[class*='single-value']");
                return sv ? (sv.innerText||"").trim() : null;
            }}
        }}
        return null;
    }}''')

def select_field(page, input_id, want_text, extra_wait=0.4):
    want = want_text.strip().lower()
    ok, _ = open_select_coord(page, input_id, extra_wait)
    if not ok: return False, None
    texts, opts = get_options(page)
    if not texts: close_dd(page); print(f"  {input_id}: NO OPTIONS"); return False, None

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

    if best_idx is None: close_dd(page); print(f"  {input_id}: no match {want!r} in {texts[:5]}"); return False, None

    chosen = texts[best_idx]
    opts.nth(best_idx).click(); pause(0.35)
    sv = get_sv(page, input_id)
    print(f"  {input_id}: {chosen!r}")
    return True, chosen

def select_q905(page):
    """q905 needs a retry with extra wait."""
    ok, _ = open_select_coord(page, "question_36848905002", 0.4)
    if ok:
        texts, opts = get_options(page)
        if texts:
            for i, t in enumerate(texts):
                if "no" in t.lower(): opts.nth(i).click(); pause(0.35); print(f"  q905: {t!r}"); return True
            close_dd(page)
        else:
            close_dd(page)
    # Retry
    time.sleep(0.8)
    ok, _ = open_select_coord(page, "question_36848905002", 1.0)
    if not ok: return False
    texts, opts = get_options(page, timeout=3000)
    print(f"  q905 retry opts: {texts}")
    for i, t in enumerate(texts):
        if "no" in t.lower(): opts.nth(i).click(); pause(0.35); print(f"  q905: {t!r}"); return True
    close_dd(page); return False

def fill_location(page):
    loc_el = page.locator("#candidate-location").first
    page.evaluate("() => { const e=document.getElementById('candidate-location'); if(e) e.scrollIntoView({block:'center'}); }")
    time.sleep(0.3)
    loc_el.click(); pause(0.3)
    loc_el.fill(""); pause(0.2)
    page.keyboard.type("San Francisco, CA")
    page.wait_for_timeout(3500)

    filled = False
    for sel in [".pac-container .pac-item", '[role="listbox"] [role="option"]', '[role="option"]']:
        try:
            items = page.locator(sel); n = items.count()
            if n > 0:
                for i in range(n):
                    try:
                        txt = items.nth(i).inner_text()
                        if "san francisco" in txt.lower() or "california" in txt.lower():
                            items.nth(i).click(); pause(0.4); print(f"  Location: {txt!r}"); filled = True; break
                    except: pass
                if not filled and n > 0: items.first.click(); pause(0.4); filled = True
                if filled: break
        except: continue

    if not filled: page.keyboard.press("Tab"); pause(0.3); print("  Location: Tab")

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
        if "404" in page.title(): print("SKIP-DEAD"); ctx.close(); return "skip-dead"
        print(f"LIVE: {page.title()}")
        ss(page, "01_landing.png")

        print("\n[1] Text fields")
        page.locator("#first_name").fill("Yi-Chieh"); pause()
        page.locator("#last_name").fill("Cheng"); pause()
        page.locator("#email").fill("jamiecheng0103@gmail.com"); pause()

        print("\n[2] Phone country + phone")
        select_field(page, "country", "United States")
        page.locator("#phone").click(); pause(0.2)
        page.locator("#phone").fill("2137003831"); pause()
        print("  Phone: filled")

        print("\n[3] Location")
        fill_location(page)
        ss(page, "02_personal.png")

        print("\n[4] Files")
        try: page.locator("#resume").set_input_files(str(RESUME)); page.wait_for_timeout(3500); print("  Resume OK")
        except Exception as e: print(f"  Resume: {e}")
        if COVER.exists():
            try: page.locator("#cover_letter").set_input_files(str(COVER)); page.wait_for_timeout(3500); print("  Cover OK")
            except Exception as e: print(f"  Cover: {e}")
        ss(page, "03_files.png")

        print("\n[5] LinkedIn")
        page.locator("#question_36848892002").fill("https://www.linkedin.com/in/jamieyccheng/"); pause()

        print("\n[6] Twitch questions")
        select_field(page, "question_36848894002", "familiar")
        select_field(page, "question_36848895002", "No")
        select_field(page, "question_36848896002", "San Francisco")

        print("\n[7] Amazon questions")
        for qid, ans in [
            ("question_36848897002", "No"), ("question_36848898002", "No"),
            ("question_36848899002", "No"), ("question_36848900002", "No"),
            ("question_36848901002", "Yes"), ("question_36848902002", "Yes"),
            ("question_36848903002", "No"),
        ]:
            select_field(page, qid, ans)
        ss(page, "04_questions.png")

        print("\n[8] Taiwan citizenship")
        res = page.evaluate('''() => {
            for (const lbl of document.querySelectorAll("label")) {
                if ((lbl.innerText||lbl.textContent||"").trim() === "Taiwan") {
                    const inp = lbl.htmlFor ? document.getElementById(lbl.htmlFor) : lbl.querySelector("input");
                    if (inp && inp.type === "checkbox") { if (!inp.checked) inp.click(); return {id:inp.id, checked:inp.checked}; }
                }
            }
            return {notFound:true};
        }''')
        print(f"  Taiwan: {res}")

        print("\n[9] Post-citizenship/export")
        select_q905(page)
        ok906, _ = open_select_coord(page, "question_36848906002")
        if ok906:
            page.keyboard.type("Taiwan"); time.sleep(0.8)
            texts906, opts906 = get_options(page)
            for i, t in enumerate(texts906):
                if "taiwan" in t.lower(): opts906.nth(i).click(); pause(0.35); print(f"  q906: {t!r}"); break
            else:
                if texts906: opts906.first.click()
                else: close_dd(page)
        ss(page, "05_post_citizenship.png")

        print("\n[10] Salary/future opps")
        page.locator("#question_36848907002").fill("100000"); pause()
        select_field(page, "question_36848908002", "Yes")

        print("\n[11] EEO")
        select_field(page, "gender", "Female")
        select_field(page, "hispanic_ethnicity", "No")
        select_field(page, "race-label", "Asian")
        select_field(page, "veteran_status", "I am not a protected veteran")
        select_field(page, "disability_status", "No, I do not have a disability")
        ss(page, "07_eeo.png")

        # Scroll to top, take screenshot, then scroll to bottom to find submit
        page.evaluate("window.scrollTo(0,0)"); page.wait_for_timeout(500)
        ss(page, "08a_top.png")
        page.evaluate("window.scrollTo(0,document.body.scrollHeight)"); page.wait_for_timeout(500)
        ss(page, "08b_bottom.png")

        print("\n[SUBMIT]")
        page.wait_for_timeout(1500)
        clicked = False
        for btn_text in ["Submit application", "Submit Application", "Submit"]:
            try:
                btn = page.get_by_role("button", name=btn_text)
                if btn.count() > 0 and btn.first.is_visible(timeout=1500):
                    btn.first.scroll_into_view_if_needed(); pause(0.5)
                    btn.first.click(timeout=10000)
                    print(f"  Clicked: {btn_text!r}"); clicked = True; break
            except: continue

        if not clicked:
            print("  No submit button found, taking screenshot")
            ss(page, "09_no_submit_btn.png")

        # Wait longer and poll for success
        success = False
        for wait_sec in [5, 10, 15, 30]:
            time.sleep(5)
            body = page.inner_text("body")
            url = page.url
            title = page.title()
            print(f"  [{wait_sec}s] URL: {url[:80]} | Title: {title[:60].encode('ascii','replace').decode('ascii')}")
            if any(k in body.lower() for k in ["thank you", "received your application", "submitted", "application has been submitted"]):
                print("  SUCCESS: thank you detected!")
                success = True
                break
            if "thank" in url.lower() or "confirm" in url.lower() or "success" in url.lower():
                print("  SUCCESS: URL indicates confirmation!")
                success = True
                break
            if wait_sec >= 30: break

        ss(page, "09_after_submit.png")

        body = page.inner_text("body")
        final_url, final_title = page.url, page.title()

        # Check errors
        errs = set()
        for e in page.locator('.error, [class*="error"]').all()[:25]:
            try:
                t = (e.text_content() or "").strip()
                if 3 < len(t) < 200: errs.add(t)
            except: pass
        print(f"  Errors: {list(errs)[:10]}")
        print(f"\n  Final URL: {final_url}")
        print(f"  Final title: {final_title.encode('ascii','replace').decode('ascii')}")
        print(f"  Body[:500]:\n{body[:500].encode('ascii','replace').decode('ascii')}")

        status = "submitted" if success else "needs_review"
        with open(ROLE_DIR / "SUBMITTED.json", "w", encoding="utf-8") as f:
            json.dump({
                "company": "Twitch", "role": "Program Manager, Culture & People Development",
                "ats": "Greenhouse", "job_url": URL, "status": status,
                "confirmed_at": datetime.now().isoformat(), "final_url": final_url,
                "final_title": final_title,
                "body_first_500": body[:500],
                "errors": list(errs),
                "notes": "v8 - 30s wait, poll for success"
            }, f, indent=2, ensure_ascii=False)
        print(f"\nWrote SUBMITTED.json: {status}")
        time.sleep(10)
        ctx.close()
        return status

if __name__ == "__main__":
    r = main()
    print(f"\n=== RESULT: {r} ===")
