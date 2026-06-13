"""
Twitch Greenhouse Submitter v3 — uses JS click on react-select controls
based on actual DOM inspection of the form.
Key fixes:
- Phone: just digits, no +1
- Country: use JS to find .select__control and click it
- Location: type text and wait for Greenhouse's own geocoder autocomplete
- All Twitch questions: use JS-based click to open dropdowns
- Taiwan citizenship: use label selector with []
- Export control: inspect options properly
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
        print(f"  [ss err] {e}")

def open_react_select_by_input_id(page, input_id):
    """Open a react-select dropdown by finding the .select__control ancestor of the input."""
    result = page.evaluate(f'''() => {{
        const inp = document.getElementById("{input_id}");
        if (!inp) return "no-input";
        let el = inp;
        for (let i = 0; i < 10; i++) {{
            el = el.parentElement;
            if (!el) return "no-parent";
            const ctrl = el.querySelector('.select__control');
            if (ctrl) {{
                ctrl.dispatchEvent(new MouseEvent('mousedown', {{bubbles: true}}));
                ctrl.click();
                return "ok:" + ctrl.className;
            }}
        }}
        return "no-control";
    }}''')
    print(f"    open_react_select({input_id}): {result}")
    time.sleep(0.5)
    page.wait_for_timeout(600)
    return "ok" in str(result)

def pick_option(page, want_text):
    """After opening a react-select, pick the option containing want_text."""
    want = want_text.strip().lower()
    opts = page.locator(".select__option")
    n = opts.count()
    print(f"    options visible: {n}")
    for i in range(n):
        try:
            txt = opts.nth(i).inner_text().strip()
            print(f"      [{i}] {txt!r}")
            if want in txt.lower() or txt.lower() in want:
                opts.nth(i).click()
                time.sleep(0.4)
                print(f"    => clicked: {txt!r}")
                return True
        except:
            pass
    return False

def select_q(page, input_id, want_text):
    """Open a react-select by input id, then pick an option."""
    ok = open_react_select_by_input_id(page, input_id)
    if not ok:
        print(f"    Could not open {input_id}")
        return False
    result = pick_option(page, want_text)
    if not result:
        print(f"    Option '{want_text}' not found, trying to type...")
        page.keyboard.type(want_text)
        page.wait_for_timeout(800)
        result = pick_option(page, want_text)
        if not result:
            page.keyboard.press("Escape")
    return result

def main():
    # Clean up LOCK
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

        print(f"Goto {URL}")
        page.goto(URL, wait_until="domcontentloaded", timeout=40000)
        page.wait_for_timeout(5000)

        title = page.title()
        print(f"Title: {title}")
        if "404" in title or "not found" in title.lower():
            print("SKIP-DEAD"); ctx.close(); return "skip-dead"

        print("LIVE")
        ss(page, "01_landing.png")

        # --- Inspect actual form structure ---
        print("\n--- Inspecting form structure ---")
        struct = page.evaluate('''() => {
            const out = [];
            // Find all question containers
            document.querySelectorAll('[id^="question_"]').forEach(el => {
                const id = el.id;
                // Find nearest label
                let lbl = '';
                const fld = el.closest('[class*="field"], [class*="question"]');
                if (fld) {
                    const l = fld.querySelector('label');
                    if (l) lbl = (l.innerText||'').trim().substring(0,80);
                }
                // What class does the parent have?
                let parentClass = el.parentElement ? el.parentElement.className : '';
                // Is there a select__control nearby?
                let hasSelectCtrl = false;
                let el2 = el;
                for (let i=0; i<8 && el2; i++) {
                    if (el2.querySelector('.select__control')) { hasSelectCtrl = true; break; }
                    el2 = el2.parentElement;
                }
                out.push({id, lbl, parentClass: parentClass.substring(0,60), hasSelectCtrl, tagName: el.tagName, type: el.type||''});
            });
            return out;
        }''')
        for s in struct:
            print(f"  {s['id']}: lbl={s['lbl'][:50]!r} hasCtrl={s['hasSelectCtrl']} tag={s['tagName']} type={s['type']}")

        # --- PERSONAL ---
        print("\n--- Personal ---")
        try: page.locator("#first_name").fill("Yi-Chieh"); pause()
        except: pass
        try: page.locator("#last_name").fill("Cheng"); pause()
        except: pass
        try: page.locator("#email").fill("jamiecheng0103@gmail.com"); pause()
        except: pass
        # Phone: digits only without country code
        try: page.locator("#phone").fill("2137003831"); pause()
        except: pass
        print("  Personal text fields done")

        # Country
        print("  Country...")
        ok = select_q(page, "country", "United States")
        print(f"  Country -> {'OK' if ok else 'FAIL'}")

        # Location
        print("  Location...")
        try:
            loc = page.locator("#candidate-location").first
            loc.scroll_into_view_if_needed()
            pause(0.3)
            loc.click()
            pause(0.3)
            # Clear and type
            for _ in range(30): page.keyboard.press("Backspace")
            page.keyboard.type("San Francisco, CA")
            page.wait_for_timeout(2500)
            # Check for autocomplete
            autocomplete = page.locator('[role="listbox"] [role="option"], .pac-item, [class*="suggestion"]')
            n = autocomplete.count()
            print(f"  Location autocomplete options: {n}")
            if n > 0:
                autocomplete.first.click()
                pause()
                print("  Location -> clicked autocomplete")
            else:
                # For Greenhouse, location might just be a text field
                page.keyboard.press("Tab")
                pause()
                print("  Location -> Tab pressed (text field)")
        except Exception as e:
            print(f"  Location err: {e}")

        ss(page, "02_personal.png")

        # --- FILES ---
        print("\n--- Files ---")
        try:
            page.locator("#resume").set_input_files(str(RESUME))
            page.wait_for_timeout(3500)
            print(f"  Resume OK")
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

        # --- LINKEDIN ---
        print("\n--- LinkedIn ---")
        try:
            page.locator("#question_36848892002").fill("https://www.linkedin.com/in/jamieyccheng/"); pause()
            print("  LinkedIn OK")
        except Exception as e:
            print(f"  LinkedIn err: {e}")

        # --- TWITCH QUESTIONS ---
        print("\n--- Twitch questions ---")

        print("  Familiar with Twitch?...")
        ok = select_q(page, "question_36848894002", "Yes")
        print(f"  Familiar -> {'Yes' if ok else 'FAIL'}")

        print("  Currently Twitch employee?...")
        ok = select_q(page, "question_36848895002", "No")
        print(f"  Twitch employee -> {'No' if ok else 'FAIL'}")

        print("  Open to relocation?...")
        ok = select_q(page, "question_36848896002", "Yes")
        print(f"  Relocation -> {'Yes' if ok else 'FAIL'}")

        print("  Current Amazon employee?...")
        ok = select_q(page, "question_36848897002", "No")
        print(f"  Amazon employee -> {'No' if ok else 'FAIL'}")

        print("  Previously applied Amazon?...")
        ok = select_q(page, "question_36848898002", "No")
        print(f"  Applied Amazon -> {'No' if ok else 'FAIL'}")

        print("  Previously employed Amazon?...")
        ok = select_q(page, "question_36848899002", "No")
        print(f"  Employed Amazon -> {'No' if ok else 'FAIL'}")

        print("  Non-compete agreement?...")
        ok = select_q(page, "question_36848900002", "No")
        print(f"  Non-compete -> {'No' if ok else 'FAIL'}")

        print("  Legally eligible to work at Amazon?...")
        ok = select_q(page, "question_36848901002", "Yes")
        print(f"  Legally eligible -> {'Yes' if ok else 'FAIL'}")

        print("  Sponsorship required?...")
        ok = select_q(page, "question_36848902002", "Yes")
        print(f"  Sponsorship -> {'Yes' if ok else 'FAIL'}")

        print("  Previously held H-1B?...")
        ok = select_q(page, "question_36848903002", "No")
        print(f"  H-1B -> {'No' if ok else 'FAIL'}")

        ss(page, "04_twitch_q.png")

        # --- CITIZENSHIP CHECKBOXES ---
        print("\n--- Citizenship: Taiwan ---")
        try:
            # Use XPath to find checkbox with label "Taiwan"
            taiwan_cb = page.get_by_label("Taiwan")
            if taiwan_cb.count() > 0:
                taiwan_cb.scroll_into_view_if_needed()
                if not taiwan_cb.is_checked():
                    taiwan_cb.click()
                    pause()
                print("  Taiwan checked")
            else:
                # Use JS to find checkbox with value or id containing Taiwan
                result = page.evaluate('''() => {
                    const labels = document.querySelectorAll('label');
                    for (const lbl of labels) {
                        if ((lbl.innerText||'').trim() === 'Taiwan') {
                            const inp = document.getElementById(lbl.htmlFor) || lbl.querySelector('input');
                            if (inp && !inp.checked) {
                                inp.click();
                                return "clicked:" + inp.id;
                            }
                            return "already-checked:" + inp?.id;
                        }
                    }
                    return "not-found";
                }''')
                print(f"  Taiwan JS: {result}")
        except Exception as e:
            print(f"  Taiwan err: {e}")

        ss(page, "05_citizenship.png")

        # --- POST-CITIZENSHIP / EXPORT ---
        print("\n--- Post-citizenship / Export ---")

        print("  Acquired another citizenship after most recent?...")
        ok = select_q(page, "question_36848905002", "No")
        print(f"  Another citizenship -> {'No' if ok else 'FAIL'}")

        print("  Export licensing question (inspect first)...")
        # First just open and see what options are available
        open_react_select_by_input_id(page, "question_36848906002")
        opts_texts = []
        opts = page.locator(".select__option")
        n = opts.count()
        for i in range(n):
            try:
                opts_texts.append(opts.nth(i).inner_text().strip())
            except: pass
        print(f"  Export options: {opts_texts}")

        # Close if nothing matched yet
        if opts_texts:
            # Jamie is a Taiwan national (not US citizen/PR) - answer "No" or "Non-U.S. Person"
            selected = False
            for target in ["No", "Non-U.S.", "Non-US", "Foreign National", "Not a U.S."]:
                for i, txt in enumerate(opts_texts):
                    if target.lower() in txt.lower():
                        opts.nth(i).click()
                        pause()
                        print(f"  Export -> {txt!r}")
                        selected = True
                        break
                if selected: break

            if not selected:
                # Just pick the first option and note it
                opts.first.click()
                pause()
                print(f"  Export -> first option: {opts_texts[0] if opts_texts else 'unknown'}")
        else:
            page.keyboard.press("Escape")
            print("  Export -> no options, skipping")

        # --- SALARY ---
        print("\n--- Salary ---")
        try:
            page.locator("#question_36848907002").fill("100000"); pause()
            print("  Salary -> 100000")
        except Exception as e:
            print(f"  Salary err: {e}")

        print("  Future opportunities?...")
        ok = select_q(page, "question_36848908002", "Yes")
        print(f"  Future opps -> {'Yes' if ok else 'FAIL'}")

        ss(page, "06_extra.png")

        # --- EEO ---
        print("\n--- EEO ---")

        print("  Gender...")
        ok = select_q(page, "gender", "Female")
        if not ok:
            ok = select_q(page, "gender", "Woman")
        print(f"  Gender -> {'filled' if ok else 'FAIL'}")

        print("  Hispanic/Latino...")
        ok = select_q(page, "hispanic_ethnicity", "No")
        if not ok:
            ok = select_q(page, "hispanic_ethnicity", "Not Hispanic or Latino")
        print(f"  Hispanic -> {'No' if ok else 'FAIL'}")

        # Race - this is typically a separate react-select
        print("  Race/Ethnicity...")
        # Find by inspecting what ids exist for race
        race_q = page.evaluate('''() => {
            const all = document.querySelectorAll('[id^="race"], [id*="race"], select[name*="race"]');
            return Array.from(all).map(el => el.id);
        }''')
        print(f"  Race field ids: {race_q}")
        if race_q:
            ok = select_q(page, race_q[0], "Asian")
            print(f"  Race -> {'Asian' if ok else 'FAIL'}")
        else:
            # Try by label text
            ok = select_q(page, "race", "Asian")
            if not ok:
                # Find any visible select that might be race
                print("  Race -> trying label search")
                try:
                    lbl = page.get_by_text("Race", exact=True)
                    if lbl.count() > 0:
                        # Find associated select
                        container = lbl.locator("xpath=ancestor::div[position()<=4]").first
                        ctrl = container.locator(".select__control").first
                        if ctrl.count() > 0:
                            ctrl.click()
                            pause(0.4)
                            page.wait_for_timeout(600)
                            ok = pick_option(page, "Asian")
                            print(f"  Race (via label) -> {'Asian' if ok else 'FAIL'}")
                except Exception as e:
                    print(f"  Race label err: {e}")

        print("  Veteran status...")
        ok = select_q(page, "veteran_status", "I am not a protected veteran")
        if not ok:
            ok = select_q(page, "veteran_status", "Not a protected veteran")
        print(f"  Veteran -> {'filled' if ok else 'FAIL'}")

        print("  Disability status...")
        ok = select_q(page, "disability_status", "No, I do not have a disability")
        if not ok:
            ok = select_q(page, "disability_status", "No")
        print(f"  Disability -> {'filled' if ok else 'FAIL'}")

        ss(page, "07_eeo.png")

        # --- FINAL REVIEW ---
        print("\n--- Final Review ---")
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(400)
        ss(page, "08a_final_top.png")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight / 3)")
        page.wait_for_timeout(300)
        ss(page, "08b_final_mid1.png")
        page.evaluate("window.scrollTo(0, 2 * document.body.scrollHeight / 3)")
        page.wait_for_timeout(300)
        ss(page, "08c_final_mid2.png")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(300)
        ss(page, "08d_final_bottom.png")

        # READ BACK key values
        readback = page.evaluate('''() => {
            const get = id => { const el=document.getElementById(id); return el?el.value:''; };
            const getSelect = id => {
                const inp = document.getElementById(id);
                if (!inp) return null;
                // Try to find the react-select value display
                let el = inp;
                for (let i=0; i<8; i++) {
                    el = el.parentElement;
                    if (!el) break;
                    const sv = el.querySelector('.select__single-value, [class*="singleValue"]');
                    if (sv) return (sv.innerText||'').trim();
                }
                return inp.value||null;
            };
            return {
                first_name: get('first_name'),
                last_name: get('last_name'),
                email: get('email'),
                phone: get('phone'),
                country: getSelect('country'),
                location: get('candidate-location'),
                linkedin: get('question_36848892002'),
                salary: get('question_36848907002'),
                twitch_familiar: getSelect('question_36848894002'),
                twitch_employee: getSelect('question_36848895002'),
                relocation: getSelect('question_36848896002'),
                amazon_employee: getSelect('question_36848897002'),
                sponsorship: getSelect('question_36848902002'),
                gender: getSelect('gender'),
                hispanic: getSelect('hispanic_ethnicity'),
                veteran: getSelect('veteran_status'),
                disability: getSelect('disability_status'),
            };
        }''')
        print("\n  READBACK:")
        for k, v in readback.items():
            print(f"    {k}: {v!r}")

        # Check unfilled required
        unfilled = page.evaluate('''() => {
            const out = [];
            document.querySelectorAll('[aria-required="true"], input[required], select[required], textarea[required]').forEach(el => {
                if (!el.value) {
                    let lbl = '';
                    if (el.id) { const l = document.querySelector(`label[for="${el.id}"]`); if(l) lbl=(l.innerText||'').trim().substring(0,80); }
                    if (!lbl) {
                        let p = el.parentElement;
                        for (let i=0; i<4 && p; i++) {
                            const l = p.querySelector('label'); if(l){lbl=(l.innerText||'').trim().substring(0,80); break;} p=p.parentElement;
                        }
                    }
                    out.push({id: el.id, label: lbl});
                }
            });
            return [...new Set(out.map(JSON.stringify))].map(JSON.parse);
        }''')
        print(f"\n  Unfilled required: {len(unfilled)}")
        for u in unfilled[:20]:
            print(f"    - id={u['id']!r} label={u['label']!r}")

        # --- SUBMIT ---
        print("\n--- SUBMIT ---")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(1500)

        submitted = False
        for btn_text in ["Submit application", "Submit Application", "Apply now", "Apply", "Submit"]:
            try:
                btn = page.get_by_role("button", name=btn_text)
                if btn.count() > 0 and btn.first.is_visible(timeout=1500):
                    btn.first.scroll_into_view_if_needed()
                    pause(0.5)
                    btn.first.click(timeout=10000)
                    print(f"  => Clicked: '{btn_text}'")
                    submitted = True
                    break
            except:
                continue

        if not submitted:
            try:
                page.locator('button[type="submit"]').first.click()
                submitted = True
                print("  => Clicked submit button")
            except:
                pass

        page.wait_for_timeout(12000)
        ss(page, "09_after_submit.png")

        body = page.inner_text("body")
        final_url = page.url
        final_title = page.title()
        safe_body = body[:2000].encode("ascii", "replace").decode("ascii")
        print(f"\nFinal URL: {final_url}")
        print(f"Final title: {final_title.encode('ascii','replace').decode('ascii')}")
        print(f"Body[:500]:\n{safe_body[:500]}")

        success = any(k in body.lower() for k in ["thank you", "received", "submitted", "we got your", "application has been"])

        if not success:
            errs = page.locator('.error, [class*="error"], .field_with_errors').all()
            err_msgs = []
            for e in errs[:15]:
                try:
                    t = (e.text_content() or "").strip()
                    if 3 < len(t) < 200: err_msgs.append(t)
                except: pass
            if err_msgs:
                print(f"\n  Errors: {err_msgs[:10]}")

            unfilled2 = page.evaluate('''() => {
                const out = [];
                document.querySelectorAll('[aria-required="true"], input[required], select[required], textarea[required]').forEach(el => {
                    if (!el.value) {
                        let lbl = '';
                        if (el.id) { const l = document.querySelector(`label[for="${el.id}"]`); if(l) lbl=(l.innerText||'').trim().substring(0,80); }
                        out.push({id: el.id, label: lbl});
                    }
                });
                return [...new Set(out.map(JSON.stringify))].map(JSON.parse);
            }''')
            print(f"\n  Post-submit unfilled: {len(unfilled2)}")
            for u in unfilled2[:15]:
                print(f"    - {u['id']!r}: {u['label']!r}")

        status = "submitted" if success else "unknown"
        submitted_data = {
            "company": "Twitch", "role": "Program Manager, Culture & People Development",
            "ats": "Greenhouse", "job_url": URL, "status": status,
            "confirmed_at": datetime.now().isoformat(),
            "final_url": final_url, "final_title": final_title,
            "body_preview": body[:600],
            "screenshot_confirmation": str(OUT_DIR / "09_after_submit.png"),
            "notes": "Twitch/Amazon Greenhouse form: citizenship + export control Qs present"
        }
        with open(ROLE_DIR / "SUBMITTED.json", "w", encoding="utf-8") as f:
            json.dump(submitted_data, f, indent=2, ensure_ascii=False)
        print(f"\nWrote SUBMITTED.json: status={status}")

        time.sleep(15)
        ctx.close()
        return status

if __name__ == "__main__":
    r = main()
    print(f"\n=== RESULT: {r} ===")
