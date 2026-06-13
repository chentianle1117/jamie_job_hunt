#!/usr/bin/env python3
"""
Ripple DEI PM — Greenhouse iframe submit v2.
The Ripple careers page embeds Greenhouse in an iframe at job-boards.greenhouse.io.
We need to use page.frame_locator() to reach elements inside the iframe.
Fallback: navigate directly to the canonical Greenhouse boards URL.
"""
import os, sys, time, json, subprocess, random, socket
from datetime import datetime
from pathlib import Path

# ── paths ──────────────────────────────────────────────────────────────────
ROLE_DIR    = Path(r"C:\Users\chent\Agentic_Workflows_2026\oracle-job-search\outputs\2026-06-12-feed-first\applications\ripple_dei_pm")
RESUME      = ROLE_DIR / "resume.pdf"
COVER       = ROLE_DIR / "cover_letter.pdf"
SCREENSHOTS = ROLE_DIR / "screenshots"
SCREENSHOTS.mkdir(exist_ok=True)

CHROME_BIN  = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
DEBUG_PORT  = 9404
USER_DATA   = r"C:\Users\chent\ats_agent_9404"

# We'll try the canonical boards.greenhouse.io URL directly — no embed, no iframe
APP_URL = "https://boards.greenhouse.io/ripple/jobs/7951682"

# candidate data
FIRST, LAST = "Yi-Chieh", "Cheng"
EMAIL       = "jamiecheng0103@gmail.com"
PHONE       = "2137003831"
COUNTRY     = "United States"
CITY        = "New York, NY"
LINKEDIN    = "https://www.linkedin.com/in/jamieyccheng/"
PREFERRED   = "Jamie"
AUTHORIZED  = "Yes"
SPONSOR     = "Yes"

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

def pause(lo=0.4, hi=1.0):
    time.sleep(random.uniform(lo, hi))

def is_port_open(port):
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=2):
            return True
    except Exception:
        return False

def launch_chrome():
    if is_port_open(DEBUG_PORT):
        print(f"[chrome] already running on {DEBUG_PORT}")
        return
    print(f"[chrome] launching on {DEBUG_PORT}...")
    args = [
        CHROME_BIN,
        f"--remote-debugging-port={DEBUG_PORT}",
        f"--user-data-dir={USER_DATA}",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-features=TranslateUI",
        "--disable-popup-blocking",
        "--disable-notifications",
        "--window-size=1400,960",
    ]
    subprocess.Popen(args, creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP)
    for _ in range(15):
        time.sleep(1)
        if is_port_open(DEBUG_PORT):
            print("[chrome] CDP ready")
            return
    print("[chrome] WARNING: CDP not confirmed open after 15s")

def combo(fl, selector_or_locator, option_text):
    """Drive a Greenhouse/react-select combobox inside a frame locator."""
    want = option_text.strip().lower()
    if isinstance(selector_or_locator, str):
        loc = fl.locator(selector_or_locator)
    else:
        loc = selector_or_locator
    loc.scroll_into_view_if_needed(); pause()
    loc.click(); pause(); time.sleep(0.7)

    # 1) pre-rendered options
    try:
        opts = fl.locator(".select__option"); n = opts.count()
        for i in range(n):
            t = opts.nth(i).inner_text(timeout=3000).strip().lower()
            if want in t:
                opts.nth(i).click(); pause(); return True
    except: pass

    # 2) type + click
    try:
        fl.locator("body").press(None)
        # type into whatever is focused
        import patchright.sync_api as pw_sync
    except: pass
    try:
        loc.type(option_text, delay=60); time.sleep(1.0)
        opts = fl.locator(".select__option"); n = opts.count()
        for i in range(n):
            t = opts.nth(i).inner_text(timeout=3000).strip().lower()
            if want in t:
                opts.nth(i).click(); pause(); return True
    except: pass

    # 3) Enter
    try:
        from patchright.sync_api import Page
        # press Enter on current page keyboard
    except: pass
    time.sleep(0.3)
    return False

def fill_field(fl, selector, value, method="fill"):
    """Fill a field inside a frame locator, with retries."""
    try:
        loc = fl.locator(selector).first
        loc.wait_for(state="visible", timeout=8000)
        if method == "fill":
            loc.fill(value)
        else:
            loc.type(value, delay=50)
        pause()
        return True
    except Exception as e:
        print(f"    fill_field({selector}): {e}")
        return False

def main():
    launch_chrome()
    time.sleep(2)

    from patchright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(f"http://localhost:{DEBUG_PORT}")
        print(f"[cdp] connected, {len(browser.contexts)} contexts")
        ctx = browser.contexts[0] if browser.contexts else browser.new_context()
        page = ctx.new_page()
        page.set_default_timeout(20000)

        # ── Step 1: Navigate directly to boards.greenhouse.io (no iframe) ─
        print(f"\n[step1] navigating to {APP_URL}")
        try:
            page.goto(APP_URL, wait_until="networkidle", timeout=45000)
        except Exception as e:
            print(f"  networkidle timeout (ok): {e}")
        page.wait_for_timeout(4000)
        page.screenshot(path=str(SCREENSHOTS / "01_landing.png"), full_page=True)
        print(f"  title: {page.title()}")
        print(f"  url:   {page.url}")

        # Detect if we were redirected to ripple.com (iframe embed path)
        current_url = page.url
        use_frame = False
        fl = page  # default: operate on page directly

        if "ripple.com" in current_url or "boards.greenhouse.io" not in current_url:
            print("  [redirect detected] will use frame_locator for Greenhouse iframe")
            # Try to find the iframe
            try:
                iframe_loc = page.frame_locator("iframe[src*='greenhouse.io'], iframe[src*='job-boards']")
                # Check if it has our fields
                fn = iframe_loc.locator("#first_name")
                fn.wait_for(state="visible", timeout=8000)
                fl = iframe_loc
                use_frame = True
                print("  [iframe] found Greenhouse iframe — using frame_locator")
            except Exception as e:
                print(f"  [iframe] not found or not ready: {e}")
                # Navigate directly to the canonical URL
                print(f"  [fallback] navigating directly to Greenhouse boards URL")
                try:
                    page.goto(APP_URL, wait_until="domcontentloaded", timeout=30000)
                    page.wait_for_timeout(4000)
                    page.screenshot(path=str(SCREENSHOTS / "01b_direct_gh.png"), full_page=True)
                    print(f"  title: {page.title()}")
                    print(f"  url:   {page.url}")
                    fl = page
                    use_frame = False
                except Exception as e2:
                    print(f"  direct nav err: {e2}")
        else:
            print("  [direct] on boards.greenhouse.io, using page directly")
            fl = page

        # ── Step 2: Wait for form to be ready ─────────────────────────────
        print("\n[step2] waiting for form...")
        try:
            fl.locator("#first_name").wait_for(state="visible", timeout=15000)
            print("  form ready (#first_name visible)")
        except Exception as e:
            print(f"  #first_name not visible: {e}")
            page.screenshot(path=str(SCREENSHOTS / "02_form_check.png"), full_page=True)
            # Show page source snippet to debug
            try:
                html = page.content()[:3000]
                print(f"  page html snippet: {html[:800]}")
            except: pass

        # ── Step 3: Fill personal fields ──────────────────────────────────
        print("\n[step3] personal fields...")

        fill_field(fl, "#first_name", FIRST)
        print(f"  first_name = {FIRST}")

        fill_field(fl, "#last_name", LAST)
        print(f"  last_name = {LAST}")

        fill_field(fl, "#email", EMAIL)
        print(f"  email = {EMAIL}")

        fill_field(fl, "#phone", PHONE)
        print(f"  phone = {PHONE}")

        # Country combobox
        try:
            combo(fl, fl.locator("#country").first, COUNTRY)
            print(f"  country = {COUNTRY}")
        except Exception as e:
            print(f"  country err: {e}")

        # Location
        loc_filled = False
        for sel in ["#candidate-location", 'input[name*="location" i]', 'input[placeholder*="city" i]']:
            try:
                loc = fl.locator(sel).first
                loc.wait_for(state="visible", timeout=3000)
                loc.click(); pause(); time.sleep(0.5)
                loc.type("New York, NY", delay=60); time.sleep(2.0)
                fl.locator("body").press("ArrowDown"); pause()
                fl.locator("body").press("Enter"); pause()
                print(f"  location set via {sel}")
                loc_filled = True
                break
            except: continue
        if not loc_filled:
            # Try via keyboard on whatever is active
            try:
                page.keyboard.type("New York, NY"); time.sleep(2.0)
                page.keyboard.press("ArrowDown"); pause()
                page.keyboard.press("Enter"); pause()
                print("  location set via keyboard fallback")
                loc_filled = True
            except Exception as e:
                print(f"  location NOT filled: {e}")

        # LinkedIn
        for sel in ["input[id*='linkedin' i]", "input[id*='linkedin']", "#job_application_answers_attributes_0_text_value"]:
            try:
                loc = fl.locator(sel).first
                if loc.count() > 0:
                    loc.wait_for(state="visible", timeout=3000)
                    loc.fill(LINKEDIN); pause()
                    print(f"  linkedin via {sel}")
                    break
            except: continue

        # ── Step 4: Uploads ────────────────────────────────────────────────
        print("\n[step4] file uploads...")
        try:
            fl.locator("#resume").set_input_files(str(RESUME)); pause()
            time.sleep(3)
            print(f"  resume OK")
        except Exception as e:
            print(f"  #resume err: {e}")
            try:
                page.locator('input[type="file"]').nth(0).set_input_files(str(RESUME))
                time.sleep(3); print("  resume OK via file[0]")
            except Exception as e2:
                print(f"  resume err2: {e2}")

        if COVER.exists():
            try:
                fl.locator("#cover_letter").set_input_files(str(COVER)); pause()
                time.sleep(3)
                print("  cover OK")
            except Exception as e:
                print(f"  #cover_letter err: {e}")
                try:
                    page.locator('input[type="file"]').nth(1).set_input_files(str(COVER))
                    time.sleep(3); print("  cover OK via file[1]")
                except: pass

        page.screenshot(path=str(SCREENSHOTS / "03_uploads_done.png"), full_page=True)

        # ── Step 5: Scan + fill custom questions ──────────────────────────
        print("\n[step5] scanning questions...")
        # Use page.evaluate or frame.evaluate for the scan
        scan_target = page
        try:
            questions = scan_target.evaluate('''() => {
                const out = [];
                document.querySelectorAll("input, textarea, select").forEach(el => {
                    const rect = el.getBoundingClientRect();
                    if (rect.width <= 0 || rect.height <= 0) return;
                    if (el.type === "hidden") return;
                    const id = el.id || "";
                    const type = el.tagName.toLowerCase() + (el.type ? ":" + el.type : "");
                    let label = "";
                    if (id) { const lbl = document.querySelector(`label[for="${id}"]`); if (lbl) label = (lbl.innerText||"").trim(); }
                    if (!label) { let p = el.parentElement; for (let i=0;i<5&&p;i++){const t=(p.innerText||"").trim().split("\\n")[0]; if(t&&t.length<300){label=t;break;} p=p.parentElement;} }
                    out.push({id, type, label: label.substring(0,250)});
                });
                return out;
            }''')
            print(f"  found {len(questions)} visible fields")
            for q in questions:
                if q['id'] or q['label']:
                    print(f"    id={q['id']!r:<40} type={q['type']!r:<25} label={q['label'][:80]!r}")
        except Exception as e:
            print(f"  scan err: {e}"); questions = []

        SKIP_IDS = {"first_name","last_name","email","phone","country","candidate-location","resume","cover_letter"}
        for q in questions:
            qid = q.get("id","")
            if qid in SKIP_IDS: continue
            label_lower = q.get("label","").lower()
            tp = q.get("type","")
            if not qid and not label_lower: continue

            try:
                if "linkedin" in label_lower or "linkedin" in qid.lower():
                    if qid: fill_field(fl, f"#{qid}", LINKEDIN)
                    print(f"  [q] LinkedIn -> #{qid}")
                    continue
                if "preferred" in label_lower and ("name" in label_lower or "first" in label_lower):
                    if qid: fill_field(fl, f"#{qid}", PREFERRED)
                    print(f"  [q] Preferred -> #{qid}")
                    continue
                if "salary" in label_lower or "compensation" in label_lower:
                    if qid: fill_field(fl, f"#{qid}", "116000")
                    print(f"  [q] Salary -> #{qid}")
                    continue
                if ("website" in label_lower or "portfolio" in label_lower) and "input" in tp:
                    continue
                if "legally authorized" in label_lower or "authorized to work" in label_lower:
                    combo(fl, fl.locator(f"#{qid}"), AUTHORIZED)
                    print(f"  [q] Authorized={AUTHORIZED}")
                    continue
                if "sponsorship" in label_lower or ("visa" in label_lower and "require" in label_lower) or "will you now or in the future" in label_lower:
                    combo(fl, fl.locator(f"#{qid}"), SPONSOR)
                    print(f"  [q] Sponsorship={SPONSOR}")
                    continue
                if "how did you hear" in label_lower or "referral" in label_lower:
                    for v in ["LinkedIn","Job board","Other"]:
                        try: combo(fl, fl.locator(f"#{qid}"), v); print(f"  [q] Source={v}"); break
                        except: continue
                    continue
                if any(k in label_lower for k in ["in office","in-office","hybrid","new york","nyc"]):
                    if "select" in tp:
                        combo(fl, fl.locator(f"#{qid}"), "Yes"); print(f"  [q] Office=Yes")
                    elif "textarea" in tp or "input:text" in tp:
                        fill_field(fl, f"#{qid}", "Yes, I can work in-office in New York.")
                    continue
                if "us-based" in label_lower or "us based" in label_lower:
                    combo(fl, fl.locator(f"#{qid}"), "Yes"); print(f"  [q] USBased=Yes"); continue
                if "18 years" in label_lower or "at least 18" in label_lower:
                    combo(fl, fl.locator(f"#{qid}"), "Yes"); print(f"  [q] Age18+=Yes"); continue
                if any(k in label_lower for k in ["dei","inclusion","diversity","why ripple","tell us"]):
                    if "textarea" in tp or "input:text" in tp:
                        fill_field(fl, f"#{qid}", SCREENING_ANSWER)
                        print(f"  [q] DEI screening -> #{qid}")
                    continue
                if any(k in label_lower for k in ["gender","hispanic","race","ethnicity","veteran","disability"]):
                    if "select" in tp:
                        if "gender" in label_lower: cands=["Woman","Female"]
                        elif "hispanic" in label_lower: cands=["No","Not Hispanic or Latino"]
                        elif "race" in label_lower or "ethnicity" in label_lower: cands=["Asian","Asian (Not Hispanic or Latino)"]
                        elif "veteran" in label_lower: cands=["I am not a protected veteran","Not a protected veteran","No"]
                        elif "disability" in label_lower: cands=["No, I do not have a disability","No"]
                        else: cands=[]
                        for c in cands:
                            try: combo(fl, fl.locator(f"#{qid}"), c); print(f"  [demog] #{qid}={c}"); break
                            except: continue
                    continue
                # log unmapped
                if label_lower and "input" in tp:
                    print(f"  [q] UNMAPPED: #{qid} label='{q['label'][:80]}'")
            except Exception as e:
                print(f"  [q] #{qid}: {e}")

        # ── Step 6: Pre-submit screenshot ─────────────────────────────────
        print("\n[step6] pre-submit screenshot...")
        try:
            page.evaluate("window.scrollTo(0,0)"); time.sleep(1)
        except: pass
        page.screenshot(path=str(SCREENSHOTS / "04_prefill_top.png"), full_page=True)
        try:
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)"); time.sleep(1.5)
        except: pass
        page.screenshot(path=str(SCREENSHOTS / "04_prefill_bottom.png"), full_page=True)

        # ── Step 7: CAPTCHA check ──────────────────────────────────────────
        body_text = page.inner_text("body").lower()
        if any(c in body_text for c in ["recaptcha","hcaptcha","turnstile","i am not a robot","verify you are human"]):
            print("\n[CAPTCHA] detected — tab left open for human")
            result = {"company":"Ripple","role":"Program Manager, DEI","ats":"Greenhouse",
                      "status":"CAPTCHA_STAGED","confirmed_at":datetime.now().isoformat(),
                      "screenshot":str(SCREENSHOTS/"04_prefill_bottom.png"),
                      "notes":"CAPTCHA before submit","job_url":APP_URL}
            with open(ROLE_DIR/"SUBMITTED.json","w",encoding="utf-8") as f:
                json.dump(result,f,indent=2)
            time.sleep(30); return

        # ── Step 8: SUBMIT ─────────────────────────────────────────────────
        print("\n[step8] submitting...")
        submitted = False

        # Try the frame locator first
        for btn_name in ["Submit application","Submit Application","Submit"]:
            for target in [fl, page]:
                try:
                    btn = target.get_by_role("button", name=btn_name, exact=False).first
                    if btn.count() > 0:
                        btn.wait_for(state="visible", timeout=5000)
                        btn.scroll_into_view_if_needed(); pause()
                        btn.click(timeout=15000)
                        time.sleep(12)
                        submitted = True
                        print(f"  clicked '{btn_name}'")
                        break
                except Exception as e:
                    pass
            if submitted: break

        if not submitted:
            # Try by text
            for target in [fl, page]:
                try:
                    btn = target.get_by_text("Submit application", exact=False).first
                    if btn.count() > 0:
                        btn.scroll_into_view_if_needed(); pause()
                        btn.click(timeout=15000)
                        time.sleep(12)
                        submitted = True
                        print("  clicked via get_by_text")
                        break
                except: pass

        if not submitted:
            # Last resort: JS click
            try:
                page.evaluate("""() => {
                    const btns = [...document.querySelectorAll('button, input[type=submit]')];
                    const sub = btns.find(b => (b.textContent||b.value||'').toLowerCase().includes('submit'));
                    if (sub) sub.click();
                }""")
                time.sleep(12)
                submitted = True
                print("  submitted via JS click")
            except Exception as e:
                print(f"  JS click err: {e}")

        page.screenshot(path=str(SCREENSHOTS / "05_after_submit.png"), full_page=True)

        # ── Step 9: Verify ─────────────────────────────────────────────────
        final_url = page.url
        title = page.title()
        body = page.inner_text("body")

        safe_body = body[:2500].encode("ascii","replace").decode("ascii")
        print(f"\n[result] URL:   {final_url}")
        print(f"[result] Title: {title.encode('ascii','replace').decode('ascii')}")
        print(f"[result] Body preview:\n{safe_body[:1500]}")

        success = any(kw in body.lower() for kw in [
            "thank you","received","submitted","application received",
            "we got your","successfully submitted","your application"
        ])

        if not submitted:
            print("\n[ERROR] submit button never clicked")
        elif not success:
            print("\n[WARN] submitted but success keywords not found — check screenshot")

            # Show errors
            try:
                errs = page.locator('.error, [class*="error"], [aria-invalid="true"]').all()
                print(f"  {len(errs)} error elements:")
                for e in errs[:15]:
                    t = (e.text_content() or "").strip().encode("ascii","replace").decode("ascii")
                    if t and 5 < len(t) < 300: print(f"    - {t[:200]}")
            except: pass

        status = "SUBMITTED" if success else ("ATTEMPTED_UNCONFIRMED" if submitted else "FAILED_NO_SUBMIT")

        result = {
            "company":"Ripple","role":"Program Manager, DEI","ats":"Greenhouse",
            "status":status,"confirmed_at":datetime.now().isoformat(),
            "screenshot":str(SCREENSHOTS/"05_after_submit.png"),
            "notes":f"url={final_url} title={title} submitted={submitted}",
            "job_url":APP_URL,"body_preview":body[:2000]
        }
        with open(ROLE_DIR/"SUBMITTED.json","w",encoding="utf-8") as f:
            json.dump(result,f,indent=2)

        if success:
            print("\n" + "="*60 + "\n*** RIPPLE APPLICATION SUBMITTED ***\n" + "="*60)

        time.sleep(15)

if __name__ == "__main__":
    main()
