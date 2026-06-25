"""
Lineage Phenom ATS driver v7.
- Step 4 fix: fill EEO dropdowns (gender/race/hispanic/veteran) AND T&C checkbox on same page
- Then Save & Continue -> step 5 Review -> Submit
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
EMAIL = "jamiecheng0103@gmail.com"
PHONE_NUMBER = "2137003831"


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
                time.sleep(4)
                return True
        except Exception:
            pass
    return False


def handle_step4_combined(page, screenshot_paths):
    """Step 4: Fill EEO dropdowns first, then check T&C checkbox."""
    print("\n=== STEP 4: EEO + TERMS & CONDITIONS ===")

    # --- 1. Fill EEO selects ---
    selects = get_all_selects(page)
    print(f"[DEBUG] All selects on step 4: {[s['id'] for s in selects]}")

    for s in selects:
        fid = s["id"]
        fid_lower = fid.lower()
        opts = s["opts"]

        if "gender" in fid_lower:
            fv = next((o["v"] for o in opts if "female" in o["t"].lower()), None)
            if fv:
                js_set(page, fid, fv)
                try:
                    page.select_option(f"[id='{fid}']", value=fv)
                except Exception:
                    pass
                print(f"  [FILL] Gender = Female ({fv})")
            else:
                print(f"  [WARN] Gender options: {[o['t'] for o in opts]}")

        elif "hispanic" in fid_lower:
            # hispanicOrLatino — NO (Jamie is Asian, not Hispanic)
            fv = next((o["v"] for o in opts if o["t"].lower() in ["no", "i am not", "not hispanic"]), None)
            if not fv:
                fv = next((o["v"] for o in opts if "no" in o["t"].lower()), None)
            if fv:
                js_set(page, fid, fv)
                try:
                    page.select_option(f"[id='{fid}']", value=fv)
                except Exception:
                    pass
                print(f"  [FILL] Hispanic = No ({fv})")
            else:
                print(f"  [WARN] Hispanic options: {[o['t'] for o in opts]}")

        elif "ethnic" in fid_lower or "race" in fid_lower:
            fv = next((o["v"] for o in opts if "asian" in o["t"].lower()), None)
            if fv:
                js_set(page, fid, fv)
                try:
                    page.select_option(f"[id='{fid}']", value=fv)
                except Exception:
                    pass
                print(f"  [FILL] Race/Ethnicity = Asian ({fv})")
            else:
                print(f"  [WARN] Race/Ethnicity options: {[o['t'] for o in opts]}")

        elif "veteran" in fid_lower or "vet" in fid_lower:
            fv = next((o["v"] for o in opts
                       if "not a protected" in o["t"].lower() or
                          "i am not" in o["t"].lower() or
                          o["t"].lower() == "no"), None)
            if not fv:
                # Try "Not" or any non-veteran option
                fv = next((o["v"] for o in opts if "not" in o["t"].lower()), None)
            if fv:
                js_set(page, fid, fv)
                try:
                    page.select_option(f"[id='{fid}']", value=fv)
                except Exception:
                    pass
                print(f"  [FILL] Veteran = Not protected vet ({fv})")
            else:
                print(f"  [WARN] Veteran options: {[o['t'] for o in opts]}")

        elif "disab" in fid_lower:
            fv = next((o["v"] for o in opts
                       if "no, i don" in o["t"].lower() or
                          "do not have" in o["t"].lower() or
                          o["t"].lower() == "no"), None)
            if not fv:
                fv = next((o["v"] for o in opts if "no" in o["t"].lower()), None)
            if fv:
                js_set(page, fid, fv)
                try:
                    page.select_option(f"[id='{fid}']", value=fv)
                except Exception:
                    pass
                print(f"  [FILL] Disability = No ({fv})")
            else:
                print(f"  [WARN] Disability options: {[o['t'] for o in opts]}")

    time.sleep(0.5)
    path = ss(page, "v7_eeo_filled")
    screenshot_paths.append(path)

    # --- 2. Scroll to bottom for T&C ---
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    time.sleep(0.5)
    page.evaluate("""() => {
        const scrollables = document.querySelectorAll('[style*="overflow"], [class*="scroll"], [class*="content"]');
        for (const el of scrollables) {
            if (el.scrollHeight > el.clientHeight) {
                el.scrollTop = el.scrollHeight;
            }
        }
    }""")
    time.sleep(0.5)

    # --- 3. Check T&C checkboxes ---
    checkboxes = page.evaluate("""() =>
        Array.from(document.querySelectorAll('input[type=checkbox]'))
            .filter(e => e.offsetParent !== null)
            .map(e => ({id: e.id, name: e.name, checked: e.checked, value: e.value}))
    """)
    print(f"[DEBUG] Checkboxes: {checkboxes}")

    for cb in checkboxes:
        if not cb["checked"]:
            cb_id = cb["id"]
            cb_name = cb["name"]
            sel = f"[id='{cb_id}']" if cb_id else f"[name='{cb_name}']"
            try:
                page.check(sel)
                print(f"[FILL] Checkbox checked: {cb_id or cb_name}")
            except Exception as e:
                print(f"[WARN] Checkbox check via page.check failed: {e}")
                page.evaluate(f"""() => {{
                    const el = document.querySelector("{sel}");
                    if (el) {{ el.checked = true; el.dispatchEvent(new Event('change', {{bubbles: true}})); }}
                }}""")
                print(f"[FILL] Checkbox JS checked: {cb_id}")

    time.sleep(0.5)
    path = ss(page, "v7_tnc_checked")
    screenshot_paths.append(path)

    # Verify state
    selects_after = get_all_selects(page)
    for s in selects_after:
        fid = s["id"]
        fid_lower = fid.lower()
        if any(k in fid_lower for k in ["gender", "ethnic", "race", "hispanic", "veteran", "disab"]):
            print(f"  [VERIFY] {fid} = '{s['value']}'")

    checkboxes_after = page.evaluate("""() =>
        Array.from(document.querySelectorAll('input[type=checkbox]'))
            .filter(e => e.offsetParent !== null)
            .map(e => ({id: e.id, checked: e.checked, value: e.value}))
    """)
    print(f"[VERIFY] Checkboxes: {checkboxes_after}")


def main():
    from patchright.sync_api import sync_playwright

    screenshot_paths = []

    with sync_playwright() as pw:
        print("[CONNECT] CDP port 9400...")
        browser = None
        for attempt in range(3):
            try:
                browser = pw.chromium.connect_over_cdp("http://localhost:9400")
                print(f"[CONNECT] Success (attempt {attempt+1})")
                break
            except Exception as e:
                print(f"[RETRY {attempt+1}] CDP: {e}")
                time.sleep(2)

        if not browser:
            print("[ERROR] Could not connect to Chrome on port 9400")
            sys.exit(1)

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
        path = ss(page, "v7_start")
        screenshot_paths.append(path)
        print(f"[URL] {page.url}")

        max_iterations = 15
        for iteration in range(max_iterations):
            current_url = page.url
            page_text = page.inner_text("body")
            page_text_lower = page_text.lower()
            fields = get_all_fields(page)
            field_ids = [f["id"] for f in fields]

            print(f"\n[ITER {iteration}] URL: {current_url}")
            print(f"  Fields: {field_ids[:15]}")

            # Check confirmed
            if any(kw in page_text_lower for kw in ["thank you", "application received", "successfully submitted",
                                                     "application submitted", "we'll be in touch", "under review",
                                                     "application complete"]):
                print("[CONFIRMED] Application submitted!")
                path = ss(page, "v7_confirmed")
                screenshot_paths.append(path)
                write_result({
                    "company": "Lineage", "role": "HR Generalist", "ats": "Phenom",
                    "apply_url": APPLY_URL, "submitted": True, "outcome": "submitted",
                    "confirmed_at": datetime.now(timezone.utc).isoformat(),
                    "screenshot_paths": screenshot_paths,
                    "notes": f"SUBMITTED. Yi-Chieh Cheng. {EMAIL}. Sponsorship YES. EEO: Female/Asian/No-vet/No-disability."
                })
                print("[DONE] submitted")
                return

            if detect_captcha(page):
                path = ss(page, "captcha_detected")
                screenshot_paths.append(path)
                write_result({
                    "company": "Lineage", "role": "HR Generalist", "ats": "Phenom",
                    "apply_url": APPLY_URL, "submitted": False, "outcome": "captcha-staged",
                    "confirmed_at": None, "screenshot_paths": screenshot_paths,
                    "notes": "Interactive CAPTCHA detected."
                })
                sys.exit(0)

            # --- Step routing ---
            if "step=4" in current_url or "voluntaryinformation" in current_url.lower():
                handle_step4_combined(page, screenshot_paths)
                time.sleep(1)
                click_next(page, "Step 4 EEO+TnC")

            elif "step=5" in current_url or "review" in current_url.lower():
                print("[STEP 5] Review page")
                pre_submit_path = str(SCREENSHOTS_DIR / "pre_submit_review.png")
                page.screenshot(path=pre_submit_path, full_page=True)
                screenshot_paths.append(pre_submit_path)
                print("[SCREENSHOT] pre_submit_review.png")

                print(f"[VERIFY] Yi-Chieh in page: {'Yi-Chieh' in page_text}, email: {EMAIL in page_text}")

                if detect_captcha(page):
                    path = ss(page, "captcha_detected")
                    screenshot_paths.append(path)
                    write_result({
                        "company": "Lineage", "role": "HR Generalist", "ats": "Phenom",
                        "apply_url": APPLY_URL, "submitted": False, "outcome": "captcha-staged",
                        "confirmed_at": None, "screenshot_paths": screenshot_paths,
                        "notes": "CAPTCHA on review page."
                    })
                    sys.exit(0)

                btns = page.evaluate("""
                    () => Array.from(document.querySelectorAll('button'))
                        .filter(b => b.offsetParent !== null && !b.disabled)
                        .map(b => b.textContent.trim())
                """)
                print(f"[DEBUG] Buttons on review: {btns}")

                submitted = False
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
                    print("[SUBMIT] No submit button found, trying click_next")
                    click_next(page, "Step 5 Review")

                break  # Exit loop after submit attempt

            elif "step=1" in current_url or any(fid in field_ids for fid in ["cntryFields.firstName", "email"]):
                print("[STEP 1] Unexpected back to step 1 — trying to advance")
                click_next(page, "Step 1 re-advance")

            elif "step=2" in current_url or any("experiencedata" in fid.lower() for fid in field_ids):
                print("[STEP 2] Unexpected back to step 2 — clicking next")
                click_next(page, "Step 2 re-advance")

            elif "step=3" in current_url or any(fid.startswith("jsqData") for fid in field_ids):
                print("[STEP 3] Unexpected back to step 3 — clicking next")
                click_next(page, "Step 3 re-advance")

            else:
                h1h2 = page.evaluate("() => document.querySelector('h1,h2')?.textContent?.trim()")
                print(f"  [UNKNOWN] H1/H2: {h1h2}")
                # Try clicking next as fallback
                click_next(page, "Unknown step")

            path = ss(page, f"v7_after_iter{iteration}")
            screenshot_paths.append(path)

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
                f"Sponsorship: YES truthful. EEO: Female/Asian/No-vet/No-disability."
            )
        })
        print(f"[DONE] {outcome}")


if __name__ == "__main__":
    main()
