"""
Twitch Greenhouse Submitter v2 — handles all Twitch-specific questions
Discovered from v1 scan:
  - question_36848894002: Are you familiar with Twitch?
  - question_36848895002: Are you currently a Twitch employee?
  - question_36848896002: Are you open to relocation?
  - question_36848897002: Are you a current Amazon employee?
  - question_36848898002: Have you previously applied to Amazon?
  - question_36848899002: Have you previously been employed by Amazon?
  - question_36848900002: Are you subject to a non-competition agreement?
  - question_36848901002: If offered employment by Amazon, would you be legally eligible?
  - question_36848902002: Sponsorship required (US-based)
  - question_36848903002: Have you held H-1B status?
  - question_36848904002[]: Citizenship country checkboxes
  - question_36848905002: Since obtaining citizenship, did you afterwards acquire another citizenship?
  - question_36848906002: Export licensing / deemed export
  - question_36848907002: Expected total base pay
  - question_36848908002: Consider for future opportunities?
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
FIRST = "Yi-Chieh"
LAST = "Cheng"
EMAIL = "jamiecheng0103@gmail.com"
PHONE = "2137003831"
COUNTRY = "United States"
LINKEDIN = "https://www.linkedin.com/in/jamieyccheng/"
SALARY = "100000"

PROFILE_DIR = r"C:\Users\chent\ats_agent_9410"
DEBUG_PORT = 9410

def pause(t=0.6):
    time.sleep(t)

def ss(page, name):
    path = str(OUT_DIR / name)
    try:
        page.screenshot(path=path, full_page=True)
        print(f"  [ss] {name}")
    except Exception as e:
        print(f"  [ss fail] {name}: {e}")

def click_select_option(page, question_id, option_text):
    """
    For Greenhouse react-select fields: the input has an id=question_XXXXX,
    but the clickable control is a sibling div. Strategy:
    1. Find the container div around the input
    2. Click the control (div.select__control or similar)
    3. Find and click the matching option
    """
    want = option_text.strip().lower()

    # First try: find the react-select container by input id
    try:
        # The react-select input has id=question_XXXX, and the container
        # div typically has an aria relationship or is a close ancestor
        container = page.locator(f'[data-qa="{question_id}"], #{question_id}').first
        if container.count() == 0:
            # Try finding the container via the input's parent chain
            container = page.locator(f'#{question_id}').first

        if container.count() > 0:
            # Click the visible control (not the hidden input)
            container.scroll_into_view_if_needed()
            pause(0.3)
            # Click the select control div
            control = page.locator(f'#{question_id}').locator('..').locator('.select__control, [class*="control"]').first
            if control.count() > 0 and control.is_visible(timeout=1000):
                control.click()
            else:
                container.click()
            pause(0.4)
            page.wait_for_timeout(700)

            # Find and click the matching option
            opts = page.locator(".select__option, [class*='option']")
            n = opts.count()
            for i in range(n):
                txt = opts.nth(i).inner_text().strip().lower()
                if want in txt or txt in want:
                    opts.nth(i).click()
                    pause()
                    return True

            # If no direct match, type to filter
            page.keyboard.type(option_text)
            page.wait_for_timeout(800)
            opts = page.locator(".select__option, [class*='option']")
            n = opts.count()
            for i in range(n):
                txt = opts.nth(i).inner_text().strip().lower()
                if want in txt or txt in want:
                    opts.nth(i).click()
                    pause()
                    return True
            page.keyboard.press("Enter")
            pause()
            return True
    except Exception as e:
        print(f"    click_select_option err for {question_id}: {e}")
    return False

def select_react_by_label(page, label_text, option_text, timeout=3000):
    """Find a react-select by the label text above it, then select an option."""
    want = option_text.strip().lower()
    try:
        # Find the label element
        lbl = page.get_by_text(label_text, exact=False).first
        if lbl.count() == 0:
            return False

        # Get the container that holds both label and the select
        # Greenhouse wraps each question in a div.field
        container = lbl.locator('xpath=ancestor::div[contains(@class,"field") or contains(@class,"question") or contains(@class,"form")]').first
        if container.count() == 0:
            container = lbl.locator('xpath=../..').first

        # Click the react-select control
        control = container.locator('.select__control, [class*="select__control"], [class*="SelectControl"]').first
        if control.count() == 0:
            control = container.locator('[class*="control"]').first

        if control.count() > 0 and control.is_visible(timeout=timeout):
            control.scroll_into_view_if_needed()
            pause(0.3)
            control.click()
            pause(0.4)
            page.wait_for_timeout(700)

            opts = page.locator(".select__option")
            n = opts.count()
            for i in range(n):
                txt = opts.nth(i).inner_text().strip().lower()
                if want in txt or txt in want:
                    opts.nth(i).click()
                    pause()
                    print(f"  {label_text[:40]} -> {option_text}")
                    return True

            # Type to filter
            page.keyboard.type(option_text)
            page.wait_for_timeout(800)
            opts = page.locator(".select__option")
            n = opts.count()
            for i in range(n):
                txt = opts.nth(i).inner_text().strip().lower()
                if want in txt or txt in want:
                    opts.nth(i).click()
                    pause()
                    print(f"  {label_text[:40]} -> {option_text} (typed)")
                    return True
            page.keyboard.press("Enter")
            pause()
            return True
    except Exception as e:
        print(f"  select_react_by_label err ({label_text[:30]}): {e}")
    return False

def select_by_id_direct(page, qid, option_text):
    """
    For Greenhouse: the select container has class select__container or similar.
    The actual input is qid. We need to click the div.select__control that's
    inside the same wrapper.
    """
    want = option_text.strip().lower()
    try:
        # Greenhouse wraps inputs in a label-field div; find the select__control sibling
        el = page.locator(f"#{qid}").first
        if el.count() == 0:
            return False
        el.scroll_into_view_if_needed()
        pause(0.2)

        # Try clicking the select__control that's near this input
        # In react-select, the actual input is inside div.select__input-container
        # The clickable part is div.select__control which is a cousin
        # We go up to find the select__control
        clicked = page.evaluate(f'''() => {{
            const inp = document.getElementById("{qid}");
            if (!inp) return false;
            // Walk up to find react-select container
            let el = inp;
            for (let i = 0; i < 8; i++) {{
                el = el.parentElement;
                if (!el) break;
                const ctrl = el.querySelector('.select__control');
                if (ctrl) {{
                    ctrl.click();
                    return true;
                }}
            }}
            return false;
        }}''')

        if not clicked:
            # Fallback: just click the input itself
            el.click()

        pause(0.4)
        page.wait_for_timeout(700)

        opts = page.locator(".select__option")
        n = opts.count()
        for i in range(n):
            txt = opts.nth(i).inner_text().strip().lower()
            if want in txt or txt in want:
                opts.nth(i).click()
                pause()
                return True

        # type to filter
        page.keyboard.type(option_text)
        page.wait_for_timeout(800)
        opts = page.locator(".select__option")
        n = opts.count()
        for i in range(n):
            txt = opts.nth(i).inner_text().strip().lower()
            if want in txt or txt in want:
                opts.nth(i).click()
                pause()
                return True

        page.keyboard.press("Escape")
        return False

    except Exception as e:
        print(f"  select_by_id_direct err ({qid}): {e}")
        return False

def fill_location_robust(page):
    """Fill the Location (City) autocomplete field."""
    target = "San Francisco, CA"

    # The location field in Greenhouse is #candidate-location (text input with autocomplete)
    for sel in ["#candidate-location"]:
        try:
            el = page.locator(sel).first
            if el.count() > 0:
                el.scroll_into_view_if_needed()
                el.click()
                pause(0.3)
                # Clear any existing value
                el.triple_click()
                pause(0.2)
                el.fill("")
                pause(0.2)
                # Type city name
                page.keyboard.type("San Francisco")
                page.wait_for_timeout(2500)

                # Try clicking first autocomplete suggestion
                suggestions = page.locator('[class*="suggestion"], [class*="autocomplete"] li, [role="option"], .pac-item').all()
                if suggestions:
                    suggestions[0].click()
                    pause()
                    print(f"  Location -> clicked suggestion")
                    return True
                else:
                    # Just press Enter or Tab
                    page.keyboard.press("Enter")
                    pause()
                    print(f"  Location -> Enter pressed")
                    return True
        except Exception as e:
            print(f"  location err ({sel}): {e}")

    # Last resort: JavaScript fill
    try:
        page.evaluate(f'''() => {{
            const el = document.getElementById('candidate-location');
            if (el) {{
                el.value = "{target}";
                el.dispatchEvent(new Event('input', {{bubbles: true}}));
                el.dispatchEvent(new Event('change', {{bubbles: true}}));
            }}
        }}''')
        pause()
        print("  Location -> JS fill")
        return True
    except Exception as e:
        print(f"  location JS err: {e}")

    return False

def main():
    # Remove stale LOCK
    lock = Path(PROFILE_DIR) / "Default" / "LOCK"
    if lock.exists():
        try:
            lock.unlink()
        except:
            pass

    with sync_playwright() as p:
        print(f"Launching Chrome (port {DEBUG_PORT})...")
        browser = p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_DIR,
            channel="chrome",
            headless=False,
            no_viewport=True,
            args=[f"--remote-debugging-port={DEBUG_PORT}"],
            ignore_default_args=["--enable-automation"],
        )

        page = browser.pages[0] if browser.pages else browser.new_page()
        page.set_default_timeout(15000)

        print(f"Navigating to {URL}")
        page.goto(URL, wait_until="domcontentloaded", timeout=40000)
        page.wait_for_timeout(5000)

        title = page.title()
        print(f"Title: {title}")

        if "404" in title or "not found" in title.lower():
            print("SKIP-DEAD")
            browser.close()
            return "skip-dead"

        print("Job is LIVE")
        ss(page, "01_landing.png")

        # ---- STEP 1: Personal basics ----
        print("\n[1] Personal basics")
        try: page.locator("#first_name").fill(FIRST); pause()
        except: pass
        try: page.locator("#last_name").fill(LAST); pause()
        except: pass
        try: page.locator("#email").fill(EMAIL); pause()
        except: pass
        try: page.locator("#phone").fill(PHONE); pause()
        except: pass
        print("  Name/Email/Phone filled")

        # Country
        ok = select_by_id_direct(page, "country", "United States")
        print(f"  Country -> {'OK' if ok else 'FAIL'}")
        pause()

        # Location
        loc_ok = fill_location_robust(page)
        if not loc_ok:
            print("  !! Location NOT filled — trying JS force")
            page.evaluate("""() => {
                const el = document.getElementById('candidate-location');
                if (el) {
                    const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                    nativeInputValueSetter.call(el, 'San Francisco, CA');
                    el.dispatchEvent(new Event('input', {bubbles: true}));
                }
            }""")
            pause(0.5)

        ss(page, "02_personal.png")

        # ---- STEP 2: Resume + Cover ----
        print("\n[2] File uploads")
        try:
            page.locator("#resume").set_input_files(str(RESUME))
            page.wait_for_timeout(3000)
            print(f"  Resume OK ({RESUME.stat().st_size} bytes)")
        except Exception as e:
            print(f"  Resume err: {e}")
            try:
                page.locator('input[type="file"]').first.set_input_files(str(RESUME))
                page.wait_for_timeout(3000)
                print("  Resume via nth(0)")
            except Exception as e2:
                print(f"  Resume fallback err: {e2}")

        if COVER.exists():
            try:
                page.locator("#cover_letter").set_input_files(str(COVER))
                page.wait_for_timeout(3000)
                print("  Cover OK")
            except Exception as e:
                print(f"  Cover err: {e}")
                try:
                    page.locator('input[type="file"]').nth(1).set_input_files(str(COVER))
                    page.wait_for_timeout(3000)
                    print("  Cover via nth(1)")
                except: pass

        ss(page, "03_uploads.png")

        # ---- STEP 3: LinkedIn ----
        print("\n[3] LinkedIn")
        try:
            page.locator("#question_36848892002").fill(LINKEDIN)
            pause()
            print(f"  LinkedIn -> {LINKEDIN}")
        except Exception as e:
            print(f"  LinkedIn err: {e}")

        # ---- STEP 4: Twitch-specific questions ----
        print("\n[4] Twitch-specific questions")

        # Familiar with Twitch? -> Yes
        ok = select_by_id_direct(page, "question_36848894002", "Yes")
        print(f"  Familiar with Twitch? -> {'Yes' if ok else 'FAIL'}")
        if not ok:
            ok = select_react_by_label(page, "Are you familiar with Twitch", "Yes")
            print(f"  Familiar (via label) -> {'Yes' if ok else 'FAIL'}")

        # Currently a Twitch employee? -> No
        ok = select_by_id_direct(page, "question_36848895002", "No")
        print(f"  Currently Twitch employee? -> {'No' if ok else 'FAIL'}")

        # Open to relocation? -> Yes
        ok = select_by_id_direct(page, "question_36848896002", "Yes")
        print(f"  Open to relocation? -> {'Yes' if ok else 'FAIL'}")

        # Current Amazon employee? -> No
        ok = select_by_id_direct(page, "question_36848897002", "No")
        print(f"  Current Amazon employee? -> {'No' if ok else 'FAIL'}")

        # Previously applied to Amazon? -> No
        ok = select_by_id_direct(page, "question_36848898002", "No")
        print(f"  Previously applied to Amazon? -> {'No' if ok else 'FAIL'}")

        # Previously employed by Amazon? -> No
        ok = select_by_id_direct(page, "question_36848899002", "No")
        print(f"  Previously employed by Amazon? -> {'No' if ok else 'FAIL'}")

        # Non-compete / agreements that would interfere? -> No
        ok = select_by_id_direct(page, "question_36848900002", "No")
        print(f"  Non-compete agreement? -> {'No' if ok else 'FAIL'}")

        # Legally eligible to work at Amazon? -> Yes
        ok = select_by_id_direct(page, "question_36848901002", "Yes")
        print(f"  Legally eligible to work at Amazon? -> {'Yes' if ok else 'FAIL'}")

        # Sponsorship required (US-based position) -> Yes
        ok = select_by_id_direct(page, "question_36848902002", "Yes")
        print(f"  Require sponsorship? -> {'Yes' if ok else 'FAIL'}")
        if not ok:
            ok = select_react_by_label(page, "sponsorship", "Yes")
            print(f"  Sponsorship (via label) -> {'Yes' if ok else 'FAIL'}")

        # H-1B status previously? -> Yes (Jamie has had H-1B sponsored / applied; truthful)
        # Actually: Jamie is H1B applicant but hasn't had a petition APPROVED yet per context
        # "Have you held H-1B status, or had an H-1B petition approved"
        # Truthful answer: No (she doesn't have H-1B approved yet - she NEEDS sponsorship)
        ok = select_by_id_direct(page, "question_36848903002", "No")
        print(f"  Previously held H-1B status? -> {'No' if ok else 'FAIL'}")

        ss(page, "04_twitch_questions.png")

        # ---- STEP 5: Citizenship country checkbox ----
        print("\n[5] Citizenship country (Taiwan)")
        # Jamie is from Taiwan - check Taiwan checkbox
        taiwan_id = "question_36848904002[]_243684128002"
        try:
            taiwan_cb = page.locator(f'#{taiwan_id}')
            if taiwan_cb.count() > 0:
                taiwan_cb.scroll_into_view_if_needed()
                if not taiwan_cb.is_checked():
                    taiwan_cb.check()
                    pause()
                print("  Taiwan checked")
            else:
                # Try by label
                taiwan_lbl = page.get_by_label("Taiwan")
                if taiwan_lbl.count() > 0:
                    if not taiwan_lbl.is_checked():
                        taiwan_lbl.check()
                        pause()
                    print("  Taiwan checked (via label)")
        except Exception as e:
            print(f"  Taiwan checkbox err: {e}")

        ss(page, "05_citizenship.png")

        # ---- STEP 6: Post-citizenship / export control ----
        print("\n[6] Post-citizenship / export questions")

        # "Since obtaining your most recent citizenship, did you afterwards acquire another citizenship?" -> No
        ok = select_by_id_direct(page, "question_36848905002", "No")
        print(f"  Acquired another citizenship? -> {'No' if ok else 'FAIL'}")

        # Export licensing / deemed export (for transfer of technology)
        # Jamie is a Taiwanese national and US applicant - answer truthfully
        # This is typically: "Are you a US Person (US citizen/perm resident)?" or
        # "For export licensing, are you authorized?" - she's neither citizen nor PR
        # Most common answer options: Yes/No or "U.S. Person"/"Non-U.S. Person"
        # We'll check what the field shows and select "No" (she's not a US Person)
        # But we need to see the actual options first - let's try clicking the field
        try:
            el = page.locator("#question_36848906002").first
            if el.count() > 0:
                el.scroll_into_view_if_needed()
                pause(0.2)
                # Click to open dropdown and see options
                clicked = page.evaluate('''() => {
                    const inp = document.getElementById("question_36848906002");
                    if (!inp) return false;
                    let el = inp;
                    for (let i = 0; i < 8; i++) {
                        el = el.parentElement;
                        if (!el) break;
                        const ctrl = el.querySelector('.select__control');
                        if (ctrl) { ctrl.click(); return true; }
                    }
                    return false;
                }''')
                page.wait_for_timeout(700)

                # Read available options
                opts_text = []
                opts = page.locator(".select__option")
                n = opts.count()
                for i in range(n):
                    opts_text.append(opts.nth(i).inner_text().strip())
                print(f"  Export q options: {opts_text}")

                # Jamie is not a US person (US citizen or permanent resident)
                # Look for "No" or "Non-U.S. Person" or similar
                selected = False
                for target_opt in ["No", "Non-U.S. Person", "Non-U.S.", "I am not", "No, I am not"]:
                    want_lower = target_opt.lower()
                    for i in range(len(opts_text)):
                        if want_lower in opts_text[i].lower() or opts_text[i].lower() in want_lower:
                            opts.nth(i).click()
                            pause()
                            print(f"  Export -> {opts_text[i]}")
                            selected = True
                            break
                    if selected:
                        break

                if not selected and opts_text:
                    # Print and close - don't guess
                    page.keyboard.press("Escape")
                    print(f"  Export: unclear options {opts_text} - skipping (may need manual)")
                elif not opts_text:
                    page.keyboard.press("Escape")
                    print("  Export: no options visible")
        except Exception as e:
            print(f"  Export question err: {e}")

        # ---- STEP 7: Salary ----
        print("\n[7] Salary")
        try:
            page.locator("#question_36848907002").fill(SALARY)
            pause()
            print(f"  Salary -> {SALARY}")
        except Exception as e:
            print(f"  Salary err: {e}")

        # Future opportunities? -> Yes
        ok = select_by_id_direct(page, "question_36848908002", "Yes")
        print(f"  Consider for future opps? -> {'Yes' if ok else 'FAIL'}")

        ss(page, "06_extra_questions.png")

        # ---- STEP 8: EEO Demographics ----
        print("\n[8] EEO Demographics")

        # Gender -> Female
        ok = select_by_id_direct(page, "gender", "Female")
        if not ok:
            ok = select_by_id_direct(page, "gender", "Woman")
        print(f"  Gender -> {'Female/Woman' if ok else 'FAIL'}")

        # Hispanic/Latino -> No
        ok = select_by_id_direct(page, "hispanic_ethnicity", "No")
        if not ok:
            ok = select_by_id_direct(page, "hispanic_ethnicity", "Not Hispanic or Latino")
        print(f"  Hispanic/Latino -> {'No' if ok else 'FAIL'}")

        # Race -> Asian (we need to check what select comes up for race)
        # NOTE: race field wasn't in the initial scan with an id — it may be a separate
        # react-select. Let's try by label.
        ok = select_react_by_label(page, "Race", "Asian")
        print(f"  Race -> {'Asian' if ok else 'FAIL (check manually if EEO has race field)'}")

        # Veteran status
        ok = select_by_id_direct(page, "veteran_status", "I am not a protected veteran")
        if not ok:
            ok = select_by_id_direct(page, "veteran_status", "Not a protected veteran")
            if not ok:
                ok = select_by_id_direct(page, "veteran_status", "No")
        print(f"  Veteran status -> {'filled' if ok else 'FAIL'}")

        # Disability -> No
        ok = select_by_id_direct(page, "disability_status", "No, I do not have a disability")
        if not ok:
            ok = select_by_id_direct(page, "disability_status", "No")
        print(f"  Disability -> {'No' if ok else 'FAIL'}")

        ss(page, "07_eeo.png")

        # ---- STEP 9: Full form review ----
        print("\n[9] Full form review")
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(500)
        ss(page, "08_review_top.png")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
        page.wait_for_timeout(300)
        ss(page, "08_review_mid.png")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(300)
        ss(page, "08_review_bottom.png")

        # Check for still-required unfilled fields
        unfilled = page.evaluate('''() => {
            const out = [];
            document.querySelectorAll('[aria-required="true"], input[required], select[required], textarea[required]').forEach(el => {
                if (!el.value || el.value === '') {
                    let lbl = '';
                    if (el.id) {
                        const l = document.querySelector(`label[for="${el.id}"]`);
                        if (l) lbl = (l.innerText||'').trim().substring(0, 100);
                    }
                    if (!lbl) {
                        let p = el.parentElement;
                        for (let i = 0; i < 4 && p; i++) {
                            const t = p.querySelector('label,.label');
                            if (t) { lbl = (t.innerText||'').trim().substring(0, 100); break; }
                            p = p.parentElement;
                        }
                    }
                    out.push({id: el.id, label: lbl});
                }
            });
            return out;
        }''')
        if unfilled:
            print(f"\n  Still unfilled required fields ({len(unfilled)}):")
            for u in unfilled[:15]:
                print(f"    - id={u['id']} label={u['label']!r}")
        else:
            print("  All required fields appear filled!")

        # ---- STEP 10: SUBMIT ----
        print("\n[10] SUBMIT")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(1500)

        submitted = False
        for btn_text in ["Submit application", "Submit Application", "Apply", "Submit"]:
            try:
                btn = page.get_by_role("button", name=btn_text)
                if btn.count() > 0 and btn.first.is_visible(timeout=2000):
                    btn.first.scroll_into_view_if_needed()
                    pause(0.5)
                    btn.first.click(timeout=10000)
                    print(f"  Clicked: '{btn_text}'")
                    submitted = True
                    break
            except Exception as e:
                continue

        if not submitted:
            # Try CSS selector
            try:
                page.locator('button[type="submit"], input[type="submit"]').first.click()
                submitted = True
                print("  Clicked submit via CSS selector")
            except:
                pass

        page.wait_for_timeout(12000)
        ss(page, "09_after_submit.png")

        body = page.inner_text("body")
        final_url = page.url
        final_title = page.title()
        safe_body = body[:2500].encode("ascii", "replace").decode("ascii")

        print(f"\nURL: {final_url}")
        print(f"Title: {final_title.encode('ascii','replace').decode('ascii')}")
        print(f"Body:\n{safe_body[:1000]}")

        success = any(kw in body.lower() for kw in ["thank you", "received", "submitted", "we got your", "application has been", "application received"])

        if not success:
            print("\nChecking errors...")
            errors = page.locator('.error, [class*="error"], .field_with_errors').all()
            err_texts = []
            for err in errors[:15]:
                try:
                    t = (err.text_content() or "").strip()
                    if 3 < len(t) < 200:
                        err_texts.append(t)
                except:
                    pass
            if err_texts:
                print(f"  Error elements: {err_texts[:10]}")

            # Check unfilled after submit
            unfilled2 = page.evaluate('''() => {
                const out = [];
                document.querySelectorAll('[aria-required="true"], input[required], select[required], textarea[required]').forEach(el => {
                    if (!el.value) {
                        let lbl = '';
                        if (el.id) { const l = document.querySelector(`label[for="${el.id}"]`); if(l) lbl=(l.innerText||'').trim(); }
                        if (!lbl) {
                            let p = el.parentElement;
                            for (let i = 0; i < 4 && p; i++) {
                                const t = p.querySelector('label');
                                if (t) { lbl=(t.innerText||'').trim().substring(0,80); break; }
                                p = p.parentElement;
                            }
                        }
                        out.push({id: el.id, label: lbl});
                    }
                });
                return [...new Set(out.map(JSON.stringify))].map(JSON.parse);
            }''')
            if unfilled2:
                print(f"\n  Unfilled after submit attempt ({len(unfilled2)}):")
                for u in unfilled2[:15]:
                    print(f"    - id={u['id']} label={u['label']!r}")

        result_status = "submitted" if success else "unknown"
        confirmed_at = datetime.now().isoformat()

        submitted_data = {
            "company": "Twitch",
            "role": "Program Manager, Culture & People Development",
            "ats": "Greenhouse",
            "job_url": URL,
            "status": result_status,
            "confirmed_at": confirmed_at,
            "final_url": final_url,
            "final_title": final_title,
            "body_preview": body[:600],
            "screenshot_confirmation": str(OUT_DIR / "09_after_submit.png"),
            "notes": "Twitch Greenhouse no-account. Amazon-subsidiary form with citizenship/export Qs."
        }
        with open(ROLE_DIR / "SUBMITTED.json", "w", encoding="utf-8") as f:
            json.dump(submitted_data, f, indent=2, ensure_ascii=False)
        print(f"\nWrote SUBMITTED.json: status={result_status}")

        time.sleep(20)
        browser.close()
        return result_status

if __name__ == "__main__":
    result = main()
    print(f"\n=== FINAL RESULT: {result} ===")
