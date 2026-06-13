"""
Twitch Greenhouse Submitter FINAL2
Critical fixes:
1. ITI country: click #phone FIRST to make flag visible, then click flag -> search US
2. q894 / q896: These fields are off-screen on page load. Need to:
   - Scroll the PAGE to the field
   - Use page.scroll_to_element() or viewport scroll
   - Wait for the element to be in viewport
   - Then open/select
3. Location: after listbox click, check if value was set; if not, use JS to get the place name
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

def get_options(page, timeout=4000):
    try: page.wait_for_selector(".select__option", timeout=timeout, state="visible"); time.sleep(0.15)
    except: pass
    opts = page.locator(".select__option")
    n = opts.count()
    texts = [opts.nth(i).inner_text().strip() for i in range(n) if True]
    return texts, opts

def open_rs(page, input_id):
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

def select_field(page, input_id, want_text, retry_types=None):
    want = want_text.strip().lower()

    # Scroll to element via JS
    page.evaluate(f'''() => {{
        const el = document.getElementById("{input_id}");
        if (el) el.scrollIntoView({{block: "center"}});
    }}''')
    time.sleep(0.4)

    r = open_rs(page, input_id)
    texts, opts = get_options(page)

    if not texts:
        # Type to filter
        if retry_types:
            page.keyboard.type(retry_types[0])
        else:
            page.keyboard.type(want_text)
        time.sleep(0.8)
        texts, opts = get_options(page)
        if not texts:
            page.keyboard.press("Escape")
            print(f"  {input_id}: NO OPTIONS (tried typing)")
            return False, None

    # For "Yes" — pick shortest non-partner option
    best_idx = None
    if want == "yes":
        yes_opts = [(i, t) for i, t in enumerate(texts) if "yes" in t.lower()]
        if yes_opts:
            # Sort by length and prefer non-partner/affiliate
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
        for i, t in enumerate(texts):
            if any(w in t.lower() for w in want.split()): best_idx = i; break

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
        for (let i=0;i<10;i++) {{
            el = el.parentElement; if(!el) break;
            const sv = el.querySelector(".select__single-value");
            if(sv) return (sv.innerText||"").trim();
        }}
        return null;
    }}''')
    print(f"  {input_id}: {chosen!r} [{sv!r}]")
    return True, chosen

def set_iti_country_us(page):
    """Set ITI phone country to United States by scrolling to phone and clicking flag."""
    try:
        # Scroll to phone section
        page.evaluate('''() => {
            const el = document.getElementById("phone");
            if (el) el.scrollIntoView({block: "center"});
        }''')
        time.sleep(0.5)

        # Click the phone field to make ITI interactive
        page.locator("#phone").click(); pause(0.3)

        # Now try to click the flag button
        flag_selectors = [
            ".iti__selected-flag",
            ".iti__flag-container",
            "[class*='iti__selected-flag']",
            ".iti button",
        ]
        clicked = False
        for sel in flag_selectors:
            try:
                flag = page.locator(sel).first
                if flag.count() > 0:
                    # Try clicking even if not visible (may be behind another element)
                    page.evaluate(f'''() => {{
                        const el = document.querySelector("{sel}");
                        if (el) el.click();
                    }}''')
                    time.sleep(0.6)
                    # Check if dropdown opened
                    search = page.locator("#iti-0__search-input")
                    if search.count() > 0 and search.is_visible(timeout=1000):
                        clicked = True
                        print(f"  ITI opened via {sel!r}")
                        break
            except: continue

        if not clicked:
            print("  ITI: couldn't open flag dropdown")
            return False

        # Type to filter
        search = page.locator("#iti-0__search-input")
        search.fill("United States"); pause(0.4)
        page.wait_for_timeout(600)

        # Find and click United States (not US territories)
        items = page.locator(".iti__country")
        n = items.count()
        print(f"  ITI items: {n}")
        for i in range(n):
            try:
                txt = items.nth(i).inner_text().strip()
                if "united states" in txt.lower() and "territories" not in txt.lower() and "island" not in txt.lower() and "samoa" not in txt.lower():
                    items.nth(i).click(); pause(0.3)
                    print(f"  ITI: {txt!r}")
                    return True
            except: continue

        # Fallback: press Enter
        page.keyboard.press("Enter"); pause(0.3)
        print("  ITI: Enter pressed")
        return True

    except Exception as e:
        print(f"  ITI err: {e}")
        return False

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

        # === 2. PHONE + ITI COUNTRY ===
        print("\n[2] Phone + ITI country")
        ok = set_iti_country_us(page)
        print(f"  ITI US: {'OK' if ok else 'FAIL'}")

        # Fill phone after setting country
        try:
            phone_el = page.locator("#phone")
            phone_el.click(); pause(0.2)
            phone_el.fill("2137003831"); pause()
            print("  Phone: filled")
        except Exception as e:
            print(f"  Phone err: {e}")

        # Verify ITI country
        iti_check = page.evaluate('''() => {
            const flag = document.querySelector(".iti__selected-flag, .iti__selected-dial-code");
            const dialCode = document.querySelector(".iti__selected-dial-code,.iti__dial-code");
            return {
                flagClass: flag?.className?.substring(0,60),
                dialCode: dialCode?.innerText||"",
                ariaLabel: flag?.getAttribute("aria-label")||""
            };
        }''')
        print(f"  ITI check: {iti_check}")

        # === 3. LOCATION ===
        print("\n[3] Location")
        loc_el = page.locator("#candidate-location").first
        page.evaluate("() => { const el=document.getElementById('candidate-location'); if(el)el.scrollIntoView({block:'center'}); }")
        time.sleep(0.3)
        loc_el.click(); pause(0.3)
        loc_el.fill(""); pause(0.2)
        page.keyboard.type("San Francisco, CA")
        page.wait_for_timeout(3500)

        # Try to find PAC/listbox suggestions
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
            # Just Tab out
            page.keyboard.press("Tab"); pause(0.3)
            print("  Location: Tab (no autocomplete found)")

        # Check actual value
        loc_val = loc_el.input_value() if loc_el.count() > 0 else ""
        print(f"  Location value: {loc_val!r}")
        if not loc_val:
            # Force set via JS React-compatible approach
            # This Greenhouse form uses React controlled inputs - set via nativeInputValueSetter
            set_result = page.evaluate('''() => {
                const el = document.getElementById("candidate-location");
                if (!el) return "no-el";
                const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
                nativeSetter.call(el, "San Francisco, CA");
                el.dispatchEvent(new Event("input", {bubbles: true}));
                el.dispatchEvent(new Event("change", {bubbles: true}));
                return el.value;
            }''')
            print(f"  Location JS force: {set_result!r}")

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

        # === 6. TWITCH/AMAZON QUESTIONS ===
        print("\n[6] Twitch/Amazon questions")

        # q894 - Familiar with Twitch?
        # Scroll to this field specifically
        page.evaluate("() => { const e=document.getElementById('question_36848894002'); if(e)e.scrollIntoView({block:'center'}); }")
        time.sleep(0.6)
        r = open_rs(page, "question_36848894002")
        texts894, opts894 = get_options(page, timeout=5000)
        print(f"  q894 options: {texts894}")
        if texts894:
            best894 = None
            for t in sorted(texts894, key=len):
                if "yes" in t.lower() and "partner" not in t.lower() and "affiliate" not in t.lower():
                    best894 = t; break
            if best894 is None:
                for t in sorted(texts894, key=len):
                    if "yes" in t.lower(): best894 = t; break
            if best894:
                for i, t in enumerate(texts894):
                    if t == best894: opts894.nth(i).click(); pause(0.3); print(f"  q894: {best894!r}"); break
            else:
                page.keyboard.press("Escape")
        else:
            # Try scrolling more and retry
            page.evaluate("() => window.scrollTo(0, 600)")
            time.sleep(0.5)
            r = open_rs(page, "question_36848894002")
            texts894b, opts894b = get_options(page, timeout=3000)
            print(f"  q894 retry options: {texts894b}")
            if texts894b:
                best894b = None
                for t in sorted(texts894b, key=len):
                    if "yes" in t.lower() and "partner" not in t.lower(): best894b = t; break
                if best894b:
                    for i, t in enumerate(texts894b):
                        if t == best894b: opts894b.nth(i).click(); pause(0.3); print(f"  q894: {best894b!r}"); break
                else:
                    page.keyboard.press("Escape")

        # q895 - Twitch employee?
        select_field(page, "question_36848895002", "No")

        # q896 - Relocation?
        page.evaluate("() => { const e=document.getElementById('question_36848896002'); if(e)e.scrollIntoView({block:'center'}); }")
        time.sleep(0.6)
        r = open_rs(page, "question_36848896002")
        texts896, opts896 = get_options(page, timeout=5000)
        print(f"  q896 options: {texts896}")
        if texts896:
            for i, t in enumerate(texts896):
                if "yes" in t.lower():
                    opts896.nth(i).click(); pause(0.3); print(f"  q896: {t!r}"); break
            else:
                page.keyboard.press("Escape"); print(f"  q896: no Yes in {texts896}")
        else:
            print("  q896: no options")

        # Amazon questions
        for qid, ans in [
            ("question_36848897002", "No"),
            ("question_36848898002", "No"),
            ("question_36848899002", "No"),
            ("question_36848900002", "No"),
            ("question_36848901002", "Yes"),
            ("question_36848902002", "Yes"),  # Sponsorship
            ("question_36848903002", "No"),   # H-1B
        ]:
            select_field(page, qid, ans)

        ss(page, "04_twitch_q.png")

        # === 7. TAIWAN ===
        print("\n[7] Taiwan citizenship")
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
        select_field(page, "question_36848905002", "No")

        # Export: Taiwan
        page.evaluate("() => { const e=document.getElementById('question_36848906002'); if(e)e.scrollIntoView({block:'center'}); }")
        time.sleep(0.4)
        open_rs(page, "question_36848906002")
        texts906, opts906 = get_options(page, timeout=3000)
        if not texts906:
            page.keyboard.type("Taiwan"); time.sleep(0.8)
            texts906, opts906 = get_options(page)
        print(f"  q906 options: {texts906}")
        for i, t in enumerate(texts906):
            if "taiwan" in t.lower():
                opts906.nth(i).click(); pause(0.3); print(f"  Export: {t!r}"); break
        else:
            if texts906:
                opts906.first.click(); pause(0.3)
            else:
                page.keyboard.press("Escape")

        # === 9. SALARY / FUTURE OPPS ===
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
                const inp = document.getElementById(id); if (!inp) return null;
                let el = inp;
                for (let i=0;i<10;i++) { el=el.parentElement; if(!el)break; const sv=el.querySelector(".select__single-value"); if(sv) return (sv.innerText||"").trim(); }
                return inp.value||null;
            };
            const g = id => document.getElementById(id)?.value||"";
            const dialCode = document.querySelector(".iti__selected-dial-code,.iti__dial-code")?.innerText||"";
            return {
                first_name: g("first_name"), last_name: g("last_name"), email: g("email"), phone: g("phone"),
                location: g("candidate-location"), linkedin: g("question_36848892002"), salary: g("question_36848907002"),
                familiar: getSV("question_36848894002"), twitch_emp: getSV("question_36848895002"),
                relocation: getSV("question_36848896002"), amz_emp: getSV("question_36848897002"),
                amz_applied: getSV("question_36848898002"), amz_employed: getSV("question_36848899002"),
                noncompete: getSV("question_36848900002"), legal: getSV("question_36848901002"),
                sponsor: getSV("question_36848902002"), h1b: getSV("question_36848903002"),
                other_citizen: getSV("question_36848905002"), export_country: getSV("question_36848906002"),
                future_opps: getSV("question_36848908002"), gender: getSV("gender"),
                hispanic: getSV("hispanic_ethnicity"), race: getSV("race"),
                veteran: getSV("veteran_status"), disability: getSV("disability_status"),
                taiwan_checked: document.querySelectorAll("input[name='question_36848904002[]']:checked").length,
                iti_dial: dialCode,
            };
        }''')
        for k, v in rb.items():
            print(f"  {'OK' if v else '??'} {k}: {repr(v)}")

        # Final screenshots
        page.evaluate("window.scrollTo(0,0)"); page.wait_for_timeout(300); ss(page, "08a_pre_top.png")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight/2)"); page.wait_for_timeout(200); ss(page, "08b_pre_mid.png")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)"); page.wait_for_timeout(200); ss(page, "08c_pre_bottom.png")

        # === SUBMIT ===
        print("\n[SUBMIT]")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)"); page.wait_for_timeout(1500)
        submitted = False
        for btn_text in ["Submit application", "Submit Application", "Apply", "Submit"]:
            try:
                btn = page.get_by_role("button", name=btn_text)
                if btn.count() > 0 and btn.first.is_visible(timeout=1500):
                    btn.first.scroll_into_view_if_needed(); pause(0.5)
                    btn.first.click(timeout=10000)
                    print(f"  Clicked: {btn_text!r}"); submitted = True; break
            except: continue

        page.wait_for_timeout(12000)
        ss(page, "09_after_submit.png")

        body = page.inner_text("body")
        final_url, final_title = page.url, page.title()
        print(f"\nURL: {final_url}")
        print(f"Title: {final_title.encode('ascii','replace').decode('ascii')}")
        print(f"Body[:400]:\n{body[:400].encode('ascii','replace').decode('ascii')}")

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
                "notes": "Final2 - ITI JS click + q894/896 scroll fix"
            }, f, indent=2, ensure_ascii=False)
        print(f"\nWrote SUBMITTED.json: {status}")
        time.sleep(20)
        ctx.close()
        return status

if __name__ == "__main__":
    r = main()
    print(f"\n=== RESULT: {r} ===")
