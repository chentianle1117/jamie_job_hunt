"""
Curai Health — People Operations & System Specialist
Lever ATS submission (no-account). Port 9431.
"""
import os, sys, time, random, json, re
from datetime import datetime
from pathlib import Path

sys.path.insert(0, r"C:\Users\chent\Agentic_Workflows_2026\jamie-autopilot\lib")
from patchright.sync_api import sync_playwright

ROLE_DIR = Path(r"C:\Users\chent\Agentic_Workflows_2026\oracle-job-search\outputs\2026-06-18-overnight\applications\Curai-Health_People-Operations-System-Specialist")
RESUME   = ROLE_DIR / "resume.pdf"
COVER    = ROLE_DIR / "cover_letter.pdf"
OUT_DIR  = ROLE_DIR / "screenshots"
OUT_DIR.mkdir(exist_ok=True)

TOKEN     = "6bbb82d9-042b-4adf-ae49-9b4135906417"
JOB_URL   = f"https://jobs.lever.co/curai/{TOKEN}"
APPLY_URL = f"https://jobs.lever.co/curai/{TOKEN}/apply"
BOARD_URL = "https://jobs.lever.co/curai"
PROFILE_DIR = r"C:\Users\chent\ats_agent_9431"
PORT = 9431

FIRST      = "Yi-Chieh"
LAST       = "Cheng"
EMAIL      = "jamiecheng0103@gmail.com"
PHONE      = "(213) 700-3831"
COMPANY    = "InGenius Prep"
LINKEDIN   = "https://www.linkedin.com/in/jamieyccheng/"
PREF_NAME  = "Jamie"

SCREENING_WHY = (
    "I'm drawn to this role because it sits right where People operations and the "
    "systems behind them meet—and that overlap is where I do my best work. At InGenius "
    "Prep I manage 20+ programs and 10+ vendors and built the guides and workflows that "
    "keep 70+ cross-functional staff aligned, cutting onboarding time by 75%. At Vestas "
    "I optimized onboarding across three global locations by analyzing the process and "
    "clarifying responsibilities. On the systems and data side, with ODN Oregon I "
    "upskilled an HR team to audit 300+ leave cases and surface evidence on $362K in "
    "leave costs—work that lived or died on clean data and clear reporting and led to "
    "real policy redesigns. I'm comfortable across HRIS, ATS, and knowledge-management "
    "tools (including Notion, which Curai uses) and pick up new systems quickly. My MS "
    "in Organizational Psychology from USC (3.95 GPA) gives me the rigor to keep records "
    "trustworthy and turn them into insight. I'd love to help Curai's people operations "
    "and systems grow together as the team scales."
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
    try:
        el = page.locator(selector).first
        if el.count() > 0 and el.is_visible(timeout=4000):
            el.click(); pause(0.2, 0.4)
            el.fill(""); pause(0.1, 0.2)
            el.fill(value); pause(0.2, 0.4)
            print(f"  {desc or selector} = {value[:80]}")
            return True
    except Exception as e:
        print(f"  {desc or selector} ERR: {e}")
    return False

def choose_radio_or_select(page, label_text, value_text):
    label_lower = label_text.lower(); value_lower = value_text.lower()
    try:
        selects = page.locator("select").all()
        for sel in selects:
            try:
                parent = sel.locator("xpath=ancestor::div[@class][1]")
                p_text = (parent.inner_text(timeout=2000) or "").lower()
            except:
                p_text = ""
            if label_lower in p_text or any(w in p_text for w in label_lower.split() if len(w) > 3):
                for opt in sel.locator("option").all():
                    opt_text = (opt.text_content() or "").lower().strip()
                    if value_lower in opt_text or (opt_text and opt_text in value_lower):
                        sel.select_option(value=opt.get_attribute("value") or "")
                        print(f"  select({label_text[:40]}) = {value_text}"); pause()
                        return True
    except Exception as e:
        print(f"  select ERR: {e}")
    try:
        radios = page.locator('input[type="radio"]').all()
        for r in radios:
            rid = r.get_attribute("id") or ""
            val = (r.get_attribute("value") or "").lower()
            if not rid: continue
            try:
                lbl = page.locator(f'label[for="{rid}"]')
                lbl_text = (lbl.text_content(timeout=1000) or "").lower().strip()
            except:
                lbl_text = val
            try:
                card_text = (r.locator("xpath=ancestor::div[contains(@class,'custom-question') or contains(@class,'application-question')][1]").inner_text(timeout=2000) or "").lower()
            except:
                card_text = ""
            question_matches = label_lower in card_text or any(w in card_text for w in label_lower.split() if len(w) > 3)
            value_matches = value_lower in lbl_text or (lbl_text and lbl_text in value_lower) or value_lower == val
            if question_matches and value_matches:
                r.scroll_into_view_if_needed(); pause(0.2, 0.4)
                r.check()
                print(f"  radio({label_text[:40]}) = {lbl_text}"); pause()
                return True
    except Exception as e:
        print(f"  radio ERR: {e}")
    return False

def main():
    print("=" * 60)
    print("CURAI HEALTH — People Operations & System Specialist")
    print(f"URL: {JOB_URL}")
    print("=" * 60)

    with sync_playwright() as p:
        lock_file = Path(PROFILE_DIR) / "Default" / "LOCK"
        if lock_file.exists():
            try: lock_file.unlink(); print("  Removed stale LOCK file")
            except: pass

        browser = p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_DIR,
            channel="chrome",
            headless=False,
            no_viewport=True,
            args=["--start-maximized", f"--remote-debugging-port={PORT}"],
        )
        page = browser.pages[0] if browser.pages else browser.new_page()
        page.set_default_timeout(25000)

        print("\n[STEP 0] Verifying job posting...")
        page.goto(JOB_URL, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(5000)
        take(page, "00_landing.png")
        body_text = page.inner_text("body").lower()
        title_text = page.title()
        print(f"  Title: {title_text}")
        print(f"  URL:   {page.url}")

        dead_signals = ["404", "job not found", "no longer", "position has been filled",
                        "posting has expired", "this job is no longer"]
        if any(s in body_text for s in dead_signals) or "404" in title_text:
            take(page, "00_dead.png")
            json.dump({"company":"Curai Health","role":"People Operations & System Specialist",
                       "ats":"Lever","job_url":JOB_URL,"status":"posting-dead",
                       "confirmed_at":datetime.now().isoformat()},
                      open(ROLE_DIR/"SUBMITTED.json","w",encoding="utf-8"), indent=2)
            print("  RESULT: posting-dead"); browser.close(); return

        no_sponsor_patterns = [
            "we do not provide visa sponsorship","we do not sponsor","unable to sponsor",
            "cannot sponsor","does not provide sponsorship","will not sponsor",
            "no visa sponsorship","sponsorship is not available","without need for sponsorship",
            "without visa sponsorship","not able to sponsor",
            "must be authorized to work in the united states without sponsorship",
        ]
        for pat in no_sponsor_patterns:
            if pat in body_text:
                idx = body_text.find(pat)
                snippet = body_text[max(0,idx-80):idx+200].replace("\n"," ")
                print(f'  SKIP — explicit no-sponsor: "...{snippet}..."')
                json.dump({"company":"Curai Health","role":"People Operations & System Specialist",
                           "ats":"Lever","job_url":JOB_URL,"status":"skip-no-sponsor",
                           "no_sponsor_quote":snippet,"confirmed_at":datetime.now().isoformat()},
                          open(ROLE_DIR/"SUBMITTED.json","w",encoding="utf-8"), indent=2)
                browser.close(); return

        if "itar" in body_text:
            print("  SKIP — ITAR found")
            json.dump({"company":"Curai Health","role":"People Operations & System Specialist",
                       "ats":"Lever","job_url":JOB_URL,"status":"skip-itar",
                       "confirmed_at":datetime.now().isoformat()},
                      open(ROLE_DIR/"SUBMITTED.json","w",encoding="utf-8"), indent=2)
            browser.close(); return

        print("  LIVE — no hard-stop language found. Proceeding to apply form.")

        print("\n[STEP 1] Opening Lever apply form...")
        page.goto(APPLY_URL, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(5000)
        take(page, "01_apply_form.png")
        print(f"  Apply URL: {page.url}")

        print("\n[STEP 2] Filling standard fields...")
        name_single = page.locator("input[name='name'], #name").first
        if name_single.count() > 0 and name_single.is_visible(timeout=3000):
            try:
                name_single.fill(f"{FIRST} {LAST}"); pause()
                print(f"  name (single) = {FIRST} {LAST}")
            except Exception as e:
                print(f"  name single ERR: {e}")
                fill_field(page, "input[name='firstName'], #firstName", FIRST, "first_name")
                fill_field(page, "input[name='lastName'], #lastName", LAST, "last_name")
        else:
            if not fill_field(page, "input[name='firstName'], #firstName", FIRST, "first_name"):
                fill_field(page, "input[placeholder*='first' i]", FIRST, "first_name")
            if not fill_field(page, "input[name='lastName'], #lastName", LAST, "last_name"):
                fill_field(page, "input[placeholder*='last' i]", LAST, "last_name")

        fill_field(page, "input[name='email'], #email, input[type='email']", EMAIL, "email")
        fill_field(page, "input[name='phone'], #phone, input[type='tel']", PHONE, "phone")
        if not fill_field(page, "input[name='org'], #org, input[name='company']", COMPANY, "current_company"):
            fill_field(page, "input[placeholder*='company' i], input[placeholder*='employer' i]", COMPANY, "current_company")

        if not fill_field(page, "input[name='urls[LinkedIn]']", LINKEDIN, "linkedin"):
            if not fill_field(page, "input[name='urls[0]'], input[placeholder*='linkedin' i]", LINKEDIN, "linkedin"):
                for inp in page.locator("input[type='url'], input[placeholder*='url' i]").all():
                    try:
                        ph=(inp.get_attribute("placeholder") or "").lower(); nm=(inp.get_attribute("name") or "").lower()
                        if "linkedin" in ph or "linkedin" in nm:
                            inp.fill(LINKEDIN); pause(); print(f"  linkedin (url-input) = {LINKEDIN}"); break
                    except: pass
        take(page, "02_fields_filled.png")

        print("\n[STEP 3] Uploading files via CDP set_input_files...")
        resume_uploaded = False
        for sel in ["input[name='resume']","#resume","input[type='file'][name*='resume' i]",
                    "input[type='file'][accept*='pdf']","input[type='file']"]:
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

        # read back the uploaded filename
        try:
            shown = page.evaluate('''() => {
                const fi = document.querySelector("input[type=file]");
                if (fi && fi.files && fi.files.length) return fi.files[0].name;
                const t = document.body.innerText;
                const m = t.match(/[\\w\\-\\. ]+\\.pdf/i);
                return m ? m[0] : "";
            }''')
            print(f"  [readback] uploaded filename on page: {shown!r}")
        except Exception as e:
            print(f"  readback ERR: {e}")

        if COVER.exists():
            file_inputs = page.locator("input[type='file']").all()
            if len(file_inputs) >= 2:
                try:
                    file_inputs[1].set_input_files(str(COVER)); page.wait_for_timeout(3000)
                    print("  cover_letter.pdf uploaded to 2nd file input")
                except Exception as e:
                    print(f"  cover upload ERR: {e}")
        take(page, "03_files_uploaded.png")

        print("\n[STEP 4] Scanning custom cards + screening questions...")
        page.wait_for_timeout(2000)
        all_inputs = page.evaluate('''() => {
            const out = [];
            document.querySelectorAll("input, textarea, select").forEach(el => {
                const rect = el.getBoundingClientRect();
                if (rect.width <= 0 || rect.height <= 0) return;
                if (el.type === "hidden" || el.type === "file") return;
                const id = el.id || ""; const name = el.name || "";
                const type = el.tagName.toLowerCase() + (el.type ? ":" + el.type : "");
                const placeholder = el.placeholder || "";
                let label = "";
                if (id) { const lbl = document.querySelector(`label[for="${id}"]`); if (lbl) label = (lbl.innerText||lbl.textContent||"").trim(); }
                if (!label) { let parent = el.parentElement;
                    for (let i=0;i<6&&parent;i++){ const txt=(parent.innerText||"").trim().split("\\n")[0];
                        if (txt && txt.length>3 && txt.length<300){label=txt;break;} parent=parent.parentElement; } }
                out.push({id,name,type,label:label.substring(0,250),placeholder});
            });
            return out;
        }''')
        print(f"  Found {len(all_inputs)} visible input elements")
        for q in all_inputs:
            print(f"    [{q['type']}] id={q['id']!r} name={q['name']!r} label={q['label'][:60]!r}")

        FILLED_NAMES = {"name","email","phone","org","urls[LinkedIn]","urls[0]",
                        "firstName","lastName","resume","coverLetter","company"}
        for q in all_inputs:
            nm=q.get("name",""); qid=q.get("id",""); tp=q.get("type",""); ll=q.get("label","").lower(); ph=q.get("placeholder","").lower()
            if nm in FILLED_NAMES or qid in FILLED_NAMES: continue
            if not nm and not qid: continue
            sel = f"#{qid}" if qid else f"[name='{nm}']"
            try:
                if ("preferred" in ll or "preferred" in ph) and ("name" in ll or "name" in ph):
                    fill_field(page, sel, PREF_NAME, "preferred_name"); continue
                if "linkedin" in ll or "linkedin" in ph or "linkedin" in nm.lower():
                    fill_field(page, sel, LINKEDIN, "linkedin_custom"); continue
                if "how did you hear" in ll or "source" in ll or "referred" in ll:
                    if "select" in tp:
                        try: page.locator(sel).select_option(label="LinkedIn"); print("  source = LinkedIn"); pause()
                        except:
                            try: page.locator(sel).select_option(index=1); pause()
                            except: pass
                    elif "input:text" in tp or "textarea" in tp:
                        fill_field(page, sel, "LinkedIn", "source")
                    continue
                if "legally authorized" in ll or "authorized to work" in ll:
                    if "radio" in tp: choose_radio_or_select(page, ll, "Yes")
                    elif "select" in tp:
                        try: page.locator(sel).select_option(label="Yes"); pause(); print("  authorized = Yes")
                        except: pass
                    elif "input" in tp: fill_field(page, sel, "Yes", "authorized")
                    continue
                if "sponsor" in ll or ("visa" in ll and "require" in ll) or "now or in the future" in ll:
                    if "radio" in tp: choose_radio_or_select(page, ll, "Yes")
                    elif "select" in tp:
                        try: page.locator(sel).select_option(label="Yes"); pause(); print("  sponsorship = Yes")
                        except: pass
                    elif "input" in tp: fill_field(page, sel, "Yes", "sponsorship")
                    continue
                if "salary" in ll or "compensation" in ll or ("desired" in ll and "pay" in ll):
                    fill_field(page, sel, "70000", "salary"); continue
                if "textarea" in tp and any(k in ll for k in
                        ["why","tell us","describe","experience","background","interest","motivation","share","relevant","learn","anything else"]):
                    fill_field(page, sel, SCREENING_WHY, f"screening({ll[:30]})"); continue
                if "gender" in ll:
                    if "select" in tp:
                        for v in ["Female","Woman","Female (she/her)","Female/Woman"]:
                            try: page.locator(sel).select_option(label=v); pause(); print(f"  gender = {v}"); break
                            except: pass
                    elif "radio" in tp: choose_radio_or_select(page, ll, "Female")
                    continue
                if "hispanic" in ll or "latino" in ll:
                    if "select" in tp:
                        for v in ["No","Not Hispanic or Latino","No, Not Hispanic or Latino"]:
                            try: page.locator(sel).select_option(label=v); pause(); print(f"  hispanic = {v}"); break
                            except: pass
                    elif "radio" in tp: choose_radio_or_select(page, ll, "No")
                    continue
                if "race" in ll or "ethnicity" in ll:
                    if "select" in tp:
                        for v in ["Asian","Asian (Not Hispanic or Latino)","Asian / Pacific Islander"]:
                            try: page.locator(sel).select_option(label=v); pause(); print(f"  race = {v}"); break
                            except: pass
                    elif "radio" in tp: choose_radio_or_select(page, ll, "Asian")
                    continue
                if "veteran" in ll:
                    if "select" in tp:
                        for v in ["I am not a protected veteran","Not a protected veteran","I don't wish to answer","Decline to self-identify"]:
                            try: page.locator(sel).select_option(label=v); pause(); print(f"  veteran = {v}"); break
                            except: pass
                    elif "radio" in tp: choose_radio_or_select(page, ll, "not a protected veteran")
                    continue
                if "disability" in ll:
                    if "select" in tp:
                        for v in ["No, I do not have a disability","No, I don't have a disability","I don't wish to answer","Decline to self-identify"]:
                            try: page.locator(sel).select_option(label=v); pause(); print(f"  disability = {v}"); break
                            except: pass
                    elif "radio" in tp: choose_radio_or_select(page, ll, "No")
                    continue
            except Exception as e:
                print(f"  Q({qid}|{nm}|{ll[:25]}): ERR {e}")
        take(page, "04_custom_cards.png")

        print("\n[STEP 5] Pre-submit readback...")
        page.evaluate("window.scrollTo(0, 0)"); page.wait_for_timeout(1500)
        form_snapshot = page.evaluate('''() => {
            const vals = {};
            document.querySelectorAll("input, textarea, select").forEach(el => {
                if (el.type === "hidden" || el.type === "file") return;
                const rect = el.getBoundingClientRect(); if (rect.width <= 0) return;
                const k = (el.id || el.name || el.placeholder || "anon").substring(0,60);
                const v = (el.value || "").substring(0,150); if (v) vals[k] = v;
            });
            return vals;
        }''')
        print("  Form snapshot:")
        for k,v in form_snapshot.items(): print(f"    {k} = {v[:100]}")
        full_values = " ".join(v for v in form_snapshot.values()).lower()
        if "docs.google" in full_values or "drive.google" in full_values:
            print("  !! ABORT — Drive link detected!"); take(page,"ABORT_drive_link.png"); browser.close(); return
        if "{group|" in full_values or "{kw|" in full_values or "&#" in full_values:
            print("  !! ABORT — Template markup detected!"); take(page,"ABORT_markup.png"); browser.close(); return
        name_ok = any(FIRST.lower() in v.lower() or LAST.lower() in v.lower() for v in form_snapshot.values())
        email_ok = any(EMAIL in v for v in form_snapshot.values())
        print(f"  name_ok={name_ok}, email_ok={email_ok}")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)"); page.wait_for_timeout(1000)
        take(page, "05_pre_submit_bottom.png")
        page.evaluate("window.scrollTo(0, 0)"); page.wait_for_timeout(500)
        take(page, "05_pre_submit_top.png")

        print("\n[STEP 6] Submitting application...")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)"); page.wait_for_timeout(2000)
        submitted = False
        for sel in ["button[data-qa='btn-submit-form']","button[type='submit']",".template-btn-submit",
                    "button:has-text('Submit application')","button:has-text('Submit Application')",
                    "button:has-text('Submit')","input[type='submit']"]:
            try:
                btn = page.locator(sel).first
                if btn.count() > 0 and btn.is_visible(timeout=5000):
                    btn.scroll_into_view_if_needed(); pause(0.5,1.0)
                    print(f"  Found submit button: {sel}")
                    take(page, "06_before_click.png")
                    btn.click(timeout=15000); page.wait_for_timeout(12000)
                    submitted = True; print(f"  Clicked submit: {sel}"); break
            except Exception as e:
                print(f"  submit sel {sel}: {e}")
        if not submitted:
            try:
                for b in page.get_by_role("button").all():
                    txt = (b.text_content() or "").lower().strip()
                    if "submit" in txt:
                        b.scroll_into_view_if_needed(); pause(0.3,0.6)
                        print(f"  Fallback submit button: '{txt}'")
                        take(page, "06_fallback_before_click.png")
                        b.click(timeout=15000); page.wait_for_timeout(12000)
                        submitted = True; print("  Clicked fallback submit"); break
            except Exception as e:
                print(f"  fallback submit ERR: {e}")
        take(page, "07_after_submit.png")

        final_url = page.url; final_title = page.title(); body_after = page.inner_text("body")
        print(f"\n  URL after submit: {final_url}")
        print(f"  Title after submit: {final_title}")
        print(f"  Body (first 1000): {body_after[:1000]}")
        success_kws = ["thank you","received","submitted","we've got your","application has been",
                       "we'll be in touch","confirmation","application submitted","successfully submitted"]
        success = any(kw in body_after.lower() for kw in success_kws)
        if not success:
            print("\n  Checking for validation errors...")
            for e in page.locator(".error-message,.field_with_errors,[aria-invalid='true'],.error,[class*='error'],[class*='invalid']").all()[:15]:
                try:
                    t=(e.text_content() or "").strip()[:200]
                    if t: print(f"    ERR: {t}")
                except: pass

        status = "submitted" if success else "attempted-check-screenshot"
        json.dump({"company":"Curai Health","role":"People Operations & System Specialist",
                   "ats":"Lever","job_url":JOB_URL,"apply_url":APPLY_URL,"status":status,
                   "confirmed_at":datetime.now().isoformat(),"url_after_submit":final_url,
                   "title_after_submit":final_title,"body_preview":body_after[:600],
                   "resume_file":str(RESUME),"screenshot":str(OUT_DIR/"07_after_submit.png"),
                   "notes":f"success_detected={success}; submitted_btn_clicked={submitted}"},
                  open(ROLE_DIR/"SUBMITTED.json","w",encoding="utf-8"), indent=2)

        if success:
            print("\n*** APPLICATION SUBMITTED SUCCESSFULLY ***")
        else:
            print("\n*** Submit may need manual review — check 07_after_submit.png ***")
        time.sleep(15)
        browser.close()

if __name__ == "__main__":
    main()
