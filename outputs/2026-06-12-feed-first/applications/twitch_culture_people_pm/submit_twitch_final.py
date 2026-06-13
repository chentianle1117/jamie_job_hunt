"""
Twitch Greenhouse Submitter FINAL
Targeted fixes based on 5 prior runs:
1. Country (ITI phone widget): click the flag button -> search for "United States" -> click
2. Location: type city -> wait longer for PAC -> if no PAC, just leave the typed text
3. q894 "Familiar with Twitch?": there's a non-partner "Yes" option - need to scroll into view
   and pick the right option (not "Yes, I'm a Twitch Partner")
4. q896 "Relocation": scroll into view, then open - timeout issue in v5
5. All other q's working correctly in v5
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

def get_all_options(page, timeout=3000):
    """Wait for options and return them."""
    try:
        page.wait_for_selector(".select__option", timeout=timeout, state="visible")
        time.sleep(0.15)
    except: pass
    opts = page.locator(".select__option")
    n = opts.count()
    texts = []
    for i in range(n):
        try: texts.append(opts.nth(i).inner_text().strip())
        except: pass
    return texts, opts

def open_react_select(page, input_id):
    """Open the react-select by finding .select__control ancestor of input_id."""
    return page.evaluate(f'''() => {{
        const inp = document.getElementById("{input_id}");
        if (!inp) return "no-input";
        let el = inp;
        for (let i = 0; i < 12; i++) {{
            el = el.parentElement;
            if (!el) return "no-parent";
            const ctrl = el.querySelector(".select__control");
            if (ctrl) {{
                ctrl.dispatchEvent(new MouseEvent("mousedown", {{bubbles:true, cancelable:true}}));
                ctrl.click();
                return "ok";
            }}
        }}
        return "no-ctrl";
    }}''')

def select_field(page, input_id, want_text, scroll_first=True):
    """Select an option from a react-select field."""
    want = want_text.strip().lower()

    if scroll_first:
        try:
            page.locator(f"#{input_id}").first.scroll_into_view_if_needed()
            pause(0.3)
        except: pass

    r = open_react_select(page, input_id)
    texts, opts = get_all_options(page)

    if not texts:
        # Type to filter
        page.keyboard.type(want_text)
        texts, opts = get_all_options(page)
        if not texts:
            page.keyboard.press("Escape")
            return False, None

    # Find best match: not-partner Yes variant for Twitch question
    best_idx = None
    # For "Yes" requests: prefer the shortest "Yes" option (avoid "Yes, I'm a Twitch Partner")
    if want == "yes":
        # Find "Yes" options, prefer shorter/simpler ones
        yes_opts = [(i, t) for i, t in enumerate(texts) if "yes" in t.lower()]
        if yes_opts:
            # Pick shortest
            best_idx = min(yes_opts, key=lambda x: len(x[1]))[0]

    if best_idx is None:
        for i, t in enumerate(texts):
            if t.lower() == want:
                best_idx = i; break

    if best_idx is None:
        for i, t in enumerate(texts):
            if want in t.lower() and ("partner" not in t.lower() or want != "yes"):
                best_idx = i; break

    if best_idx is None:
        for i, t in enumerate(texts):
            if want in t.lower():
                best_idx = i; break

    if best_idx is None:
        print(f"    {input_id}: no match for {want_text!r} in {texts}")
        page.keyboard.press("Escape")
        return False, None

    chosen = texts[best_idx]
    opts.nth(best_idx).click()
    pause(0.35)

    sv = page.evaluate(f'''() => {{
        const inp = document.getElementById("{input_id}");
        if (!inp) return null;
        let el = inp;
        for (let i=0;i<10;i++) {{
            el=el.parentElement; if(!el)break;
            const sv=el.querySelector(".select__single-value");
            if(sv) return (sv.innerText||"").trim();
        }}
        return null;
    }}''')
    print(f"  {input_id}: {chosen!r} [display={sv!r}]")
    return True, chosen

def set_iti_country(page, country_name="United States"):
    """Set the ITI (intl-tel-input) phone widget country by clicking the flag button and searching."""
    try:
        # Click the flag button to open the country picker
        flag_btn = page.locator(".iti__selected-flag, .iti__flag-container button, [class*='iti__selected']").first
        if flag_btn.count() > 0:
            flag_btn.scroll_into_view_if_needed()
            flag_btn.click(); pause(0.5)

            # Wait for the dropdown to open
            page.wait_for_timeout(800)

            # Type in the search box
            search = page.locator("#iti-0__search-input")
            if search.count() > 0 and search.is_visible(timeout=2000):
                search.fill(country_name); pause(0.3)
                page.wait_for_timeout(500)

                # Click the matching item
                items = page.locator(".iti__country.iti__highlight, .iti__country[aria-selected='true'], .iti__country")
                n = items.count()
                for i in range(n):
                    try:
                        txt = items.nth(i).inner_text().strip()
                        if country_name.lower() in txt.lower():
                            items.nth(i).click(); pause(0.3)
                            print(f"  ITI country: {txt!r}")
                            return True
                    except: pass

                # Fallback: press Enter
                page.keyboard.press("Enter"); pause(0.3)
                return True
    except Exception as e:
        print(f"  ITI country err: {e}")
    return False

def fill_location(page):
    """Fill the location field with San Francisco, CA."""
    loc = page.locator("#candidate-location").first
    loc.scroll_into_view_if_needed(); pause(0.3)
    loc.click(); pause(0.3)
    loc.fill(""); pause(0.2)
    page.keyboard.type("San Francisco, CA")
    page.wait_for_timeout(3000)

    # Try PAC autocomplete
    try:
        pac = page.locator(".pac-container .pac-item")
        n = pac.count()
        if n > 0:
            pac.first.click(); pause(0.3)
            print("  Location: PAC clicked")
            return
    except: pass

    # Try [role="listbox"] options
    try:
        listbox = page.locator('[role="listbox"] [role="option"], [role="option"]')
        n = listbox.count()
        if n > 0:
            # Click first option that contains "San Francisco"
            for i in range(n):
                try:
                    txt = listbox.nth(i).inner_text()
                    if "san francisco" in txt.lower():
                        listbox.nth(i).click(); pause(0.3)
                        print(f"  Location: listbox {txt!r}")
                        return
                except: pass
            listbox.first.click(); pause(0.3)
            print("  Location: listbox first")
            return
    except: pass

    # Just press Tab to accept the typed text
    page.keyboard.press("Tab"); pause(0.3)
    val = loc.input_value()
    print(f"  Location: Tab (value={val!r})")

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

        # === 1. PERSONAL TEXT FIELDS ===
        print("\n[1] Text fields")
        page.locator("#first_name").fill("Yi-Chieh"); pause()
        page.locator("#last_name").fill("Cheng"); pause()
        page.locator("#email").fill("jamiecheng0103@gmail.com"); pause()
        print("  name/email done")

        # === 2. PHONE + COUNTRY (ITI widget) ===
        print("\n[2] Phone + Country (ITI)")
        # Set the ITI phone country to United States first
        iti_ok = set_iti_country(page, "United States")
        print(f"  ITI country: {'OK' if iti_ok else 'FAIL'}")

        # Then fill phone number (just digits, ITI handles the +1)
        page.locator("#phone").fill("2137003831"); pause()
        print("  Phone: 2137003831")

        # === 3. LOCATION ===
        print("\n[3] Location")
        fill_location(page)

        ss(page, "02_personal.png")

        # === 4. FILES ===
        print("\n[4] Files")
        try:
            page.locator("#resume").set_input_files(str(RESUME))
            page.wait_for_timeout(3500)
            print(f"  Resume OK")
        except Exception as e: print(f"  Resume err: {e}")

        if COVER.exists():
            try:
                page.locator("#cover_letter").set_input_files(str(COVER))
                page.wait_for_timeout(3500)
                print("  Cover OK")
            except Exception as e: print(f"  Cover err: {e}")

        ss(page, "03_files.png")

        # === 5. LINKEDIN ===
        print("\n[5] LinkedIn")
        page.locator("#question_36848892002").fill("https://www.linkedin.com/in/jamieyccheng/"); pause()

        # === 6. TWITCH QUESTIONS ===
        print("\n[6] Twitch/Amazon questions")

        # Familiar with Twitch? — scroll to field, pick non-partner Yes
        try: page.locator("#question_36848894002").scroll_into_view_if_needed(); pause(0.5)
        except: pass
        r894 = open_react_select(page, "question_36848894002")
        texts894, opts894 = get_all_options(page, timeout=5000)
        print(f"  q894 options: {texts894}")
        if texts894:
            # Pick the least-specific Yes (avoid Partner/Affiliate)
            best = None
            for t in sorted(texts894, key=len):  # shortest first
                if "yes" in t.lower() and "partner" not in t.lower() and "affiliate" not in t.lower():
                    best = t; break
            if best is None:
                for t in sorted(texts894, key=len):
                    if "yes" in t.lower():
                        best = t; break
            if best:
                for o, t in zip([opts894.nth(i) for i in range(len(texts894))], texts894):
                    if t == best:
                        o.click(); pause(0.3)
                        print(f"  q894: {best!r}"); break
            else:
                page.keyboard.press("Escape")
                print("  q894: no good Yes option found")

        # Currently Twitch employee? -> No
        ok, chosen = select_field(page, "question_36848895002", "No")

        # Relocation? -> Yes (scroll first, then open)
        try: page.locator("#question_36848896002").scroll_into_view_if_needed(); pause(0.8)
        except: pass
        r896 = open_react_select(page, "question_36848896002")
        texts896, opts896 = get_all_options(page, timeout=5000)
        print(f"  q896 options: {texts896}")
        if texts896:
            best896 = None
            for t in texts896:
                if "yes" in t.lower():
                    best896 = t; break
            if best896:
                for i, t in enumerate(texts896):
                    if t == best896:
                        opts896.nth(i).click(); pause(0.3)
                        print(f"  q896: {best896!r}"); break
            else:
                page.keyboard.press("Escape")
                print(f"  q896: no Yes option in {texts896}")

        # Amazon questions
        for qid, ans in [
            ("question_36848897002", "No"),   # Amazon employee
            ("question_36848898002", "No"),   # Applied to Amazon
            ("question_36848899002", "No"),   # Employed by Amazon
            ("question_36848900002", "No"),   # Non-compete
            ("question_36848901002", "Yes"),  # Legally eligible
            ("question_36848902002", "Yes"),  # Sponsorship
            ("question_36848903002", "No"),   # H-1B
        ]:
            select_field(page, qid, ans)

        ss(page, "04_twitch_q.png")

        # === 7. CITIZENSHIP: TAIWAN ===
        print("\n[7] Taiwan citizenship checkbox")
        res = page.evaluate('''() => {
            for (const lbl of document.querySelectorAll("label")) {
                if ((lbl.innerText||lbl.textContent||"").trim() === "Taiwan") {
                    const inp = lbl.htmlFor ? document.getElementById(lbl.htmlFor) : lbl.querySelector("input");
                    if (inp && inp.type === "checkbox") {
                        if (!inp.checked) inp.click();
                        return {id: inp.id, checked: inp.checked};
                    }
                }
            }
            return {notFound: true};
        }''')
        print(f"  Taiwan: {res}")
        ss(page, "05_citizenship.png")

        # === 8. POST-CITIZENSHIP / EXPORT ===
        print("\n[8] Post-citizenship / export")
        select_field(page, "question_36848905002", "No")  # Another citizenship?

        # Export: Taiwan
        try: page.locator("#question_36848906002").scroll_into_view_if_needed(); pause(0.5)
        except: pass
        r906 = open_react_select(page, "question_36848906002")
        texts906, opts906 = get_all_options(page, timeout=3000)
        if not texts906:
            page.keyboard.type("Taiwan"); page.wait_for_timeout(1000)
            texts906, opts906 = get_all_options(page)
        print(f"  q906 options: {texts906}")
        exported = False
        for i, t in enumerate(texts906):
            if "taiwan" in t.lower():
                opts906.nth(i).click(); pause(0.3)
                print(f"  Export: {t!r}"); exported = True; break
        if not exported:
            page.keyboard.press("Escape")
            print("  Export: Taiwan not found")

        # === 9. SALARY + FUTURE OPPS ===
        print("\n[9] Salary / future opps")
        page.locator("#question_36848907002").fill("100000"); pause()
        select_field(page, "question_36848908002", "Yes")

        ss(page, "06_extra.png")

        # === 10. EEO ===
        print("\n[10] EEO")
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
                const inp = document.getElementById(id);
                if (!inp) return null;
                let el = inp;
                for (let i=0;i<10;i++) {
                    el=el.parentElement; if(!el) break;
                    const sv=el.querySelector(".select__single-value");
                    if(sv) return (sv.innerText||"").trim();
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
                familiar: getSV("question_36848894002"),
                twitch_emp: getSV("question_36848895002"),
                relocation: getSV("question_36848896002"),
                amz_emp: getSV("question_36848897002"),
                amz_applied: getSV("question_36848898002"),
                amz_employed: getSV("question_36848899002"),
                noncompete: getSV("question_36848900002"),
                legal: getSV("question_36848901002"),
                sponsor: getSV("question_36848902002"),
                h1b: getSV("question_36848903002"),
                other_citizen: getSV("question_36848905002"),
                export_country: getSV("question_36848906002"),
                future_opps: getSV("question_36848908002"),
                gender: getSV("gender"),
                hispanic: getSV("hispanic_ethnicity"),
                race: getSV("race"),
                veteran: getSV("veteran_status"),
                disability: getSV("disability_status"),
                taiwan_checked: document.querySelectorAll("input[name='question_36848904002[]']:checked").length,
                iti_country: document.querySelector(".iti__selected-dial-code,.iti__dial-code")?.innerText||"",
            };
        }''')
        for k, v in rb.items():
            print(f"  {'OK' if v else '??'} {k}: {repr(v)}")

        # Screenshots before submit
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
            try: page.locator('button[type="submit"]').first.click(); submitted = True
            except: pass

        page.wait_for_timeout(12000)
        ss(page, "09_after_submit.png")

        body = page.inner_text("body")
        final_url = page.url
        final_title = page.title()
        print(f"\nURL: {final_url}")
        print(f"Title: {final_title.encode('ascii','replace').decode('ascii')}")
        print(f"Body[:500]:\n{body[:500].encode('ascii','replace').decode('ascii')}")

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
                "screenshot_confirmation": str(OUT_DIR / "09_after_submit.png"),
                "notes": "Final run - ITI country fix"
            }, f, indent=2, ensure_ascii=False)
        print(f"\nWrote SUBMITTED.json: {status}")
        time.sleep(20)
        ctx.close()
        return status

if __name__ == "__main__":
    r = main()
    print(f"\n=== RESULT: {r} ===")
