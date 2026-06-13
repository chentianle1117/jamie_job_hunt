"""
Gong Senior Talent Development Program Manager — Greenhouse submission.
Port 9406, user-data-dir=C:\\Users\\chent\\ats_agent_9406
Step 0: verify live + no hard-stop. Step 1+: fill + submit.
"""
import os, sys, time, random, json, re
from datetime import datetime
from pathlib import Path

sys.path.insert(0, r"C:\Users\chent\Agentic_Workflows_2026\jamie-autopilot\lib")
from patchright.sync_api import sync_playwright

ROLE_DIR = Path(r"C:\Users\chent\Agentic_Workflows_2026\oracle-job-search\outputs\2026-06-12-feed-first\applications\gong_talent_dev_pm")
RESUME   = ROLE_DIR / "resume.pdf"
COVER    = ROLE_DIR / "cover_letter.pdf"
OUT_DIR  = ROLE_DIR / "screenshots"
OUT_DIR.mkdir(exist_ok=True)

JOB_URL = "https://job-boards.greenhouse.io/gongio/jobs/4669018006"
PROFILE_DIR = r"C:\Users\chent\ats_agent_9406"

# Candidate data
FIRST      = "Yi-Chieh"
LAST       = "Cheng"
EMAIL      = "jamiecheng0103@gmail.com"
PHONE      = "+12137003831"
COUNTRY    = "United States"
LOC        = "Portland, OR"
LINKEDIN   = "https://www.linkedin.com/in/jamieyccheng/"
SPONSOR    = "Yes"
AUTHORIZED = "Yes"
PREF_NAME  = "Jamie"

# Free-text screening answer — Jamie's voice, truthful
SCREENING_WHY = (
    "I'm drawn to Gong because great talent development demands the same rigor that "
    "Gong brings to revenue intelligence — grounding every program in evidence, not "
    "assumption. In my current role at InGenius Prep I manage 15–20+ programs and "
    "8–10+ vendors, run needs assessments with 25+ global stakeholders to identify "
    "capability gaps, and have designed 3 new learning programs from the ground up. "
    "At NextGen Healthcare I led a manager-effectiveness initiative and analyzed "
    "2,000+ employee experiences to guide C-suite L&D strategy. And at Vestas I "
    "designed an Inclusive Leadership workshop that started with 12 leaders and "
    "scaled to 23 global locations — so building programs that travel across an org "
    "is exactly my wheelhouse. My MS in Org Psychology (USC, 3.95 GPA) gives me "
    "the research foundation to measure whether people actually grow, not just "
    "whether they attended. I know this role leans senior; I'd bring genuine "
    "program-design depth plus the energy to grow into the strategic scope fast."
)

def pause(a=0.4, b=0.9):
    time.sleep(random.uniform(a, b))

def take(page, name):
    p = OUT_DIR / name
    try:
        page.screenshot(path=str(p), full_page=True)
        print(f"  [screenshot] {name}")
    except Exception as e:
        print(f"  [screenshot ERR] {name}: {e}")

def combo(page, locator, option_text):
    """Drive a react-select / Aurora combobox."""
    try:
        locator.scroll_into_view_if_needed()
    except: pass
    pause()
    try:
        locator.click()
    except: pass
    pause()
    page.wait_for_timeout(600)
    want = option_text.strip().lower()
    # Try clicking existing option first (no typing)
    try:
        opts = page.locator(".select__option")
        n = opts.count()
        for i in range(n):
            txt = opts.nth(i).inner_text().strip().lower()
            if want in txt or txt in want:
                opts.nth(i).click(); pause(); return
    except: pass
    # Type to filter then click
    try:
        page.keyboard.type(option_text)
        page.wait_for_timeout(900)
        opts = page.locator(".select__option")
        n = opts.count()
        for i in range(n):
            txt = opts.nth(i).inner_text().strip().lower()
            if want in txt or txt in want:
                opts.nth(i).click(); pause(); return
    except: pass
    # Last resort: Enter on typed value
    page.wait_for_timeout(300)
    page.keyboard.press("Enter")
    pause()

def fill_text(page, sel, value, desc=""):
    """Fill a text/tel/email input, trying multiple selector forms."""
    selectors = [sel] if sel else []
    for s in selectors:
        try:
            el = page.locator(s).first
            if el.count() > 0 and el.is_visible(timeout=3000):
                el.fill(value)
                pause()
                print(f"  {desc or s} = {value[:60]}")
                return True
        except: pass
    return False

def main():
    print("=" * 60)
    print("GONG — Senior Talent Development Program Manager")
    print(f"URL: {JOB_URL}")
    print("=" * 60)

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_DIR,
            channel="chrome",
            headless=False,
            no_viewport=True,
            args=["--start-maximized"],
        )
        page = browser.pages[0] if browser.pages else browser.new_page()
        page.set_default_timeout(20000)

        # -------------------------------------------------------
        # STEP 0 — verify live + scan for hard-stop language
        # -------------------------------------------------------
        print("\n[STEP 0] Verifying job posting...")
        page.goto(JOB_URL, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(4000)
        take(page, "00_landing.png")

        body_text = page.inner_text("body").lower()
        title_text = page.title()
        url_now = page.url

        print(f"  Title: {title_text}")
        print(f"  URL:   {url_now}")

        # Check for 404 / dead posting
        if "404" in title_text or "not found" in title_text.lower() or "no longer" in body_text:
            print("SKIP — posting appears dead / 404")
            json.dump({"status": "skip-dead", "url": url_now, "title": title_text},
                      open(ROLE_DIR / "SUBMITTED.json", "w"), indent=2)
            browser.close(); return

        # Check for explicit no-sponsor language
        no_sponsor_patterns = [
            "we do not provide visa sponsorship",
            "we do not sponsor",
            "unable to sponsor",
            "cannot sponsor",
            "does not provide sponsorship",
            "must be authorized to work without sponsorship",
            "must be authorized to work in the united states without sponsorship",
            "will not sponsor",
            "no visa sponsorship",
            "sponsorship is not available",
        ]
        for pat in no_sponsor_patterns:
            if pat in body_text:
                # Find and print the surrounding sentence
                idx = body_text.find(pat)
                snippet = body_text[max(0, idx-80):idx+120].replace("\n", " ")
                print(f'\nSKIP — explicit no-sponsor found: "...{snippet}..."')
                json.dump({"status": "skip-no-sponsor", "quote": snippet, "url": url_now},
                          open(ROLE_DIR / "SUBMITTED.json", "w"), indent=2)
                browser.close(); return

        # Check ITAR
        if "itar" in body_text or "us person" in body_text or "u.s. person" in body_text:
            print("SKIP — ITAR / US Person language found")
            json.dump({"status": "skip-itar", "url": url_now},
                      open(ROLE_DIR / "SUBMITTED.json", "w"), indent=2)
            browser.close(); return

        print("  LIVE — no hard-stop language. Proceeding to apply.")

        # -------------------------------------------------------
        # Navigate to the application form (click Apply button)
        # -------------------------------------------------------
        print("\n[STEP 1] Opening application form...")
        apply_clicked = False
        for btn_text in ["Apply for this Job", "Apply Now", "Apply", "Submit Application"]:
            try:
                btn = page.get_by_role("link", name=btn_text, exact=False).first
                if btn.count() > 0 and btn.is_visible(timeout=3000):
                    btn.click(); pause(0.5, 1.2)
                    page.wait_for_timeout(3000)
                    apply_clicked = True
                    print(f"  Clicked '{btn_text}'")
                    break
            except: pass
        if not apply_clicked:
            # Try button element
            for btn_text in ["Apply for this Job", "Apply Now", "Apply"]:
                try:
                    btn = page.get_by_role("button", name=btn_text, exact=False).first
                    if btn.count() > 0 and btn.is_visible(timeout=3000):
                        btn.click(); pause(0.5, 1.2)
                        page.wait_for_timeout(3000)
                        apply_clicked = True
                        print(f"  Clicked button '{btn_text}'")
                        break
                except: pass
        if not apply_clicked:
            print("  No Apply button found — may already be on the form")

        take(page, "01_form_opened.png")

        # -------------------------------------------------------
        # STEP 2 — Fill personal fields
        # -------------------------------------------------------
        print("\n[STEP 2] Filling personal fields...")

        # First name
        fill_text(page, "#first_name", FIRST, "first_name")

        # Last name
        fill_text(page, "#last_name", LAST, "last_name")

        # Email
        fill_text(page, "#email", EMAIL, "email")

        # Phone
        fill_text(page, "#phone", PHONE, "phone")

        # Country combobox
        try:
            combo(page, page.locator("#country").first, COUNTRY)
            print(f"  country = {COUNTRY}")
        except Exception as e:
            print(f"  country ERR: {e}")

        # Location / city autocomplete
        loc_filled = False
        for sel in ["#candidate-location", 'input[name*="location" i]',
                    'input[id*="location" i]', 'input[placeholder*="city" i]',
                    'input[placeholder*="location" i]']:
            try:
                el = page.locator(sel).first
                if el.count() > 0 and el.is_visible(timeout=2500):
                    el.click(); pause()
                    page.keyboard.type("Portland, OR")
                    page.wait_for_timeout(1800)
                    page.keyboard.press("ArrowDown"); pause()
                    page.keyboard.press("Enter"); pause()
                    print(f"  location = Portland, OR (via {sel})")
                    loc_filled = True
                    break
            except: pass
        if not loc_filled:
            print("  !! location NOT filled")

        # -------------------------------------------------------
        # STEP 3 — Upload resume (and cover if field exists)
        # -------------------------------------------------------
        print("\n[STEP 3] Uploading files...")
        try:
            page.locator("#resume").set_input_files(str(RESUME))
            page.wait_for_timeout(3000)
            print(f"  resume.pdf uploaded ({RESUME.stat().st_size} bytes)")
        except Exception as e:
            print(f"  #resume err: {e}; trying nth(0)")
            try:
                page.locator('input[type="file"]').nth(0).set_input_files(str(RESUME))
                page.wait_for_timeout(3000)
                print("  resume via nth(0)")
            except Exception as e2:
                print(f"  resume nth(0) ERR: {e2}")

        if COVER.exists():
            try:
                page.locator("#cover_letter").set_input_files(str(COVER))
                page.wait_for_timeout(3000)
                print("  cover_letter.pdf uploaded")
            except Exception as e:
                print(f"  #cover_letter err: {e}; trying nth(1)")
                try:
                    page.locator('input[type="file"]').nth(1).set_input_files(str(COVER))
                    page.wait_for_timeout(3000)
                    print("  cover via nth(1)")
                except: pass

        take(page, "02_files_uploaded.png")

        # -------------------------------------------------------
        # STEP 4 — Scan + fill all remaining questions
        # -------------------------------------------------------
        print("\n[STEP 4] Scanning remaining questions...")
        questions = page.evaluate('''() => {
            const out = [];
            document.querySelectorAll('input, textarea, select').forEach(el => {
                const rect = el.getBoundingClientRect();
                if (rect.width <= 0 || rect.height <= 0) return;
                if (el.type === "hidden") return;
                const id = el.id || "";
                const name = el.name || "";
                const type = el.tagName.toLowerCase() + (el.type ? ":" + el.type : "");
                let label = "";
                if (id) {
                    const lbl = document.querySelector(`label[for="${id}"]`);
                    if (lbl) label = (lbl.innerText || lbl.textContent || "").trim();
                }
                if (!label) {
                    let parent = el.parentElement;
                    for (let i = 0; i < 5 && parent; i++) {
                        const txt = (parent.innerText || "").trim().split("\\n")[0];
                        if (txt && txt.length < 300) { label = txt; break; }
                        parent = parent.parentElement;
                    }
                }
                out.push({id, name, type, label: label.substring(0, 250)});
            });
            return out;
        }''')

        FILLED = {"first_name", "last_name", "email", "phone", "country",
                  "candidate-location", "resume", "cover_letter"}
        REVIEW_FLAGS = []

        for q in questions:
            if q["id"] in FILLED: continue
            ll = q["label"].lower()
            qid = q["id"]
            tp = q["type"]
            if not qid: continue

            try:
                # LinkedIn
                if "linkedin" in ll and "input" in tp:
                    page.locator(f"#{qid}").fill(LINKEDIN); pause()
                    print(f"  linkedin = {LINKEDIN[:50]}")
                    continue

                # Preferred / preferred first name
                if ("preferred" in ll and ("name" in ll or "first" in ll)) and "input" in tp:
                    page.locator(f"#{qid}").fill(PREF_NAME); pause()
                    print(f"  preferred_name = {PREF_NAME}")
                    continue

                # Salary / compensation
                if ("salary" in ll or "compensation" in ll or "pay" in ll) and ("input" in tp or "textarea" in tp):
                    page.locator(f"#{qid}").fill("124000"); pause()
                    print("  salary = 124000")
                    continue

                # Website / portfolio — skip
                if ("website" in ll or "portfolio" in ll) and "input" in tp:
                    continue

                # How did you hear
                if "how did you hear" in ll or "referral source" in ll or ll.strip() == "source":
                    for v in ["LinkedIn", "Job board", "Company website", "Other"]:
                        try:
                            combo(page, page.locator(f"#{qid}"), v)
                            print(f"  source = {v}"); break
                        except: continue
                    continue

                # Authorized to work
                if "legally authorized" in ll or "authorized to work" in ll:
                    combo(page, page.locator(f"#{qid}"), AUTHORIZED)
                    print(f"  authorized = {AUTHORIZED}")
                    continue

                # Sponsorship
                if "sponsorship" in ll or ("visa" in ll and "require" in ll) or "now or in the future require" in ll:
                    combo(page, page.locator(f"#{qid}"), SPONSOR)
                    print(f"  sponsorship = {SPONSOR}")
                    continue

                # US-based
                if "us-based" in ll or "us based" in ll or "currently us" in ll or "currently located in the us" in ll:
                    combo(page, page.locator(f"#{qid}"), "Yes")
                    print("  us_based = Yes")
                    continue

                # Years of experience (select or text)
                if "years of experience" in ll:
                    if "select" in tp:
                        for v in ["3", "3 years", "2-3 years", "2-4 years", "1-3 years"]:
                            try:
                                combo(page, page.locator(f"#{qid}"), v)
                                print(f"  yoe = {v}"); break
                            except: continue
                    else:
                        try:
                            page.locator(f"#{qid}").fill("3"); pause()
                            print("  yoe = 3")
                        except: pass
                    continue

                # Open-ended "why" / motivation / experience textarea
                if ("textarea" in tp) and any(k in ll for k in
                        ["why", "tell us", "describe", "experience", "motivation",
                         "interest", "relevant", "share", "background"]):
                    try:
                        page.locator(f"#{qid}").fill(SCREENING_WHY); pause(0.3, 0.6)
                        print(f"  screening_text ({ll[:40]}) = [filled]")
                    except Exception as e:
                        print(f"  textarea ERR ({qid}): {e}")
                    continue

                # Age 18+
                if "18 years" in ll or "at least 18" in ll or "age of 18" in ll:
                    combo(page, page.locator(f"#{qid}"), "Yes")
                    print("  age_18 = Yes"); continue

                # Contractual obligations / non-compete
                if "contractual obligation" in ll or "non-compete" in ll or ("agreements" in ll and "interfere" in ll):
                    combo(page, page.locator(f"#{qid}"), "No")
                    print("  non_compete = No"); continue

                # Acknowledge / agree
                if "acknowledge" in ll or "i agree" in ll or "i have read" in ll:
                    for v in ["Yes", "I acknowledge", "I agree", "Acknowledged"]:
                        try:
                            combo(page, page.locator(f"#{qid}"), v)
                            print(f"  acknowledge = {v}"); break
                        except: continue
                    continue

                # Demographics — truthful
                if "gender" in ll:
                    for v in ["Woman", "Female"]:
                        try:
                            combo(page, page.locator(f"#{qid}"), v)
                            print(f"  gender = {v}"); break
                        except: continue
                    continue
                if "hispanic" in ll:
                    for v in ["No", "Not Hispanic or Latino", "No, not Hispanic or Latino"]:
                        try:
                            combo(page, page.locator(f"#{qid}"), v)
                            print(f"  hispanic = {v}"); break
                        except: continue
                    continue
                if "race" in ll or "ethnicity" in ll:
                    for v in ["Asian", "Asian (Not Hispanic or Latino)"]:
                        try:
                            combo(page, page.locator(f"#{qid}"), v)
                            print(f"  race = {v}"); break
                        except: continue
                    continue
                if "veteran" in ll:
                    for v in ["I am not a protected veteran", "Not a protected veteran", "No"]:
                        try:
                            combo(page, page.locator(f"#{qid}"), v)
                            print(f"  veteran = {v}"); break
                        except: continue
                    continue
                if "disability" in ll:
                    for v in ["No, I do not have a disability", "No, I don't have a disability", "No"]:
                        try:
                            combo(page, page.locator(f"#{qid}"), v)
                            print(f"  disability = {v}"); break
                        except: continue
                    continue

                # ITAR/export-control — flag for review but answer
                if "deemed export" in ll or "itar" in ll or "export controlled" in ll:
                    REVIEW_FLAGS.append(f"EXPORT-CONTROL: {q['label'][:150]}")
                    for v in ["Yes", "No"]:
                        try:
                            combo(page, page.locator(f"#{qid}"), v)
                            print(f"  export_ctrl = {v} [FLAGGED]"); break
                        except: continue
                    continue

            except Exception as e:
                print(f"  Q({qid}|{ll[:30]}): ERR {e}")

        take(page, "03_pre_submit.png")

        # -------------------------------------------------------
        # STEP 5 — Pre-submit readback
        # -------------------------------------------------------
        print("\n[STEP 5] Pre-submit readback...")
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(1000)
        form_snapshot = page.evaluate('''() => {
            const vals = {};
            document.querySelectorAll("input, textarea, select").forEach(el => {
                if (el.type === "hidden") return;
                const rect = el.getBoundingClientRect();
                if (rect.width <= 0) return;
                const k = el.id || el.name || "anon";
                vals[k] = (el.value || "").substring(0, 120);
            });
            return vals;
        }''')
        print("  Form snapshot (key fields):")
        for k in ["first_name", "last_name", "email", "phone"]:
            print(f"    {k} = {form_snapshot.get(k, '[NOT FOUND]')}")

        # Detect sponsorship field value
        sponsor_val = "[not detected]"
        for k, v in form_snapshot.items():
            if v.lower() in ["yes", "no"] and "sponsor" in k.lower():
                sponsor_val = f"{k}={v}"
        print(f"    sponsorship = {sponsor_val}")

        # Detect resume attached
        resume_attached = any("resume" in k.lower() and v for k, v in form_snapshot.items())
        print(f"    resume_attached = {resume_attached}")

        # Check for any Drive links or markup (FAIL-SAFE)
        full_text = " ".join(v for v in form_snapshot.values())
        if "docs.google" in full_text or "drive.google" in full_text:
            print("  !! ABORT — Drive link detected in form values!")
            take(page, "ABORT_drive_link.png")
            browser.close(); return
        if "{group|" in full_text or "&#" in full_text or "&amp;" in full_text:
            print("  !! ABORT — markup detected in form values!")
            take(page, "ABORT_markup.png")
            browser.close(); return

        print("  Readback OK — no drive links, no markup.")
        take(page, "04_readback.png")

        # -------------------------------------------------------
        # STEP 6 — SUBMIT
        # -------------------------------------------------------
        print("\n[STEP 6] Submitting...")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(2000)

        submitted = False
        for btn_name in ["Submit application", "Submit Application", "Submit"]:
            try:
                btn = page.get_by_role("button", name=btn_name, exact=False).first
                if btn.count() > 0 and btn.is_visible(timeout=5000):
                    btn.scroll_into_view_if_needed(); pause(0.3, 0.6)
                    btn.click(timeout=12000)
                    page.wait_for_timeout(10000)
                    submitted = True
                    print(f"  Clicked '{btn_name}'")
                    break
            except Exception as e:
                print(f"  btn '{btn_name}': {e}")

        if not submitted:
            # Try any submit-looking button
            try:
                btns = page.get_by_role("button").all()
                for b in btns:
                    txt = (b.text_content() or "").lower().strip()
                    if "submit" in txt:
                        b.scroll_into_view_if_needed(); pause()
                        b.click(timeout=12000)
                        page.wait_for_timeout(10000)
                        submitted = True
                        print(f"  Clicked fallback submit: '{txt}'")
                        break
            except Exception as e:
                print(f"  fallback submit ERR: {e}")

        take(page, "05_after_submit.png")

        final_url = page.url
        final_title = page.title()
        body_after = page.inner_text("body")
        body_safe = body_after[:2000].encode("ascii", "replace").decode("ascii")

        print(f"\n  URL after: {final_url}")
        print(f"  Title after: {final_title}")
        print(f"  Body excerpt:\n{body_safe[:800]}")

        # Detect success
        success_kws = ["thank you", "received", "submitted", "we got your", "application has been"]
        success = any(kw in body_after.lower() for kw in success_kws)

        if not success:
            # Check for validation errors
            print("\n  Checking for errors...")
            errs = page.locator(".error-message, .field_with_errors, [aria-invalid='true'], .error").all()
            for e in errs[:15]:
                try:
                    t = (e.text_content() or "").strip()[:150].encode("ascii", "replace").decode("ascii")
                    if t: print(f"    ERR: {t}")
                except: pass

        # -------------------------------------------------------
        # Save SUBMITTED.json
        # -------------------------------------------------------
        result = {
            "company": "Gong",
            "role": "Senior Talent Development Program Manager",
            "ats": "Greenhouse",
            "job_url": JOB_URL,
            "status": "submitted" if success else "attempted-check-screenshot",
            "confirmed_at": datetime.now().isoformat(),
            "url_after_submit": final_url,
            "title_after_submit": final_title,
            "body_preview": body_after[:500],
            "screenshot": str(OUT_DIR / "05_after_submit.png"),
            "notes": f"success={success}; review_flags={REVIEW_FLAGS}",
        }
        with open(ROLE_DIR / "SUBMITTED.json", "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)

        if success:
            print("\n" + "=" * 60)
            print("*** APPLICATION SUBMITTED SUCCESSFULLY ***")
            print("=" * 60)
        else:
            print("\n*** Submit may not have completed — check 05_after_submit.png ***")

        time.sleep(15)
        browser.close()

if __name__ == "__main__":
    main()
