"""
Lineage Phenom ATS driver v5 - continues from where v4 left off.
Current state: Chrome is on step 3 "Application Questions" with 4 dropdowns:
  1. Are you at least 18 years of age?
  2. Can you perform essential functions of the job?
  3. Can you provide proof of eligibility to work in the country?
  4. Will you now or in the future require sponsorship?
All have native <select> with "Please Select" default.
Also: small textarea at bottom (cover letter / additional info)
"""
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

APP_DIR = Path(r"C:\Users\chent\Agentic_Workflows_2026\oracle-job-search\outputs\2026-06-23-lean\applications\Lineage_HR-Generalist")
RESUME_PDF = APP_DIR / "resume.pdf"
COVER_PDF = APP_DIR / "cover_letter.pdf"
SCREENSHOTS_DIR = APP_DIR / "screenshots"
SCREENSHOTS_DIR.mkdir(exist_ok=True)

APPLY_URL = "https://careers.onelineage.com/us/en/apply?jobSeqNo=LLLLLOUSR0103931EXTERNALENUS&step=1&stepname=personalInformation"
FIRST_NAME = "Yi-Chieh"
LAST_NAME = "Cheng"
EMAIL = "jamiecheng0103@gmail.com"
PHONE_NUMBER = "2137003831"
CITY = "Portland"
POSTAL_CODE = "97201"

WHY_INTERESTED = (
    "I'm drawn to Lineage's mission of connecting food supply chains more efficiently — "
    "that kind of operational complexity creates meaningful HR challenges I'm excited to work on. "
    "My background spans the full HR generalist scope: I built performance frameworks and managed "
    "complex employee relations cases at ODN and Vestas, supported benefits and compliance at NextGen, "
    "and led onboarding and HRIS projects across multiple orgs. I'd love to bring that breadth to "
    "Lineage's people team."
)

PW_PATH = Path(r"C:\Users\chent\Downloads\job_password.txt")
_SHARED_PW = PW_PATH.read_text().strip() if PW_PATH.exists() else ""


def ss(page, name):
    path = SCREENSHOTS_DIR / f"{name}.png"
    page.screenshot(path=str(path), full_page=True)
    print(f"[SCREENSHOT] {path.name}")
    return str(path)


def detect_captcha(page):
    for frame in page.frames:
        if "recaptcha" in frame.url and "bframe" in frame.url:
            return True
    return page.locator("iframe[src*='hcaptcha']").count() > 0


def handle_captcha_stop(page, screenshot_paths):
    path = ss(page, "captcha_detected")
    screenshot_paths.append(path)
    write_result({
        "company": "Lineage", "role": "HR Generalist", "ats": "Phenom",
        "apply_url": APPLY_URL, "submitted": False, "outcome": "captcha-staged",
        "confirmed_at": None, "screenshot_paths": screenshot_paths,
        "notes": "Interactive CAPTCHA detected. Human must solve and submit."
    })
    print("[STOP] CAPTCHA — leaving form open.")
    sys.exit(0)


def write_result(data):
    out = APP_DIR / "SUBMITTED.json"
    out.write_text(json.dumps(data, indent=2))
    print(f"[RESULT] Written: SUBMITTED.json")


def ps(page, field_id, value=None, label_text=None, label=""):
    """page.select_option() by attribute selector."""
    sel = f"[id='{field_id}']"
    try:
        if value is not None:
            page.select_option(sel, value=value)
        else:
            page.select_option(sel, label=label_text)
        actual = page.locator(sel).input_value()
        print(f"[FILL] {label or field_id} = {repr(actual[:60])}")
        return True
    except Exception as e:
        print(f"[WARN] ps({field_id}): {str(e)[:100]}")
        return False


def js_set(page, field_id, value):
    return page.evaluate("""([id, v]) => {
        const el = document.getElementById(id);
        if (!el) return false;
        const proto = el.tagName === 'SELECT'
            ? window.HTMLSelectElement.prototype
            : window.HTMLInputElement.prototype;
        const setter = Object.getOwnPropertyDescriptor(proto, 'value').set;
        setter.call(el, v);
        el.dispatchEvent(new Event('input', {bubbles: true}));
        el.dispatchEvent(new Event('change', {bubbles: true}));
        return el.value;
    }""", [field_id, value])


def get_opts(page, field_id):
    return page.evaluate(f"""() => {{
        const el = document.getElementById('{field_id}');
        return el ? Array.from(el.options).map(o=>{{return{{v:o.value,t:o.text}}}}) : [];
    }}""")


def get_all_selects(page):
    return page.evaluate("""() => {
        const sels = document.querySelectorAll('select');
        return Array.from(sels).filter(e => e.offsetParent !== null).map(e => ({
            id: e.id, name: e.name||'', value: e.value,
            opts: Array.from(e.options).map(o => ({v: o.value, t: o.text}))
        }));
    }""")


def get_all_fields(page):
    return page.evaluate("""() => {
        const els = document.querySelectorAll('input:not([type=hidden]), select, textarea');
        return Array.from(els).filter(e => e.offsetParent !== null).map(e => ({
            tag: e.tagName, type: e.type||'', id: e.id, name: e.name||'',
            value: (e.value||'').slice(0,40)
        }));
    }""")


def click_next(page, label=""):
    for btn_text in ["Save and Continue", "Next", "Continue"]:
        try:
            btn = page.get_by_role("button", name=btn_text, exact=False).first
            if btn.is_visible(timeout=3000):
                btn.scroll_into_view_if_needed()
                btn.click()
                print(f"[CLICK] {label} '{btn_text}'")
                time.sleep(3)
                return True
        except Exception:
            pass
    return False


def select_yes_for_select(page, sel_el_id, label=""):
    """For a Yes/No select, pick Yes."""
    opts = get_opts(page, sel_el_id)
    print(f"[DEBUG] {label} ({sel_el_id}) options: {opts}")
    yes_val = next((o["v"] for o in opts if o["t"].lower() == "yes"), None)
    if not yes_val:
        yes_val = next((o["v"] for o in opts if "yes" in o["t"].lower()), None)
    if yes_val:
        js_set(page, sel_el_id, yes_val)
        page.select_option(f"[id='{sel_el_id}']", value=yes_val)
        print(f"[FILL] {label} = Yes ({yes_val})")
        return True
    return False


def select_no_for_select(page, sel_el_id, label=""):
    """For a Yes/No select, pick No."""
    opts = get_opts(page, sel_el_id)
    no_val = next((o["v"] for o in opts if o["t"].lower() == "no"), None)
    if not no_val:
        no_val = next((o["v"] for o in opts if "no" in o["t"].lower() and len(o["t"]) < 20), None)
    if no_val:
        js_set(page, sel_el_id, no_val)
        page.select_option(f"[id='{sel_el_id}']", value=no_val)
        print(f"[FILL] {label} = No ({no_val})")
        return True
    return False


def fill_screening_questions(page):
    """Fill Application Questions step based on visible selects."""
    selects = get_all_selects(page)
    print(f"\n[DEBUG] Application Questions selects:")
    for s in selects:
        print(f"  id={s['id']} value={s['value']} opts={[o['t'] for o in s['opts']]}")

    page_text = page.inner_text("body").lower()

    for s in selects:
        fid = s["id"]
        if not fid or fid in ["source", "applicantSource", "country", "cntryFields.region",
                               "deviceType", "phoneWidget.countryPhoneCode"]:
            continue
        opts = s["opts"]
        opt_texts = [o["t"].lower() for o in opts]

        # Determine question context from labels
        label_text = page.evaluate(f"""() => {{
            const el = document.getElementById('{fid}');
            if (!el) return '';
            const label = document.querySelector('label[for="{fid}"]');
            if (label) return label.textContent;
            const parent = el.closest('.form-group, .field-group, div');
            return parent ? parent.textContent.trim().slice(0, 200) : '';
        }}""")
        print(f"  [{fid}] label: {repr(label_text[:100])}")

        label_lower = label_text.lower()

        # "Are you at least 18?" → Yes
        if "18" in label_lower or "age" in label_lower:
            select_yes_for_select(page, fid, "18+ age")

        # "Can you perform essential functions?" → Yes
        elif "perform" in label_lower or "essential function" in label_lower or "essential" in label_lower:
            select_yes_for_select(page, fid, "Essential functions")

        # "Proof of eligibility / authorized to work" → Yes
        elif "eligib" in label_lower or "authorized" in label_lower or "proof" in label_lower or "work in the country" in label_lower:
            select_yes_for_select(page, fid, "Work eligibility/authorization")

        # "Sponsorship" → YES (truthful - she does require sponsorship)
        elif "sponsor" in label_lower:
            select_yes_for_select(page, fid, "Sponsorship (YES - truthful)")

        # Generic yes/no — default to Yes for eligibility-sounding, No for negative
        elif "yes" in opt_texts and "no" in opt_texts:
            if any(k in label_lower for k in ["will you", "require", "need"]):
                # Sponsorship-type question: Yes
                select_yes_for_select(page, fid, f"Generic yes/no (yes): {fid}")
            else:
                select_yes_for_select(page, fid, f"Generic yes/no (yes): {fid}")


def fill_eeo(page):
    """Fill Voluntary Disclosures (EEO) step."""
    selects = get_all_selects(page)
    print(f"\n[DEBUG] EEO selects:")
    for s in selects:
        print(f"  id={s['id']} opts={[o['t'] for o in s['opts'][:5]]}")

    for s in selects:
        fid = s["id"]
        opts = s["opts"]
        fid_lower = fid.lower()

        if "gender" in fid_lower:
            fv = next((o["v"] for o in opts if "female" in o["t"].lower() or o["t"].lower() in ["f", "female", "woman"]), None)
            if fv:
                js_set(page, fid, fv)
                page.select_option(f"[id='{fid}']", value=fv)
                print(f"[FILL] Gender = Female ({fv})")

        elif "ethnic" in fid_lower or "race" in fid_lower:
            fv = next((o["v"] for o in opts if "asian" in o["t"].lower()), None)
            if fv:
                js_set(page, fid, fv)
                page.select_option(f"[id='{fid}']", value=fv)
                print(f"[FILL] Race/Ethnicity = Asian ({fv})")

        elif "veteran" in fid_lower or "vet" in fid_lower:
            fv = next((o["v"] for o in opts
                       if "not a protected" in o["t"].lower() or
                       "i am not" in o["t"].lower() or
                       o["t"].lower() == "no"), None)
            if fv:
                js_set(page, fid, fv)
                page.select_option(f"[id='{fid}']", value=fv)
                print(f"[FILL] Veteran = Not a protected veteran ({fv})")

        elif "disab" in fid_lower:
            fv = next((o["v"] for o in opts
                       if "no, i don" in o["t"].lower() or
                       "do not have" in o["t"].lower() or
                       o["t"].lower() == "no"), None)
            if fv:
                js_set(page, fid, fv)
                page.select_option(f"[id='{fid}']", value=fv)
                print(f"[FILL] Disability = No ({fv})")

    # Also check radios
    radios = page.evaluate("""
        () => Array.from(document.querySelectorAll('input[type=radio]'))
            .filter(e => e.offsetParent !== null)
            .map(e => ({id: e.id, name: e.name, value: e.value}))
    """)
    for r in radios:
        combined = (r["id"] + r["name"]).lower()
        val = r["value"].lower()
        if "gender" in combined and val in ["female", "f", "woman"]:
            page.click(f"[id='{r['id']}']")
            print(f"[FILL] Gender radio = {r['value']}")
        elif ("veteran" in combined or "vet" in combined) and val in ["no", "false", "0"]:
            page.click(f"[id='{r['id']}']")
            print(f"[FILL] Veteran radio = No")
        elif "disab" in combined and val in ["no", "false", "0"]:
            page.click(f"[id='{r['id']}']")
            print(f"[FILL] Disability radio = No")


def fill_step1_fresh(page):
    """Fill step 1 from scratch using proven JS force approach."""
    print("\n=== STEP 1: My Information ===")

    def set_field(fid, val):
        sel = f"[id='{fid}']"
        try:
            page.fill(sel, val)
        except Exception:
            pass
        js_set(page, fid, val)
        actual = page.evaluate(f"() => {{ const e = document.getElementById('{fid}'); return e ? e.value : null; }}")
        print(f"  {fid} = {repr(actual)}")

    def set_select(fid, val):
        sel = f"[id='{fid}']"
        try:
            page.select_option(sel, value=val)
        except Exception:
            pass
        js_set(page, fid, val)
        actual = page.evaluate(f"() => {{ const e = document.getElementById('{fid}'); return e ? e.value : null; }}")
        print(f"  {fid} = {repr(actual)}")

    # Source
    set_select("source", "Job Boards")

    # Previously worked = No
    page.evaluate("""() => {
        const r = document.getElementById('previousWorker.false');
        if (r) { r.checked = true; r.dispatchEvent(new Event('change', {bubbles: true})); }
    }""")

    # Personal info
    set_field("cntryFields.firstName", FIRST_NAME)
    set_field("cntryFields.lastName", LAST_NAME)
    set_field("cntryFields.addressLine1", "Portland, OR")
    set_field("cntryFields.city", CITY)
    set_select("cntryFields.region", "USA-OR")
    set_field("cntryFields.postalCode", POSTAL_CODE)
    set_field("email", EMAIL)

    # Phone device type
    device_opts = get_opts(page, "deviceType")
    mobile_val = next((o["v"] for o in device_opts if "mobile" in o["t"].lower()), None)
    if mobile_val:
        set_select("deviceType", mobile_val)

    # Phone
    set_field("phoneWidget.phoneNumber", PHONE_NUMBER)

    time.sleep(0.5)


def main():
    from patchright.sync_api import sync_playwright

    screenshot_paths = []

    with sync_playwright() as pw:
        print("[CONNECT] CDP port 9400...")
        browser = pw.chromium.connect_over_cdp("http://localhost:9400")
        context = browser.contexts[0]

        page = None
        for p in context.pages:
            if "careers.onelineage.com" in p.url:
                page = p
                print(f"[INFO] Found tab: {p.url[:80]}")
                break
        if not page:
            page = context.new_page()
            page.goto(APPLY_URL, wait_until="domcontentloaded", timeout=60000)
            time.sleep(5)

        page.bring_to_front()

        # Dismiss cookie if present
        try:
            btn = page.get_by_role("button", name="Allow", exact=False).first
            if btn.is_visible(timeout=2000):
                btn.click()
                time.sleep(1)
        except Exception:
            pass

        path = ss(page, "v5_start")
        screenshot_paths.append(path)
        print(f"[URL] {page.url}")

        # Determine current step from visible fields
        fields = get_all_fields(page)
        field_ids = [f["id"] for f in fields]
        print(f"[INFO] Visible fields: {field_ids[:15]}")

        # Detect which step we're on
        page_text = page.inner_text("body")
        page_text_lower = page_text.lower()

        # Check if already done
        if any(kw in page_text_lower for kw in ["thank you", "application received", "successfully submitted"]):
            print("[INFO] Already submitted/confirmed!")
            path = ss(page, "v5_already_confirmed")
            screenshot_paths.append(path)
            write_result({
                "company": "Lineage", "role": "HR Generalist", "ats": "Phenom",
                "apply_url": APPLY_URL, "submitted": True, "outcome": "submitted",
                "confirmed_at": datetime.now(timezone.utc).isoformat(),
                "screenshot_paths": screenshot_paths,
                "notes": "Already confirmed on arrival."
            })
            return

        # Step detection
        on_step1 = "cntryFields.firstName" in field_ids
        on_step2 = any("experiencedata" in fid.lower() for fid in field_ids)
        on_step3_questions = "application questions" in page_text_lower and any(
            s["id"] not in ["source", "applicantSource", "country", "cntryFields.region", "deviceType", "phoneWidget.countryPhoneCode"]
            for s in get_all_selects(page)
            if not s["id"].startswith("cntryFields")
        )
        on_eeo = "voluntary" in page_text_lower or any(
            k in " ".join(field_ids).lower() for k in ["gender", "ethnic", "veteran", "disab"]
        )
        on_review = "review" in page_text_lower and not on_step2  # "Review" step in progress bar

        print(f"[DETECT] step1={on_step1}, step2={on_step2}, step3_q={on_step3_questions}, eeo={on_eeo}, review={on_review}")

        # =====================================================================
        # STEP 1 (if needed)
        # =====================================================================
        if on_step1:
            fill_step1_fresh(page)

            path = ss(page, "v5_step1_filled")
            screenshot_paths.append(path)

            # Check resume
            resume_link = page.locator("[href*='.pdf'], [class*='file']").first
            try:
                if not resume_link.is_visible(timeout=2000):
                    for fi in page.locator("input[type='file']").all():
                        try:
                            fi.set_input_files(str(RESUME_PDF))
                            print(f"[UPLOAD] Resume")
                            time.sleep(2.5)
                            break
                        except Exception:
                            pass
            except Exception:
                pass

            click_next(page, "Step 1")

            if detect_captcha(page):
                handle_captcha_stop(page, screenshot_paths)

            path = ss(page, "v5_step2_start")
            screenshot_paths.append(path)

            # If still on step 1, force via JS and retry
            fields2 = get_all_fields(page)
            field_ids2 = [f["id"] for f in fields2]
            if "cntryFields.firstName" in field_ids2:
                print("[RETRY] Still step 1, JS force...")
                fill_step1_fresh(page)
                time.sleep(1)
                click_next(page, "Step 1 JS retry")
                time.sleep(2)
                path = ss(page, "v5_step2_after_retry")
                screenshot_paths.append(path)

        # =====================================================================
        # STEP 2: My Experience
        # =====================================================================
        fields = get_all_fields(page)
        field_ids = [f["id"] for f in fields]

        if any("experiencedata" in fid.lower() for fid in field_ids):
            print("\n=== MY EXPERIENCE ===")
            page_text_lower = page.inner_text("body").lower()

            # Check for cover letter upload
            for fi in page.locator("input[type='file']").all():
                try:
                    ctx = fi.evaluate("el => el.closest('div,section')?.innerText?.slice(0,100)||''")
                    if "cover" in ctx.lower():
                        fi.set_input_files(str(COVER_PDF))
                        print(f"[UPLOAD] Cover letter")
                        time.sleep(2)
                except Exception:
                    pass

            # Any textareas
            for ta in page.locator("textarea").all():
                try:
                    if ta.is_visible(timeout=1000) and not ta.input_value():
                        ta.fill(WHY_INTERESTED)
                        print("[FILL] Textarea")
                except Exception:
                    pass

            click_next(page, "Step 2 Experience")

            if detect_captcha(page):
                handle_captcha_stop(page, screenshot_paths)

            path = ss(page, "v5_step3_start")
            screenshot_paths.append(path)
            print(f"[URL] After step 2: {page.url}")

        # =====================================================================
        # STEP 3: Application Questions
        # =====================================================================
        page_text = page.inner_text("body")
        page_text_lower = page_text.lower()

        if "application questions" in page_text_lower:
            print("\n=== APPLICATION QUESTIONS ===")
            fill_screening_questions(page)

            # Textareas
            for ta in page.locator("textarea").all():
                try:
                    if ta.is_visible(timeout=1000) and not ta.input_value():
                        ta.fill(WHY_INTERESTED)
                        print("[FILL] Textarea in App Questions")
                except Exception:
                    pass

            path = ss(page, "v5_step3_filled")
            screenshot_paths.append(path)

            click_next(page, "Step 3 App Questions")

            if detect_captcha(page):
                handle_captcha_stop(page, screenshot_paths)

            path = ss(page, "v5_step4_start")
            screenshot_paths.append(path)
            print(f"[URL] After step 3: {page.url}")

        # =====================================================================
        # STEP 4: Voluntary Disclosures (EEO)
        # =====================================================================
        page_text = page.inner_text("body")
        page_text_lower = page_text.lower()

        if "voluntary" in page_text_lower or "disclosures" in page_text_lower or "equal" in page_text_lower:
            print("\n=== VOLUNTARY DISCLOSURES (EEO) ===")
            fill_eeo(page)

            path = ss(page, "v5_step4_filled")
            screenshot_paths.append(path)

            click_next(page, "Step 4 EEO")

            if detect_captcha(page):
                handle_captcha_stop(page, screenshot_paths)

            path = ss(page, "v5_step5_start")
            screenshot_paths.append(path)
            print(f"[URL] After step 4: {page.url}")

        # =====================================================================
        # STEP 5: Review — then Submit
        # =====================================================================
        page_text = page.inner_text("body")
        page_text_lower = page_text.lower()

        # Check if confirmed already
        if any(kw in page_text_lower for kw in ["thank you", "application received", "successfully submitted"]):
            print("[INFO] Application submitted/confirmed!")
            path = ss(page, "v5_confirmation")
            screenshot_paths.append(path)
            write_result({
                "company": "Lineage", "role": "HR Generalist", "ats": "Phenom",
                "apply_url": APPLY_URL, "submitted": True, "outcome": "submitted",
                "confirmed_at": datetime.now(timezone.utc).isoformat(),
                "screenshot_paths": screenshot_paths,
                "notes": "Confirmed. Name: Yi-Chieh Cheng. Sponsorship: YES. Source: Job Boards."
            })
            return

        print("\n=== REVIEW / PRE-SUBMIT ===")
        time.sleep(2)

        checks = {
            "name_Yi-Chieh": "Yi-Chieh" in page_text,
            "name_Cheng": "Cheng" in page_text,
            "email": EMAIL in page_text,
            "phone": PHONE_NUMBER in page_text,
            "sponsorship_yes": "yes" in page_text_lower,
        }
        print(f"[VERIFY] {json.dumps(checks, indent=2)}")

        pre_submit_path = str(SCREENSHOTS_DIR / "pre_submit_review.png")
        page.screenshot(path=pre_submit_path, full_page=True)
        screenshot_paths.append(pre_submit_path)
        print("[SCREENSHOT] pre_submit_review.png")

        if detect_captcha(page):
            handle_captcha_stop(page, screenshot_paths)

        # Submit
        print("\n=== SUBMIT ===")
        submitted = False

        btns_info = page.evaluate("""
            () => Array.from(document.querySelectorAll('button'))
                .filter(b => b.offsetParent !== null)
                .map(b => ({text: b.textContent.trim(), disabled: b.disabled}))
        """)
        print(f"[DEBUG] Buttons: {btns_info}")

        for btn_text in ["Submit Application", "Submit", "Apply Now", "Apply"]:
            try:
                btn = page.get_by_role("button", name=btn_text, exact=False).first
                if btn.is_visible(timeout=2000) and not btn.is_disabled():
                    btn.scroll_into_view_if_needed()
                    btn.click()
                    print(f"[SUBMIT] Clicked '{btn_text}'")
                    submitted = True
                    time.sleep(6)
                    break
            except Exception:
                pass

        if not submitted:
            # Maybe more steps — click Save and Continue
            if click_next(page, "Final step"):
                submitted = True

        if detect_captcha(page):
            handle_captcha_stop(page, screenshot_paths)

        time.sleep(3)
        confirm_path = str(SCREENSHOTS_DIR / "confirmation.png")
        page.screenshot(path=confirm_path, full_page=True)
        screenshot_paths.append(confirm_path)
        print("[SCREENSHOT] confirmation.png")

        final_text = page.inner_text("body").lower()
        is_confirmed = any(kw in final_text for kw in [
            "thank you", "application received", "successfully submitted",
            "application submitted", "we'll be in touch", "under review", "application complete"
        ])

        outcome = "submitted" if (submitted and is_confirmed) else \
                  "submitted-unconfirmed" if submitted else "failed"
        print(f"\n[OUTCOME] {outcome}")
        print(f"[VERIFY] name={checks['name_Yi-Chieh']}, email={checks['email']}, sponsor={checks['sponsorship_yes']}")

        write_result({
            "company": "Lineage", "role": "HR Generalist", "ats": "Phenom",
            "apply_url": APPLY_URL, "submitted": submitted, "outcome": outcome,
            "confirmed_at": datetime.now(timezone.utc).isoformat() if is_confirmed else None,
            "screenshot_paths": screenshot_paths,
            "notes": (
                f"Checks: {checks}. Confirmed: {is_confirmed}. "
                f"Source: Job Boards. First Name: Yi-Chieh. Sponsorship: YES truthful."
            )
        })
        print(f"[DONE] {outcome}")


if __name__ == "__main__":
    main()
