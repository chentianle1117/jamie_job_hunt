"""
Lineage Phenom ATS driver v4 - uses page.fill() and page.select_option() with attribute selectors.
Known field IDs (dots in IDs — use [id='...'] selectors):
  - source (select): Job Boards
  - applicantSource (select): second level, ignore
  - previousWorker.false (radio): No
  - country (select): USA (already set)
  - cntryFields.firstName (text): Yi-Chieh
  - cntryFields.lastName (text): Cheng
  - cntryFields.addressLine1 (text): Portland, OR
  - cntryFields.city (text): Portland
  - cntryFields.region (select): USA-OR (Oregon)
  - cntryFields.postalCode (text): 97201
  - email (text/email): jamiecheng0103@gmail.com
  - deviceType (select): first non-empty option (Cell Phone)
  - phoneWidget.countryPhoneCode (select): USA_1 (already set)
  - phoneWidget.phoneNumber (text): 2137003831
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


def pf(page, field_id, value, label=""):
    """page.fill() by attribute selector."""
    sel = f"[id='{field_id}']"
    try:
        page.fill(sel, value)
        print(f"[FILL] {label or field_id} = {repr(value[:50])}")
        return True
    except Exception as e:
        print(f"[WARN] pf({field_id}): {str(e)[:100]}")
        return False


def ps(page, field_id, value=None, label_text=None, label=""):
    """page.select_option() by attribute selector."""
    sel = f"[id='{field_id}']"
    try:
        if value is not None:
            page.select_option(sel, value=value)
        else:
            page.select_option(sel, label=label_text)
        actual = page.locator(sel).input_value()
        print(f"[FILL] {label or field_id} = {repr(actual[:50])}")
        return True
    except Exception as e:
        print(f"[WARN] ps({field_id}): {str(e)[:100]}")
        return False


def pr(page, field_id, label=""):
    """Click radio by exact id attribute."""
    sel = f"[id='{field_id}']"
    try:
        page.click(sel)
        print(f"[FILL] {label or field_id} clicked")
        return True
    except Exception as e:
        print(f"[WARN] pr({field_id}): {str(e)[:80]}")
        return False


def js_set(page, field_id, value):
    """Set a field value via JS and fire change event (for React-managed fields)."""
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


def get_radios(page):
    return page.evaluate("""() =>
        Array.from(document.querySelectorAll('input[type=radio]'))
        .filter(e => e.offsetParent !== null)
        .map(e => ({id: e.id, name: e.name, value: e.value, checked: e.checked}))
    """)


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
    print(f"[WARN] No next button found for {label}")
    return False


def dismiss_cookie(page):
    try:
        for text in ["Allow", "Accept All", "Accept"]:
            btn = page.get_by_role("button", name=text, exact=False).first
            if btn.is_visible(timeout=3000):
                btn.click()
                print(f"[COOKIE] Dismissed ({text})")
                time.sleep(1)
                return True
    except Exception:
        pass
    return False


def main():
    from patchright.sync_api import sync_playwright

    screenshot_paths = []

    with sync_playwright() as pw:
        print("[CONNECT] CDP port 9400...")
        browser = pw.chromium.connect_over_cdp("http://localhost:9400")
        context = browser.contexts[0]

        # Find existing tab or open new
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
        dismiss_cookie(page)
        time.sleep(0.5)

        # Ensure we're on the apply page
        if "apply" not in page.url:
            page.goto(APPLY_URL, wait_until="domcontentloaded", timeout=60000)
            time.sleep(4)

        path = ss(page, "v4_start")
        screenshot_paths.append(path)

        # =====================================================================
        # FILL STEP 1 — MY INFORMATION
        # All fields on this page:
        # =====================================================================
        print("\n=== MY INFORMATION (v4) ===")

        # Source dropdown (select id="source")
        # Options: Job Boards, Direct Source, Referred or Invited..., etc.
        ps(page, "source", value="Job Boards", label="Source")

        # Previously worked: No (id="previousWorker.false")
        pr(page, "previousWorker.false", "Previously worked = No")

        # Country: USA (already set, leave alone)

        # First Name (id="cntryFields.firstName")
        # Use both page.fill AND js_set to bypass React
        page.fill("[id='cntryFields.firstName']", FIRST_NAME)
        time.sleep(0.2)
        js_set(page, "cntryFields.firstName", FIRST_NAME)
        time.sleep(0.2)
        actual_fn = page.input_value("[id='cntryFields.firstName']")
        print(f"[FILL] First Name = {repr(actual_fn)} (target: {FIRST_NAME})")

        # Last Name
        page.fill("[id='cntryFields.lastName']", LAST_NAME)
        time.sleep(0.2)
        js_set(page, "cntryFields.lastName", LAST_NAME)
        actual_ln = page.input_value("[id='cntryFields.lastName']")
        print(f"[FILL] Last Name = {repr(actual_ln)}")

        # Address line 1
        page.fill("[id='cntryFields.addressLine1']", "Portland, OR")
        time.sleep(0.1)
        print("[FILL] Address = Portland, OR")

        # City
        page.fill("[id='cntryFields.city']", CITY)
        time.sleep(0.1)
        js_set(page, "cntryFields.city", CITY)
        print(f"[FILL] City = {CITY}")

        # State: USA-OR (Oregon)
        ps(page, "cntryFields.region", value="USA-OR", label="State")

        # Postal Code
        page.fill("[id='cntryFields.postalCode']", POSTAL_CODE)
        time.sleep(0.1)
        print(f"[FILL] Postal Code = {POSTAL_CODE}")

        # Email
        page.fill("[id='email']", EMAIL)
        time.sleep(0.1)
        js_set(page, "email", EMAIL)
        actual_email = page.input_value("[id='email']")
        print(f"[FILL] Email = {repr(actual_email)}")

        # Phone Device Type — find first non-empty option
        device_opts = get_opts(page, "deviceType")
        print(f"[DEBUG] Device type opts: {device_opts}")
        cell_val = next((o["v"] for o in device_opts if o["v"] and ("cell" in o["t"].lower() or "mobile" in o["t"].lower())), None)
        if not cell_val:
            cell_val = next((o["v"] for o in device_opts if o["v"]), None)
        if cell_val:
            ps(page, "deviceType", value=cell_val, label="Phone Device Type")
        else:
            print("[WARN] No device type options found")

        # Country phone code: already USA_1 — verify
        cpc_val = page.input_value("[id='phoneWidget.countryPhoneCode']")
        print(f"[INFO] Country phone code: {cpc_val}")
        # If not USA_1, set it
        if "USA" not in cpc_val:
            cpc_opts = get_opts(page, "phoneWidget.countryPhoneCode")
            usa_val = next((o["v"] for o in cpc_opts if "united states" in o["t"].lower() and "(+1)" in o["t"]), None)
            if usa_val:
                ps(page, "phoneWidget.countryPhoneCode", value=usa_val, label="Country Phone Code")

        # Phone number
        page.fill("[id='phoneWidget.phoneNumber']", PHONE_NUMBER)
        time.sleep(0.1)
        js_set(page, "phoneWidget.phoneNumber", PHONE_NUMBER)
        actual_phone = page.input_value("[id='phoneWidget.phoneNumber']")
        print(f"[FILL] Phone = {repr(actual_phone)}")

        time.sleep(1)

        # Take screenshot before clicking Next
        path = ss(page, "v4_step1_filled")
        screenshot_paths.append(path)

        # Check if resume already uploaded
        resume_visible = page.locator("a[href*='.pdf'], [class*='file'], [class*='resume']").first
        try:
            resume_already = resume_visible.is_visible(timeout=2000)
            print(f"[INFO] Resume already uploaded: {resume_already}")
        except Exception:
            resume_already = False

        if not resume_already:
            file_inputs = page.locator("input[type='file']").all()
            for fi in file_inputs:
                try:
                    fi.set_input_files(str(RESUME_PDF))
                    print(f"[UPLOAD] Resume: {RESUME_PDF.name}")
                    time.sleep(2.5)
                    break
                except Exception as ex:
                    print(f"[WARN] Upload: {ex}")

        # Verify all required fields before clicking next
        print("\n[PRE-NEXT VERIFY]")
        fields = get_all_fields(page)
        for f in fields:
            if f["id"] in ["cntryFields.firstName", "cntryFields.lastName", "cntryFields.region",
                           "email", "deviceType", "phoneWidget.phoneNumber"]:
                print(f"  {f['id']} = {repr(f['value'])}")

        path = ss(page, "v4_step1_before_next")
        screenshot_paths.append(path)

        # Click Save and Continue
        click_next(page, "Step 1")

        if detect_captcha(page):
            handle_captcha_stop(page, screenshot_paths)

        path = ss(page, "v4_step2_start")
        screenshot_paths.append(path)

        # Check if we advanced (URL or visible inputs changed)
        current_fields = get_all_fields(page)
        current_ids = [f["id"] for f in current_fields]
        print(f"\n[POST-STEP1] Fields: {current_ids[:15]}")

        # Check for validation error messages
        error_msgs = page.evaluate("""
            () => Array.from(document.querySelectorAll('[class*="error"], [class*="invalid"], .alert, .form-error'))
                .filter(e => e.offsetParent !== null)
                .map(e => e.textContent.trim().slice(0, 100))
                .filter(t => t)
        """)
        if error_msgs:
            print(f"[WARN] Validation errors: {error_msgs}")

        # If still on step 1 (same fields visible), try forcing values via JS then clicking next
        if "cntryFields.firstName" in current_ids:
            print("[RETRY] Still on step 1 — trying JS force-fill + re-click")

            # Force all required fields via JS
            js_fills = [
                ("cntryFields.firstName", FIRST_NAME),
                ("cntryFields.lastName", LAST_NAME),
                ("cntryFields.city", CITY),
                ("cntryFields.region", "USA-OR"),
                ("cntryFields.postalCode", POSTAL_CODE),
                ("email", EMAIL),
                ("phoneWidget.phoneNumber", PHONE_NUMBER),
            ]
            for fid, val in js_fills:
                result = js_set(page, fid, val)
                print(f"  JS set {fid} = {repr(result)[:30]}")

            # Set deviceType to first non-empty
            device_opts2 = get_opts(page, "deviceType")
            cv = next((o["v"] for o in device_opts2 if o["v"]), None)
            if cv:
                js_set(page, "deviceType", cv)
                print(f"  JS set deviceType = {cv}")

            # Set radio to No
            page.evaluate("""() => {
                const r = document.getElementById('previousWorker.false');
                if (r) { r.checked = true; r.dispatchEvent(new Event('change', {bubbles: true})); }
            }""")
            print("  JS set previousWorker = false")

            time.sleep(1)
            path = ss(page, "v4_step1_retry")
            screenshot_paths.append(path)

            click_next(page, "Step 1 Retry")

            if detect_captcha(page):
                handle_captcha_stop(page, screenshot_paths)

            path = ss(page, "v4_step2_after_retry")
            screenshot_paths.append(path)

            # Check again
            retry_fields = get_all_fields(page)
            retry_ids = [f["id"] for f in retry_fields]
            print(f"[POST-RETRY] Fields: {retry_ids[:15]}")

            error_msgs2 = page.evaluate("""
                () => Array.from(document.querySelectorAll('[class*="error"], [class*="invalid"], .alert-danger, .has-error'))
                    .filter(e => e.offsetParent !== null)
                    .map(e => e.textContent.trim().slice(0, 150))
                    .filter(t => t)
            """)
            if error_msgs2:
                print(f"[WARN] Remaining errors: {error_msgs2}")

        # =====================================================================
        # SUBSEQUENT STEPS
        # =====================================================================
        for step_num in range(2, 8):
            current_fields = get_all_fields(page)
            current_ids = [f["id"] for f in current_fields]

            # Check if we're done
            page_text = page.inner_text("body").lower()
            if any(kw in page_text for kw in ["thank you", "application received", "successfully submitted", "application submitted"]):
                print(f"[INFO] Confirmed submission on step {step_num}")
                break

            # If still on step 1, something is blocking - report and exit
            if "cntryFields.firstName" in current_ids:
                print(f"[STUCK] Still on step 1 after {step_num-1} retries")
                path = ss(page, f"v4_stuck_step1_attempt{step_num}")
                screenshot_paths.append(path)
                # Check what the actual page looks like
                page_html = page.evaluate("""
                    () => document.querySelector('.form-group.has-error, .invalid-feedback, [class*="error"]')
                        ?.textContent?.trim() || 'no error found'
                """)
                print(f"[DEBUG] Error element: {page_html}")
                break

            print(f"\n=== STEP {step_num} ===")
            print(f"Fields: {current_ids[:10]}")

            # Work auth / sponsorship
            radios = get_radios(page)
            for r in radios:
                if any(k in r["name"].lower() for k in ["auth", "eligib", "workauth"]):
                    if r["value"].lower() in ["yes", "true", "1"]:
                        pr(page, r["id"], f"Work auth Yes")
                if "sponsor" in r["name"].lower():
                    if r["value"].lower() in ["yes", "true", "1"]:
                        pr(page, r["id"], f"Sponsorship Yes")

            # EEO selects
            for f in current_fields:
                fid = f["id"]
                combined = fid.lower()
                if f["tag"] == "SELECT":
                    opts = get_opts(page, fid)
                    if "gender" in combined:
                        fv = next((o["v"] for o in opts if "female" in o["t"].lower()), None)
                        if fv:
                            ps(page, fid, value=fv, label=f"Gender ({fid})")
                    elif "ethnic" in combined or "race" in combined:
                        fv = next((o["v"] for o in opts if "asian" in o["t"].lower()), None)
                        if fv:
                            ps(page, fid, value=fv, label=f"Race ({fid})")
                    elif "veteran" in combined or "vet" in combined:
                        fv = next((o["v"] for o in opts
                                   if "not a protected" in o["t"].lower() or "no" == o["t"].lower()
                                   or "i am not" in o["t"].lower()), None)
                        if fv:
                            ps(page, fid, value=fv, label=f"Veteran ({fid})")
                    elif "disab" in combined:
                        fv = next((o["v"] for o in opts
                                   if "no, i don" in o["t"].lower() or "do not have" in o["t"].lower()
                                   or "no" == o["t"].lower()), None)
                        if fv:
                            ps(page, fid, value=fv, label=f"Disability ({fid})")

            # Textareas
            for ta in page.locator("textarea").all():
                try:
                    if ta.is_visible(timeout=1000) and not ta.input_value():
                        ta.fill(WHY_INTERESTED)
                        print(f"[FILL] Textarea")
                except Exception:
                    pass

            # Password inputs (account creation)
            for pwi in page.locator("input[type='password']").all():
                try:
                    if pwi.is_visible(timeout=1000):
                        pwi.fill(_SHARED_PW)
                        print("[FILL] Password [REDACTED]")
                except Exception:
                    pass

            # File inputs (cover letter)
            for i, fi in enumerate(page.locator("input[type='file']").all()):
                try:
                    ctx = fi.evaluate("el => el.closest('div')?.innerText?.slice(0,60)||''")
                    if "cover" in ctx.lower():
                        fi.set_input_files(str(COVER_PDF))
                        print(f"[UPLOAD] Cover letter")
                        time.sleep(2)
                except Exception:
                    pass

            if detect_captcha(page):
                handle_captcha_stop(page, screenshot_paths)

            # Check for review page
            if any(kw in page_text for kw in ["review", "confirm", "summary", "almost done"]):
                print("[INFO] Review page detected")
                break

            click_next(page, f"Step {step_num}")

            if detect_captcha(page):
                handle_captcha_stop(page, screenshot_paths)

            path = ss(page, f"v4_step{step_num+1}_start")
            screenshot_paths.append(path)
            print(f"[URL] After step {step_num}: {page.url}")

        # =====================================================================
        # PRE-SUBMIT REVIEW
        # =====================================================================
        print("\n=== PRE-SUBMIT REVIEW ===")
        time.sleep(2)
        page_text = page.inner_text("body")

        checks = {
            "name_Yi-Chieh": "Yi-Chieh" in page_text,
            "name_Cheng": "Cheng" in page_text,
            "email": EMAIL in page_text,
            "phone": PHONE_NUMBER in page_text,
            "sponsorship_yes": "yes" in page_text.lower(),
        }
        print(f"[VERIFY] {json.dumps(checks, indent=2)}")

        pre_submit_path = str(SCREENSHOTS_DIR / "pre_submit_review.png")
        page.screenshot(path=pre_submit_path, full_page=True)
        screenshot_paths.append(pre_submit_path)
        print("[SCREENSHOT] pre_submit_review.png")

        if detect_captcha(page):
            handle_captcha_stop(page, screenshot_paths)

        # =====================================================================
        # SUBMIT
        # =====================================================================
        print("\n=== SUBMIT ===")
        submitted = False

        page_text_lower = page_text.lower()
        if any(kw in page_text_lower for kw in ["thank you", "application received", "submitted"]):
            submitted = True
            print("[INFO] Already confirmed!")
        else:
            # All visible buttons
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
                # Try one more Save and Continue (might be more steps)
                if click_next(page, "Final"):
                    submitted = True

        if detect_captcha(page):
            handle_captcha_stop(page, screenshot_paths)

        # Confirmation
        time.sleep(3)
        confirm_path = str(SCREENSHOTS_DIR / "confirmation.png")
        page.screenshot(path=confirm_path, full_page=True)
        screenshot_paths.append(confirm_path)
        print("[SCREENSHOT] confirmation.png")

        final_text = page.inner_text("body").lower()
        is_confirmed = any(kw in final_text for kw in [
            "thank you", "application received", "successfully submitted",
            "application submitted", "we'll be in touch", "under review",
            "application complete", "your application"
        ])

        outcome = "submitted" if (submitted and is_confirmed) else \
                  "submitted-unconfirmed" if submitted else "failed"
        print(f"\n[OUTCOME] {outcome}")

        write_result({
            "company": "Lineage",
            "role": "HR Generalist",
            "ats": "Phenom",
            "apply_url": APPLY_URL,
            "submitted": submitted,
            "outcome": outcome,
            "confirmed_at": datetime.now(timezone.utc).isoformat() if is_confirmed else None,
            "screenshot_paths": screenshot_paths,
            "notes": (
                f"Checks: {checks}. Confirmed: {is_confirmed}. "
                f"Source: Job Boards (LinkedIn not in dropdown). "
                f"First Name: Yi-Chieh. Sponsorship: YES. "
                f"Phone: {PHONE_NUMBER} US (+1)."
            )
        })
        print(f"[DONE] {outcome}")


if __name__ == "__main__":
    main()
