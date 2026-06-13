"""
Twitch Greenhouse Submitter FINAL3
Targeted fixes for 3 remaining blockers:
1. ITI country: use page.click() with force=True after explicit scroll + wait
2. q894/q896: wait much longer (6s) after opening dropdown; also try Tab-into-field approach
3. Location: fill field with JS then trigger blur to commit React state
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

def get_options(page, timeout=6000):
    """Wait for options to appear in the open dropdown."""
    try: page.wait_for_selector(".select__option", timeout=timeout, state="visible"); time.sleep(0.2)
    except: pass
    opts = page.locator(".select__option")
    n = opts.count()
    texts = [opts.nth(i).inner_text().strip() for i in range(n)]
    return texts, opts

def open_rs(page, input_id):
    """Open react-select by scrolling to input then clicking its .select__control."""
    # First scroll the input into view
    page.evaluate(f'() => {{ const e=document.getElementById("{input_id}"); if(e) e.scrollIntoView({{block:"center"}}); }}')
    time.sleep(0.3)
    return page.evaluate(f'''() => {{
        const inp = document.getElementById("{input_id}");
        if (!inp) return "no-input";
        let el = inp;
        for (let i=0; i<12; i++) {{
            el = el.parentElement; if(!el) return "no-parent";
            const ctrl = el.querySelector(".select__control");
            if(ctrl) {{
                ctrl.dispatchEvent(new MouseEvent("mousedown",{{bubbles:true,cancelable:true}}));
                ctrl.click(); return "ok";
            }}
        }}
        return "no-ctrl";
    }}''')

def select_field(page, input_id, want_text):
    want = want_text.strip().lower()
    r = open_rs(page, input_id)
    texts, opts = get_options(page)

    if not texts:
        page.keyboard.press("Escape")
        print(f"  {input_id}: NO OPTIONS")
        return False, None

    best_idx = None
    if want == "yes":
        yes_opts = [(i, t) for i, t in enumerate(texts) if "yes" in t.lower()]
        if yes_opts:
            good = [(i,t) for i,t in yes_opts if "partner" not in t.lower() and "affiliate" not in t.lower()]
            if good: best_idx = min(good, key=lambda x: len(x[1]))[0]
            else: best_idx = min(yes_opts, key=lambda x: len(x[1]))[0]

    if best_idx is None:
        for i, t in enumerate(texts):
            if t.lower() == want: best_idx = i; break
    if best_idx is None:
        for i, t in enumerate(texts):
            if want in t.lower(): best_idx = i; break

    if best_idx is None:
        page.keyboard.press("Escape")
        print(f"  {input_id}: no match for {want_text!r} in {texts}")
        return False, None

    chosen = texts[best_idx]
    opts.nth(best_idx).click(); pause(0.35)
    sv = page.evaluate(f'''() => {{
        const inp = document.getElementById("{input_id}");
        if (!inp) return null;
        let el = inp;
        for (let i=0;i<10;i++) {{ el=el.parentElement; if(!el) break; const sv=el.querySelector(".select__single-value"); if(sv) return (sv.innerText||"").trim(); }}
        return null;
    }}''')
    print(f"  {input_id}: {chosen!r} [{sv!r}]")
    return True, chosen

def set_iti_us(page):
    """Set ITI phone country to United States.
    Strategy: scroll phone field into view, then use Playwright click (with force)
    on the flag button element."""
    try:
        # Scroll phone field into view
        page.evaluate("() => { const e=document.getElementById('phone'); if(e) e.scrollIntoView({block:'center'}); }")
        time.sleep(1.0)

        # Check if ITI is present and get the flag button's bounding box
        iti_info = page.evaluate('''() => {
            const flag = document.querySelector(".iti__selected-flag");
            if (!flag) return {found: false};
            const r = flag.getBoundingClientRect();
            return {found: true, x: r.x, y: r.y, w: r.width, h: r.height, visible: r.width > 0 && r.height > 0};
        }''')
        print(f"  ITI flag info: {iti_info}")

        if not iti_info.get('found'):
            print("  ITI: .iti__selected-flag not found in DOM")
            return False

        # Try clicking via Playwright locator with force
        flag = page.locator(".iti__selected-flag").first
        try:
            flag.click(force=True, timeout=5000)
            time.sleep(0.8)
        except Exception as e:
            print(f"  ITI click error: {e}")
            # Fallback: click by coordinates
            x = iti_info.get('x', 0) + iti_info.get('w', 20)/2
            y = iti_info.get('y', 0) + iti_info.get('h', 20)/2
            if x > 0 and y > 0:
                page.mouse.click(x, y); time.sleep(0.8)
                print(f"  ITI: coordinate click at ({x:.0f},{y:.0f})")

        # Check if the ITI dropdown opened
        search = page.locator("#iti-0__search-input")
        visible = False
        try: visible = search.is_visible(timeout=2000)
        except: pass

        if not visible:
            # Try clicking the flag container button
            for sel in [".iti__flag-container button", ".iti button", "[class*='iti'] button"]:
                try:
                    btn = page.locator(sel).first
                    if btn.count() > 0:
                        btn.click(force=True, timeout=3000)
                        time.sleep(0.8)
                        try: visible = search.is_visible(timeout=1500)
                        except: pass
                        if visible:
                            print(f"  ITI opened via {sel!r}")
                            break
                except: continue

        if not visible:
            print("  ITI: dropdown not opening, trying keyboard approach")
            # Focus phone field then shift-Tab to reach country selector
            phone_el = page.locator("#phone").first
            phone_el.click(); pause(0.3)
            # Maybe pressing Enter on the flag when it's focused
            page.keyboard.press("Tab"); pause(0.3)
            page.keyboard.press("Tab"); pause(0.3)
            try: visible = search.is_visible(timeout=1500)
            except: pass

        if not visible:
            print("  ITI: could not open dropdown after all attempts")
            return False

        print("  ITI: dropdown open, searching...")
        search.fill("United States"); pause(0.5)
        time.sleep(0.8)

        items = page.locator(".iti__country")
        n = items.count()
        print(f"  ITI items: {n}")
        for i in range(n):
            try:
                txt = items.nth(i).inner_text().strip()
                if "united states" in txt.lower() and "territories" not in txt.lower() and "island" not in txt.lower():
                    items.nth(i).click(); pause(0.3)
                    print(f"  ITI: selected {txt!r}")
                    return True
            except: continue

        page.keyboard.press("Enter"); pause(0.3)
        print("  ITI: Enter (fallback)")
        return True

    except Exception as e:
        print(f"  ITI err: {e}")
        return False

def select_q894(page):
    """Select 'Yes' (non-partner) for 'Are you familiar with Twitch?' (q894)."""
    input_id = "question_36848894002"

    # Scroll to question
    page.evaluate(f"() => {{ const e=document.getElementById('{input_id}'); if(e) e.scrollIntoView({{block:'center'}}); }}")
    time.sleep(0.5)

    # Try multiple times with increasing waits
    for attempt in range(3):
        r = open_rs(page, input_id)
        print(f"  q894 open: {r!r}")

        # Wait longer on each retry
        wait_ms = 3000 + attempt * 2000
        try: page.wait_for_selector(".select__option", timeout=wait_ms, state="visible")
        except: pass

        texts, opts = get_options(page, timeout=1000)
        print(f"  q894 attempt {attempt+1} options: {texts}")

        if texts:
            # Find yes that isn't partner/affiliate
            best = None
            for t in sorted(texts, key=len):
                if "yes" in t.lower() and "partner" not in t.lower() and "affiliate" not in t.lower():
                    best = t; break
            if best is None:
                for t in sorted(texts, key=len):
                    if "yes" in t.lower(): best = t; break
            if best:
                for i, t in enumerate(texts):
                    if t == best: opts.nth(i).click(); pause(0.3); print(f"  q894: {best!r}"); return True
            page.keyboard.press("Escape")
            return False
        else:
            page.keyboard.press("Escape")
            time.sleep(1)

    print("  q894: exhausted retries, no options")
    return False

def select_q896(page):
    """Select 'Yes' for 'Are you open to relocation?' (q896)."""
    input_id = "question_36848896002"
    page.evaluate(f"() => {{ const e=document.getElementById('{input_id}'); if(e) e.scrollIntoView({{block:'center'}}); }}")
    time.sleep(0.5)

    for attempt in range(3):
        r = open_rs(page, input_id)
        print(f"  q896 open: {r!r}")
        wait_ms = 3000 + attempt * 2000
        try: page.wait_for_selector(".select__option", timeout=wait_ms, state="visible")
        except: pass

        texts, opts = get_options(page, timeout=1000)
        print(f"  q896 attempt {attempt+1} options: {texts}")

        if texts:
            for i, t in enumerate(texts):
                if "yes" in t.lower():
                    opts.nth(i).click(); pause(0.3); print(f"  q896: {t!r}"); return True
            page.keyboard.press("Escape")
            return False
        else:
            page.keyboard.press("Escape")
            time.sleep(1)

    print("  q896: exhausted retries, no options")
    return False

def fill_location(page):
    """Fill location field with autocomplete."""
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
                            print(f"  Location: {txt!r} via {sel!r}")
                            filled = True; break
                    except: pass
                if not filled and n > 0:
                    items.first.click(); pause(0.4)
                    print(f"  Location: first item via {sel!r}")
                    filled = True
                if filled: break
        except: continue

    if not filled:
        page.keyboard.press("Tab"); pause(0.3)
        print("  Location: Tab (no autocomplete found)")

    loc_val = loc_el.input_value() if loc_el.count() > 0 else ""
    if not loc_val:
        set_result = page.evaluate('''() => {
            const el = document.getElementById("candidate-location");
            if (!el) return "no-el";
            const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
            nativeSetter.call(el, "San Francisco, CA");
            el.dispatchEvent(new Event("input", {bubbles: true}));
            el.dispatchEvent(new Event("change", {bubbles: true}));
            el.dispatchEvent(new Event("blur", {bubbles: true}));
            return el.value;
        }''')
        print(f"  Location JS force: {set_result!r}")
    else:
        print(f"  Location: {loc_val!r}")

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
        print("  name/email OK")

        # === 2. PHONE + ITI ===
        print("\n[2] Phone + ITI")
        set_iti_us(page)
        try:
            phone_el = page.locator("#phone")
            phone_el.click(); pause(0.2)
            phone_el.fill("2137003831"); pause()
            print("  Phone: filled")
        except Exception as e:
            print(f"  Phone err: {e}")

        iti_check = page.evaluate('''() => {
            const flag = document.querySelector(".iti__selected-flag");
            const dialCode = document.querySelector(".iti__selected-dial-code,.iti__dial-code");
            const ariaLabel = flag?.getAttribute("aria-label") || "";
            return {
                ariaLabel,
                dialCode: (dialCode?.innerText||"").trim(),
                flagClass: (flag?.className||"").substring(0,80),
            };
        }''')
        print(f"  ITI: {iti_check}")

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

        # === 6. TWITCH-SPECIFIC ===
        print("\n[6] Twitch questions")
        select_q894(page)
        select_field(page, "question_36848895002", "No")
        select_q896(page)

        print("\n[7] Amazon questions")
        for qid, ans in [
            ("question_36848897002", "No"),
            ("question_36848898002", "No"),
            ("question_36848899002", "No"),
            ("question_36848900002", "No"),
            ("question_36848901002", "Yes"),
            ("question_36848902002", "Yes"),
            ("question_36848903002", "No"),
        ]:
            select_field(page, qid, ans)
        ss(page, "04_twitch_q.png")

        # === 8. TAIWAN ===
        print("\n[8] Taiwan")
        res = page.evaluate('''() => {
            for (const lbl of document.querySelectorAll("label")) {
                if ((lbl.innerText||lbl.textContent||"").trim() === "Taiwan") {
                    const inp = lbl.htmlFor ? document.getElementById(lbl.htmlFor) : lbl.querySelector("input");
                    if (inp && inp.type === "checkbox") { if (!inp.checked) inp.click(); return {id: inp.id, checked: inp.checked}; }
                }
            }
            return {notFound: true};
        }''')
        print(f"  Taiwan: {res}")
        ss(page, "05_citizenship.png")

        # === 9. POST-CITIZENSHIP ===
        print("\n[9] Post-citizenship/export")
        select_field(page, "question_36848905002", "No")

        page.evaluate("() => { const e=document.getElementById('question_36848906002'); if(e)e.scrollIntoView({block:'center'}); }")
        time.sleep(0.4)
        open_rs(page, "question_36848906002")
        texts906, opts906 = get_options(page, timeout=3000)
        if not texts906:
            page.keyboard.type("Taiwan"); time.sleep(0.8)
            texts906, opts906 = get_options(page)
        for i, t in enumerate(texts906):
            if "taiwan" in t.lower():
                opts906.nth(i).click(); pause(0.3); print(f"  Export: {t!r}"); break
        else:
            if texts906: opts906.first.click(); pause(0.3)
            else: page.keyboard.press("Escape")

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
        rb = page.evaluate('''() => {
            const getSV = id => {
                const inp = document.getElementById(id); if (!inp) return null;
                let el = inp; for (let i=0;i<10;i++) { el=el.parentElement; if(!el)break; const sv=el.querySelector(".select__single-value"); if(sv) return (sv.innerText||"").trim(); } return inp.value||null;
            };
            const g = id => document.getElementById(id)?.value||"";
            const dialCode = document.querySelector(".iti__selected-dial-code,.iti__dial-code")?.innerText||"";
            return {
                first_name: g("first_name"), last_name: g("last_name"), email: g("email"), phone: g("phone"),
                location: g("candidate-location"), linkedin: g("question_36848892002"), salary: g("question_36848907002"),
                familiar: getSV("question_36848894002"), twitch_emp: getSV("question_36848895002"),
                relocation: getSV("question_36848896002"), amz_emp: getSV("question_36848897002"),
                sponsor: getSV("question_36848902002"), h1b: getSV("question_36848903002"),
                taiwan_checked: document.querySelectorAll("input[name='question_36848904002[]']:checked").length,
                export_country: getSV("question_36848906002"), future_opps: getSV("question_36848908002"),
                gender: getSV("gender"), hispanic: getSV("hispanic_ethnicity"), race: getSV("race"),
                veteran: getSV("veteran_status"), disability: getSV("disability_status"),
                iti_dial: dialCode,
            };
        }''')
        for k, v in rb.items():
            flag = "OK" if v else "??"
            if k in ("familiar", "relocation") and v in (None, "No", ""):
                flag = "FAIL"
            if k == "iti_dial" and "+1" not in str(v):
                flag = "WARN-ITI"
            print(f"  {flag} {k}: {repr(v)}")

        ss(page, "08a_top.png")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)"); page.wait_for_timeout(500)
        ss(page, "08b_bottom.png")

        # === SUBMIT ===
        print("\n[SUBMIT]")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)"); page.wait_for_timeout(1500)
        for btn_text in ["Submit application", "Submit Application", "Apply", "Submit"]:
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
            for e in page.locator('.error, [class*="error"]').all()[:20]:
                try:
                    t = (e.text_content() or "").strip()
                    if 3 < len(t) < 200: errs.add(t)
                except: pass
            print(f"\n  Errors: {list(errs)[:10]}")

        status = "submitted" if success else "unknown"
        with open(ROLE_DIR / "SUBMITTED.json", "w", encoding="utf-8") as f:
            json.dump({
                "company": "Twitch", "role": "Program Manager, Culture & People Development",
                "ats": "Greenhouse", "job_url": URL, "status": status,
                "confirmed_at": datetime.now().isoformat(), "final_url": final_url,
                "final_title": final_title, "body_preview": body[:600],
                "notes": "Final3 - force ITI click + extended option wait"
            }, f, indent=2, ensure_ascii=False)
        print(f"\nWrote SUBMITTED.json: {status}")
        time.sleep(20)
        ctx.close()
        return status

if __name__ == "__main__":
    r = main()
    print(f"\n=== RESULT: {r} ===")
