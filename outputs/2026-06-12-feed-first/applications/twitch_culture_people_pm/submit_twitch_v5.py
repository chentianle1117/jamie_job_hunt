"""
Twitch Greenhouse Submitter v5
Key insight from inspection:
- Greenhouse uses Remix/React, all fields controlled by React state
- #country is INSIDE phone-input (ITI widget) - it's the dial code, not a form country field
- There is NO separate country form field — Greenhouse captures country via phone+location
- The react-select clicks ARE working (v3 readback showed 'Female', 'No', etc.) but the
  aria-required validation checks the underlying input.value which React keeps empty in controlled mode
- SOLUTION: After clicking an option, verify via the single-value display element, NOT input.value
- The submit validation must work differently — if the visual single-value is shown, Greenhouse accepts it
- v3 showed single-value populated correctly for most fields but submit still failed for q894/896
- v3 issue: "Familiar with Twitch" options were empty (timing) and "Relocation" options were empty
- v4 fix: proper option wait but q894 still picked "No" (it was the FIRST option that appeared)
- REAL fix: wait for `.select__menu` to appear before reading options, and ensure enough wait time

New approach:
1. Click .select__control, wait for .select__menu to appear
2. Read options from .select__menu, pick correct one
3. For country/location: use ITI's own input to set country code, then fill phone number
4. Location: type "San Francisco, CA" then wait for and click pac-item OR just type and Tab away
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

def select_greenhouse_field(page, input_id, want_text, timeout_ms=5000):
    """
    Open a Greenhouse react-select field and pick an option.
    Uses proper Playwright wait for .select__menu to appear.
    """
    want = want_text.strip().lower()

    # Find and click the .select__control ancestor of the input
    clicked = page.evaluate(f'''() => {{
        const inp = document.getElementById("{input_id}");
        if (!inp) return "no-input";
        let el = inp;
        for (let i = 0; i < 12; i++) {{
            el = el.parentElement;
            if (!el) return "no-parent";
            const ctrl = el.querySelector(".select__control");
            if (ctrl) {{
                ctrl.dispatchEvent(new MouseEvent("mousedown", {{bubbles: true, cancelable: true}}));
                ctrl.click();
                return "clicked";
            }}
        }}
        return "no-ctrl";
    }}''')

    if clicked != "clicked":
        print(f"    {input_id}: {clicked}")
        return False, None

    # Wait for the menu to appear
    try:
        page.wait_for_selector(".select__menu", timeout=timeout_ms, state="visible")
        time.sleep(0.2)
    except:
        time.sleep(0.3)

    # Get all options
    opts = page.locator(".select__option")
    n = opts.count()
    texts = []
    for i in range(n):
        try: texts.append(opts.nth(i).inner_text().strip())
        except: pass

    if not texts:
        # No options appeared — try typing to filter
        page.keyboard.type(want_text)
        time.sleep(0.8)
        try: page.wait_for_selector(".select__option", timeout=3000, state="visible")
        except: pass
        opts = page.locator(".select__option")
        n = opts.count()
        texts = []
        for i in range(n):
            try: texts.append(opts.nth(i).inner_text().strip())
            except: pass
        if not texts:
            page.keyboard.press("Escape")
            print(f"    {input_id}: no options for {want_text!r}")
            return False, None

    # Find best match
    best_idx = None
    # Exact match first
    for i, t in enumerate(texts):
        if t.lower() == want:
            best_idx = i; break
    # Partial match
    if best_idx is None:
        for i, t in enumerate(texts):
            if want in t.lower() or t.lower() in want:
                best_idx = i; break
    # Word match
    if best_idx is None:
        want_words = want.split()
        for i, t in enumerate(texts):
            if any(w in t.lower() for w in want_words):
                best_idx = i; break

    if best_idx is None:
        print(f"    {input_id}: no match for {want_text!r} in {texts}")
        page.keyboard.press("Escape")
        return False, None

    chosen = texts[best_idx]
    opts.nth(best_idx).click()
    time.sleep(0.4)
    print(f"    {input_id}: => {chosen!r}")

    # Verify the selection stuck (check single-value display)
    sv = page.evaluate(f'''() => {{
        const inp = document.getElementById("{input_id}");
        if (!inp) return null;
        let el = inp;
        for (let i=0; i<10; i++) {{
            el = el.parentElement; if (!el) break;
            const sv = el.querySelector(".select__single-value");
            if (sv) return (sv.innerText||"").trim();
        }}
        return null;
    }}''')
    print(f"    {input_id}: display={sv!r}")
    return True, chosen

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
        # Phone: just digits (no country code, no dashes)
        page.locator("#phone").fill("2137003831"); pause()
        print("  name/email/phone OK")

        # === 2. LOCATION ===
        # Note: #country is inside phone-input (ITI) — it controls the flag/dial code
        # The actual country for the form application is handled via candidate-location
        print("\n[2] Location (candidate-location)")
        loc = page.locator("#candidate-location").first
        loc.scroll_into_view_if_needed()
        loc.click(); pause(0.3)
        loc.fill("")
        pause(0.2)
        page.keyboard.type("San Francisco, CA")
        page.wait_for_timeout(2000)

        # Wait for Google PAC (Places Autocomplete) container
        try:
            # PAC is typically .pac-container .pac-item or [role="listbox"]
            page.wait_for_selector(".pac-container .pac-item", timeout=3000, state="visible")
            pac_items = page.locator(".pac-container .pac-item")
            n = pac_items.count()
            print(f"  PAC items: {n}")
            if n > 0:
                pac_items.first.click(); pause()
                print("  Location -> PAC selected")
            else:
                page.keyboard.press("ArrowDown"); pause(0.2)
                page.keyboard.press("Enter"); pause()
        except:
            # No PAC — maybe it's just a text input
            page.keyboard.press("Tab"); pause()
            print("  Location -> Tab (no PAC)")

        # Verify location
        loc_val = page.locator("#candidate-location").first.input_value()
        print(f"  Location value: {loc_val!r}")

        ss(page, "02_location.png")

        # === 3. FILES ===
        print("\n[3] Files")
        try:
            page.locator("#resume").set_input_files(str(RESUME))
            page.wait_for_timeout(3500)
            print(f"  Resume OK ({RESUME.stat().st_size} bytes)")
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

        # === 4. LINKEDIN ===
        print("\n[4] LinkedIn")
        page.locator("#question_36848892002").fill("https://www.linkedin.com/in/jamieyccheng/"); pause()
        print("  LinkedIn OK")

        # === 5. TWITCH / AMAZON QUESTIONS ===
        print("\n[5] Twitch/Amazon questions")

        # "Are you familiar with Twitch?" — MUST scroll to this field first
        # The problem in v4 was no options appeared — try scrolling into view first
        try:
            q894 = page.locator("#question_36848894002").first
            q894.scroll_into_view_if_needed()
            page.wait_for_timeout(500)
        except: pass
        ok, chosen = select_greenhouse_field(page, "question_36848894002", "Yes")
        print(f"  Familiar with Twitch? -> {repr(chosen) if ok else 'FAIL'}")
        if not ok:
            # Try the full list — see what options are available
            try:
                q894 = page.locator("#question_36848894002").first
                q894.scroll_into_view_if_needed(); page.wait_for_timeout(300)
                page.evaluate('''() => {
                    const inp = document.getElementById("question_36848894002");
                    let el = inp;
                    for (let i=0; i<12; i++) { el=el.parentElement; if(!el)break; const c=el.querySelector(".select__control"); if(c){c.dispatchEvent(new MouseEvent("mousedown",{bubbles:true}));c.click();return;} }
                }''')
                page.wait_for_timeout(1200)
                opts = page.locator(".select__option").all()
                opts_txt = [o.inner_text().strip() for o in opts[:20]]
                print(f"  q894 options (retry): {opts_txt}")
                if opts_txt:
                    # Pick anything with "Yes" and not "Partner"
                    chosen_opt = None
                    for t in opts_txt:
                        if "yes" in t.lower() and "partner" not in t.lower():
                            chosen_opt = t; break
                    if not chosen_opt:
                        for t in opts_txt:
                            if "yes" in t.lower():
                                chosen_opt = t; break
                    if chosen_opt:
                        for o in page.locator(".select__option").all():
                            if o.inner_text().strip() == chosen_opt:
                                o.click(); pause(); print(f"  Familiar -> {chosen_opt!r}"); break
                    else:
                        page.keyboard.press("Escape")
            except Exception as e:
                print(f"  q894 retry err: {e}")

        # Twitch employee -> No
        ok, chosen = select_greenhouse_field(page, "question_36848895002", "No")
        print(f"  Twitch employee -> {repr(chosen) if ok else 'FAIL'}")

        # Relocation -> Yes (inspect to see actual options)
        ok, chosen = select_greenhouse_field(page, "question_36848896002", "Yes", timeout_ms=4000)
        print(f"  Relocation -> {repr(chosen) if ok else 'FAIL'}")
        if not ok:
            # See what options exist
            page.evaluate('''() => {
                const inp = document.getElementById("question_36848896002");
                let el = inp;
                for (let i=0; i<12; i++) { el=el.parentElement; if(!el)break; const c=el.querySelector(".select__control"); if(c){c.dispatchEvent(new MouseEvent("mousedown",{bubbles:true}));c.click();return;} }
            }''')
            page.wait_for_timeout(1200)
            opts = page.locator(".select__option").all()
            opts_txt = [o.inner_text().strip() for o in opts[:20]]
            print(f"  q896 options: {opts_txt}")
            if opts_txt:
                # Pick any "yes"-like option
                for t in opts_txt:
                    if "yes" in t.lower():
                        for o in page.locator(".select__option").all():
                            if o.inner_text().strip() == t:
                                o.click(); pause(); print(f"  Relocation -> {t!r}"); break
                        break
                else:
                    page.keyboard.press("Escape")

        # Amazon questions
        for qid, ans in [
            ("question_36848897002", "No"),
            ("question_36848898002", "No"),
            ("question_36848899002", "No"),
            ("question_36848900002", "No"),
            ("question_36848901002", "Yes"),
            ("question_36848902002", "Yes"),  # sponsorship
            ("question_36848903002", "No"),   # H-1B
        ]:
            ok, chosen = select_greenhouse_field(page, qid, ans)
            print(f"  {qid[-8:]} -> {repr(chosen) if ok else 'FAIL'}")

        ss(page, "04_twitch_q.png")

        # === 6. CITIZENSHIP CHECKBOX: TAIWAN ===
        print("\n[6] Taiwan citizenship")
        taiwan_result = page.evaluate('''() => {
            // Find label with text "Taiwan" and click its checkbox
            for (const lbl of document.querySelectorAll('label')) {
                if ((lbl.innerText||lbl.textContent||'').trim() === 'Taiwan') {
                    const inp = lbl.htmlFor ? document.getElementById(lbl.htmlFor) : lbl.querySelector('input');
                    if (inp && inp.type === 'checkbox') {
                        if (!inp.checked) inp.click();
                        return {id: inp.id, checked: inp.checked};
                    }
                }
            }
            return {notFound: true};
        }''')
        print(f"  Taiwan: {taiwan_result}")

        ss(page, "05_citizenship.png")

        # === 7. POST-CITIZENSHIP / EXPORT ===
        print("\n[7] Post-citizenship / export")

        # Another citizenship? -> No
        ok, chosen = select_greenhouse_field(page, "question_36848905002", "No")
        print(f"  Another citizenship -> {repr(chosen) if ok else 'FAIL'}")

        # Export licensing: pick Taiwan (citizenship/last permanent residence)
        # First type to filter
        page.evaluate('''() => {
            const inp = document.getElementById("question_36848906002");
            let el = inp;
            for (let i=0; i<12; i++) { el=el.parentElement; if(!el)break; const c=el.querySelector(".select__control"); if(c){c.dispatchEvent(new MouseEvent("mousedown",{bubbles:true}));c.click();return;} }
        }''')
        page.wait_for_timeout(800)
        page.keyboard.type("Taiwan")
        page.wait_for_timeout(1200)
        try: page.wait_for_selector(".select__option", timeout=3000, state="visible")
        except: pass
        opts = page.locator(".select__option").all()
        opts_txt = [o.inner_text().strip() for o in opts[:10]]
        print(f"  Export options: {opts_txt}")
        selected_export = False
        for o, t in zip(page.locator(".select__option").all(), opts_txt):
            if "taiwan" in t.lower():
                o.click(); pause()
                print(f"  Export -> {t!r}"); selected_export = True; break
        if not selected_export:
            page.keyboard.press("Escape")
            print("  Export -> FAIL (Taiwan not found)")

        # === 8. SALARY + FUTURE OPPS ===
        print("\n[8] Salary / future opps")
        page.locator("#question_36848907002").fill("100000"); pause()
        print("  Salary -> 100000")

        ok, chosen = select_greenhouse_field(page, "question_36848908002", "Yes")
        print(f"  Future opps -> {repr(chosen) if ok else 'FAIL'}")

        ss(page, "06_extra.png")

        # === 9. EEO ===
        print("\n[9] EEO demographics")

        ok, chosen = select_greenhouse_field(page, "gender", "Female")
        print(f"  Gender -> {repr(chosen) if ok else 'FAIL'}")

        ok, chosen = select_greenhouse_field(page, "hispanic_ethnicity", "No")
        print(f"  Hispanic -> {repr(chosen) if ok else 'FAIL'}")

        # Race
        ok, chosen = select_greenhouse_field(page, "race-label", "Asian")
        if not ok:
            ok, chosen = select_greenhouse_field(page, "race", "Asian")
        print(f"  Race -> {repr(chosen) if ok else 'FAIL'}")

        ok, chosen = select_greenhouse_field(page, "veteran_status", "I am not a protected veteran")
        print(f"  Veteran -> {repr(chosen) if ok else 'FAIL'}")

        ok, chosen = select_greenhouse_field(page, "disability_status", "No, I do not have a disability")
        print(f"  Disability -> {repr(chosen) if ok else 'FAIL'}")

        ss(page, "07_eeo.png")

        # === READBACK ===
        print("\n[READBACK]")
        rb = page.evaluate('''() => {
            const getSV = id => {
                const inp = document.getElementById(id);
                if (!inp) return null;
                let el = inp;
                for (let i=0; i<10; i++) {
                    el = el.parentElement; if (!el) break;
                    const sv = el.querySelector(".select__single-value");
                    if (sv) return (sv.innerText||"").trim();
                }
                return inp.value||null;
            };
            const g = id => document.getElementById(id)?.value||"";
            return {
                first_name: g("first_name"), last_name: g("last_name"),
                email: g("email"), phone: g("phone"),
                location: g("candidate-location"),
                linkedin: g("question_36848892002"),
                salary: g("question_36848907002"),
                familiar_twitch: getSV("question_36848894002"),
                twitch_employee: getSV("question_36848895002"),
                relocation: getSV("question_36848896002"),
                amazon_employee: getSV("question_36848897002"),
                applied_amazon: getSV("question_36848898002"),
                employed_amazon: getSV("question_36848899002"),
                noncompete: getSV("question_36848900002"),
                legally_eligible: getSV("question_36848901002"),
                sponsorship: getSV("question_36848902002"),
                h1b: getSV("question_36848903002"),
                another_citizenship: getSV("question_36848905002"),
                export_citizenship: getSV("question_36848906002"),
                future_opps: getSV("question_36848908002"),
                gender: getSV("gender"),
                hispanic: getSV("hispanic_ethnicity"),
                race: getSV("race"),
                veteran: getSV("veteran_status"),
                disability: getSV("disability_status"),
                taiwan_checked: (function(){
                    const all = document.querySelectorAll("input[name='question_36848904002[]']:checked");
                    return all.length;
                }()),
            };
        }''')
        missing = []
        for k, v in rb.items():
            status = "OK" if v else "MISS"
            if not v: missing.append(k)
            print(f"  [{status}] {k}: {v!r}")

        if missing:
            print(f"\n  Missing values: {missing}")

        # Final screenshots before submit
        page.evaluate("window.scrollTo(0,0)"); page.wait_for_timeout(300)
        ss(page, "08a_pre_top.png")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight/2)"); page.wait_for_timeout(200)
        ss(page, "08b_pre_mid.png")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)"); page.wait_for_timeout(200)
        ss(page, "08c_pre_bottom.png")

        # === SUBMIT ===
        print("\n[SUBMIT]")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(1500)

        submitted = False
        for btn_text in ["Submit application", "Submit Application", "Apply", "Submit"]:
            try:
                btn = page.get_by_role("button", name=btn_text)
                if btn.count() > 0 and btn.first.is_visible(timeout=1500):
                    btn.first.scroll_into_view_if_needed(); pause(0.5)
                    btn.first.click(timeout=10000)
                    print(f"  Clicked: {btn_text!r}")
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
        print(f"Body[:500]: {body[:500].encode('ascii','replace').decode('ascii')}")

        success = any(k in body.lower() for k in ["thank you", "received", "submitted", "application has been", "we got your"])

        if not success:
            errs = set()
            for e in page.locator('.error, [class*="error"]').all()[:20]:
                try:
                    t = (e.text_content() or "").strip()
                    if 3 < len(t) < 200: errs.add(t)
                except: pass
            print(f"\n  Errors: {list(errs)[:10]}")

            unfilled = page.evaluate('''() => {
                const out = new Map();
                document.querySelectorAll("[aria-required='true'], input[required], select[required], textarea[required]").forEach(el => {
                    if (!el.value) {
                        let lbl="";
                        if(el.id){const l=document.querySelector(`label[for="${el.id}"]`);if(l)lbl=(l.innerText||"").trim().substring(0,80);}
                        out.set(el.id, lbl);
                    }
                });
                return [...out.entries()].map(([id,label]) => ({id,label}));
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
                "notes": "v5 run — proper menu wait"
            }, f, indent=2, ensure_ascii=False)
        print(f"\nWrote SUBMITTED.json: {status}")
        time.sleep(20)
        ctx.close()
        return status

if __name__ == "__main__":
    r = main()
    print(f"\n=== RESULT: {r} ===")
