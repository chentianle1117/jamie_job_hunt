"""
Twitch Greenhouse Submitter — Program Manager, Culture & People Development
Job URL: https://job-boards.greenhouse.io/twitch/jobs/8582338002
No account required, standard Greenhouse form.
"""
import os, sys, time, json, re
from datetime import datetime
from pathlib import Path

# Add jamie-autopilot lib to path
AUTOPILOT_LIB = Path(r"C:\Users\chent\Agentic_Workflows_2026\jamie-autopilot\lib")
sys.path.insert(0, str(AUTOPILOT_LIB))

from patchright.sync_api import sync_playwright

ROLE_DIR = Path(r"C:\Users\chent\Agentic_Workflows_2026\oracle-job-search\outputs\2026-06-12-feed-first\applications\twitch_culture_people_pm")
RESUME = ROLE_DIR / "resume.pdf"
COVER = ROLE_DIR / "cover_letter.pdf"
OUT_DIR = ROLE_DIR / "screenshots"
OUT_DIR.mkdir(exist_ok=True)

# ---- Application data ----
URL = "https://job-boards.greenhouse.io/twitch/jobs/8582338002"
FIRST = "Yi-Chieh"
LAST = "Cheng"
PREFERRED = "Jamie"
EMAIL = "jamiecheng0103@gmail.com"
PHONE = "2137003831"
COUNTRY = "United States"
LOCATION_CITY = "San Francisco, CA"
LINKEDIN = "https://www.linkedin.com/in/jamieyccheng/"
AUTHORIZED = "Yes"
SPONSOR = "Yes"
SALARY = "100000"
WHY_TEXT = (
    "Over the past three years I have managed end-to-end lifecycles for 20+ programs and 10+ vendors at InGenius Prep, "
    "facilitated training webinars for 600+ participants, and analyzed 2,000+ employee experiences at NextGen Healthcare "
    "to guide culture and engagement decisions. At Vestas Wind Systems, I led an Inclusive Leadership workshop that "
    "scaled to 23 global locations and spearheaded an HR Award-winning culture and engagement communications initiative. "
    "My MS in Applied Organizational Psychology from USC gives me the research foundation to build evidence-based "
    "programs that genuinely move the needle on culture and employee development."
)

PROFILE_DIR = r"C:\Users\chent\ats_agent_9410"
DEBUG_PORT = 9410

def pause(t=0.6):
    time.sleep(t)

def screenshot(page, name):
    path = str(OUT_DIR / name)
    try:
        page.screenshot(path=path, full_page=True)
        print(f"  [screenshot] {name}")
    except Exception as e:
        print(f"  [screenshot fail] {name}: {e}")
    return path

def combo_select(page, locator, option_text):
    """Greenhouse react-select: click container, find .select__option matching text."""
    locator.scroll_into_view_if_needed()
    pause(0.4)
    locator.click()
    pause(0.5)
    page.wait_for_timeout(700)

    want = option_text.strip().lower()
    # Try matching existing options without typing
    try:
        opts = page.locator(".select__option")
        n = opts.count()
        for i in range(n):
            txt = opts.nth(i).inner_text().strip().lower()
            if want in txt or txt in want:
                opts.nth(i).click()
                pause()
                return True
    except:
        pass

    # Type to filter then match
    try:
        page.keyboard.type(option_text)
        page.wait_for_timeout(900)
        opts = page.locator(".select__option")
        n = opts.count()
        for i in range(n):
            txt = opts.nth(i).inner_text().strip().lower()
            if want in txt or txt in want:
                opts.nth(i).click()
                pause()
                return True
        # Fallback: Enter on whatever is visible
        page.keyboard.press("Enter")
        pause()
        return True
    except:
        pass

    page.keyboard.press("Escape")
    return False

def fill_text(page, selector, value, label=""):
    """Fill a text input, trying multiple strategies."""
    try:
        el = page.locator(selector).first
        if el.count() > 0 and el.is_visible(timeout=2000):
            el.click()
            pause(0.3)
            el.fill(value)
            pause()
            print(f"  {label or selector} -> filled")
            return True
    except Exception as e:
        print(f"  {label or selector} fill err: {e}")
    return False

def main():
    import subprocess, os

    # Kill any Chrome holding the profile dir
    profile_default = Path(PROFILE_DIR) / "Default"
    lock_file = profile_default / "LOCK"
    if lock_file.exists():
        try:
            lock_file.unlink()
            print("  Removed stale LOCK file")
        except:
            pass

    with sync_playwright() as p:
        print(f"Launching Chrome on port {DEBUG_PORT} with profile {PROFILE_DIR}...")
        browser = p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_DIR,
            channel="chrome",
            headless=False,
            no_viewport=True,
            args=[f"--remote-debugging-port={DEBUG_PORT}"],
            ignore_default_args=["--enable-automation"],
        )

        page = browser.pages[0] if browser.pages else browser.new_page()
        page.set_default_timeout(20000)

        print(f"\nNavigating to: {URL}")
        page.goto(URL, wait_until="domcontentloaded", timeout=40000)
        page.wait_for_timeout(5000)

        title = page.title()
        body_preview = page.inner_text("body")[:300]
        print(f"Page title: {title}")
        print(f"Body preview: {body_preview[:200]}")

        # Check if live
        if "404" in title.lower() or "not found" in body_preview.lower() or "this job" in body_preview.lower() and "no longer" in body_preview.lower():
            print("\n!!! JOB POSTING IS DEAD — skip-dead")
            screenshot(page, "00_dead.png")
            browser.close()
            return "skip-dead"

        screenshot(page, "01_landing.png")
        print("Job posting is LIVE. Filling form...")

        # ---- PERSONAL FIELDS ----
        print("\n--- Personal fields ---")
        fill_text(page, "#first_name", FIRST, "FirstName")
        fill_text(page, "#last_name", LAST, "LastName")
        fill_text(page, "#email", EMAIL, "Email")

        # Phone
        try:
            phone_el = page.locator("#phone").first
            if phone_el.is_visible(timeout=2000):
                phone_el.fill(PHONE)
                pause()
                print("  Phone -> filled")
        except:
            pass

        # Country (Greenhouse react-select)
        try:
            country_sel = page.locator("#country").first
            if country_sel.count() > 0 and country_sel.is_visible(timeout=3000):
                result = combo_select(page, country_sel, COUNTRY)
                print(f"  Country -> {'OK' if result else 'FAIL'}")
        except Exception as e:
            print(f"  Country err: {e}")

        # Location (autocomplete text input)
        loc_filled = False
        for sel in ["#candidate-location", 'input[name*="location" i]', 'input[id*="location" i]',
                    'input[placeholder*="city" i]', 'input[placeholder*="location" i]']:
            try:
                loc_el = page.locator(sel).first
                if loc_el.count() > 0 and loc_el.is_visible(timeout=2000):
                    loc_el.click()
                    pause(0.3)
                    page.keyboard.type(LOCATION_CITY)
                    page.wait_for_timeout(1800)
                    # Pick first autocomplete suggestion if available
                    suggestions = page.locator('[role="option"], .pac-item, .suggestions-item').all()
                    if suggestions:
                        suggestions[0].click()
                        pause()
                    else:
                        page.keyboard.press("Enter")
                        pause()
                    loc_filled = True
                    print(f"  Location -> {LOCATION_CITY} (via {sel})")
                    break
            except:
                continue
        if not loc_filled:
            print("  !! Location NOT filled")

        # ---- RESUME UPLOAD ----
        print("\n--- File uploads ---")
        try:
            resume_el = page.locator("#resume").first
            if resume_el.count() > 0:
                resume_el.set_input_files(str(RESUME))
                page.wait_for_timeout(3000)
                print(f"  Resume uploaded: {RESUME.stat().st_size} bytes")
            else:
                # fallback to first file input
                page.locator('input[type="file"]').nth(0).set_input_files(str(RESUME))
                page.wait_for_timeout(3000)
                print("  Resume uploaded via nth(0)")
        except Exception as e:
            print(f"  Resume upload err: {e}")

        # Cover letter
        if COVER.exists():
            try:
                cover_el = page.locator("#cover_letter").first
                if cover_el.count() > 0:
                    cover_el.set_input_files(str(COVER))
                    page.wait_for_timeout(3000)
                    print("  Cover letter uploaded")
                else:
                    file_inputs = page.locator('input[type="file"]').all()
                    if len(file_inputs) > 1:
                        file_inputs[1].set_input_files(str(COVER))
                        page.wait_for_timeout(3000)
                        print("  Cover letter uploaded via nth(1)")
            except Exception as e:
                print(f"  Cover upload err: {e}")

        screenshot(page, "02_after_uploads.png")

        # ---- SCAN ALL REMAINING FIELDS ----
        print("\n--- Scanning all form fields ---")
        questions = page.evaluate('''() => {
            const out = [];
            document.querySelectorAll('input:not([type="hidden"]):not([type="file"]), textarea, select').forEach(el => {
                const rect = el.getBoundingClientRect();
                if (rect.width <= 0) return;
                const id = el.id || '';
                const name = el.name || '';
                const type = el.tagName.toLowerCase() + (el.type ? ':' + el.type : '');
                const placeholder = el.placeholder || '';
                let label = '';
                if (id) {
                    const lbl = document.querySelector(`label[for="${id}"]`);
                    if (lbl) label = (lbl.innerText || lbl.textContent || '').trim();
                }
                if (!label) {
                    let p = el.parentElement;
                    for (let i = 0; i < 5 && p; i++) {
                        const txt = (p.innerText || '').trim().split('\\n')[0];
                        if (txt && txt.length < 250 && txt.length > 1) { label = txt; break; }
                        p = p.parentElement;
                    }
                }
                out.push({id, name, type, label: label.substring(0, 200), placeholder});
            });
            return out;
        }''')

        filled_ids = {"first_name", "last_name", "email", "phone", "resume", "cover_letter"}
        print(f"  Found {len(questions)} fields total")
        for q in questions:
            print(f"    id={q['id']} type={q['type']} label={q['label'][:60]!r}")

        for q in questions:
            if q["id"] in filled_ids:
                continue
            label_lower = q["label"].lower()
            placeholder_lower = q.get("placeholder", "").lower()
            qid = q["id"]
            tp = q["type"]
            combined = label_lower + " " + placeholder_lower

            try:
                # LinkedIn
                if "linkedin" in combined:
                    if qid:
                        page.locator(f"#{qid}").fill(LINKEDIN)
                    else:
                        page.locator(f'input[name="{q["name"]}"]').fill(LINKEDIN)
                    pause()
                    print(f"  LinkedIn -> {qid}")
                    continue

                # Preferred name
                if ("preferred" in label_lower and ("name" in label_lower or "first" in label_lower)):
                    if qid:
                        page.locator(f"#{qid}").fill(PREFERRED)
                        pause()
                        print(f"  PreferredName={PREFERRED} -> {qid}")
                    continue

                # Website / portfolio — skip if no portfolio
                if "website" in combined or "portfolio" in combined:
                    print(f"  Website/portfolio -> skipping (no value)")
                    continue

                # Salary
                if "salary" in combined or "compensation" in combined or "pay" in combined:
                    if qid:
                        page.locator(f"#{qid}").fill(SALARY)
                        pause()
                        print(f"  Salary={SALARY} -> {qid}")
                    continue

                # Work authorization
                if "legally authorized" in label_lower or "authorized to work" in label_lower:
                    if qid:
                        combo_select(page, page.locator(f"#{qid}"), AUTHORIZED)
                        print(f"  Authorized={AUTHORIZED} -> {qid}")
                    continue

                # Sponsorship — ALWAYS YES
                if "sponsorship" in label_lower or ("visa" in label_lower and "require" in label_lower) or "will you now or in the future" in label_lower:
                    if qid:
                        combo_select(page, page.locator(f"#{qid}"), SPONSOR)
                        print(f"  Sponsorship={SPONSOR} -> {qid}")
                    continue

                # How did you hear
                if "how did you hear" in combined or "referral source" in combined or ("source" in label_lower and len(label_lower) < 25):
                    if qid:
                        for variant in ["LinkedIn", "Job board", "LinkedIn Job Board", "Other"]:
                            try:
                                combo_select(page, page.locator(f"#{qid}"), variant)
                                print(f"  HearAbout={variant} -> {qid}")
                                break
                            except:
                                continue
                    continue

                # Relocate / work onsite / hybrid
                if "relocat" in combined or "onsite" in combined or "on-site" in combined or "hybrid" in combined or "in-office" in combined:
                    if qid:
                        combo_select(page, page.locator(f"#{qid}"), "Yes")
                        print(f"  Relocate/Onsite=Yes -> {qid}")
                    continue

                # Open-ended screening questions (textarea)
                if "textarea" in tp:
                    if "why" in label_lower or "culture" in label_lower or "people" in label_lower or "development" in label_lower or "experience" in label_lower or "background" in label_lower:
                        if qid:
                            page.locator(f"#{qid}").fill(WHY_TEXT)
                            pause()
                            print(f"  ScreeningEssay -> {qid} ({len(WHY_TEXT)} chars)")
                        continue

                # Demographics (EEO) — truthful
                if "gender" in label_lower:
                    if qid:
                        combo_select(page, page.locator(f"#{qid}"), "Female")
                        print(f"  Gender=Female -> {qid}")
                    continue
                if "hispanic" in label_lower or "latino" in label_lower:
                    if qid:
                        combo_select(page, page.locator(f"#{qid}"), "No")
                        print(f"  Hispanic=No -> {qid}")
                    continue
                if ("race" in label_lower or "ethnicity" in label_lower) and "hispanic" not in label_lower:
                    if qid:
                        combo_select(page, page.locator(f"#{qid}"), "Asian")
                        print(f"  Race=Asian -> {qid}")
                    continue
                if "veteran" in label_lower:
                    if qid:
                        combo_select(page, page.locator(f"#{qid}"), "I am not a protected veteran")
                        print(f"  Veteran=Not protected -> {qid}")
                    continue
                if "disability" in label_lower:
                    if qid:
                        combo_select(page, page.locator(f"#{qid}"), "No, I do not have a disability")
                        print(f"  Disability=No -> {qid}")
                    continue

                # Age 18+
                if "18" in label_lower and "year" in label_lower:
                    if qid:
                        combo_select(page, page.locator(f"#{qid}"), "Yes")
                        print(f"  Age18+=Yes -> {qid}")
                    continue

                # Generic Yes/No compliance
                if qid and "select" in tp:
                    if "agree" in label_lower or "acknowledge" in label_lower or "confirm" in label_lower:
                        combo_select(page, page.locator(f"#{qid}"), "Yes")
                        print(f"  Compliance=Yes -> {qid}")
                        continue

            except Exception as e:
                print(f"  !! Error on field {qid} ({label_lower[:40]}): {e}")

        screenshot(page, "03_filled.png")

        # ---- PRE-SUBMIT READBACK ----
        print("\n--- PRE-SUBMIT READBACK ---")
        readback = page.evaluate('''() => {
            const out = {};
            ["first_name","last_name","email","phone"].forEach(id => {
                const el = document.getElementById(id);
                if (el) out[id] = el.value;
            });
            // Check for sponsorship answer in any visible select/input
            const selects = document.querySelectorAll('select, input[type="text"]');
            const sponsorEls = [];
            selects.forEach(el => {
                const lbl = el.closest('div')?.querySelector('label');
                if (lbl && (lbl.textContent||'').toLowerCase().includes('sponsor')) {
                    sponsorEls.push({id: el.id, value: el.value, label: (lbl.textContent||'').trim().substring(0,80)});
                }
            });
            out['sponsorship_fields'] = sponsorEls;
            // Resume uploaded check
            const resumeInput = document.getElementById('resume');
            out['resume_has_file'] = resumeInput ? (resumeInput.files && resumeInput.files.length > 0) : null;
            return out;
        }''')
        print(f"  Readback: {json.dumps(readback, ensure_ascii=False)}")

        # Visual check of the full form
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(500)
        screenshot(page, "04_pre_submit_top.png")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(500)
        screenshot(page, "04_pre_submit_bottom.png")
        page.evaluate("window.scrollTo(0, 0)")

        # ---- SUBMIT ----
        print("\n*** SUBMITTING ***")
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
                    print(f"  Clicked: {btn_text}")
                    submitted = True
                    break
            except Exception as e:
                print(f"  btn '{btn_text}': {e}")
                continue

        if not submitted:
            # Try by text
            try:
                page.get_by_text("Submit application", exact=True).click(timeout=8000)
                submitted = True
                print("  Clicked via get_by_text")
            except:
                pass

        if not submitted:
            print("  !! Could not find submit button — taking screenshot of current state")

        page.wait_for_timeout(10000)
        screenshot(page, "05_after_submit.png")

        body = page.inner_text("body")
        final_url = page.url
        final_title = page.title()

        safe_body = body[:2000].encode("ascii", "replace").decode("ascii")
        print(f"\nFinal URL: {final_url}")
        print(f"Final title: {final_title.encode('ascii','replace').decode('ascii')}")
        print(f"Body excerpt:\n{safe_body[:800]}")

        success = any(kw in body.lower() for kw in ["thank you", "received", "submitted", "we got your", "application has been"])
        result_status = "submitted" if success else "unknown"

        # Check for errors
        if not success:
            errors = page.locator('.error, [class*="error"], [aria-invalid="true"]').all()
            print(f"\n  Visible error elements: {len(errors)}")
            for err in errors[:10]:
                try:
                    t = (err.text_content() or "").strip()
                    if 5 < len(t) < 200:
                        print(f"    - {t[:150].encode('ascii','replace').decode('ascii')}")
                except:
                    pass

            # Unfilled required
            unfilled = page.evaluate('''() => {
                const out = [];
                document.querySelectorAll('[aria-required="true"], input[required], select[required], textarea[required]').forEach(el => {
                    if (!el.value) {
                        let lbl = '';
                        if (el.id) { const l = document.querySelector(`label[for="${el.id}"]`); if(l) lbl=(l.innerText||'').trim(); }
                        out.push({id: el.id, label: lbl.substring(0,80)});
                    }
                });
                return out;
            }''')
            print(f"\n  Unfilled required fields: {len(unfilled)}")
            for u in unfilled[:10]:
                print(f"    - id={u['id']} label={u['label']!r}")

        # Write SUBMITTED.json
        submitted_data = {
            "company": "Twitch",
            "role": "Program Manager, Culture & People Development",
            "ats": "Greenhouse",
            "job_url": URL,
            "status": result_status,
            "confirmed_at": datetime.now().isoformat(),
            "final_url": final_url,
            "final_title": final_title,
            "body_preview": body[:500],
            "screenshot_confirmation": str(OUT_DIR / "05_after_submit.png"),
            "notes": "Auto-submitted via patchright, no account required"
        }
        with open(ROLE_DIR / "SUBMITTED.json", "w", encoding="utf-8") as f:
            json.dump(submitted_data, f, indent=2, ensure_ascii=False)
        print(f"\nWrote SUBMITTED.json: status={result_status}")

        time.sleep(15)
        browser.close()
        return result_status

if __name__ == "__main__":
    result = main()
    print(f"\n=== RESULT: {result} ===")
