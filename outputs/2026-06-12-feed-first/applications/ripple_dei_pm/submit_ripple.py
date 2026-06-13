#!/usr/bin/env python3
"""
Ripple DEI PM — Greenhouse no-account submit.
Dedicated Chrome on port 9404 to avoid collision with other agents.
"""
import os, sys, time, json, subprocess, random
from datetime import datetime
from pathlib import Path

# ── paths ──────────────────────────────────────────────────────────────────
ROLE_DIR   = Path(r"C:\Users\chent\Agentic_Workflows_2026\oracle-job-search\outputs\2026-06-12-feed-first\applications\ripple_dei_pm")
RESUME     = ROLE_DIR / "resume.pdf"
COVER      = ROLE_DIR / "cover_letter.pdf"
SCREENSHOTS = ROLE_DIR / "screenshots"
SCREENSHOTS.mkdir(exist_ok=True)

CHROME_BIN = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
DEBUG_PORT = 9404
USER_DATA  = r"C:\Users\chent\ats_agent_9404"

# The Greenhouse form URL (canonical boards.greenhouse.io URL — no account needed)
APP_URL = "https://boards.greenhouse.io/ripple/jobs/7951682"

# ── candidate data ─────────────────────────────────────────────────────────
FIRST, LAST   = "Yi-Chieh", "Cheng"
EMAIL         = "jamiecheng0103@gmail.com"
PHONE         = "2137003831"
COUNTRY       = "United States"
CITY          = "New York, NY"
LINKEDIN      = "https://www.linkedin.com/in/jamieyccheng/"
PREFERRED     = "Jamie"
AUTHORIZED    = "Yes"
SPONSOR       = "Yes"
HOW_HEARD     = "LinkedIn"

# Screening / short-answer template (Jamie's real voice, truthful):
SCREENING_ANSWER = (
    "I have worked on DEI initiatives across multiple organizational contexts. "
    "At Vestas Wind Systems, I developed and scaled an Inclusive Leadership workshop to 23 locations, "
    "co-designed a DEI culture pilot, and partnered with HR to embed inclusion practices into people processes. "
    "At NextGen, I consulted on DEI strategy and inclusive leadership for client organizations. "
    "In my current role at InGenius Prep, I manage 20+ programs and 10+ vendors, including initiatives "
    "with DEI-adjacent impact. My MS in Applied Organizational Psychology from USC grounds this work in "
    "research-backed frameworks. I am drawn to Ripple's mission of enabling economic inclusion globally "
    "and see the DEI PM role as a natural place to bring these skills to scale."
)

def pause(lo=0.4, hi=0.9): time.sleep(random.uniform(lo, hi))

def launch_chrome():
    """Launch dedicated Chrome on 9404 if not already running."""
    import socket
    try:
        with socket.create_connection(("127.0.0.1", DEBUG_PORT), timeout=2):
            print(f"[chrome] already running on {DEBUG_PORT}")
            return
    except Exception:
        pass
    print(f"[chrome] launching on port {DEBUG_PORT}...")
    args = [
        CHROME_BIN,
        f"--remote-debugging-port={DEBUG_PORT}",
        f"--user-data-dir={USER_DATA}",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-features=TranslateUI",
        "--disable-popup-blocking",
        "--disable-notifications",
        "--window-size=1400,900",
    ]
    subprocess.Popen(args, creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP)
    time.sleep(4)
    print("[chrome] launched, waiting for CDP...")
    time.sleep(3)

def combo(page, locator_or_selector, option_text):
    """Drive a Greenhouse react-select combobox."""
    from patchright.sync_api import expect
    want = option_text.strip().lower()
    if isinstance(locator_or_selector, str):
        loc = page.locator(locator_or_selector)
    else:
        loc = locator_or_selector
    loc.scroll_into_view_if_needed(); pause()
    loc.click(); pause(); page.wait_for_timeout(600)

    # Try clicking pre-rendered options (no typing needed)
    try:
        opts = page.locator(".select__option"); n = opts.count()
        for i in range(n):
            if want in opts.nth(i).inner_text().strip().lower():
                opts.nth(i).click(); pause(); return True
    except: pass

    # Type + click
    try:
        page.keyboard.type(option_text, delay=60); page.wait_for_timeout(900)
        opts = page.locator(".select__option"); n = opts.count()
        for i in range(n):
            if want in opts.nth(i).inner_text().strip().lower():
                opts.nth(i).click(); pause(); return True
    except: pass

    # Last resort: Enter
    page.wait_for_timeout(300); page.keyboard.press("Enter"); pause()
    return True

def fill_location_autocomplete(page):
    """Fill the Greenhouse location autocomplete (Google Places-style)."""
    for sel in [
        "#candidate-location",
        'input[name*="location" i]',
        'input[id*="location" i]',
        'input[placeholder*="city" i]',
        'input[placeholder*="location" i]',
    ]:
        try:
            loc = page.locator(sel).first
            if loc.count() > 0 and loc.is_visible(timeout=2500):
                loc.click(); pause(); page.wait_for_timeout(400)
                page.keyboard.type("New York, NY", delay=60); pause()
                page.wait_for_timeout(2000)
                # Try pressing ArrowDown + Enter to pick first suggestion
                page.keyboard.press("ArrowDown"); pause()
                page.keyboard.press("Enter"); pause()
                print(f"  [location] set via {sel}")
                return True
        except: continue
    return False

def fill_demog_select(page, field_id, candidates):
    """Fill a demographics select/combobox, trying each candidate until one works."""
    try:
        loc = page.locator(f"#{field_id}")
        loc.scroll_into_view_if_needed(); pause(); loc.click(); pause()
        page.wait_for_timeout(400)
        for tx in candidates:
            want = tx.lower()
            # Direct option click
            opts = page.locator(".select__option"); n = opts.count()
            for i in range(n):
                if want in opts.nth(i).inner_text().strip().lower():
                    opts.nth(i).click(); pause()
                    print(f"  [demog] #{field_id} = {tx}")
                    return True
            # Type to filter
            try:
                for _ in range(30): page.keyboard.press("Backspace")
                page.keyboard.type(tx, delay=60); page.wait_for_timeout(600)
                opts = page.locator(".select__option"); n = opts.count()
                for i in range(n):
                    if want in opts.nth(i).inner_text().strip().lower():
                        opts.nth(i).click(); pause()
                        print(f"  [demog] #{field_id} = {tx}")
                        return True
            except: pass
        # Try the native select
        try:
            page.select_option(f"#{field_id}", label=candidates[0])
            print(f"  [demog] #{field_id} native select = {candidates[0]}")
            return True
        except: pass
        page.keyboard.press("Escape")
    except Exception as e:
        print(f"  [demog] #{field_id} error: {e}")
    return False

def main():
    launch_chrome()

    from patchright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(f"http://localhost:{DEBUG_PORT}")
        ctx = browser.contexts[0] if browser.contexts else browser.new_context()
        page = ctx.new_page() if ctx.pages else ctx.pages[0]
        # Use new page to ensure clean state
        page = ctx.new_page()
        page.set_default_timeout(15000)

        # ── Step 1: Navigate ───────────────────────────────────────────────
        print(f"\n[step1] navigating to {APP_URL}")
        page.goto(APP_URL, wait_until="domcontentloaded", timeout=40000)
        page.wait_for_timeout(5000)
        page.screenshot(path=str(SCREENSHOTS / "01_landing.png"), full_page=True)
        print(f"  title: {page.title()}")
        print(f"  url:   {page.url}")

        # Check if the form is embedded (iframe) vs direct
        iframes = page.frames
        print(f"  frames: {len(iframes)}")
        # If there's a Greenhouse iframe, switch to it
        target_frame = page
        for fr in iframes:
            if "greenhouse" in (fr.url or "").lower() or fr.url.startswith("https://boards.greenhouse.io"):
                target_frame = fr
                print(f"  switching to iframe: {fr.url}")
                break

        # ── Step 2: Fill personal fields ──────────────────────────────────
        print("\n[step2] personal fields...")

        # First name
        try:
            target_frame.locator("#first_name").fill(FIRST); pause()
            print(f"  first_name = {FIRST}")
        except Exception as e:
            print(f"  first_name err: {e}")

        # Last name
        try:
            target_frame.locator("#last_name").fill(LAST); pause()
            print(f"  last_name = {LAST}")
        except Exception as e:
            print(f"  last_name err: {e}")

        # Email
        try:
            target_frame.locator("#email").fill(EMAIL); pause()
            print(f"  email = {EMAIL}")
        except Exception as e:
            print(f"  email err: {e}")

        # Phone
        try:
            target_frame.locator("#phone").fill(PHONE); pause()
            print(f"  phone = {PHONE}")
        except Exception as e:
            print(f"  phone err: {e}")

        # Country (combobox)
        try:
            combo(target_frame, target_frame.locator("#country").first, COUNTRY)
            print(f"  country = {COUNTRY}")
        except Exception as e:
            print(f"  country err: {e}")

        # Location
        loc_ok = fill_location_autocomplete(target_frame)
        if not loc_ok:
            print("  [location] NOT filled — will check again later")

        # LinkedIn
        try:
            li_field = target_frame.locator("#job_application_answers_attributes_0_text_value, input[id*='linkedin' i]").first
            if li_field.count() > 0 and li_field.is_visible(timeout=2500):
                li_field.fill(LINKEDIN); pause()
                print(f"  linkedin = {LINKEDIN}")
            else:
                # Try by label text
                all_inputs = target_frame.locator("input[type='text']").all()
                for inp in all_inputs:
                    try:
                        label_text = ""
                        inp_id = inp.get_attribute("id") or ""
                        if inp_id:
                            lbl = target_frame.locator(f"label[for='{inp_id}']")
                            if lbl.count() > 0:
                                label_text = lbl.inner_text().lower()
                        if "linkedin" in label_text or "linkedin" in inp_id.lower():
                            inp.fill(LINKEDIN); pause()
                            print(f"  linkedin (by label) = {LINKEDIN}")
                            break
                    except: continue
        except Exception as e:
            print(f"  linkedin err: {e}")

        # ── Step 3: Upload resume ──────────────────────────────────────────
        print("\n[step3] resume upload...")
        try:
            target_frame.locator("#resume").set_input_files(str(RESUME)); pause()
            target_frame.wait_for_timeout(3000)
            print(f"  resume OK ({RESUME.stat().st_size} bytes)")
        except Exception as e:
            print(f"  #resume err: {e}; trying file input nth(0)")
            try:
                target_frame.locator('input[type="file"]').nth(0).set_input_files(str(RESUME)); pause()
                target_frame.wait_for_timeout(3000)
                print("  resume OK via nth(0)")
            except Exception as e2:
                print(f"  resume nth(0) err: {e2}")

        # ── Step 4: Upload cover letter ────────────────────────────────────
        if COVER.exists():
            print("\n[step4] cover letter upload...")
            try:
                target_frame.locator("#cover_letter").set_input_files(str(COVER)); pause()
                target_frame.wait_for_timeout(3000)
                print("  cover OK")
            except Exception as e:
                print(f"  #cover_letter err: {e}; trying nth(1)")
                try:
                    target_frame.locator('input[type="file"]').nth(1).set_input_files(str(COVER)); pause()
                    target_frame.wait_for_timeout(3000)
                    print("  cover OK via nth(1)")
                except Exception as e2:
                    print(f"  cover nth(1) err: {e2}")

        page.screenshot(path=str(SCREENSHOTS / "02_uploaded.png"), full_page=True)

        # ── Step 5: Scan all custom questions ─────────────────────────────
        print("\n[step5] scanning custom questions...")
        try:
            questions = target_frame.evaluate('''() => {
                const out = [];
                document.querySelectorAll("input, textarea, select").forEach(el => {
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
                        let p = el.parentElement;
                        for (let i=0; i<5 && p; i++) {
                            const txt = (p.innerText || "").trim().split("\\n")[0];
                            if (txt && txt.length < 300) { label = txt; break; }
                            p = p.parentElement;
                        }
                    }
                    out.push({id, name, type, label: label.substring(0, 250),
                               placeholder: (el.placeholder || "").substring(0, 100)});
                });
                return out;
            }''')
        except Exception as e:
            print(f"  scan err: {e}"); questions = []

        SKIP_IDS = {"first_name", "last_name", "email", "phone", "country",
                    "candidate-location", "resume", "cover_letter"}

        for q in questions:
            qid = q.get("id", "")
            if qid in SKIP_IDS: continue
            label_lower = q.get("label", "").lower()
            tp = q.get("type", "")
            name_lower = qid.lower() + " " + q.get("name", "").lower()

            # Skip empty/tiny hidden-ish fields
            if not label_lower and not qid and not q.get("placeholder"):
                continue

            try:
                # LinkedIn
                if "linkedin" in label_lower or "linkedin" in name_lower:
                    target_frame.locator(f"#{qid}").fill(LINKEDIN) if qid else None; pause()
                    print(f"  [q] LinkedIn -> #{qid}")
                    continue

                # Preferred name
                if "preferred" in label_lower and ("name" in label_lower or "first" in label_lower):
                    if qid: target_frame.locator(f"#{qid}").fill(PREFERRED); pause()
                    print(f"  [q] PreferredName -> #{qid}")
                    continue

                # Salary
                if "salary" in label_lower or "compensation" in label_lower or "expected pay" in label_lower:
                    if qid and ("input" in tp or "textarea" in tp):
                        target_frame.locator(f"#{qid}").fill("116000"); pause()
                        print(f"  [q] Salary -> 116000")
                    continue

                # Website / portfolio
                if ("website" in label_lower or "portfolio" in label_lower) and "input" in tp:
                    continue  # skip — no portfolio URL

                # Work authorization
                if "legally authorized" in label_lower or "authorized to work" in label_lower:
                    combo(target_frame, target_frame.locator(f"#{qid}"), AUTHORIZED)
                    print(f"  [q] Authorized={AUTHORIZED}")
                    continue

                # Sponsorship
                if "sponsorship" in label_lower or ("visa" in label_lower and "require" in label_lower) or "will you now or in the future" in label_lower:
                    combo(target_frame, target_frame.locator(f"#{qid}"), SPONSOR)
                    print(f"  [q] Sponsorship={SPONSOR}")
                    continue

                # How did you hear
                if "how did you hear" in label_lower or "referral" in label_lower or label_lower.strip() == "source":
                    for v in ["LinkedIn", "Job board", "Other"]:
                        try:
                            combo(target_frame, target_frame.locator(f"#{qid}"), v)
                            print(f"  [q] Source={v}")
                            break
                        except: continue
                    continue

                # In-office / hybrid / NYC-based
                if any(k in label_lower for k in ["in office", "in-office", "hybrid", "days per week", "new york", "nyc"]):
                    if "select" in tp or "combobox" in tp:
                        combo(target_frame, target_frame.locator(f"#{qid}"), "Yes")
                        print(f"  [q] OfficeAvail=Yes -> #{qid}")
                    elif "input" in tp or "textarea" in tp:
                        target_frame.locator(f"#{qid}").fill("Yes, I am available to work in-office in New York.")
                        print(f"  [q] OfficeText -> #{qid}")
                    continue

                # US-based
                if "us-based" in label_lower or "us based" in label_lower or "currently us" in label_lower:
                    combo(target_frame, target_frame.locator(f"#{qid}"), "Yes")
                    print(f"  [q] USBased=Yes")
                    continue

                # Age 18+
                if "18 years" in label_lower or "at least 18" in label_lower or "age of 18" in label_lower:
                    combo(target_frame, target_frame.locator(f"#{qid}"), "Yes")
                    print(f"  [q] Age18+=Yes")
                    continue

                # DEI / why DEI / why Ripple — open text
                if any(k in label_lower for k in ["dei", "inclusion", "diversity", "why ripple", "experience with dei", "tell us about"]):
                    if "textarea" in tp or "input:text" in tp:
                        target_frame.locator(f"#{qid}").fill(SCREENING_ANSWER); pause()
                        print(f"  [q] DEI screening answered -> #{qid}")
                    continue

                # Generic short answer text fields we can't map — log only
                if ("textarea" in tp or "input:text" in tp) and label_lower:
                    print(f"  [q] UNMAPPED text field: #{qid} label='{q['label'][:80]}'")

                # Demographics
                if any(k in label_lower for k in ["gender", "hispanic", "race", "ethnicity", "veteran", "disability"]):
                    if "select" in tp:
                        if "gender" in label_lower:
                            fill_demog_select(target_frame, qid, ["Woman", "Female"])
                        elif "hispanic" in label_lower:
                            fill_demog_select(target_frame, qid, ["No", "Not Hispanic or Latino"])
                        elif "race" in label_lower or "ethnicity" in label_lower:
                            fill_demog_select(target_frame, qid, ["Asian", "Asian (Not Hispanic or Latino)"])
                        elif "veteran" in label_lower:
                            fill_demog_select(target_frame, qid, ["I am not a protected veteran", "Not a protected veteran", "No"])
                        elif "disability" in label_lower:
                            fill_demog_select(target_frame, qid, ["No, I do not have a disability", "I don't have a disability", "No"])
                    continue

            except Exception as e:
                print(f"  [q] #{qid} ({label_lower[:40]}): {e}")

        # ── Step 6: Scroll and screenshot pre-submit ───────────────────────
        print("\n[step6] pre-submit screenshot...")
        target_frame.evaluate("window.scrollTo(0, 0)") if hasattr(target_frame, 'evaluate') else None
        page.wait_for_timeout(1000)
        page.screenshot(path=str(SCREENSHOTS / "03_pre_submit_top.png"), full_page=True)
        # Scroll to bottom
        target_frame.evaluate("window.scrollTo(0, document.body.scrollHeight)") if hasattr(target_frame, 'evaluate') else None
        page.wait_for_timeout(1500)
        page.screenshot(path=str(SCREENSHOTS / "03_pre_submit_bottom.png"), full_page=True)

        # ── Step 7: Check for CAPTCHA before submitting ────────────────────
        body_text = page.inner_text("body").lower()
        if any(c in body_text for c in ["recaptcha", "hcaptcha", "turnstile", "i am not a robot", "verify you are human"]):
            print("\n[CAPTCHA DETECTED] — leaving tab open for human completion")
            result = {
                "company": "Ripple", "role": "Program Manager, DEI",
                "ats": "Greenhouse", "status": "CAPTCHA_STAGED",
                "confirmed_at": datetime.now().isoformat(),
                "screenshot": str(SCREENSHOTS / "03_pre_submit_bottom.png"),
                "notes": "CAPTCHA detected before submit — form filled, awaiting human click",
                "job_url": APP_URL
            }
            with open(ROLE_DIR / "SUBMITTED.json", "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2)
            print("[done] CAPTCHA_STAGED — tab left open")
            time.sleep(20)
            return

        # ── Step 8: SUBMIT ─────────────────────────────────────────────────
        print("\n[step8] SUBMITTING...")
        submitted = False
        for btn_label in ["Submit application", "Submit Application", "Submit"]:
            try:
                btn = page.get_by_role("button", name=btn_label, exact=False).first
                if btn.count() > 0 and btn.is_visible(timeout=3000):
                    btn.scroll_into_view_if_needed(); pause()
                    btn.click(timeout=12000)
                    page.wait_for_timeout(12000)
                    submitted = True
                    print(f"  clicked '{btn_label}'")
                    break
            except Exception as e:
                print(f"  btn '{btn_label}': {e}")

        if not submitted:
            # Try locating in iframe
            try:
                btn = target_frame.get_by_role("button", name="Submit application", exact=False).first
                btn.scroll_into_view_if_needed(); pause()
                btn.click(timeout=12000)
                page.wait_for_timeout(12000)
                submitted = True
                print("  submitted via iframe button")
            except Exception as e:
                print(f"  iframe btn err: {e}")

        page.screenshot(path=str(SCREENSHOTS / "04_after_submit.png"), full_page=True)

        # ── Step 9: Verify ─────────────────────────────────────────────────
        final_url = page.url
        title = page.title()
        body = page.inner_text("body")
        body_preview = body[:3000]

        safe_body = body[:2000].encode("ascii", "replace").decode("ascii")
        print(f"\n[result] URL:   {final_url}")
        print(f"[result] Title: {title.encode('ascii', 'replace').decode('ascii')}")
        print(f"[result] Body:\n{safe_body}")

        success = any(kw in body.lower() for kw in [
            "thank you", "received", "submitted", "application received",
            "we got your", "successfully submitted", "your application"
        ])

        if not submitted:
            print("\n[ERROR] submit button was never clicked — may need manual action")

        # Error elements
        if not success:
            errors = page.locator('.error, [class*="error"], [aria-invalid="true"]').all()
            print(f"\n[errors] {len(errors)} visible error elements:")
            for e in errors[:20]:
                try:
                    t = (e.text_content() or "").strip().encode("ascii", "replace").decode("ascii")
                    if t and 5 < len(t) < 300:
                        print(f"  - {t[:200]}")
                except: pass

            # Unfilled required
            try:
                unfilled = page.evaluate('''() => {
                    const out = [];
                    document.querySelectorAll("input[required], textarea[required], select[required], [aria-required=true]").forEach(el => {
                        if (!el.value) {
                            let lbl = "";
                            if (el.id) { const l = document.querySelector(`label[for="${el.id}"]`); if (l) lbl=(l.innerText||"").trim().substring(0,80); }
                            out.push({id: el.id, label: lbl});
                        }
                    });
                    return out;
                }''')
                print(f"\n[unfilled] {len(unfilled)} required fields empty:")
                for u in unfilled[:15]:
                    print(f"  - id={u['id']} label='{u['label']}'")
            except: pass

        status = "SUBMITTED" if success else ("ATTEMPTED_UNCONFIRMED" if submitted else "FAILED_NO_SUBMIT")

        result = {
            "company": "Ripple",
            "role": "Program Manager, DEI",
            "ats": "Greenhouse",
            "status": status,
            "confirmed_at": datetime.now().isoformat(),
            "screenshot": str(SCREENSHOTS / "04_after_submit.png"),
            "notes": f"final_url={final_url}, title={title}",
            "job_url": APP_URL,
            "body_preview": body_preview
        }
        with open(ROLE_DIR / "SUBMITTED.json", "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)

        if success:
            print("\n" + "="*60)
            print("*** APPLICATION SUBMITTED TO RIPPLE ***")
            print("="*60)
        else:
            print("\n[warn] success keywords not found in page body — check screenshots")

        time.sleep(15)

if __name__ == "__main__":
    main()
