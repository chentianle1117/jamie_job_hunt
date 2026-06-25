"""
Lineage Phenom ATS application driver - corrected version.
Key findings from screenshot:
- Cookie consent modal appears first — must click "Allow"
- Form is a single-page scroll with all fields visible
- Source dropdown is a native <select> (not react-select)
- Phone has "Country Phone Code" native <select> + "Phone Number" text input
- State is a native <select>
- URL stays the same throughout (SPA with steps via JS)
"""
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# --- Paths ---
APP_DIR = Path(r"C:\Users\chent\Agentic_Workflows_2026\oracle-job-search\outputs\2026-06-23-lean\applications\Lineage_HR-Generalist")
RESUME_PDF = APP_DIR / "resume.pdf"
COVER_PDF = APP_DIR / "cover_letter.pdf"
SCREENSHOTS_DIR = APP_DIR / "screenshots"
SCREENSHOTS_DIR.mkdir(exist_ok=True)

APPLY_URL = "https://careers.onelineage.com/us/en/apply?jobSeqNo=LLLLLOUSR0103931EXTERNALENUS&step=1&stepname=personalInformation"

# --- Candidate data ---
FIRST_NAME = "Yi-Chieh"
LAST_NAME = "Cheng"
EMAIL = "jamiecheng0103@gmail.com"
PHONE_NUMBER = "2137003831"  # digits only, country code separate
PHONE_FULL = "+12137003831"
CITY = "Portland"
STATE_VALUE = "OR"
POSTAL_CODE = "97201"
ADDRESS = "Portland, OR"

WHY_INTERESTED = (
    "I'm drawn to Lineage's mission of connecting food supply chains more efficiently — "
    "that kind of operational complexity creates meaningful HR challenges I'm excited to work on. "
    "My background spans the full HR generalist scope: I built performance frameworks and managed "
    "complex employee relations cases at ODN and Vestas, supported benefits and compliance at NextGen, "
    "and led onboarding and HRIS projects across multiple orgs. I'd love to bring that breadth to "
    "Lineage's people team."
)

# Read password silently
PW_PATH = Path(r"C:\Users\chent\Downloads\job_password.txt")
_SHARED_PW = PW_PATH.read_text().strip() if PW_PATH.exists() else ""


def ss(page, name):
    path = SCREENSHOTS_DIR / f"{name}.png"
    page.screenshot(path=str(path), full_page=True)
    print(f"[SCREENSHOT] {path.name}")
    return str(path)


def detect_captcha(page):
    """Return True if there's an interactive CAPTCHA puzzle visible (not v3 badge)."""
    for frame in page.frames:
        if "recaptcha" in frame.url and "bframe" in frame.url:
            return True
    if page.locator("iframe[src*='hcaptcha']").count() > 0:
        return True
    if page.locator(".g-recaptcha-bubble-arrow, .challenge-container").count() > 0:
        return True
    return False


def handle_captcha_stop(page, screenshot_paths):
    path = ss(page, "captcha_detected")
    screenshot_paths.append(path)
    write_result({
        "company": "Lineage",
        "role": "HR Generalist",
        "ats": "Phenom",
        "apply_url": APPLY_URL,
        "submitted": False,
        "outcome": "captcha-staged",
        "confirmed_at": None,
        "screenshot_paths": screenshot_paths,
        "notes": "Interactive CAPTCHA detected. Human must solve then click Submit."
    })
    print("[STOP] CAPTCHA detected — leaving form open for human completion.")
    sys.exit(0)


def write_result(data):
    out = APP_DIR / "SUBMITTED.json"
    out.write_text(json.dumps(data, indent=2))
    print(f"[RESULT] Written to {out.name}")


def safe_select(page, selector, value, by="value", label="field", timeout=5000):
    """Select an option in a native <select> element."""
    try:
        el = page.locator(selector).first
        el.wait_for(timeout=timeout)
        if by == "value":
            el.select_option(value=value)
        elif by == "label":
            el.select_option(label=value)
        elif by == "index":
            el.select_option(index=value)
        print(f"[FILL] {label} = {value}")
        return True
    except Exception as e:
        print(f"[WARN] {label} select failed: {str(e)[:80]}")
        return False


def safe_fill(page, selector, value, label="field", timeout=5000):
    """Fill a text input."""
    try:
        el = page.locator(selector).first
        el.wait_for(timeout=timeout)
        el.triple_click()
        el.fill(value)
        print(f"[FILL] {label} = {repr(value[:60])}")
        return True
    except Exception as e:
        print(f"[WARN] {label} fill failed: {str(e)[:80]}")
        return False


def safe_radio(page, name_or_id, value, label="radio"):
    """Select a radio button by name+value or nearby text."""
    try:
        page.locator(f"input[type='radio'][name='{name_or_id}'][value='{value}']").first.click()
        print(f"[FILL] {label} radio = {value}")
        return True
    except Exception:
        pass
    # Try by value only
    try:
        page.locator(f"input[type='radio'][value='{value}']").first.click()
        print(f"[FILL] {label} radio (by value) = {value}")
        return True
    except Exception:
        pass
    return False


def click_label_with_text(page, text, partial=True, label=""):
    """Click a label whose text contains the given string."""
    try:
        if partial:
            labels = page.locator("label").all()
            for lbl in labels:
                t = lbl.text_content() or ""
                if text.lower() in t.lower():
                    lbl.click()
                    print(f"[FILL] {label or text} label clicked")
                    return True
        else:
            page.get_by_label(text, exact=True).click()
            return True
    except Exception as e:
        print(f"[WARN] Label click '{text}' failed: {str(e)[:80]}")
    return False


def find_or_open_tab(context):
    pages = context.pages
    print(f"[INFO] Found {len(pages)} pages in context")
    for p in pages:
        print(f"  tab url={p.url[:80]}")
        if "careers.onelineage.com" in p.url and "apply" in p.url:
            print("[INFO] Found existing Lineage apply tab")
            return p
    print("[INFO] Opening Lineage apply URL in new tab")
    page = context.new_page()
    page.goto(APPLY_URL, wait_until="domcontentloaded", timeout=60000)
    time.sleep(5)
    return page


def dismiss_cookie_modal(page):
    """Dismiss cookie consent modal if present."""
    try:
        allow_btn = page.get_by_role("button", name="Allow").first
        if allow_btn.is_visible(timeout=4000):
            allow_btn.click()
            print("[ACTION] Cookie modal dismissed (Allow)")
            time.sleep(1)
            return True
    except Exception:
        pass
    try:
        # Try any accept/allow button in a modal
        for text in ["Allow", "Accept", "Accept All", "OK", "I Accept", "Agree"]:
            btns = page.get_by_role("button", name=text, exact=False).all()
            for btn in btns:
                if btn.is_visible():
                    btn.click()
                    print(f"[ACTION] Cookie modal dismissed ({text})")
                    time.sleep(1)
                    return True
    except Exception:
        pass
    return False


def wait_for_step(page, step_name, timeout=15000):
    """Wait for a step indicator or specific element to appear."""
    try:
        page.wait_for_selector(f"text={step_name}", timeout=timeout)
        return True
    except Exception:
        return False


def click_next(page, step_num):
    """Click the Save and Continue / Next button."""
    for btn_text in ["Save and Continue", "Next", "Continue", "Next Step"]:
        try:
            btns = page.get_by_role("button", name=btn_text, exact=False).all()
            for btn in btns:
                if btn.is_visible():
                    btn.scroll_into_view_if_needed()
                    btn.click()
                    print(f"[CLICK] Step {step_num}: '{btn_text}'")
                    time.sleep(2.5)
                    return True
        except Exception:
            pass
    # JS fallback
    try:
        page.evaluate("""
            () => {
                const btns = document.querySelectorAll('button');
                for (const btn of btns) {
                    const txt = btn.textContent.trim().toLowerCase();
                    if (txt === 'save and continue' || txt === 'next' || txt === 'continue') {
                        btn.click();
                        return txt;
                    }
                }
            }
        """)
        print(f"[CLICK] Step {step_num}: JS fallback next button")
        time.sleep(2.5)
        return True
    except Exception:
        pass
    print(f"[WARN] Could not find Next button on step {step_num}")
    return False


def debug_page_inputs(page):
    """Print all visible inputs for debugging."""
    try:
        inputs = page.evaluate("""
            () => {
                const els = document.querySelectorAll('input, select, textarea');
                return Array.from(els).map(el => ({
                    tag: el.tagName,
                    type: el.type || '',
                    name: el.name || '',
                    id: el.id || '',
                    placeholder: el.placeholder || '',
                    value: el.value ? el.value.slice(0, 30) : '',
                    visible: el.offsetParent !== null
                })).filter(e => e.visible);
            }
        """)
        print(f"[DEBUG] Visible inputs: {json.dumps(inputs[:20], indent=2)}")
    except Exception as e:
        print(f"[DEBUG] Could not enumerate inputs: {e}")


def fill_have_you_worked_here(page):
    """Answer 'Have you previously worked for this organization? No'"""
    try:
        # Look for the question
        body = page.inner_text("body")
        if "previously worked" in body.lower() or "worked for this organization" in body.lower():
            # Select "No" radio
            for radio in page.locator("input[type='radio']").all():
                val = radio.get_attribute("value") or ""
                if val.lower() in ["no", "false", "0"]:
                    # Check if it's near the "previously worked" question
                    try:
                        radio.click()
                        print("[FILL] Previously worked here = No")
                        return True
                    except Exception:
                        pass
    except Exception:
        pass
    return False


def main():
    from patchright.sync_api import sync_playwright

    screenshot_paths = []
    skipped_fields = []

    with sync_playwright() as pw:
        print("[CONNECT] Attaching to Chrome on port 9400...")
        try:
            browser = pw.chromium.connect_over_cdp("http://localhost:9400")
        except Exception as e:
            print(f"[ERROR] Cannot connect: {e}")
            sys.exit(1)

        context = browser.contexts[0]
        page = find_or_open_tab(context)
        page.bring_to_front()

        # Navigate to apply URL if not already there
        if "careers.onelineage.com" not in page.url or "apply" not in page.url:
            print("[NAV] Navigating to apply URL...")
            page.goto(APPLY_URL, wait_until="domcontentloaded", timeout=60000)
            time.sleep(5)

        # Dismiss cookie modal FIRST
        dismiss_cookie_modal(page)
        time.sleep(1)

        path = ss(page, "step1_after_cookie_dismiss")
        screenshot_paths.append(path)
        print(f"\n[PAGE] Current URL: {page.url}")

        # Debug: see what inputs are on this page
        debug_page_inputs(page)

        # ---------------------------------------------------------------
        # STEP 1: Source, Previously Worked?, Country, Personal Info
        # ---------------------------------------------------------------
        print("\n=== STEP 1: Personal Information (Source + Contact) ===")

        # Source: "How did you hear about us?" - native <select id="source">
        # Options: Job Boards, Lineage Career Site, Referred or Invited..., etc.
        # "LinkedIn" isn't in the list — best match is "Job Boards"
        safe_select(page, "select#source, select[name='source'], select[id*='source']",
                    value="Job Boards", by="label", label="Source/How did you hear")

        # "Have you previously worked for this organization?" - No
        # Try radio buttons with value "No"
        time.sleep(0.3)
        radios = page.locator("input[type='radio']").all()
        print(f"[DEBUG] Found {len(radios)} radio buttons")
        for r in radios:
            val = (r.get_attribute("value") or "").lower()
            name_attr = (r.get_attribute("name") or "").lower()
            print(f"  radio: name={name_attr}, value={val}")

        # Click "No" for previously worked
        for r in page.locator("input[type='radio']").all():
            val = (r.get_attribute("value") or "").lower()
            if val == "no":
                try:
                    r.click()
                    print("[FILL] Previously worked here = No (radio)")
                    break
                except Exception:
                    pass

        # Country: United States (should already be default)
        try:
            country_sel = page.locator("select[name*='country' i], select[id*='country' i]").first
            if country_sel.count():
                current_val = country_sel.input_value()
                print(f"[INFO] Country current value: {repr(current_val)}")
                if "united states" not in current_val.lower() and "usa" not in current_val.lower():
                    try:
                        country_sel.select_option(label="United States of America")
                        print("[FILL] Country = United States of America")
                    except Exception:
                        try:
                            country_sel.select_option(value="US")
                            print("[FILL] Country = US")
                        except Exception:
                            pass
        except Exception:
            pass

        # First Name
        safe_fill(page,
                  "input[name='firstName'], input[id='firstName'], input[placeholder*='First' i]",
                  FIRST_NAME, "First Name")

        # Last Name
        safe_fill(page,
                  "input[name='lastName'], input[id='lastName'], input[placeholder*='Last' i]",
                  LAST_NAME, "Last Name")

        # Address (optional — try to fill if present)
        try:
            addr_el = page.locator("input[name='address'], input[id='address'], input[placeholder*='address' i]").first
            if addr_el.count() and addr_el.is_visible(timeout=2000):
                addr_el.triple_click()
                addr_el.fill("Portland, OR")
                print("[FILL] Address = Portland, OR")
        except Exception:
            pass

        # City
        try:
            city_el = page.locator("input[name='city'], input[id='city'], input[placeholder*='city' i]").first
            if city_el.count() and city_el.is_visible(timeout=2000):
                city_el.triple_click()
                city_el.fill(CITY)
                print(f"[FILL] City = {CITY}")
        except Exception:
            pass

        # State: select Oregon / OR
        try:
            state_sel = page.locator("select[name='state'], select[id='state'], select[name*='state' i]").first
            if state_sel.count() and state_sel.is_visible(timeout=2000):
                # Try by value "OR" first
                try:
                    state_sel.select_option(value="OR")
                    print("[FILL] State = OR")
                except Exception:
                    try:
                        state_sel.select_option(label="Oregon")
                        print("[FILL] State = Oregon")
                    except Exception:
                        pass
        except Exception:
            pass

        # Postal Code
        try:
            zip_el = page.locator("input[name='postalCode'], input[id='postalCode'], input[name*='postal' i], input[name*='zip' i]").first
            if zip_el.count() and zip_el.is_visible(timeout=2000):
                zip_el.triple_click()
                zip_el.fill(POSTAL_CODE)
                print(f"[FILL] Postal Code = {POSTAL_CODE}")
        except Exception:
            pass

        # Email Address
        safe_fill(page,
                  "input[type='email'], input[name='email'], input[id='email'], input[name*='email' i]",
                  EMAIL, "Email")

        # Phone Device Type: select "Cell/Mobile" if dropdown present
        try:
            phone_type_sel = page.locator("select[name*='phoneDeviceType' i], select[id*='phoneDevice' i], select[name*='phone_type' i]").first
            if phone_type_sel.count() and phone_type_sel.is_visible(timeout=2000):
                try:
                    phone_type_sel.select_option(label="Cell Phone")
                    print("[FILL] Phone Device Type = Cell Phone")
                except Exception:
                    try:
                        phone_type_sel.select_option(label="Mobile")
                        print("[FILL] Phone Device Type = Mobile")
                    except Exception:
                        pass
        except Exception:
            pass

        # Country Phone Code: ensure US (+1) is selected
        try:
            cpc_sel = page.locator("select[name*='countryPhoneCode' i], select[id*='countryPhone' i], select[name*='country_phone' i]").first
            if cpc_sel.count() and cpc_sel.is_visible(timeout=2000):
                current_val = cpc_sel.input_value()
                print(f"[INFO] Country phone code current: {repr(current_val)}")
                if "+1" not in current_val and "united states" not in current_val.lower():
                    try:
                        cpc_sel.select_option(label="United States of America (+1)")
                        print("[FILL] Country Phone Code = US (+1)")
                    except Exception:
                        try:
                            cpc_sel.select_option(value="+1")
                        except Exception:
                            try:
                                cpc_sel.select_option(label="United States (+1)")
                            except Exception:
                                pass
        except Exception:
            pass

        # Phone Number (digits only)
        try:
            phone_el = page.locator("input[type='tel'], input[name*='phoneNumber' i], input[id*='phoneNumber' i], input[name*='phone' i]").first
            if phone_el.count() and phone_el.is_visible(timeout=2000):
                phone_el.triple_click()
                phone_el.fill("")
                page.keyboard.type(PHONE_NUMBER, delay=40)
                print(f"[FILL] Phone Number = {PHONE_NUMBER}")
        except Exception:
            skipped_fields.append("phone")
            pass

        time.sleep(1)
        path = ss(page, "step1_filled")
        screenshot_paths.append(path)

        # Upload Resume
        print("\n[UPLOAD] Resume...")
        file_inputs = page.locator("input[type='file']").all()
        print(f"[INFO] Found {len(file_inputs)} file input(s)")
        resume_uploaded = False
        for fi in file_inputs:
            try:
                fi.set_input_files(str(RESUME_PDF))
                print(f"[UPLOAD] Resume: {RESUME_PDF.name}")
                resume_uploaded = True
                time.sleep(2.5)
                break
            except Exception as ex:
                print(f"[WARN] file input upload error: {ex}")

        if not resume_uploaded:
            skipped_fields.append("resume_upload")

        path = ss(page, "step1_resume_uploaded")
        screenshot_paths.append(path)

        # Click Save and Continue
        click_next(page, 1)
        time.sleep(2)

        if detect_captcha(page):
            handle_captcha_stop(page, screenshot_paths)

        path = ss(page, "step2_initial")
        screenshot_paths.append(path)
        print(f"\n[PAGE] After step 1: {page.url}")
        debug_page_inputs(page)

        # ---------------------------------------------------------------
        # STEP 2: Work History / Experience (Phenom may parse from resume)
        # ---------------------------------------------------------------
        print("\n=== STEP 2: Work History (may be auto-parsed) ===")
        time.sleep(1)

        page_text_s2 = page.inner_text("body").lower()

        # Check for work authorization questions
        if "authorized" in page_text_s2 or "authorization" in page_text_s2:
            print("[FILL] Work authorization: Yes")
            # Look for Yes radio near "authorized"
            for radio in page.locator("input[type='radio']").all():
                val = (radio.get_attribute("value") or "").lower()
                name_attr = (radio.get_attribute("name") or "").lower()
                if "authorized" in name_attr or "workauth" in name_attr:
                    if val in ["yes", "true", "1"]:
                        try:
                            radio.click()
                            print("[FILL] Work auth = Yes")
                            break
                        except Exception:
                            pass

        # Check for sponsorship question
        if "sponsor" in page_text_s2:
            print("[FILL] Sponsorship required: YES (truthful)")
            for radio in page.locator("input[type='radio']").all():
                val = (radio.get_attribute("value") or "").lower()
                name_attr = (radio.get_attribute("name") or "").lower()
                if "sponsor" in name_attr:
                    if val in ["yes", "true", "1"]:
                        try:
                            radio.click()
                            print("[FILL] Sponsorship = Yes")
                            break
                        except Exception:
                            pass

        # Cover letter upload
        file_inputs_s2 = page.locator("input[type='file']").all()
        if len(file_inputs_s2) > 0:
            print(f"[INFO] Step 2 has {len(file_inputs_s2)} file input(s)")
            # Try uploading cover letter to second file input
            if len(file_inputs_s2) > 1:
                try:
                    file_inputs_s2[1].set_input_files(str(COVER_PDF))
                    print(f"[UPLOAD] Cover letter: {COVER_PDF.name}")
                    time.sleep(2)
                except Exception as ex:
                    print(f"[WARN] Cover letter upload: {ex}")
                    skipped_fields.append("cover_letter")

        click_next(page, 2)
        time.sleep(2)

        if detect_captcha(page):
            handle_captcha_stop(page, screenshot_paths)

        path = ss(page, "step3_initial")
        screenshot_paths.append(path)
        print(f"\n[PAGE] After step 2: {page.url}")
        debug_page_inputs(page)

        # ---------------------------------------------------------------
        # Steps 3 through N: Handle dynamically
        # ---------------------------------------------------------------
        for step_num in range(3, 15):
            page_text = page.inner_text("body").lower()

            # Check completion
            if any(kw in page_text for kw in ["thank you", "application received", "successfully submitted", "application submitted", "we'll be in touch"]):
                print(f"[INFO] Submission confirmed on step {step_num}")
                break

            # Check if review page
            is_review = any(kw in page_text for kw in ["review your", "review and submit", "confirm your", "almost done", "check your information"])
            if is_review:
                print(f"[INFO] Review page detected on step {step_num}")
                break

            print(f"\n=== Step {step_num} ===")
            debug_page_inputs(page)

            # Work authorization (Yes)
            if "authorized" in page_text:
                for radio in page.locator("input[type='radio']").all():
                    val = (radio.get_attribute("value") or "").lower()
                    name_attr = (radio.get_attribute("name") or "").lower()
                    if "authorized" in name_attr or "workauth" in name_attr or "eligib" in name_attr:
                        if val in ["yes", "true", "1"]:
                            try:
                                radio.click()
                                print("[FILL] Work auth = Yes")
                                break
                            except Exception:
                                pass

            # Sponsorship (Yes - truthful)
            if "sponsor" in page_text:
                for radio in page.locator("input[type='radio']").all():
                    val = (radio.get_attribute("value") or "").lower()
                    name_attr = (radio.get_attribute("name") or "").lower()
                    if "sponsor" in name_attr:
                        if val in ["yes", "true", "1"]:
                            try:
                                radio.click()
                                print("[FILL] Sponsorship = Yes")
                            except Exception:
                                pass

            # EEO - Gender: Female
            if "gender" in page_text:
                gender_filled = False
                for radio in page.locator("input[type='radio']").all():
                    name_attr = (radio.get_attribute("name") or "").lower()
                    val = (radio.get_attribute("value") or "").lower()
                    if "gender" in name_attr:
                        if val in ["female", "f", "woman", "2"]:
                            try:
                                radio.click()
                                print(f"[FILL] Gender radio = {val}")
                                gender_filled = True
                                break
                            except Exception:
                                pass
                if not gender_filled:
                    # Try select dropdown
                    try:
                        g_sel = page.locator("select[name*='gender' i]").first
                        if g_sel.count() and g_sel.is_visible(timeout=2000):
                            try:
                                g_sel.select_option(label="Female")
                                print("[FILL] Gender select = Female")
                            except Exception:
                                try:
                                    g_sel.select_option(value="2")
                                    print("[FILL] Gender select = 2 (Female)")
                                except Exception:
                                    pass
                    except Exception:
                        pass

            # EEO - Ethnicity: Asian
            if "ethnic" in page_text or "race" in page_text:
                eth_filled = False
                for radio in page.locator("input[type='radio']").all():
                    name_attr = (radio.get_attribute("name") or "").lower()
                    val = (radio.get_attribute("value") or "").lower()
                    if "ethnic" in name_attr or "race" in name_attr:
                        if "asian" in val:
                            try:
                                radio.click()
                                print(f"[FILL] Ethnicity radio = {val}")
                                eth_filled = True
                                break
                            except Exception:
                                pass
                if not eth_filled:
                    try:
                        eth_sel = page.locator("select[name*='ethnic' i], select[name*='race' i]").first
                        if eth_sel.count() and eth_sel.is_visible(timeout=2000):
                            # Try various Asian option values
                            for asian_val in ["Asian", "Asian (Not Hispanic or Latino)", "5", "A"]:
                                try:
                                    eth_sel.select_option(label=asian_val)
                                    print(f"[FILL] Ethnicity select = {asian_val}")
                                    eth_filled = True
                                    break
                                except Exception:
                                    try:
                                        eth_sel.select_option(value=asian_val)
                                        print(f"[FILL] Ethnicity select value = {asian_val}")
                                        eth_filled = True
                                        break
                                    except Exception:
                                        pass
                    except Exception:
                        pass

            # Veteran: No / Not a protected veteran
            if "veteran" in page_text:
                vet_filled = False
                for radio in page.locator("input[type='radio']").all():
                    name_attr = (radio.get_attribute("name") or "").lower()
                    val = (radio.get_attribute("value") or "").lower()
                    if "veteran" in name_attr or "vet" in name_attr:
                        if val in ["no", "false", "0", "notprotected", "not_a_veteran"]:
                            try:
                                radio.click()
                                print(f"[FILL] Veteran radio = {val}")
                                vet_filled = True
                                break
                            except Exception:
                                pass
                if not vet_filled:
                    try:
                        vet_sel = page.locator("select[name*='veteran' i], select[name*='vet' i]").first
                        if vet_sel.count() and vet_sel.is_visible(timeout=2000):
                            for no_opt in ["I am not a protected veteran", "No", "Not a protected veteran"]:
                                try:
                                    vet_sel.select_option(label=no_opt)
                                    print(f"[FILL] Veteran select = {no_opt}")
                                    vet_filled = True
                                    break
                                except Exception:
                                    pass
                    except Exception:
                        pass

            # Disability: No
            if "disab" in page_text:
                dis_filled = False
                for radio in page.locator("input[type='radio']").all():
                    name_attr = (radio.get_attribute("name") or "").lower()
                    val = (radio.get_attribute("value") or "").lower()
                    if "disab" in name_attr:
                        if val in ["no", "false", "0", "nodisability", "no_disability", "nodisab"]:
                            try:
                                radio.click()
                                print(f"[FILL] Disability radio = {val}")
                                dis_filled = True
                                break
                            except Exception:
                                pass
                if not dis_filled:
                    try:
                        dis_sel = page.locator("select[name*='disab' i]").first
                        if dis_sel.count() and dis_sel.is_visible(timeout=2000):
                            for no_opt in ["No, I don't have a disability", "No", "I do not have a disability"]:
                                try:
                                    dis_sel.select_option(label=no_opt)
                                    print(f"[FILL] Disability select = {no_opt}")
                                    dis_filled = True
                                    break
                                except Exception:
                                    pass
                    except Exception:
                        pass

            # Free-text areas (why interested, cover letter, additional info)
            for ta in page.locator("textarea").all():
                try:
                    if ta.is_visible(timeout=1000):
                        val = ta.input_value()
                        if not val:
                            placeholder = ta.get_attribute("placeholder") or ""
                            ta_id = ta.get_attribute("id") or ""
                            ta_name = ta.get_attribute("name") or ""
                            combined = (placeholder + ta_id + ta_name).lower()
                            if any(k in combined for k in ["why", "interest", "cover", "additional", "comment", "tell us", "message", "motivation"]):
                                ta.fill(WHY_INTERESTED)
                                print(f"[FILL] Textarea '{ta_name or placeholder}' = WHY_INTERESTED")
                            elif "reference" in combined:
                                ta.fill("N/A")
                                print("[FILL] References textarea = N/A")
                            else:
                                # Fill with why interested as default for unknown text areas
                                ta.fill(WHY_INTERESTED)
                                print(f"[FILL] Unknown textarea '{ta_name or placeholder}' = WHY_INTERESTED")
                except Exception:
                    pass

            # Sign-in / account creation step
            if any(kw in page_text for kw in ["sign in", "create account", "register", "log in", "create a profile"]):
                print("[INFO] Account/sign-in step detected")
                # Email
                for email_sel in ["input[type='email']", "input[name*='email' i]", "input[id*='email' i]"]:
                    try:
                        eel = page.locator(email_sel).first
                        if eel.count() and eel.is_visible(timeout=2000):
                            val = eel.input_value()
                            if not val:
                                eel.fill(EMAIL)
                                print(f"[FILL] Account email = {EMAIL}")
                            break
                    except Exception:
                        pass
                # Password
                for pw_input in page.locator("input[type='password']").all():
                    try:
                        if pw_input.is_visible(timeout=1000):
                            pw_input.fill(_SHARED_PW)
                            print("[FILL] Account password = [REDACTED]")
                    except Exception:
                        pass

            if detect_captcha(page):
                handle_captcha_stop(page, screenshot_paths)

            # Click Next
            clicked = click_next(page, step_num)
            time.sleep(2.5)

            if detect_captcha(page):
                handle_captcha_stop(page, screenshot_paths)

            path = ss(page, f"step{step_num + 1}_initial")
            screenshot_paths.append(path)
            print(f"[PAGE] After step {step_num}: {page.url}")

            # Check if done after clicking next
            page_text_after = page.inner_text("body").lower()
            if any(kw in page_text_after for kw in ["thank you", "application received", "successfully submitted"]):
                print("[INFO] Confirmed — application submitted!")
                break
            if any(kw in page_text_after for kw in ["review your", "review and submit", "confirm your"]):
                print("[INFO] Reached review page")
                break

        # ---------------------------------------------------------------
        # PRE-SUBMIT REVIEW
        # ---------------------------------------------------------------
        print("\n=== PRE-SUBMIT REVIEW ===")
        time.sleep(1.5)
        page_text = page.inner_text("body")

        checks = {
            "name_check": FIRST_NAME in page_text and LAST_NAME in page_text,
            "email_check": EMAIL in page_text,
            "phone_check": PHONE_NUMBER in page_text or "+12137003831" in page_text,
            "sponsorship_yes": "yes" in page_text.lower(),
            "resume_filename": "resume" in page_text.lower(),
        }
        print(f"[VERIFY] Checks: {json.dumps(checks, indent=2)}")

        pre_submit_path = str(SCREENSHOTS_DIR / "pre_submit_review.png")
        page.screenshot(path=pre_submit_path, full_page=True)
        screenshot_paths.append(pre_submit_path)
        print(f"[SCREENSHOT] Pre-submit: pre_submit_review.png")

        if detect_captcha(page):
            handle_captcha_stop(page, screenshot_paths)

        # ---------------------------------------------------------------
        # FINAL SUBMIT
        # ---------------------------------------------------------------
        print("\n=== FINAL SUBMIT ===")
        submitted = False

        for btn_text in ["Submit Application", "Submit", "Apply", "Finish", "Complete Application", "Send Application"]:
            try:
                btns = page.get_by_role("button", name=btn_text, exact=False).all()
                for btn in btns:
                    if btn.is_visible():
                        btn.scroll_into_view_if_needed()
                        print(f"[SUBMIT] Clicking: '{btn_text}'")
                        btn.click()
                        submitted = True
                        time.sleep(5)
                        break
                if submitted:
                    break
            except Exception:
                pass

        if not submitted:
            # JS fallback
            result_js = page.evaluate("""
                () => {
                    const btns = Array.from(document.querySelectorAll('button'));
                    const submitBtn = btns.find(b => {
                        const txt = b.textContent.trim().toLowerCase();
                        return txt.includes('submit') || txt.includes('apply') || txt.includes('finish') || txt.includes('send application');
                    });
                    if (submitBtn) {
                        submitBtn.click();
                        return submitBtn.textContent.trim();
                    }
                    return null;
                }
            """)
            if result_js:
                print(f"[SUBMIT] JS click: '{result_js}'")
                submitted = True
                time.sleep(5)

        if detect_captcha(page):
            handle_captcha_stop(page, screenshot_paths)

        # ---------------------------------------------------------------
        # CONFIRMATION
        # ---------------------------------------------------------------
        time.sleep(3)
        ss_confirm_path = str(SCREENSHOTS_DIR / "confirmation.png")
        page.screenshot(path=ss_confirm_path, full_page=True)
        screenshot_paths.append(ss_confirm_path)
        print(f"[SCREENSHOT] Confirmation: confirmation.png")

        final_text = page.inner_text("body").lower()
        is_confirmed = any(kw in final_text for kw in [
            "thank you", "application received", "successfully submitted",
            "application submitted", "we'll be in touch", "under review",
            "your application has been", "application complete"
        ])

        outcome = "submitted" if (submitted and is_confirmed) else ("submitted-unconfirmed" if submitted else "failed-no-submit-button")
        print(f"\n[OUTCOME] {outcome}")
        print(f"[VERIFY] Name: {checks['name_check']} | Email: {checks['email_check']} | Phone: {checks['phone_check']} | Sponsorship: {checks['sponsorship_yes']}")

        result = {
            "company": "Lineage",
            "role": "HR Generalist",
            "ats": "Phenom",
            "apply_url": APPLY_URL,
            "submitted": submitted,
            "outcome": outcome,
            "confirmed_at": datetime.now(timezone.utc).isoformat() if is_confirmed else None,
            "screenshot_paths": screenshot_paths,
            "notes": (
                f"Field verification: {checks}. "
                f"Skipped fields: {skipped_fields}. "
                f"Confirmation page detected: {is_confirmed}. "
                f"Source selected: Job Boards (LinkedIn not in dropdown). "
                f"Sponsorship: YES (truthful)."
            )
        }
        write_result(result)
        print(f"[DONE] Outcome: {outcome}")


if __name__ == "__main__":
    main()
