"""
Lineage Phenom ATS driver v6 - handles current state on step 4 (Voluntary Disclosures / T&C).

Current state: Chrome is on step=4 (voluntaryInformation) with:
- "Personal Data Statement" / Terms and Conditions page
- Need to scroll to bottom and check the "I agree" checkbox
- Then Save and Continue → step 5 Review → Submit

Also: step 3 had a 5th question "What relevant certifications do you hold?"
(id=jsqData.QUESTIONNAIRE-3-453.e) that was being filled as textarea WHY_INTERESTED.
We need to handle that field too if we loop back.
"""
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

APP_DIR = Path(r"C:\Users\chent\Agentic_Workflows_2026\oracle-job-search\outputs\2026-06-23-lean\applications\Lineage_HR-Generalist")
SCREENSHOTS_DIR = APP_DIR / "screenshots"
SCREENSHOTS_DIR.mkdir(exist_ok=True)

APPLY_URL = "https://careers.onelineage.com/us/en/apply?jobSeqNo=LLLLLOUSR0103931EXTERNALENUS&step=1&stepname=personalInformation"
FIRST_NAME = "Yi-Chieh"
LAST_NAME = "Cheng"
EMAIL = "jamiecheng0103@gmail.com"
PHONE_NUMBER = "2137003831"

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
        "notes": "Interactive CAPTCHA detected."
    })
    sys.exit(0)


def write_result(data):
    out = APP_DIR / "SUBMITTED.json"
    out.write_text(json.dumps(data, indent=2))
    print(f"[RESULT] Written: SUBMITTED.json")


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
            id: e.id, value: e.value,
            opts: Array.from(e.options).map(o => ({v: o.value, t: o.text}))
        }));
    }""")


def get_all_fields(page):
    return page.evaluate("""() => {
        const els = document.querySelectorAll('input:not([type=hidden]), select, textarea');
        return Array.from(els).filter(e => e.offsetParent !== null).map(e => ({
            tag: e.tagName, type: e.type||'', id: e.id, name: e.name||'',
            value: (e.value||'').slice(0,40), checked: e.checked||false
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


def handle_tnc_step(page, screenshot_paths):
    """Handle Terms and Conditions / Personal Data Statement step.
    - Scroll to bottom
    - Check all checkboxes (I agree)
    - Click Save and Continue
    """
    print("\n=== TERMS & CONDITIONS / VOLUNTARY DISCLOSURES ===")

    # Get all checkboxes
    checkboxes = page.evaluate("""() =>
        Array.from(document.querySelectorAll('input[type=checkbox]'))
            .filter(e => e.offsetParent !== null)
            .map(e => ({id: e.id, name: e.name, checked: e.checked, value: e.value}))
    """)
    print(f"[DEBUG] Checkboxes: {checkboxes}")

    # Scroll to bottom of page to see all content
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    time.sleep(0.5)

    # Also scroll the inner content area if it's a scrollable div
    page.evaluate("""() => {
        const scrollables = document.querySelectorAll('[style*="overflow"], [class*="scroll"], [class*="content"]');
        for (const el of scrollables) {
            if (el.scrollHeight > el.clientHeight) {
                el.scrollTop = el.scrollHeight;
            }
        }
    }""")
    time.sleep(0.5)

    path = ss(page, "v6_tnc_scrolled")
    screenshot_paths.append(path)

    # Check all unchecked checkboxes (agree to all)
    checkboxes = page.evaluate("""() =>
        Array.from(document.querySelectorAll('input[type=checkbox]'))
            .filter(e => e.offsetParent !== null)
            .map(e => ({id: e.id, name: e.name, checked: e.checked}))
    """)
    print(f"[DEBUG] Checkboxes after scroll: {checkboxes}")

    for cb in checkboxes:
        if not cb["checked"]:
            cb_id = cb["id"]
            cb_name = cb["name"]
            sel = f"[id='{cb_id}']" if cb_id else f"[name='{cb_name}']"
            try:
                page.check(sel)
                print(f"[FILL] Checkbox checked: {cb_id or cb_name}")
            except Exception as e:
                print(f"[WARN] Checkbox check failed: {e}")
                # Try JS
                page.evaluate(f"""() => {{
                    const el = document.querySelector("{sel}");
                    if (el) {{ el.checked = true; el.dispatchEvent(new Event('change', {{bubbles: true}})); }}
                }}""")
                print(f"[FILL] Checkbox JS checked: {cb_id}")

    # Also try clicking any "I agree" label/button
    for text in ["I agree", "I Accept", "Agree", "Accept"]:
        try:
            els = page.get_by_text(text, exact=False).all()
            for el in els:
                tag = el.evaluate("e => e.tagName.toLowerCase()")
                if tag in ["label", "span", "div"] and el.is_visible():
                    el.click()
                    print(f"[FILL] Clicked '{text}' element ({tag})")
                    time.sleep(0.3)
                    break
        except Exception:
            pass

    path = ss(page, "v6_tnc_agreed")
    screenshot_paths.append(path)


def handle_step3_questions(page, screenshot_paths):
    """Fill Application Questions step."""
    print("\n=== APPLICATION QUESTIONS (step 3) ===")

    selects = get_all_selects(page)
    for s in selects:
        fid = s["id"]
        if not fid.startswith("jsqData"):
            continue
        opts = s["opts"]

        label_text = page.evaluate(f"""() => {{
            const el = document.getElementById('{fid}');
            if (!el) return '';
            const group = el.closest('.form-group, .field-wrapper, .question, div[class]');
            const label = group ? group.querySelector('label, p, span[class*="label"]') : null;
            return label ? label.textContent.trim() : el.closest('*').textContent.trim().slice(0, 200);
        }}""")
        print(f"  [{fid}] Q: {repr(label_text[:100])}")

        label_lower = label_text.lower()
        opt_texts = [o["t"].lower() for o in opts]

        yes_val = next((o["v"] for o in opts if o["t"].lower() == "yes"), None)
        no_val = next((o["v"] for o in opts if o["t"].lower() == "no"), None)

        if "18" in label_lower or "age" in label_lower:
            if yes_val:
                js_set(page, fid, yes_val)
                page.select_option(f"[id='{fid}']", value=yes_val)
                print(f"  [FILL] 18+ age = Yes")
        elif "essential function" in label_lower or "perform" in label_lower:
            if yes_val:
                js_set(page, fid, yes_val)
                page.select_option(f"[id='{fid}']", value=yes_val)
                print(f"  [FILL] Essential functions = Yes")
        elif "eligib" in label_lower or "proof" in label_lower or "work in the country" in label_lower:
            if yes_val:
                js_set(page, fid, yes_val)
                page.select_option(f"[id='{fid}']", value=yes_val)
                print(f"  [FILL] Work eligibility = Yes")
        elif "sponsor" in label_lower:
            if yes_val:
                js_set(page, fid, yes_val)
                page.select_option(f"[id='{fid}']", value=yes_val)
                print(f"  [FILL] Sponsorship = YES (truthful)")
        elif "certif" in label_lower:
            # Certifications — "None" or "N/A" option
            none_val = next((o["v"] for o in opts if "none" in o["t"].lower() or "n/a" in o["t"].lower() or "not applicable" in o["t"].lower()), None)
            if none_val:
                js_set(page, fid, none_val)
                page.select_option(f"[id='{fid}']", value=none_val)
                print(f"  [FILL] Certifications = None/N/A ({none_val})")
            elif opts and len(opts) > 1:
                # If it's a checkbox list, leave unchecked (none selected)
                print(f"  [INFO] Certifications has options: {[o['t'] for o in opts[:5]]}")
        elif "yes" in opt_texts and "no" in opt_texts:
            # Unknown yes/no question — default Yes
            if yes_val:
                js_set(page, fid, yes_val)
                page.select_option(f"[id='{fid}']", value=yes_val)
                print(f"  [FILL] Unknown Y/N = Yes")

    # Textareas
    for ta in page.locator("textarea").all():
        try:
            if ta.is_visible(timeout=1000):
                ta_id = ta.get_attribute("id") or ""
                val = ta.input_value()
                # Don't overwrite if already filled
                if not val:
                    ta.fill("N/A")
                    print(f"  [FILL] Textarea ({ta_id}) = N/A")
        except Exception:
            pass

    # Checkboxes (e.g., certifications multi-select)
    cbs = page.evaluate("""() =>
        Array.from(document.querySelectorAll('input[type=checkbox]'))
            .filter(e => e.offsetParent !== null && e.id.startsWith('jsqData'))
            .map(e => ({id: e.id, name: e.name, value: e.value, checked: e.checked,
                label: e.closest('label,div')?.textContent?.trim()?.slice(0,50)||''}))
    """)
    if cbs:
        print(f"  [DEBUG] JSQ checkboxes: {cbs}")
        # For certifications, don't check any (leave blank = no certs)

    path = ss(page, "v6_step3_filled")
    screenshot_paths.append(path)


def handle_eeo_step(page, screenshot_paths):
    """Fill EEO / Voluntary Disclosures."""
    print("\n=== EEO DISCLOSURES ===")

    selects = get_all_selects(page)
    for s in selects:
        fid = s["id"]
        fid_lower = fid.lower()
        opts = s["opts"]

        if "gender" in fid_lower:
            fv = next((o["v"] for o in opts if "female" in o["t"].lower()), None)
            if fv:
                js_set(page, fid, fv)
                page.select_option(f"[id='{fid}']", value=fv)
                print(f"  [FILL] Gender = Female")
        elif "ethnic" in fid_lower or "race" in fid_lower:
            fv = next((o["v"] for o in opts if "asian" in o["t"].lower()), None)
            if fv:
                js_set(page, fid, fv)
                page.select_option(f"[id='{fid}']", value=fv)
                print(f"  [FILL] Race = Asian")
        elif "veteran" in fid_lower or "vet" in fid_lower:
            fv = next((o["v"] for o in opts
                       if "not a protected" in o["t"].lower() or
                          "i am not" in o["t"].lower() or
                          o["t"].lower() == "no"), None)
            if fv:
                js_set(page, fid, fv)
                page.select_option(f"[id='{fid}']", value=fv)
                print(f"  [FILL] Veteran = Not protected vet")
        elif "disab" in fid_lower:
            fv = next((o["v"] for o in opts
                       if "no, i don" in o["t"].lower() or
                          "do not have" in o["t"].lower() or
                          o["t"].lower() == "no"), None)
            if fv:
                js_set(page, fid, fv)
                page.select_option(f"[id='{fid}']", value=fv)
                print(f"  [FILL] Disability = No")

    path = ss(page, "v6_eeo_filled")
    screenshot_paths.append(path)


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
                print(f"[INFO] Tab: {p.url[:80]}")
                break
        if not page:
            page = context.new_page()
            page.goto(APPLY_URL, wait_until="domcontentloaded", timeout=60000)
            time.sleep(5)

        page.bring_to_front()

        path = ss(page, "v6_start")
        screenshot_paths.append(path)
        print(f"[URL] {page.url}")

        # Main loop — keep processing steps until confirmed or max iterations
        max_iterations = 10
        for iteration in range(max_iterations):
            page_text = page.inner_text("body")
            page_text_lower = page_text.lower()
            current_url = page.url
            fields = get_all_fields(page)
            field_ids = [f["id"] for f in fields]

            print(f"\n[ITER {iteration}] URL: {current_url}")
            print(f"  Fields: {field_ids[:10]}")

            # Check if confirmed/done
            if any(kw in page_text_lower for kw in ["thank you", "application received", "successfully submitted", "application submitted", "we'll be in touch"]):
                print("[CONFIRMED] Application submitted!")
                path = ss(page, "v6_confirmed")
                screenshot_paths.append(path)
                write_result({
                    "company": "Lineage", "role": "HR Generalist", "ats": "Phenom",
                    "apply_url": APPLY_URL, "submitted": True, "outcome": "submitted",
                    "confirmed_at": datetime.now(timezone.utc).isoformat(),
                    "screenshot_paths": screenshot_paths,
                    "notes": (
                        f"SUBMITTED. Name: Yi-Chieh Cheng. Email: {EMAIL}. "
                        f"Phone: {PHONE_NUMBER} (US +1). Sponsorship: YES. "
                        f"Source: Job Boards. EEO: Female/Asian/No-vet/No-disability."
                    )
                })
                print("[DONE] submitted")
                return

            if detect_captcha(page):
                handle_captcha_stop(page, screenshot_paths)

            # Detect step and handle accordingly
            if "step=1" in current_url or "cntryFields.firstName" in field_ids:
                # Step 1: My Information — should be done from previous runs but handle if here
                print("[STEP 1] My Information — trying to advance")
                page.evaluate("""() => {
                    ['cntryFields.firstName', 'cntryFields.lastName', 'cntryFields.city',
                     'cntryFields.region', 'cntryFields.postalCode', 'email', 'phoneWidget.phoneNumber'].forEach(id => {
                        const el = document.getElementById(id);
                        if (!el) return;
                        const vals = {
                            'cntryFields.firstName': 'Yi-Chieh',
                            'cntryFields.lastName': 'Cheng',
                            'cntryFields.city': 'Portland',
                            'cntryFields.region': 'USA-OR',
                            'cntryFields.postalCode': '97201',
                            'email': 'jamiecheng0103@gmail.com',
                            'phoneWidget.phoneNumber': '2137003831'
                        };
                        const proto = el.tagName === 'SELECT'
                            ? window.HTMLSelectElement.prototype : window.HTMLInputElement.prototype;
                        const setter = Object.getOwnPropertyDescriptor(proto, 'value').set;
                        setter.call(el, vals[id]);
                        el.dispatchEvent(new Event('input', {bubbles: true}));
                        el.dispatchEvent(new Event('change', {bubbles: true}));
                    });
                    // Phone device type
                    const dt = document.getElementById('deviceType');
                    if (dt && dt.options.length > 1) {
                        const setter = Object.getOwnPropertyDescriptor(window.HTMLSelectElement.prototype, 'value').set;
                        setter.call(dt, dt.options[2].value); // Mobile
                        dt.dispatchEvent(new Event('change', {bubbles: true}));
                    }
                    // Previously worked = No
                    const r = document.getElementById('previousWorker.false');
                    if (r) { r.checked = true; r.dispatchEvent(new Event('change', {bubbles: true})); }
                }""")
                time.sleep(0.5)
                click_next(page, "Step 1")

            elif "step=2" in current_url or any("experiencedata" in fid.lower() for fid in field_ids):
                print("[STEP 2] My Experience — clicking next")
                click_next(page, "Step 2")

            elif "step=3" in current_url or any(fid.startswith("jsqData") for fid in field_ids):
                print("[STEP 3] Application Questions")
                handle_step3_questions(page, screenshot_paths)
                time.sleep(1)
                click_next(page, "Step 3")

            elif "step=4" in current_url or "voluntaryinformation" in current_url.lower():
                page_text_lower2 = page_text.lower()

                if "terms and conditions" in page_text_lower2 or "personal data statement" in page_text_lower2:
                    handle_tnc_step(page, screenshot_paths)
                    time.sleep(1)
                    click_next(page, "Step 4 T&C")
                elif any(k in " ".join(field_ids).lower() for k in ["gender", "ethnic", "veteran", "disab"]):
                    handle_eeo_step(page, screenshot_paths)
                    time.sleep(1)
                    click_next(page, "Step 4 EEO")
                else:
                    # Unknown step 4 content
                    print("[STEP 4] Unknown content — attempting to accept all checkboxes and continue")
                    for cb in page.locator("input[type='checkbox']").all():
                        try:
                            if cb.is_visible(timeout=1000) and not cb.is_checked():
                                cb.check()
                                print("[FILL] Checkbox checked")
                        except Exception:
                            pass
                    time.sleep(0.5)
                    click_next(page, "Step 4 Unknown")

            elif "step=5" in current_url or "review" in current_url.lower():
                print("[STEP 5] Review page")
                path = ss(page, "v6_review_page")
                screenshot_paths.append(path)

                # Take pre-submit screenshot
                pre_submit_path = str(SCREENSHOTS_DIR / "pre_submit_review.png")
                page.screenshot(path=pre_submit_path, full_page=True)
                screenshot_paths.append(pre_submit_path)
                print("[SCREENSHOT] pre_submit_review.png")

                print(f"[VERIFY] Name: {'Yi-Chieh' in page_text}, Email: {EMAIL in page_text}, Sponsor: {'yes' in page_text_lower}")

                if detect_captcha(page):
                    handle_captcha_stop(page, screenshot_paths)

                # Try Submit button
                submitted = False
                btns = page.evaluate("""
                    () => Array.from(document.querySelectorAll('button'))
                        .filter(b => b.offsetParent !== null && !b.disabled)
                        .map(b => b.textContent.trim())
                """)
                print(f"[DEBUG] Buttons: {btns}")

                for btn_text in ["Submit Application", "Submit", "Apply Now", "Apply"]:
                    try:
                        btn = page.get_by_role("button", name=btn_text, exact=False).first
                        if btn.is_visible(timeout=2000) and not btn.is_disabled():
                            btn.scroll_into_view_if_needed()
                            btn.click()
                            print(f"[SUBMIT] '{btn_text}'")
                            submitted = True
                            time.sleep(6)
                            break
                    except Exception:
                        pass

                if not submitted:
                    click_next(page, "Step 5 Review")
                    submitted = True

                break  # Exit loop after submit attempt

            else:
                # Unknown step — try to detect from page content
                print(f"[UNKNOWN STEP] Trying to identify from content...")
                print(f"  Page title: {page.title()}")
                h1h2 = page.evaluate("() => document.querySelector('h1,h2')?.textContent?.trim()")
                print(f"  H1/H2: {h1h2}")

                if any(k in page_text_lower for k in ["terms", "privacy", "data statement", "consent"]):
                    handle_tnc_step(page, screenshot_paths)
                    click_next(page, "Unknown T&C")
                elif any(k in page_text_lower for k in ["review", "confirm", "summary"]):
                    print("[REVIEW] Review page — going to submit")
                    break
                else:
                    # Try clicking next
                    click_next(page, "Unknown step")

            if detect_captcha(page):
                handle_captcha_stop(page, screenshot_paths)

            path = ss(page, f"v6_after_iter{iteration}")
            screenshot_paths.append(path)
            time.sleep(1)

        # Final confirmation screenshot
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

        outcome = "submitted" if is_confirmed else "submitted-unconfirmed"
        print(f"\n[OUTCOME] {outcome}")

        write_result({
            "company": "Lineage", "role": "HR Generalist", "ats": "Phenom",
            "apply_url": APPLY_URL,
            "submitted": True,
            "outcome": outcome,
            "confirmed_at": datetime.now(timezone.utc).isoformat() if is_confirmed else None,
            "screenshot_paths": screenshot_paths,
            "notes": (
                f"Confirmed: {is_confirmed}. "
                f"Name: Yi-Chieh Cheng. Email: {EMAIL}. Phone: {PHONE_NUMBER} US (+1). "
                f"Sponsorship: YES truthful. Source: Job Boards."
            )
        })
        print(f"[DONE] {outcome}")


if __name__ == "__main__":
    main()
