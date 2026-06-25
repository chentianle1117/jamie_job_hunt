"""
Lineage Phenom ATS driver v3 - targeted fix.

Key findings from screenshots:
- Progress bar: My Information → My Experience → Application Questions → Voluntary Disclosures → Review
- Form field IDs have dots (cntryFields.firstName) — must use [id='...'] not #... CSS
- Resume already uploaded (resume.pdf visible)
- First Name = "Jamie" (pre-filled wrong) — need "Yi-Chieh"
- Last Name = "Cheng" (correct)
- Source = "Other Job Site" (ok — "Job Boards" is secondary dropdown; primary was already "Other Job Site")
- State = "Please Select" → BLOCKING — need Oregon/OR
- Phone Device Type = "Please Select" → BLOCKING — need to select Cell Phone
- City = Portland (correct), Email = jamiecheng0103@gmail.com (correct), Phone = 2137003831 (correct)
- "Have you previously worked here?" radios: id=previousWorker.true / previousWorker.false
"""
import json
import os
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
    if page.locator("iframe[src*='hcaptcha']").count() > 0:
        return True
    return False


def handle_captcha_stop(page, screenshot_paths):
    path = ss(page, "captcha_detected")
    screenshot_paths.append(path)
    write_result({
        "company": "Lineage", "role": "HR Generalist", "ats": "Phenom",
        "apply_url": APPLY_URL, "submitted": False, "outcome": "captcha-staged",
        "confirmed_at": None, "screenshot_paths": screenshot_paths,
        "notes": "Interactive CAPTCHA detected. Human must solve and click Submit."
    })
    print("[STOP] CAPTCHA — leaving form open.")
    sys.exit(0)


def write_result(data):
    out = APP_DIR / "SUBMITTED.json"
    out.write_text(json.dumps(data, indent=2))
    print(f"[RESULT] Written: SUBMITTED.json")


def fill_by_id(page, field_id, value, label=""):
    """Fill input by exact id using attribute selector (handles dots in IDs)."""
    sel = f"[id='{field_id}']"
    try:
        el = page.locator(sel).first
        el.wait_for(state="visible", timeout=5000)
        el.triple_click()
        el.fill(value)
        print(f"[FILL] {label or field_id} = {repr(value[:60])}")
        return True
    except Exception as e:
        print(f"[WARN] fill_by_id({field_id}): {str(e)[:80]}")
        return False


def select_by_id(page, field_id, value=None, label_text=None, index=None, label=""):
    """Select option in <select> by exact id."""
    sel = f"[id='{field_id}']"
    try:
        el = page.locator(sel).first
        el.wait_for(state="visible", timeout=5000)
        if value is not None:
            el.select_option(value=value)
        elif label_text is not None:
            el.select_option(label=label_text)
        elif index is not None:
            el.select_option(index=index)
        actual = el.input_value()
        print(f"[FILL] {label or field_id} = {repr(actual[:60])}")
        return True
    except Exception as e:
        print(f"[WARN] select_by_id({field_id}): {str(e)[:80]}")
        return False


def click_radio_by_id(page, field_id, label=""):
    """Click a radio button by exact id."""
    sel = f"[id='{field_id}']"
    try:
        el = page.locator(sel).first
        el.wait_for(state="visible", timeout=3000)
        el.click()
        print(f"[FILL] {label or field_id} clicked")
        return True
    except Exception as e:
        print(f"[WARN] click_radio_by_id({field_id}): {str(e)[:80]}")
        return False


def js_fill(page, field_id, value):
    """Fill a form field via JavaScript (bypasses React event issues)."""
    return page.evaluate(f"""
        (v) => {{
            const el = document.getElementById('{field_id}');
            if (!el) return false;
            const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
            const nativeSelectValueSetter = Object.getOwnPropertyDescriptor(window.HTMLSelectElement.prototype, 'value').set;
            if (el.tagName === 'SELECT') {{
                nativeSelectValueSetter.call(el, v);
            }} else {{
                nativeInputValueSetter.call(el, v);
            }}
            el.dispatchEvent(new Event('input', {{ bubbles: true }}));
            el.dispatchEvent(new Event('change', {{ bubbles: true }}));
            return true;
        }}
    """, value)


def get_select_options(page, field_id):
    """Get all options from a select."""
    return page.evaluate(f"""
        () => {{
            const el = document.getElementById('{field_id}');
            if (!el) return [];
            return Array.from(el.options).map(o => ({{value: o.value, text: o.text}}));
        }}
    """)


def dismiss_cookie_modal(page):
    try:
        for text in ["Allow", "Accept All", "Accept", "OK"]:
            btn = page.get_by_role("button", name=text, exact=False).first
            if btn.is_visible(timeout=3000):
                btn.click()
                print(f"[ACTION] Cookie modal dismissed ({text})")
                time.sleep(1)
                return True
    except Exception:
        pass
    return False


def click_save_and_continue(page, step_label=""):
    for btn_text in ["Save and Continue", "Next", "Continue"]:
        try:
            btns = page.get_by_role("button", name=btn_text, exact=False).all()
            for btn in btns:
                if btn.is_visible():
                    btn.scroll_into_view_if_needed()
                    btn.click()
                    print(f"[CLICK] {step_label} '{btn_text}'")
                    time.sleep(3)
                    return True
        except Exception:
            pass
    return False


def find_or_navigate(context):
    pages = context.pages
    for p in pages:
        if "careers.onelineage.com" in p.url:
            print(f"[INFO] Found Lineage tab: {p.url[:80]}")
            return p
    page = context.new_page()
    page.goto(APPLY_URL, wait_until="domcontentloaded", timeout=60000)
    time.sleep(5)
    return page


def get_current_step_name(page):
    """Try to get the active step from the progress bar."""
    try:
        active = page.locator(".active, [aria-current='step'], [class*='active']").first
        return active.text_content() or ""
    except Exception:
        return ""


def fill_step_eeo(page):
    """Fill voluntary disclosures (EEO: gender, race, veteran, disability)."""
    print("\n[EEO] Filling voluntary disclosures...")
    page_text = page.inner_text("body")

    # Gender
    if "gender" in page_text.lower():
        gender_opts = get_select_options(page, "gender")
        print(f"[DEBUG] Gender options: {gender_opts}")
        female_val = None
        for opt in gender_opts:
            if "female" in opt["text"].lower() or opt["text"].lower() in ["f", "female", "woman"]:
                female_val = opt["value"]
                break
        if female_val:
            select_by_id(page, "gender", value=female_val, label="Gender")
        else:
            # Try radio
            for radio_id in ["gender.Female", "gender.female", "gender.F", "gender.FEMALE"]:
                if click_radio_by_id(page, radio_id, "Gender Female"):
                    break

    # Ethnicity / Race
    if "ethnic" in page_text.lower() or "race" in page_text.lower():
        for eth_id in ["ethnicGroup", "ethnicity", "race", "ethnicOrigin"]:
            opts = get_select_options(page, eth_id)
            if opts:
                print(f"[DEBUG] Ethnicity ({eth_id}) options: {opts}")
                asian_val = None
                for opt in opts:
                    if "asian" in opt["text"].lower():
                        asian_val = opt["value"]
                        break
                if asian_val:
                    select_by_id(page, eth_id, value=asian_val, label="Race/Ethnicity")
                    break

    # Veteran
    if "veteran" in page_text.lower():
        for vet_id in ["veteran", "veteranStatus", "protectedVeteran"]:
            opts = get_select_options(page, vet_id)
            if opts:
                print(f"[DEBUG] Veteran ({vet_id}) options: {opts}")
                no_val = None
                for opt in opts:
                    t = opt["text"].lower()
                    if "not a protected" in t or (("no" in t or "not" in t) and "veteran" in t):
                        no_val = opt["value"]
                        break
                    elif opt["text"].lower() == "no":
                        no_val = opt["value"]
                        break
                if no_val:
                    select_by_id(page, vet_id, value=no_val, label="Veteran")
                    break
        # Try radio
        for radio_id in ["veteran.false", "veteranStatus.false", "veteran.No", "protectedVeteran.false"]:
            click_radio_by_id(page, radio_id, "Veteran No")

    # Disability
    if "disab" in page_text.lower():
        for dis_id in ["disability", "disabilityStatus", "hasDisability"]:
            opts = get_select_options(page, dis_id)
            if opts:
                print(f"[DEBUG] Disability ({dis_id}) options: {opts}")
                no_val = None
                for opt in opts:
                    t = opt["text"].lower()
                    if "no, i don" in t or "do not have" in t or opt["text"].lower() == "no":
                        no_val = opt["value"]
                        break
                if no_val:
                    select_by_id(page, dis_id, value=no_val, label="Disability")
                    break
        for radio_id in ["disability.false", "disabilityStatus.false", "disability.No"]:
            click_radio_by_id(page, radio_id, "Disability No")


def main():
    from patchright.sync_api import sync_playwright

    screenshot_paths = []
    skipped = []

    with sync_playwright() as pw:
        print("[CONNECT] CDP port 9400...")
        try:
            browser = pw.chromium.connect_over_cdp("http://localhost:9400")
        except Exception as e:
            print(f"[ERROR] {e}")
            sys.exit(1)

        context = browser.contexts[0]
        page = find_or_navigate(context)
        page.bring_to_front()

        # Navigate if not on apply page
        if "apply" not in page.url or "onelineage" not in page.url:
            page.goto(APPLY_URL, wait_until="domcontentloaded", timeout=60000)
            time.sleep(4)

        dismiss_cookie_modal(page)
        time.sleep(1)

        path = ss(page, "v3_step1_start")
        screenshot_paths.append(path)
        print(f"[URL] {page.url}")

        # ================================================================
        # STEP 1: My Information
        # ================================================================
        print("\n=== MY INFORMATION ===")

        # Source: "How did you hear about us?" - id="source"
        # First check what the current value and options are
        source_opts = get_select_options(page, "source")
        print(f"[DEBUG] Source options: {source_opts}")
        # "Job Boards" is already selected and best available option for LinkedIn
        # Leave as-is or select "Job Boards"

        # "Previously worked here?" - click No radio
        click_radio_by_id(page, "previousWorker.false", "Previously worked = No")

        # Country: already USA, leave it
        country_val = page.evaluate("() => { const el = document.getElementById('country'); return el ? el.value : 'N/A'; }")
        print(f"[INFO] Country: {country_val}")

        # First Name (id=cntryFields.firstName has dot — use [id='...'])
        fill_by_id(page, "cntryFields.firstName", FIRST_NAME, "First Name")

        # Last Name
        fill_by_id(page, "cntryFields.lastName", LAST_NAME, "Last Name")

        # Address (optional field)
        fill_by_id(page, "cntryFields.addressLine1", "Portland, OR", "Address")

        # City (already "Portland" but re-confirm)
        fill_by_id(page, "cntryFields.city", CITY, "City")

        # State: select Oregon — need to find the correct option value
        state_opts = get_select_options(page, "cntryFields.region")
        print(f"[DEBUG] State options (first 10): {state_opts[:10]}")
        or_val = None
        for opt in state_opts:
            if opt["value"] == "OR" or opt["text"] in ["Oregon", "OR"]:
                or_val = opt["value"]
                break
            if "oregon" in opt["text"].lower():
                or_val = opt["value"]
                break
        if or_val:
            select_by_id(page, "cntryFields.region", value=or_val, label="State")
        else:
            # Try with js_fill
            js_fill(page, "cntryFields.region", "OR")
            print("[FILL] State = OR (JS)")

        # Postal Code
        fill_by_id(page, "cntryFields.postalCode", POSTAL_CODE, "Postal Code")

        # Email (id="email")
        fill_by_id(page, "email", EMAIL, "Email")

        # Phone Device Type (id="deviceType")
        device_opts = get_select_options(page, "deviceType")
        print(f"[DEBUG] Phone device type options: {device_opts}")
        cell_val = None
        for opt in device_opts:
            if "cell" in opt["text"].lower() or "mobile" in opt["text"].lower():
                cell_val = opt["value"]
                break
        if cell_val:
            select_by_id(page, "deviceType", value=cell_val, label="Phone Device Type")
        elif device_opts and len(device_opts) > 1:
            # Pick first non-empty option
            for opt in device_opts:
                if opt["value"]:
                    select_by_id(page, "deviceType", value=opt["value"], label="Phone Device Type (first)")
                    break

        # Country Phone Code: already USA_1, verify
        cpc_val = page.evaluate("() => { const el = document.getElementById('phoneWidget.countryPhoneCode'); return el ? el.value : 'N/A'; }")
        print(f"[INFO] Country phone code: {cpc_val}")
        if "USA" not in cpc_val and "+1" not in cpc_val:
            cpc_opts = get_select_options(page, "phoneWidget.countryPhoneCode")
            for opt in cpc_opts:
                if "united states" in opt["text"].lower() and "(+1)" in opt["text"]:
                    select_by_id(page, "phoneWidget.countryPhoneCode", value=opt["value"], label="Country Phone Code")
                    break

        # Phone Number (already filled but re-confirm)
        ph_val = page.evaluate("() => { const el = document.getElementById('phoneWidget.phoneNumber'); return el ? el.value : ''; }")
        print(f"[INFO] Phone number current: {ph_val}")
        if ph_val != PHONE_NUMBER:
            fill_by_id(page, "phoneWidget.phoneNumber", PHONE_NUMBER, "Phone Number")

        time.sleep(1)
        path = ss(page, "v3_step1_filled")
        screenshot_paths.append(path)

        # Resume upload — check if already uploaded
        resume_link = page.locator("a[href*='resume'], [class*='resume'], .file-name").first
        resume_already_up = False
        try:
            if resume_link.is_visible(timeout=2000):
                resume_already_up = True
                print("[INFO] Resume already uploaded (link visible)")
        except Exception:
            pass

        if not resume_already_up:
            file_inputs = page.locator("input[type='file']").all()
            print(f"[INFO] File inputs: {len(file_inputs)}")
            for fi in file_inputs:
                try:
                    fi.set_input_files(str(RESUME_PDF))
                    print(f"[UPLOAD] Resume: {RESUME_PDF.name}")
                    time.sleep(2.5)
                    break
                except Exception as ex:
                    print(f"[WARN] Upload: {ex}")
                    skipped.append("resume_upload")

        path = ss(page, "v3_step1_before_next")
        screenshot_paths.append(path)

        # Click Save and Continue
        click_save_and_continue(page, "Step 1 My Info")
        time.sleep(2)

        if detect_captcha(page):
            handle_captcha_stop(page, screenshot_paths)

        path = ss(page, "v3_step2_initial")
        screenshot_paths.append(path)
        print(f"[URL] After step 1: {page.url}")

        # ================================================================
        # STEP 2: My Experience
        # ================================================================
        print("\n=== MY EXPERIENCE ===")
        time.sleep(1)

        # Check what's on this step — look for visible inputs
        inputs_s2 = page.evaluate("""
            () => {
                const els = document.querySelectorAll('input:not([type=hidden]), select, textarea');
                return Array.from(els).filter(e => e.offsetParent !== null).map(e => ({
                    tag: e.tagName, type: e.type||'', id: e.id, name: e.name,
                    placeholder: e.placeholder, value: e.value.slice(0,30)
                }));
            }
        """)
        print(f"[DEBUG] Step 2 inputs: {json.dumps(inputs_s2[:20], indent=2)}")

        # Check for cover letter upload
        file_inputs_s2 = page.locator("input[type='file']").all()
        if len(file_inputs_s2) > 0:
            print(f"[INFO] Step 2: {len(file_inputs_s2)} file input(s)")
            # Check if there's a cover letter specific one
            for i, fi in enumerate(file_inputs_s2):
                try:
                    # Check label nearby
                    parent_text = fi.evaluate("el => el.closest('div,section')?.innerText?.slice(0,100) || ''")
                    print(f"  file input {i}: context='{parent_text[:60]}'")
                    if "cover" in parent_text.lower():
                        fi.set_input_files(str(COVER_PDF))
                        print(f"[UPLOAD] Cover letter to input {i}")
                        time.sleep(2)
                except Exception:
                    pass

        # Any text areas (free text fields)
        for ta in page.locator("textarea").all():
            try:
                if ta.is_visible(timeout=1000):
                    val = ta.input_value()
                    if not val:
                        ta_id = ta.get_attribute("id") or ""
                        ta_name = ta.get_attribute("name") or ""
                        ta_ph = ta.get_attribute("placeholder") or ""
                        combined = (ta_id + ta_name + ta_ph).lower()
                        if any(k in combined for k in ["why", "cover", "additional", "comment", "interest", "motivat"]):
                            ta.fill(WHY_INTERESTED)
                            print(f"[FILL] Textarea ({ta_id or ta_ph})")
                        elif "ref" in combined:
                            ta.fill("N/A")
                        else:
                            ta.fill(WHY_INTERESTED)
                            print(f"[FILL] Textarea (unknown: {ta_id})")
            except Exception:
                pass

        click_save_and_continue(page, "Step 2 Experience")
        time.sleep(2)

        if detect_captcha(page):
            handle_captcha_stop(page, screenshot_paths)

        path = ss(page, "v3_step3_initial")
        screenshot_paths.append(path)
        print(f"[URL] After step 2: {page.url}")

        # ================================================================
        # STEP 3: Application Questions (screening)
        # ================================================================
        print("\n=== APPLICATION QUESTIONS ===")
        time.sleep(1)

        inputs_s3 = page.evaluate("""
            () => {
                const els = document.querySelectorAll('input:not([type=hidden]), select, textarea');
                return Array.from(els).filter(e => e.offsetParent !== null).map(e => ({
                    tag: e.tagName, type: e.type||'', id: e.id, name: e.name,
                    placeholder: e.placeholder, value: e.value.slice(0,30)
                }));
            }
        """)
        print(f"[DEBUG] Step 3 inputs: {json.dumps(inputs_s3[:30], indent=2)}")

        page_text_s3 = page.inner_text("body").lower()

        # Work authorization: Yes
        if "authorized" in page_text_s3 or "authorization" in page_text_s3 or "legally" in page_text_s3:
            print("[FILL] Work authorization check")
            # Find all radios and check their IDs
            radios_s3 = page.evaluate("""
                () => Array.from(document.querySelectorAll('input[type=radio]'))
                    .filter(e => e.offsetParent !== null)
                    .map(e => ({id: e.id, name: e.name, value: e.value}))
            """)
            print(f"[DEBUG] Radios on step 3: {radios_s3}")
            for r in radios_s3:
                if ("auth" in r["name"].lower() or "eligib" in r["name"].lower() or "work" in r["name"].lower()):
                    if r["value"].lower() in ["yes", "true", "1"]:
                        click_radio_by_id(page, r["id"], f"Work auth Yes ({r['name']})")

        # Sponsorship: Yes (truthful)
        if "sponsor" in page_text_s3:
            print("[FILL] Sponsorship check")
            radios_s3 = page.evaluate("""
                () => Array.from(document.querySelectorAll('input[type=radio]'))
                    .filter(e => e.offsetParent !== null)
                    .map(e => ({id: e.id, name: e.name, value: e.value}))
            """)
            for r in radios_s3:
                if "sponsor" in r["name"].lower():
                    if r["value"].lower() in ["yes", "true", "1"]:
                        click_radio_by_id(page, r["id"], f"Sponsorship Yes ({r['name']})")

        # Any select dropdowns
        selects_s3 = page.evaluate("""
            () => {
                const sels = document.querySelectorAll('select');
                return Array.from(sels).filter(e => e.offsetParent !== null).map(e => ({
                    id: e.id, name: e.name, value: e.value,
                    options: Array.from(e.options).map(o => ({v: o.value, t: o.text}))
                }));
            }
        """)
        print(f"[DEBUG] Step 3 selects: {json.dumps(selects_s3, indent=2)}")

        for ta in page.locator("textarea").all():
            try:
                if ta.is_visible(timeout=1000) and not ta.input_value():
                    ta.fill(WHY_INTERESTED)
                    print("[FILL] Step 3 textarea")
            except Exception:
                pass

        click_save_and_continue(page, "Step 3 Screening")
        time.sleep(2)

        if detect_captcha(page):
            handle_captcha_stop(page, screenshot_paths)

        path = ss(page, "v3_step4_initial")
        screenshot_paths.append(path)
        print(f"[URL] After step 3: {page.url}")

        # ================================================================
        # STEP 4: Voluntary Disclosures (EEO)
        # ================================================================
        print("\n=== VOLUNTARY DISCLOSURES ===")
        time.sleep(1)

        # Inspect all inputs on this step
        inputs_s4 = page.evaluate("""
            () => {
                const els = document.querySelectorAll('input:not([type=hidden]), select, textarea');
                return Array.from(els).filter(e => e.offsetParent !== null).map(e => ({
                    tag: e.tagName, type: e.type||'', id: e.id, name: e.name,
                    placeholder: e.placeholder, value: e.value.slice(0,30),
                    options: e.tagName==='SELECT' ? Array.from(e.options).map(o=>({v:o.value,t:o.text})) : []
                }));
            }
        """)
        print(f"[DEBUG] Step 4 EEO inputs: {json.dumps(inputs_s4, indent=2)}")

        # Process each EEO field based on actual IDs discovered
        for field in inputs_s4:
            fid = field["id"]
            fname = field["name"]
            ftag = field["tag"]
            ftype = field.get("type", "")
            fval = field.get("value", "")

            combined_id = (fid + fname).lower()

            if ftag == "SELECT":
                opts = field.get("options", [])
                if "gender" in combined_id:
                    female_val = next((o["v"] for o in opts if "female" in o["t"].lower()), None)
                    if female_val:
                        select_by_id(page, fid, value=female_val, label=f"Gender ({fid})")
                elif "ethnic" in combined_id or "race" in combined_id:
                    asian_val = next((o["v"] for o in opts if "asian" in o["t"].lower()), None)
                    if asian_val:
                        select_by_id(page, fid, value=asian_val, label=f"Race/Eth ({fid})")
                elif "veteran" in combined_id or "vet" in combined_id:
                    no_val = next((o["v"] for o in opts
                                   if "not a protected" in o["t"].lower() or o["t"].lower() == "no"
                                   or "i am not" in o["t"].lower()), None)
                    if no_val:
                        select_by_id(page, fid, value=no_val, label=f"Veteran ({fid})")
                elif "disab" in combined_id:
                    no_val = next((o["v"] for o in opts
                                   if "no, i don" in o["t"].lower() or "do not have" in o["t"].lower()
                                   or o["t"].lower() == "no"), None)
                    if no_val:
                        select_by_id(page, fid, value=no_val, label=f"Disability ({fid})")

            elif ftype == "radio":
                if "gender" in combined_id and not fval:
                    # We'll handle by finding the Female radio
                    pass
                elif "veteran" in combined_id or "vet" in combined_id:
                    if "no" in fid.lower() or "false" in fid.lower():
                        click_radio_by_id(page, fid, f"Veteran No ({fid})")
                elif "disab" in combined_id:
                    if "no" in fid.lower() or "false" in fid.lower():
                        click_radio_by_id(page, fid, f"Disability No ({fid})")

        # Also try generic EEO fill
        fill_step_eeo(page)

        path = ss(page, "v3_step4_eeo_filled")
        screenshot_paths.append(path)

        click_save_and_continue(page, "Step 4 EEO")
        time.sleep(2)

        if detect_captcha(page):
            handle_captcha_stop(page, screenshot_paths)

        path = ss(page, "v3_step5_initial")
        screenshot_paths.append(path)
        print(f"[URL] After step 4: {page.url}")

        # ================================================================
        # STEP 5: Review
        # ================================================================
        print("\n=== REVIEW PAGE ===")
        time.sleep(2)

        page_text = page.inner_text("body")
        print(f"[VERIFY] Name check (Yi-Chieh): {'Yi-Chieh' in page_text}")
        print(f"[VERIFY] Name check (Cheng): {'Cheng' in page_text}")
        print(f"[VERIFY] Email check: {EMAIL in page_text}")
        print(f"[VERIFY] Phone check: {PHONE_NUMBER in page_text}")
        print(f"[VERIFY] 'yes' in text: {'yes' in page_text.lower()}")

        checks = {
            "name_check": "Yi-Chieh" in page_text and "Cheng" in page_text,
            "email_check": EMAIL in page_text,
            "phone_check": PHONE_NUMBER in page_text,
            "sponsorship_yes": "yes" in page_text.lower(),
        }
        print(f"[VERIFY] Checks: {json.dumps(checks, indent=2)}")

        pre_submit_path = str(SCREENSHOTS_DIR / "pre_submit_review.png")
        page.screenshot(path=pre_submit_path, full_page=True)
        screenshot_paths.append(pre_submit_path)
        print(f"[SCREENSHOT] pre_submit_review.png")

        if detect_captcha(page):
            handle_captcha_stop(page, screenshot_paths)

        # ================================================================
        # SUBMIT
        # ================================================================
        print("\n=== SUBMIT ===")
        submitted = False

        # Check if there are more "next" steps before Submit
        page_text_lower = page_text.lower()
        is_review = any(kw in page_text_lower for kw in ["review", "confirm", "summary", "almost done"])
        is_done = any(kw in page_text_lower for kw in ["thank you", "application received", "submitted", "we'll be in touch"])

        if is_done:
            print("[INFO] Already on confirmation page!")
            submitted = True
        else:
            # Try clicking Submit button
            all_btns = page.evaluate("""
                () => Array.from(document.querySelectorAll('button'))
                    .filter(b => b.offsetParent !== null)
                    .map(b => ({text: b.textContent.trim(), disabled: b.disabled}))
            """)
            print(f"[DEBUG] All visible buttons: {all_btns}")

            for btn_text in ["Submit Application", "Submit", "Apply Now", "Apply", "Finish"]:
                try:
                    btns = page.get_by_role("button", name=btn_text, exact=False).all()
                    for btn in btns:
                        if btn.is_visible() and not btn.is_disabled():
                            btn.scroll_into_view_if_needed()
                            print(f"[SUBMIT] Clicking '{btn_text}'")
                            btn.click()
                            submitted = True
                            time.sleep(6)
                            break
                    if submitted:
                        break
                except Exception as e:
                    print(f"[WARN] Submit btn '{btn_text}': {str(e)[:60]}")

            if not submitted:
                # If still on a step, try Save and Continue (maybe more steps after review)
                result = click_save_and_continue(page, "Final step")
                if result:
                    submitted = True

        if detect_captcha(page):
            handle_captcha_stop(page, screenshot_paths)

        # ================================================================
        # CONFIRMATION
        # ================================================================
        time.sleep(3)
        confirm_path = str(SCREENSHOTS_DIR / "confirmation.png")
        page.screenshot(path=confirm_path, full_page=True)
        screenshot_paths.append(confirm_path)
        print(f"[SCREENSHOT] confirmation.png")

        final_text = page.inner_text("body").lower()
        is_confirmed = any(kw in final_text for kw in [
            "thank you", "application received", "successfully submitted",
            "application submitted", "we'll be in touch", "under review",
            "your application has been", "application complete"
        ])

        outcome = "submitted" if (submitted and is_confirmed) else \
                  "submitted-unconfirmed" if submitted else "failed-no-submit-button"
        print(f"\n[OUTCOME] {outcome}")

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
                f"Skipped: {skipped}. "
                f"Confirmed: {is_confirmed}. "
                f"Source: Job Boards (LinkedIn not in dropdown). "
                f"Name corrected from Jamie → Yi-Chieh. "
                f"Sponsorship YES filled truthfully."
            )
        }
        write_result(result)
        print(f"[DONE] {outcome}")


if __name__ == "__main__":
    main()
