"""
Twitch Greenhouse Submitter v4
Key fixes based on v3 analysis:
- Country select was selecting phone dial code widget instead of form country
- Location: use Playwright's built-in approach without autocomplete interference
- All Q answers not persisting: react-select selections are working visually but
  the hidden input behind them needs the React change event
- "Familiar with Twitch": options include "Yes, I watch Twitch" type answers
- Relocation: options may differ from "Yes" - need to see actual list
- Export 906002: needs to get the right citizenship value (Taiwan)
"""
import os, sys, time, json
from datetime import datetime
from pathlib import Path

AUTOPILOT_LIB = Path(r"C:\Users\chent\Agentic_Workflows_2026\jamie-autopilot\lib")
sys.path.insert(0, str(AUTOPILOT_LIB))

from patchright.sync_api import sync_playwright

ROLE_DIR = Path(r"C:\Users\chent\Agentic_Workflows_2026\oracle-job-search\outputs\2026-06-12-feed-first\applications\twitch_culture_people_pm")
RESUME = ROLE_DIR / "resume.pdf"
COVER = ROLE_DIR / "cover_letter.pdf"
OUT_DIR = ROLE_DIR / "screenshots"
OUT_DIR.mkdir(exist_ok=True)

URL = "https://job-boards.greenhouse.io/twitch/jobs/8582338002"
PROFILE_DIR = r"C:\Users\chent\ats_agent_9410"

def pause(t=0.7):
    time.sleep(t)

def ss(page, name):
    try:
        page.screenshot(path=str(OUT_DIR / name), full_page=True)
        print(f"  [ss] {name}")
    except Exception as e:
        print(f"  [ss] err: {e}")

def open_ctrl_and_get_options(page, input_id):
    """Open the react-select for input_id and return list of option texts."""
    # Click the select__control that is the ancestor of the input
    page.evaluate(f'''() => {{
        const inp = document.getElementById("{input_id}");
        if (!inp) return;
        let el = inp;
        for (let i = 0; i < 10; i++) {{
            el = el.parentElement;
            if (!el) break;
            const ctrl = el.querySelector('.select__control');
            if (ctrl) {{ ctrl.dispatchEvent(new MouseEvent('mousedown', {{bubbles:true}})); ctrl.click(); return; }}
        }}
    }}''')
    time.sleep(0.5)
    page.wait_for_timeout(700)

    opts = page.locator(".select__option")
    n = opts.count()
    texts = []
    for i in range(n):
        try: texts.append(opts.nth(i).inner_text().strip())
        except: pass
    return texts, opts

def select_option(page, opts, opts_texts, want_text):
    """Pick the best-matching option from the open dropdown."""
    want = want_text.strip().lower()
    # Exact first, then partial
    for priority in [lambda t: t == want, lambda t: want in t or t in want, lambda t: any(w in t for w in want.split())]:
        for i, txt in enumerate(opts_texts):
            if priority(txt.lower()):
                try:
                    opts.nth(i).click()
                    time.sleep(0.4)
                    print(f"    => {txt!r}")
                    return True, txt
                except:
                    pass
    return False, None

def select_q(page, input_id, want_text, inspect=False):
    """Open react-select by input_id, pick matching option."""
    texts, opts = open_ctrl_and_get_options(page, input_id)
    if inspect or not texts:
        print(f"    Options for {input_id}: {texts}")
    if not texts:
        # Type to filter
        page.keyboard.type(want_text)
        page.wait_for_timeout(800)
        texts, opts = [], page.locator(".select__option")
        n = opts.count()
        for i in range(n):
            try: texts.append(opts.nth(i).inner_text().strip())
            except: pass
        if not texts:
            page.keyboard.press("Escape")
            return False, None
    ok, chosen = select_option(page, opts, texts, want_text)
    if not ok:
        # Try typing to filter
        page.keyboard.type(want_text)
        page.wait_for_timeout(800)
        new_texts, new_opts = [], page.locator(".select__option")
        n = new_opts.count()
        for i in range(n):
            try: new_texts.append(new_opts.nth(i).inner_text().strip())
            except: pass
        ok, chosen = select_option(page, new_opts, new_texts, want_text)
        if not ok:
            page.keyboard.press("Escape")
    return ok, chosen

def main():
    lock = Path(PROFILE_DIR) / "Default" / "LOCK"
    if lock.exists():
        try: lock.unlink()
        except: pass

    with sync_playwright() as p:
        print("Launching Chrome...")
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_DIR,
            channel="chrome",
            headless=False,
            no_viewport=True,
            args=["--remote-debugging-port=9410"],
            ignore_default_args=["--enable-automation"],
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.set_default_timeout(15000)
        page.goto(URL, wait_until="domcontentloaded", timeout=40000)
        page.wait_for_timeout(5000)

        if "404" in page.title():
            print("SKIP-DEAD"); ctx.close(); return "skip-dead"
        print("LIVE")
        ss(page, "01_landing.png")

        # === STEP 1: BASIC TEXT FIELDS ===
        print("\n[1] Text fields")
        page.locator("#first_name").fill("Yi-Chieh"); pause()
        page.locator("#last_name").fill("Cheng"); pause()
        page.locator("#email").fill("jamiecheng0103@gmail.com"); pause()
        page.locator("#phone").fill("2137003831"); pause()
        print("  name/email/phone done")

        # === STEP 2: COUNTRY (Greenhouse react-select, NOT phone flag) ===
        print("\n[2] Country")
        # Greenhouse form has BOTH:
        # - A phone flag/dial-code widget (ITI - intl-tel-input)
        # - A country react-select for the actual form question
        # The #country input is the react-select. But the phone field also has a country dropdown.
        # We need to find the correct container.

        # First, let's inspect what #country is
        country_info = page.evaluate('''() => {
            const el = document.getElementById('country');
            if (!el) return {found: false};
            const parent = el.parentElement;
            const grandparent = el.parentElement?.parentElement;
            return {
                found: true,
                parentClass: parent?.className?.substring(0,80),
                grandClass: grandparent?.className?.substring(0,80),
                nearestSelectCtrl: !!el.closest('.select__control') || !!(function(){
                    let e=el;
                    for(let i=0;i<8;i++){e=e.parentElement;if(!e)return false;if(e.querySelector('.select__control'))return true;}
                    return false;
                }()),
                form_group_label: (function(){
                    let e=el;
                    for(let i=0;i<6;i++){
                        e=e.parentElement;
                        if(!e)return '';
                        const lbl=e.querySelector('label');
                        if(lbl) return (lbl.innerText||'').trim().substring(0,80);
                    }
                    return '';
                }()),
            };
        }''')
        print(f"  Country field info: {country_info}")

        ok, chosen = select_q(page, "country", "United States", inspect=True)
        print(f"  Country -> {repr(chosen) if ok else 'FAIL'}")

        # === STEP 3: LOCATION ===
        print("\n[3] Location")
        # The candidate-location field in Greenhouse is typically a Google Maps autocomplete
        # Let's type the city and then press ArrowDown + Enter to accept first suggestion
        loc_el = page.locator("#candidate-location").first
        try:
            loc_el.scroll_into_view_if_needed()
            pause(0.3)
            loc_el.click()
            pause(0.3)
            loc_el.fill("")
            pause(0.2)
            page.keyboard.type("San Francisco")
            page.wait_for_timeout(2000)

            # Find ONLY the Google Places autocomplete (pac-container), not ITI dropdown
            pac_items = page.locator(".pac-item, .pac-container .pac-item")
            n = pac_items.count()
            print(f"  PAC items: {n}")
            if n > 0:
                pac_items.first.click()
                pause()
                print("  Location -> PAC first item clicked")
            else:
                # Try pressing ArrowDown then Enter
                page.keyboard.press("ArrowDown")
                pause(0.3)
                page.keyboard.press("Enter")
                pause()
                print("  Location -> ArrowDown+Enter")
        except Exception as e:
            print(f"  Location err: {e}")

        ss(page, "02_country_location.png")

        # === STEP 4: FILES ===
        print("\n[4] Files")
        try:
            page.locator("#resume").set_input_files(str(RESUME))
            page.wait_for_timeout(3500)
            print("  Resume OK")
        except Exception as e:
            print(f"  Resume err: {e}")

        if COVER.exists():
            try:
                page.locator("#cover_letter").set_input_files(str(COVER))
                page.wait_for_timeout(3500)
                print("  Cover OK")
            except Exception as e:
                print(f"  Cover err: {e}")

        ss(page, "03_files.png")

        # === STEP 5: LINKEDIN ===
        print("\n[5] LinkedIn")
        page.locator("#question_36848892002").fill("https://www.linkedin.com/in/jamieyccheng/"); pause()

        # === STEP 6: TWITCH QUESTIONS — inspect all options first ===
        print("\n[6] Twitch/Amazon questions (inspect mode)")

        # Familiar with Twitch — see what options are available
        texts_894, opts_894 = open_ctrl_and_get_options(page, "question_36848894002")
        print(f"  [894] Familiar options: {texts_894}")
        # Pick "Yes" variant that's NOT "Twitch Partner" (she's not a streamer/partner)
        # Want the most basic "Yes" or "Yes, I watch Twitch"
        best_894 = None
        for prefer in ["Yes, I watch Twitch", "Yes, I use Twitch", "Yes, I", "Yes"]:
            for t in texts_894:
                if prefer.lower() in t.lower() and "partner" not in t.lower() and "affiliate" not in t.lower():
                    best_894 = t; break
            if best_894: break
        if not best_894 and texts_894:
            # Just take first non-partner option
            for t in texts_894:
                if "partner" not in t.lower() and "affiliate" not in t.lower():
                    best_894 = t; break
        if not best_894 and texts_894:
            best_894 = texts_894[-1]  # last option
        print(f"  [894] Will pick: {best_894!r}")
        if best_894:
            ok_894, _ = select_option(page, opts_894, texts_894, best_894)
            if not ok_894:
                open_ctrl_and_get_options(page, "question_36848894002")
                texts_894b, opts_894b = open_ctrl_and_get_options(page, "question_36848894002")
                select_option(page, opts_894b, texts_894b, best_894)
        print(f"  Familiar -> done")

        # Relocation — inspect options
        texts_896, opts_896 = open_ctrl_and_get_options(page, "question_36848896002")
        print(f"  [896] Relocation options: {texts_896}")
        best_896 = None
        for prefer in ["Yes", "Open to relocation", "Yes, open"]:
            for t in texts_896:
                if prefer.lower() in t.lower():
                    best_896 = t; break
            if best_896: break
        if not best_896 and texts_896: best_896 = texts_896[0]
        if best_896:
            ok_896, _ = select_option(page, opts_896, texts_896, best_896)
            print(f"  Relocation -> {best_896!r}: {'OK' if ok_896 else 'FAIL'}")

        # Current Amazon employee -> No
        ok, chosen = select_q(page, "question_36848897002", "No")
        print(f"  Amazon employee -> {repr(chosen) if ok else 'FAIL'}")

        # Previously applied Amazon -> No
        ok, chosen = select_q(page, "question_36848898002", "No")
        print(f"  Applied Amazon -> {repr(chosen) if ok else 'FAIL'}")

        # Previously employed Amazon -> No
        ok, chosen = select_q(page, "question_36848899002", "No")
        print(f"  Employed Amazon -> {repr(chosen) if ok else 'FAIL'}")

        # Non-compete -> No
        ok, chosen = select_q(page, "question_36848900002", "No")
        print(f"  Non-compete -> {repr(chosen) if ok else 'FAIL'}")

        # Legally eligible -> Yes
        ok, chosen = select_q(page, "question_36848901002", "Yes")
        print(f"  Legally eligible -> {repr(chosen) if ok else 'FAIL'}")

        # Sponsorship -> Yes
        ok, chosen = select_q(page, "question_36848902002", "Yes")
        print(f"  Sponsorship -> {repr(chosen) if ok else 'FAIL'}")

        # H-1B -> No
        ok, chosen = select_q(page, "question_36848903002", "No")
        print(f"  H-1B -> {repr(chosen) if ok else 'FAIL'}")

        ss(page, "04_twitch_q.png")

        # === STEP 7: CITIZENSHIP CHECKBOXES ===
        print("\n[7] Citizenship: Taiwan")
        result = page.evaluate('''() => {
            // Find the Taiwan label
            const allLabels = document.querySelectorAll('label');
            for (const lbl of allLabels) {
                const txt = (lbl.innerText || lbl.textContent || '').trim();
                if (txt === 'Taiwan') {
                    const forId = lbl.htmlFor;
                    let inp = forId ? document.getElementById(forId) : lbl.querySelector('input[type="checkbox"]');
                    if (inp && !inp.checked) {
                        inp.click();
                        return {clicked: true, id: inp.id};
                    } else if (inp && inp.checked) {
                        return {alreadyChecked: true, id: inp.id};
                    }
                }
            }
            return {notFound: true};
        }''')
        print(f"  Taiwan: {result}")

        ss(page, "05_citizenship.png")

        # === STEP 8: POST-CITIZENSHIP ===
        print("\n[8] Post-citizenship / export")

        # After most recent citizenship, acquired another? -> No
        ok, chosen = select_q(page, "question_36848905002", "No")
        print(f"  Another citizenship -> {repr(chosen) if ok else 'FAIL'}")

        # Export licensing / deemed export (q906002) - inspect
        texts_906, opts_906 = open_ctrl_and_get_options(page, "question_36848906002")
        print(f"  [906] Export options: {texts_906}")
        # This q asks: "For the sole purpose of determining export licensing requirements,
        # provide your country of citizenship or legal permanent residence, whichever was obtained last"
        # So the options are COUNTRIES (like the country list), and we pick Taiwan
        if texts_906:
            ok_906, chosen_906 = select_option(page, opts_906, texts_906, "Taiwan")
            if not ok_906:
                # Type Taiwan to filter
                page.keyboard.type("Taiwan")
                page.wait_for_timeout(800)
                texts_906b, opts_906b = [], page.locator(".select__option")
                n = opts_906b.count()
                for i in range(n):
                    try: texts_906b.append(opts_906b.nth(i).inner_text().strip())
                    except: pass
                print(f"  [906] After typing Taiwan: {texts_906b}")
                ok_906, chosen_906 = select_option(page, opts_906b, texts_906b, "Taiwan")
                if not ok_906:
                    page.keyboard.press("Escape")
            print(f"  Export/Citizenship -> {repr(chosen_906) if ok_906 else 'FAIL'}")
        else:
            # No options shown initially, try typing
            page.keyboard.type("Taiwan")
            page.wait_for_timeout(800)
            texts_906c, opts_906c = [], page.locator(".select__option")
            n = opts_906c.count()
            for i in range(n):
                try: texts_906c.append(opts_906c.nth(i).inner_text().strip())
                except: pass
            print(f"  [906] After typing: {texts_906c}")
            ok_906, chosen_906 = select_option(page, opts_906c, texts_906c, "Taiwan")
            if not ok_906:
                page.keyboard.press("Escape")
            print(f"  Export -> {repr(chosen_906) if ok_906 else 'FAIL'}")

        # === STEP 9: SALARY + FUTURE OPPS ===
        print("\n[9] Salary")
        page.locator("#question_36848907002").fill("100000"); pause()
        ok, chosen = select_q(page, "question_36848908002", "Yes")
        print(f"  Future opps -> {repr(chosen) if ok else 'FAIL'}")

        ss(page, "06_export_salary.png")

        # === STEP 10: EEO ===
        print("\n[10] EEO demographics")
        ok, chosen = select_q(page, "gender", "Female")
        print(f"  Gender -> {repr(chosen) if ok else 'FAIL'}")

        ok, chosen = select_q(page, "hispanic_ethnicity", "No")
        if not ok:
            ok, chosen = select_q(page, "hispanic_ethnicity", "Not Hispanic")
        print(f"  Hispanic -> {repr(chosen) if ok else 'FAIL'}")

        ok, chosen = select_q(page, "race-label", "Asian")
        if not ok:
            ok, chosen = select_q(page, "race", "Asian")
        print(f"  Race -> {repr(chosen) if ok else 'FAIL'}")

        ok, chosen = select_q(page, "veteran_status", "not a protected veteran")
        print(f"  Veteran -> {repr(chosen) if ok else 'FAIL'}")

        ok, chosen = select_q(page, "disability_status", "No, I do not have a disability")
        print(f"  Disability -> {repr(chosen) if ok else 'FAIL'}")

        ss(page, "07_eeo.png")

        # === READBACK ===
        print("\n[READBACK]")
        readback = page.evaluate('''() => {
            const getSV = id => {
                const inp = document.getElementById(id);
                if (!inp) return null;
                let el = inp;
                for (let i=0; i<10; i++) {
                    el = el.parentElement; if (!el) break;
                    const sv = el.querySelector('.select__single-value');
                    if (sv) return (sv.innerText||'').trim();
                }
                return inp.value||null;
            };
            const get = id => { const el=document.getElementById(id); return el?el.value:''; };
            return {
                first_name: get('first_name'), last_name: get('last_name'),
                email: get('email'), phone: get('phone'),
                country: getSV('country'), location: get('candidate-location'),
                linkedin: get('question_36848892002'), salary: get('question_36848907002'),
                familiar_twitch: getSV('question_36848894002'),
                twitch_employee: getSV('question_36848895002'),
                relocation: getSV('question_36848896002'),
                amazon_employee: getSV('question_36848897002'),
                amazon_applied: getSV('question_36848898002'),
                amazon_employed: getSV('question_36848899002'),
                noncompete: getSV('question_36848900002'),
                legally_eligible: getSV('question_36848901002'),
                sponsorship: getSV('question_36848902002'),
                h1b: getSV('question_36848903002'),
                another_citizenship: getSV('question_36848905002'),
                export_citizenship: getSV('question_36848906002'),
                future_opps: getSV('question_36848908002'),
                gender: getSV('gender'), hispanic: getSV('hispanic_ethnicity'),
                race: getSV('race'), veteran: getSV('veteran_status'),
                disability: getSV('disability_status'),
            };
        }''')
        print("  Values:")
        for k, v in readback.items():
            marker = "OK" if v else "??"
            print(f"    [{marker}] {k}: {v!r}")

        # === SCREENSHOTS before submit ===
        page.evaluate("window.scrollTo(0, 0)"); page.wait_for_timeout(400)
        ss(page, "08a_pre_top.png")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)"); page.wait_for_timeout(300)
        ss(page, "08b_pre_mid.png")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)"); page.wait_for_timeout(300)
        ss(page, "08c_pre_bottom.png")

        # === SUBMIT ===
        print("\n[SUBMIT]")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(1500)

        submitted = False
        for btn_txt in ["Submit application", "Submit Application", "Apply", "Submit"]:
            try:
                btn = page.get_by_role("button", name=btn_txt)
                if btn.count() > 0 and btn.first.is_visible(timeout=1500):
                    btn.first.scroll_into_view_if_needed(); pause(0.5)
                    btn.first.click(timeout=10000)
                    print(f"  Clicked: {btn_txt!r}")
                    submitted = True; break
            except: continue
        if not submitted:
            try:
                page.locator('button[type="submit"]').first.click()
                submitted = True; print("  Clicked submit[type=submit]")
            except: pass

        page.wait_for_timeout(12000)
        ss(page, "09_after_submit.png")

        body = page.inner_text("body")
        final_url = page.url
        final_title = page.title()
        print(f"\nURL: {final_url}")
        print(f"Title: {final_title.encode('ascii','replace').decode('ascii')}")
        print(f"Body[:400]: {body[:400].encode('ascii','replace').decode('ascii')}")

        success = any(k in body.lower() for k in ["thank you", "received", "submitted", "application has been", "we got your"])

        if not success:
            errs = page.locator('.error, [class*="error"]').all()
            err_msgs = set()
            for e in errs[:20]:
                try:
                    t = (e.text_content() or "").strip()
                    if 3 < len(t) < 200: err_msgs.add(t)
                except: pass
            print(f"\n  Errors: {list(err_msgs)[:10]}")

            unfilled = page.evaluate('''() => {
                const out = new Set();
                document.querySelectorAll('[aria-required="true"], input[required], select[required], textarea[required]').forEach(el => {
                    if (!el.value) {
                        let lbl = '';
                        if (el.id) { const l = document.querySelector(`label[for="${el.id}"]`); if(l) lbl=(l.innerText||'').trim().substring(0,80); }
                        out.add(JSON.stringify({id: el.id, label: lbl}));
                    }
                });
                return [...out].map(JSON.parse);
            }''')
            print(f"\n  Unfilled ({len(unfilled)}):")
            for u in unfilled[:20]: print(f"    - {u['id']!r}: {u['label']!r}")

        status = "submitted" if success else "unknown"
        with open(ROLE_DIR / "SUBMITTED.json", "w", encoding="utf-8") as f:
            json.dump({
                "company": "Twitch", "role": "Program Manager, Culture & People Development",
                "ats": "Greenhouse", "job_url": URL, "status": status,
                "confirmed_at": datetime.now().isoformat(),
                "final_url": final_url, "final_title": final_title,
                "body_preview": body[:600],
                "screenshot_confirmation": str(OUT_DIR / "09_after_submit.png"),
                "notes": "v4 run"
            }, f, indent=2, ensure_ascii=False)
        print(f"\nWrote SUBMITTED.json: {status}")
        time.sleep(15)
        ctx.close()
        return status

if __name__ == "__main__":
    r = main()
    print(f"\n=== RESULT: {r} ===")
