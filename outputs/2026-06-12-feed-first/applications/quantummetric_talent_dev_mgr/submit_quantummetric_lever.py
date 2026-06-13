"""
Quantum Metric — Talent Development Manager
Lever ATS submission.
Port 9409, user-data-dir=C:\\Users\\chent\\ats_agent_9409
Step 0: verify live + no hard-stop. Step 1+: fill + submit.
"""
import os, sys, time, random, json, re
from datetime import datetime
from pathlib import Path

sys.path.insert(0, r"C:\Users\chent\Agentic_Workflows_2026\jamie-autopilot\lib")
from patchright.sync_api import sync_playwright

ROLE_DIR = Path(r"C:\Users\chent\Agentic_Workflows_2026\oracle-job-search\outputs\2026-06-12-feed-first\applications\quantummetric_talent_dev_mgr")
RESUME   = ROLE_DIR / "resume.pdf"
COVER    = ROLE_DIR / "cover_letter.pdf"
OUT_DIR  = ROLE_DIR / "screenshots"
OUT_DIR.mkdir(exist_ok=True)

JOB_URL   = "https://jobs.lever.co/quantummetric/6fbf169b-05f7-40f1-a3f0-8349bb4e494e"
APPLY_URL = "https://jobs.lever.co/quantummetric/6fbf169b-05f7-40f1-a3f0-8349bb4e494e/apply"
BOARD_URL = "https://jobs.lever.co/quantummetric"
PROFILE_DIR = r"C:\Users\chent\ats_agent_9409"

# Candidate data
FIRST      = "Yi-Chieh"
LAST       = "Cheng"
EMAIL      = "jamiecheng0103@gmail.com"
PHONE      = "(213) 700-3831"
COMPANY    = "InGenius Prep"
LINKEDIN   = "https://www.linkedin.com/in/jamieyccheng/"
PREF_NAME  = "Jamie"

# Lever standard fields
# urls[LinkedIn] = LINKEDIN
# org = COMPANY

# Free-text — Jamie's voice, truthful (Talent Dev / Quantum Metric specific)
SCREENING_WHY = (
    "I'm drawn to this role because Quantum Metric's product — surfacing behavioral "
    "data to help teams understand what customers actually experience — mirrors exactly "
    "how I approach talent development: ground every program in evidence, not assumption. "
    "At InGenius Prep I manage 15-20+ learning programs and 8-10+ vendors, run needs "
    "assessments with 25+ global stakeholders to identify capability gaps, and have "
    "designed 3 new programs from the ground up. At NextGen Healthcare I led a "
    "manager-effectiveness initiative and analyzed 2,000+ employee experiences to guide "
    "C-suite L&D strategy. At Vestas I designed an Inclusive Leadership workshop that "
    "started with 12 leaders and scaled to 23 global locations — building programs that "
    "travel across a distributed org is central to my work. My MS in Org Psychology "
    "(USC, 3.95 GPA) gives me the research foundation to measure whether people grow, "
    "not just whether they attended. I'm excited to bring that combination of "
    "evidence-based design and cross-functional program management to Quantum Metric."
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

def fill_field(page, selector, value, desc=""):
    """Fill a visible input/textarea by CSS selector."""
    try:
        el = page.locator(selector).first
        if el.count() > 0 and el.is_visible(timeout=4000):
            el.click(); pause(0.2, 0.4)
            el.triple_click(); pause(0.1, 0.2)
            el.fill(value); pause(0.2, 0.4)
            print(f"  {desc or selector} = {value[:80]}")
            return True
    except Exception as e:
        print(f"  {desc or selector} ERR: {e}")
    return False

def choose_radio_or_select(page, label_text, value_text):
    """Find a radio button or select option by label text and value."""
    label_lower = label_text.lower()
    value_lower = value_text.lower()

    # Try select dropdowns first
    try:
        selects = page.locator("select").all()
        for sel in selects:
            # Check nearby label
            try:
                parent = sel.locator("xpath=ancestor::div[@class][1]")
                p_text = (parent.inner_text(timeout=2000) or "").lower()
            except:
                p_text = ""
            if label_lower in p_text or any(w in p_text for w in label_lower.split()):
                # Try to pick the option
                options = sel.locator("option").all()
                for opt in options:
                    opt_text = (opt.text_content() or "").lower().strip()
                    if value_lower in opt_text or opt_text in value_lower:
                        sel.select_option(value=opt.get_attribute("value") or "")
                        print(f"  select({label_text[:40]}) = {value_text}")
                        pause()
                        return True
    except Exception as e:
        print(f"  select ERR: {e}")

    # Try radio buttons
    try:
        # Lever custom cards use radio inputs
        radios = page.locator('input[type="radio"]').all()
        for r in radios:
            # Get the label for this radio
            rid = r.get_attribute("id") or ""
            val = (r.get_attribute("value") or "").lower()
            if not rid:
                continue
            try:
                lbl = page.locator(f'label[for="{rid}"]')
                lbl_text = (lbl.text_content(timeout=1000) or "").lower().strip()
            except:
                lbl_text = val

            # Check parent card for question text
            try:
                card_text = (r.locator("xpath=ancestor::div[contains(@class,'custom-question') or contains(@class,'application-question')][1]").inner_text(timeout=2000) or "").lower()
            except:
                card_text = ""

            question_matches = label_lower in card_text or any(w in card_text for w in label_lower.split() if len(w) > 3)
            value_matches = value_lower in lbl_text or lbl_text in value_lower or value_lower == val

            if question_matches and value_matches:
                r.scroll_into_view_if_needed(); pause(0.2, 0.4)
                r.check()
                print(f"  radio({label_text[:40]}) = {lbl_text}")
                pause()
                return True
    except Exception as e:
        print(f"  radio ERR: {e}")

    return False

def main():
    print("=" * 60)
    print("QUANTUM METRIC — Talent Development Manager")
    print(f"URL: {JOB_URL}")
    print("=" * 60)

    with sync_playwright() as p:
        # Clean up LOCK file if needed
        lock_file = Path(PROFILE_DIR) / "Default" / "LOCK"
        if lock_file.exists():
            try:
                lock_file.unlink()
                print("  Removed stale LOCK file")
            except: pass

        browser = p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_DIR,
            channel="chrome",
            headless=False,
            no_viewport=True,
            args=[
                "--start-maximized",
                f"--remote-debugging-port=9409",
            ],
        )
        page = browser.pages[0] if browser.pages else browser.new_page()
        page.set_default_timeout(25000)

        # -------------------------------------------------------
        # STEP 0 — verify live + scan for hard-stop language
        # -------------------------------------------------------
        print("\n[STEP 0] Verifying job posting...")
        page.goto(JOB_URL, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(5000)
        take(page, "00_landing.png")

        body_text = page.inner_text("body").lower()
        title_text = page.title()
        url_now = page.url
        print(f"  Title: {title_text}")
        print(f"  URL:   {url_now}")

        # Check for 404 / dead posting
        dead_signals = ["404", "job not found", "no longer", "position has been filled",
                        "posting has expired", "this job is no longer"]
        is_dead = any(s in body_text for s in dead_signals) or "404" in title_text

        if is_dead:
            print(f"\n  DEAD posting detected — checking board for alternatives...")
            take(page, "00_dead.png")

            # Load the board and look for similar roles
            page.goto(BOARD_URL, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(4000)
            take(page, "00_board.png")
            board_text = page.inner_text("body")

            # Look for talent/learning/people development roles
            people_roles = []
            links = page.locator("a[data-qa='posting-name'], a.posting-title, .posting-name").all()
            for link in links:
                txt = (link.text_content() or "").strip()
                url = link.get_attribute("href") or ""
                if any(kw in txt.lower() for kw in ["talent", "learning", "people", "development", "l&d", "hr"]):
                    people_roles.append({"title": txt, "url": url})

            result = {
                "company": "Quantum Metric",
                "role": "Talent Development Manager",
                "ats": "Lever",
                "job_url": JOB_URL,
                "status": "skip-dead",
                "confirmed_at": datetime.now().isoformat(),
                "alternative_people_roles": people_roles,
                "notes": f"Original posting 404/expired. Board scanned. Found {len(people_roles)} people roles.",
            }
            with open(ROLE_DIR / "SUBMITTED.json", "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2)
            print(f"\n  RESULT: skip-dead")
            print(f"  People roles found on board: {people_roles}")
            browser.close(); return

        # Confirm "Talent Development" in title/body
        if "talent development" not in body_text and "talent development" not in title_text.lower():
            print("  WARNING: 'Talent Development' not found in body — scanning page content...")

        print(f"  Body excerpt: {body_text[200:600]}")

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
            "without need for sponsorship",
            "without visa sponsorship",
            "not able to sponsor",
        ]
        for pat in no_sponsor_patterns:
            if pat in body_text:
                idx = body_text.find(pat)
                snippet = body_text[max(0, idx-80):idx+200].replace("\n", " ")
                print(f'\n  SKIP — explicit no-sponsor: "...{snippet}..."')
                result = {
                    "company": "Quantum Metric",
                    "role": "Talent Development Manager",
                    "ats": "Lever",
                    "job_url": JOB_URL,
                    "status": "skip-no-sponsor",
                    "confirmed_at": datetime.now().isoformat(),
                    "no_sponsor_quote": snippet,
                    "notes": f"Explicit no-sponsorship language: '{pat}'",
                }
                with open(ROLE_DIR / "SUBMITTED.json", "w", encoding="utf-8") as f:
                    json.dump(result, f, indent=2)
                browser.close(); return

        # Check ITAR
        if "itar" in body_text or ("us person" in body_text and "requirement" in body_text):
            print("  SKIP — ITAR / US Person requirement found")
            result = {
                "company": "Quantum Metric",
                "role": "Talent Development Manager",
                "ats": "Lever",
                "job_url": JOB_URL,
                "status": "skip-itar",
                "confirmed_at": datetime.now().isoformat(),
            }
            with open(ROLE_DIR / "SUBMITTED.json", "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2)
            browser.close(); return

        # Note YOE and role scope from JD
        print("\n  LIVE — no hard-stop language found.")
        print("  Checking role scope + YOE requirements...")
        # Extract salary/yoe context
        for kw in ["years of experience", "salary", "compensation", "$", "remote"]:
            if kw in body_text:
                idx = body_text.find(kw)
                snip = body_text[max(0, idx-30):idx+120].replace("\n", " ")
                print(f"    [{kw}] ...{snip}...")

        print("\n  Proceeding to application form.")

        # -------------------------------------------------------
        # STEP 1 — Navigate to Lever /apply form
        # -------------------------------------------------------
        print("\n[STEP 1] Opening Lever apply form...")
        page.goto(APPLY_URL, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(5000)
        take(page, "01_apply_form.png")

        apply_url_now = page.url
        apply_title = page.title()
        print(f"  Apply URL: {apply_url_now}")
        print(f"  Apply Title: {apply_title}")

        # Verify we got the form (Lever forms have these characteristic elements)
        form_check = page.locator("input[name='name'], #name, input[placeholder*='name' i]").count()
        print(f"  Name field count: {form_check}")

        # -------------------------------------------------------
        # STEP 2 — Fill standard Lever fields
        # -------------------------------------------------------
        print("\n[STEP 2] Filling standard fields...")

        # Lever standard: name is a single full-name field OR first/last split
        # First check if there's a single "name" field
        name_single = page.locator("input[name='name'], #name").first
        if name_single.count() > 0 and name_single.is_visible(timeout=3000):
            try:
                name_single.fill(f"{FIRST} {LAST}"); pause()
                print(f"  name (single) = {FIRST} {LAST}")
            except Exception as e:
                print(f"  name single ERR: {e}")
                # Try first/last split
                fill_field(page, "input[name='firstName'], #firstName, input[placeholder*='first' i]", FIRST, "first_name")
                fill_field(page, "input[name='lastName'], #lastName, input[placeholder*='last' i]", LAST, "last_name")
        else:
            # Try first/last split
            filled = fill_field(page, "input[name='firstName'], #firstName", FIRST, "first_name")
            if not filled:
                fill_field(page, "input[placeholder*='first' i]", FIRST, "first_name")
            filled2 = fill_field(page, "input[name='lastName'], #lastName", LAST, "last_name")
            if not filled2:
                fill_field(page, "input[placeholder*='last' i]", LAST, "last_name")

        # Email
        fill_field(page, "input[name='email'], #email, input[type='email']", EMAIL, "email")

        # Phone
        fill_field(page, "input[name='phone'], #phone, input[type='tel']", PHONE, "phone")

        # Current company / org
        company_filled = fill_field(page, "input[name='org'], #org, input[name='company']", COMPANY, "current_company")
        if not company_filled:
            fill_field(page, "input[placeholder*='company' i], input[placeholder*='employer' i]", COMPANY, "current_company")

        # LinkedIn URL — Lever uses urls[LinkedIn] field name
        linkedin_filled = fill_field(page, "input[name='urls[LinkedIn]']", LINKEDIN, "linkedin")
        if not linkedin_filled:
            linkedin_filled = fill_field(page, "input[name='urls[0]'], input[placeholder*='linkedin' i], input[placeholder*='LinkedIn' i]", LINKEDIN, "linkedin")
        if not linkedin_filled:
            # Try finding URL inputs and fill the LinkedIn one
            url_inputs = page.locator("input[type='url'], input[placeholder*='url' i]").all()
            for inp in url_inputs:
                try:
                    ph = (inp.get_attribute("placeholder") or "").lower()
                    nm = (inp.get_attribute("name") or "").lower()
                    if "linkedin" in ph or "linkedin" in nm:
                        inp.fill(LINKEDIN); pause()
                        print(f"  linkedin (url-input) = {LINKEDIN}")
                        break
                except: pass

        take(page, "02_fields_filled.png")

        # -------------------------------------------------------
        # STEP 3 — Upload resume + cover letter
        # -------------------------------------------------------
        print("\n[STEP 3] Uploading files...")

        # Lever resume upload — look for file input or drag-drop zone
        resume_uploaded = False
        resume_selectors = [
            "input[name='resume']",
            "#resume",
            "input[type='file'][name*='resume' i]",
            "input[type='file'][accept*='pdf']",
            "input[type='file']",
        ]
        for sel in resume_selectors:
            try:
                el = page.locator(sel).first
                if el.count() > 0:
                    el.set_input_files(str(RESUME))
                    page.wait_for_timeout(4000)
                    print(f"  resume.pdf uploaded via {sel} ({RESUME.stat().st_size} bytes)")
                    resume_uploaded = True
                    break
            except Exception as e:
                print(f"  resume sel {sel} ERR: {e}")

        if not resume_uploaded:
            print("  !! Could not upload resume via any selector")

        # Cover letter — optional on Lever
        if COVER.exists():
            for sel in ["input[name='coverLetter']", "#coverLetter", "input[type='file']:nth-child(2)"]:
                try:
                    el = page.locator(sel).nth(0 if "coverLetter" in sel else 1)
                    if el.count() > 0 and el.is_visible(timeout=2000):
                        el.set_input_files(str(COVER))
                        page.wait_for_timeout(3000)
                        print("  cover_letter.pdf uploaded")
                        break
                except: pass

        take(page, "03_files_uploaded.png")

        # -------------------------------------------------------
        # STEP 4 — Scan + fill custom cards / screening questions
        # -------------------------------------------------------
        print("\n[STEP 4] Scanning custom cards + screening questions...")

        page.wait_for_timeout(2000)

        # Lever custom application cards — scan all visible inputs
        all_inputs = page.evaluate('''() => {
            const out = [];
            document.querySelectorAll("input, textarea, select").forEach(el => {
                const rect = el.getBoundingClientRect();
                if (rect.width <= 0 || rect.height <= 0) return;
                if (el.type === "hidden" || el.type === "file") return;
                const id = el.id || "";
                const name = el.name || "";
                const type = el.tagName.toLowerCase() + (el.type ? ":" + el.type : "");
                const placeholder = el.placeholder || "";
                let label = "";
                if (id) {
                    const lbl = document.querySelector(`label[for="${id}"]`);
                    if (lbl) label = (lbl.innerText || lbl.textContent || "").trim();
                }
                if (!label) {
                    let parent = el.parentElement;
                    for (let i = 0; i < 6 && parent; i++) {
                        const txt = (parent.innerText || "").trim().split("\\n")[0];
                        if (txt && txt.length > 3 && txt.length < 300) { label = txt; break; }
                        parent = parent.parentElement;
                    }
                }
                out.push({id, name, type, label: label.substring(0, 250), placeholder});
            });
            return out;
        }''')

        print(f"  Found {len(all_inputs)} visible input elements")
        for q in all_inputs:
            print(f"    [{q['type']}] id={q['id']!r} name={q['name']!r} label={q['label'][:60]!r}")

        FILLED_NAMES = {"name", "email", "phone", "org", "urls[LinkedIn]", "urls[0]",
                        "firstName", "lastName", "resume", "coverLetter", "company"}

        for q in all_inputs:
            nm = q.get("name", "")
            qid = q.get("id", "")
            tp = q.get("type", "")
            ll = q.get("label", "").lower()
            ph = q.get("placeholder", "").lower()

            if nm in FILLED_NAMES or qid in FILLED_NAMES:
                continue
            if not nm and not qid:
                continue

            sel = f"#{qid}" if qid else f"[name='{nm}']"

            try:
                # Preferred name
                if ("preferred" in ll or "preferred" in ph) and ("name" in ll or "name" in ph):
                    fill_field(page, sel, PREF_NAME, "preferred_name")
                    continue

                # LinkedIn (in case we missed it above)
                if "linkedin" in ll or "linkedin" in ph or "linkedin" in nm.lower():
                    fill_field(page, sel, LINKEDIN, "linkedin_custom")
                    continue

                # Website / portfolio
                if ("website" in ll or "portfolio" in ll or "website" in ph) and "input" in tp:
                    continue  # Skip

                # How did you hear
                if "how did you hear" in ll or "source" in ll or "referred" in ll:
                    if "select" in tp:
                        try:
                            page.locator(sel).select_option(label="LinkedIn")
                            print("  source = LinkedIn"); pause()
                        except:
                            try: page.locator(sel).select_option(index=1); pause()
                            except: pass
                    elif "input:text" in tp or "textarea" in tp:
                        fill_field(page, sel, "LinkedIn", "source")
                    continue

                # Work authorization / legally authorized
                if "legally authorized" in ll or "authorized to work" in ll:
                    if "radio" in tp:
                        choose_radio_or_select(page, ll, "Yes")
                    elif "select" in tp:
                        try:
                            page.locator(sel).select_option(label="Yes"); pause()
                            print(f"  authorized = Yes")
                        except: pass
                    elif "input" in tp:
                        fill_field(page, sel, "Yes", "authorized")
                    continue

                # Sponsorship — ALWAYS YES
                if "sponsor" in ll or ("visa" in ll and "require" in ll) or "now or in the future" in ll:
                    if "radio" in tp:
                        choose_radio_or_select(page, ll, "Yes")
                    elif "select" in tp:
                        try:
                            page.locator(sel).select_option(label="Yes"); pause()
                            print(f"  sponsorship = Yes")
                        except: pass
                    elif "input" in tp:
                        fill_field(page, sel, "Yes", "sponsorship")
                    continue

                # Salary
                if "salary" in ll or "compensation" in ll or "desired" in ll:
                    fill_field(page, sel, "110000-140000", "salary")
                    continue

                # Open-ended text / textarea — use screening why
                if "textarea" in tp and any(k in ll for k in
                        ["why", "tell us", "describe", "experience", "background",
                         "interest", "motivation", "share", "relevant", "learn"]):
                    fill_field(page, sel, SCREENING_WHY, f"screening({ll[:30]})")
                    continue

                # EEO / Demographics — handle truthfully
                if "gender" in ll:
                    if "select" in tp:
                        for v in ["Female", "Woman", "Female (she/her)", "Female/Woman"]:
                            try:
                                page.locator(sel).select_option(label=v); pause()
                                print(f"  gender = {v}"); break
                            except: pass
                    elif "radio" in tp:
                        choose_radio_or_select(page, ll, "Female")
                    continue

                if "hispanic" in ll or "latino" in ll:
                    if "select" in tp:
                        for v in ["No", "Not Hispanic or Latino", "No, Not Hispanic or Latino"]:
                            try:
                                page.locator(sel).select_option(label=v); pause()
                                print(f"  hispanic = {v}"); break
                            except: pass
                    elif "radio" in tp:
                        choose_radio_or_select(page, ll, "No")
                    continue

                if "race" in ll or "ethnicity" in ll:
                    if "select" in tp:
                        for v in ["Asian", "Asian (Not Hispanic or Latino)", "Asian / Pacific Islander"]:
                            try:
                                page.locator(sel).select_option(label=v); pause()
                                print(f"  race = {v}"); break
                            except: pass
                    elif "radio" in tp:
                        choose_radio_or_select(page, ll, "Asian")
                    continue

                if "veteran" in ll:
                    if "select" in tp:
                        for v in ["I am not a protected veteran", "Not a protected veteran",
                                  "I don't wish to answer", "Decline to self-identify"]:
                            try:
                                page.locator(sel).select_option(label=v); pause()
                                print(f"  veteran = {v}"); break
                            except: pass
                    elif "radio" in tp:
                        choose_radio_or_select(page, ll, "not a protected veteran")
                    continue

                if "disability" in ll:
                    if "select" in tp:
                        for v in ["No, I do not have a disability",
                                  "No, I don't have a disability",
                                  "I don't wish to answer", "Decline to self-identify"]:
                            try:
                                page.locator(sel).select_option(label=v); pause()
                                print(f"  disability = {v}"); break
                            except: pass
                    elif "radio" in tp:
                        choose_radio_or_select(page, ll, "No")
                    continue

            except Exception as e:
                print(f"  Q({qid}|{nm}|{ll[:25]}): ERR {e}")

        take(page, "04_custom_cards.png")

        # -------------------------------------------------------
        # STEP 5 — Pre-submit readback
        # -------------------------------------------------------
        print("\n[STEP 5] Pre-submit readback...")
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(1500)

        form_snapshot = page.evaluate('''() => {
            const vals = {};
            document.querySelectorAll("input, textarea, select").forEach(el => {
                if (el.type === "hidden" || el.type === "file") return;
                const rect = el.getBoundingClientRect();
                if (rect.width <= 0) return;
                const k = (el.id || el.name || el.placeholder || "anon").substring(0, 60);
                const v = (el.value || "").substring(0, 150);
                if (v) vals[k] = v;
            });
            return vals;
        }''')

        print("  Form snapshot (all filled fields):")
        for k, v in form_snapshot.items():
            print(f"    {k} = {v[:100]}")

        # Safety checks
        full_values = " ".join(v for v in form_snapshot.values()).lower()

        if "docs.google" in full_values or "drive.google" in full_values:
            print("  !! ABORT — Drive link detected in form fields!")
            take(page, "ABORT_drive_link.png")
            browser.close(); return

        if "{group|" in full_values or "&#" in full_values or "&amp;" in full_values:
            print("  !! ABORT — Template markup detected!")
            take(page, "ABORT_markup.png")
            browser.close(); return

        # Check name filled
        name_ok = any(FIRST.lower() in v.lower() or LAST.lower() in v.lower() for v in form_snapshot.values())
        email_ok = EMAIL in form_snapshot.values() or any(EMAIL in v for v in form_snapshot.values())
        print(f"  name_ok={name_ok}, email_ok={email_ok}")

        if not email_ok:
            print("  WARNING: Email not confirmed in form snapshot — may be an issue")

        # Scroll down for a full-form screenshot
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(1000)
        take(page, "05_pre_submit_bottom.png")
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(500)
        take(page, "05_pre_submit_top.png")

        print("  Readback complete — no drive links, no markup.")

        # -------------------------------------------------------
        # STEP 6 — SUBMIT
        # -------------------------------------------------------
        print("\n[STEP 6] Submitting application...")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(2000)

        submitted = False

        # Lever submit button patterns
        submit_selectors = [
            "button[data-qa='btn-submit-form']",
            "button[type='submit']",
            ".template-btn-submit",
            "button:has-text('Submit application')",
            "button:has-text('Submit Application')",
            "button:has-text('Submit')",
            "input[type='submit']",
        ]
        for sel in submit_selectors:
            try:
                btn = page.locator(sel).first
                if btn.count() > 0 and btn.is_visible(timeout=5000):
                    btn.scroll_into_view_if_needed(); pause(0.5, 1.0)
                    print(f"  Found submit button: {sel}")
                    take(page, "06_before_click.png")
                    btn.click(timeout=15000)
                    page.wait_for_timeout(12000)
                    submitted = True
                    print(f"  Clicked submit: {sel}")
                    break
            except Exception as e:
                print(f"  submit sel {sel}: {e}")

        if not submitted:
            # Last resort: find any button with "submit" text
            try:
                all_btns = page.get_by_role("button").all()
                for b in all_btns:
                    txt = (b.text_content() or "").lower().strip()
                    if "submit" in txt:
                        b.scroll_into_view_if_needed(); pause(0.3, 0.6)
                        print(f"  Fallback submit button: '{txt}'")
                        take(page, "06_fallback_before_click.png")
                        b.click(timeout=15000)
                        page.wait_for_timeout(12000)
                        submitted = True
                        print("  Clicked fallback submit button")
                        break
            except Exception as e:
                print(f"  fallback submit ERR: {e}")

        take(page, "07_after_submit.png")

        final_url = page.url
        final_title = page.title()
        body_after = page.inner_text("body")
        print(f"\n  URL after submit: {final_url}")
        print(f"  Title after submit: {final_title}")
        print(f"  Body (first 1000 chars): {body_after[:1000]}")

        # Detect success
        success_kws = ["thank you", "received", "submitted", "we've got your",
                       "application has been", "we'll be in touch", "confirmation",
                       "application submitted", "successfully submitted"]
        success = any(kw in body_after.lower() for kw in success_kws)

        if not success:
            print("\n  Checking for validation errors...")
            errs = page.locator(
                ".error-message, .field_with_errors, [aria-invalid='true'], "
                ".error, [class*='error'], [class*='invalid']"
            ).all()
            for e in errs[:15]:
                try:
                    t = (e.text_content() or "").strip()[:200]
                    if t: print(f"    ERR: {t}")
                except: pass

        # -------------------------------------------------------
        # Save SUBMITTED.json
        # -------------------------------------------------------
        status = "submitted" if success else "attempted-check-screenshot"
        result = {
            "company": "Quantum Metric",
            "role": "Talent Development Manager",
            "ats": "Lever",
            "job_url": JOB_URL,
            "apply_url": APPLY_URL,
            "status": status,
            "confirmed_at": datetime.now().isoformat(),
            "url_after_submit": final_url,
            "title_after_submit": final_title,
            "body_preview": body_after[:600],
            "screenshot": str(OUT_DIR / "07_after_submit.png"),
            "notes": f"success_detected={success}; submitted_btn_clicked={submitted}",
        }
        with open(ROLE_DIR / "SUBMITTED.json", "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)

        if success:
            print("\n" + "=" * 60)
            print("*** APPLICATION SUBMITTED SUCCESSFULLY ***")
            print("=" * 60)
        else:
            print("\n*** Submit may need manual review — check 07_after_submit.png ***")
            if not submitted:
                print("    Submit button was NOT clicked — possible form issue")

        time.sleep(20)
        browser.close()

if __name__ == "__main__":
    main()
