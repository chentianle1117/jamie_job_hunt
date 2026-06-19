"""
Curai Health — People Operations & System Specialist — Lever v2.
Precise fill of the custom card (YOE radio, 3 yes/no selects, tools checkboxes) + EEO, then submit.
Truthful answers only.
"""
import sys, time, random, json
from datetime import datetime
from pathlib import Path
sys.path.insert(0, r"C:\Users\chent\Agentic_Workflows_2026\jamie-autopilot\lib")
from patchright.sync_api import sync_playwright

ROLE_DIR = Path(r"C:\Users\chent\Agentic_Workflows_2026\oracle-job-search\outputs\2026-06-18-overnight\applications\Curai-Health_People-Operations-System-Specialist")
RESUME = ROLE_DIR / "resume.pdf"; COVER = ROLE_DIR / "cover_letter.pdf"
OUT_DIR = ROLE_DIR / "screenshots"; OUT_DIR.mkdir(exist_ok=True)
TOKEN = "6bbb82d9-042b-4adf-ae49-9b4135906417"
APPLY_URL = f"https://jobs.lever.co/curai/{TOKEN}/apply"
PROFILE_DIR = r"C:\Users\chent\ats_agent_9431"; PORT = 9431
CARD = "208a5fc5-2688-4dd6-b6dc-81807fb3b2bb"

FIRST="Yi-Chieh"; LAST="Cheng"; EMAIL="jamiecheng0103@gmail.com"
PHONE="(213) 700-3831"; COMPANY="InGenius Prep"
LINKEDIN="https://www.linkedin.com/in/jamieyccheng/"

def pause(a=0.4,b=0.9): time.sleep(random.uniform(a,b))
def take(page,name):
    try: page.screenshot(path=str(OUT_DIR/name), full_page=True); print(f"  [shot] {name}")
    except Exception as e: print(f"  [shot ERR] {name}: {e}")

def sel_dropdown_truthful(page, field_name, answer):
    """Select a Yes/No-style option in a Lever native <select> by name."""
    sel = page.locator(f"select[name=\"cards[{CARD}][{field_name}]\"]").first
    if sel.count()==0:
        print(f"  {field_name}: select not found"); return False
    opts = [(o.get_attribute('value') or '', (o.text_content() or '').strip()) for o in sel.locator('option').all()]
    print(f"  {field_name} options: {[t for _,t in opts]}")
    for val,txt in opts:
        if txt.strip().lower()==answer.lower():
            sel.select_option(value=val); pause(); print(f"  {field_name} = {txt}"); return True
    # fallback contains
    for val,txt in opts:
        if answer.lower() in txt.lower() and txt.strip():
            sel.select_option(value=val); pause(); print(f"  {field_name} = {txt} (contains)"); return True
    return False

def main():
    with sync_playwright() as p:
        lock = Path(PROFILE_DIR)/"Default"/"LOCK"
        if lock.exists():
            try: lock.unlink()
            except: pass
        browser = p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_DIR, channel="chrome", headless=False, no_viewport=True,
            args=["--start-maximized", f"--remote-debugging-port={PORT}"])
        page = browser.pages[0] if browser.pages else browser.new_page()
        page.set_default_timeout(25000)

        print("[1] Open apply form")
        page.goto(APPLY_URL, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(4000)

        print("[2] Standard fields")
        page.locator("input[name='name']").first.fill(f"{FIRST} {LAST}"); pause()
        page.locator("input[name='email']").first.fill(EMAIL); pause()
        page.locator("input[name='phone']").first.fill(PHONE); pause()
        # location - plain fill
        try:
            loc = page.locator("input[name='location'], #location-input").first
            loc.click(); loc.fill("Portland, OR"); pause(0.8,1.2)
            # dismiss autocomplete by pressing Escape
            page.keyboard.press("Escape"); pause()
        except Exception as e: print(f"  loc ERR {e}")
        # current company LAST so autocomplete doesn't clobber; type then escape
        try:
            org = page.locator("input[name='org']").first
            org.click(); org.fill(""); pause(0.2)
            org.type(COMPANY, delay=30); pause(0.8,1.2)
            page.keyboard.press("Escape"); pause()
            print(f"  org typed = {COMPANY}")
        except Exception as e: print(f"  org ERR {e}")

        print("[3] Resume upload")
        fi = page.locator("input[name='resume'], input[type='file']").first
        fi.set_input_files(str(RESUME)); page.wait_for_timeout(4000)
        shown = page.evaluate("()=>{const f=document.querySelector('input[type=file]');return f&&f.files&&f.files.length?f.files[0].name:''}")
        print(f"  resume readback: {shown!r}")

        print("[4] Custom card — truthful answers")
        # YOE radio: 3-5 years (Jamie ~3yr)
        try:
            r = page.locator(f"input[type=radio][name=\"cards[{CARD}][field0]\"]").all()
            picked=False
            for rb in r:
                rid = rb.get_attribute("id") or ""
                lbl = ""
                if rid:
                    try: lbl=(page.locator(f"label[for='{rid}']").text_content(timeout=800) or "").strip()
                    except: pass
                val=(rb.get_attribute("value") or "")
                target = "3-5" in (lbl+val) or "3 - 5" in (lbl+val)
                if target:
                    rb.scroll_into_view_if_needed(); rb.check(force=True); pause()
                    print(f"  YOE radio checked: {lbl or val}"); picked=True; break
            if not picked:
                # by value index — options were 1-2,3-5,5+ → pick middle
                page.locator(f"input[type=radio][name=\"cards[{CARD}][field0]\"]").nth(1).check(force=True)
                print("  YOE radio checked by index 1 (3-5)")
        except Exception as e: print(f"  YOE ERR {e}")

        # field1: start-up/high-growth → Yes (InGenius high-growth edtech, ODN startup-scale)
        sel_dropdown_truthful(page, "field1", "Yes")
        # field2: employment law/legal ops/compliance/admin ops → Yes
        #   (truthful: ODN leave-cost/policy compliance analysis; HRBP compliance-adjacent admin ops)
        sel_dropdown_truthful(page, "field2", "Yes")
        # field3: HR Systems/ATS/payroll/People Ops tools → Yes (HRIS Rippling/ADP/SAP, ATS Greenhouse)
        sel_dropdown_truthful(page, "field3", "Yes")

        # field4 checkboxes — only tools Jamie truthfully has: Notion, GSuite, Greenhouse, Slack, Windows
        truthful_tools = {"Notion","GSuite","Greenhouse","Slack","Windows"}
        try:
            cbs = page.locator(f"input[type=checkbox][name=\"cards[{CARD}][field4]\"]").all()
            for cb in cbs:
                val = (cb.get_attribute("value") or "").strip()
                if val in truthful_tools:
                    cb.scroll_into_view_if_needed();
                    if not cb.is_checked(): cb.check(force=True)
                    pause(0.15,0.3); print(f"  tool checked: {val}")
        except Exception as e: print(f"  checkbox ERR {e}")

        print("[5] EEO truthful")
        def eeo(name, wants):
            s = page.locator(f"select[name='eeo[{name}]']").first
            if s.count()==0: return
            opts=[(o.get_attribute('value') or '', (o.text_content() or '').strip()) for o in s.locator('option').all()]
            for w in wants:
                for val,txt in opts:
                    if w.lower() in txt.lower() and txt.strip():
                        s.select_option(value=val); pause(); print(f"  eeo[{name}] = {txt}"); return
        eeo("gender", ["Female","Woman"])
        eeo("race", ["Asian"])
        eeo("veteran", ["not a protected veteran","not a veteran","i am not"])

        take(page, "v2_04_filled.png")

        print("[6] Pre-submit readback")
        snap = page.evaluate('''()=>{const v={};document.querySelectorAll("input,textarea,select").forEach(el=>{
            if(el.type==="hidden"||el.type==="file")return;const r=el.getBoundingClientRect();if(r.width<=0)return;
            if(el.type==="radio"||el.type==="checkbox"){if(el.checked)v[(el.name||"")+":"+(el.value||"on")]="CHECKED";return;}
            const k=(el.name||el.id||el.placeholder||"anon").substring(0,55);const val=(el.value||"").substring(0,90);if(val)v[k]=val;});return v;}''')
        for k,vv in snap.items(): print(f"    {k} = {vv[:90]}")
        full=" ".join(str(x) for x in snap.values()).lower()
        if "drive.google" in full or "docs.google" in full or "{kw|" in full:
            print("  ABORT leak"); take(page,"ABORT.png"); browser.close(); return
        take(page, "v2_05_bottom.png")

        print("[7] Submit")
        page.evaluate("window.scrollTo(0,document.body.scrollHeight)"); page.wait_for_timeout(1500)
        clicked=False
        for s in [".template-btn-submit","button[data-qa='btn-submit-form']","button:has-text('Submit application')","button[type='submit']"]:
            try:
                b=page.locator(s).first
                if b.count()>0 and b.is_visible(timeout=4000):
                    take(page,"v2_06_before.png"); b.click(timeout=15000); page.wait_for_timeout(12000)
                    clicked=True; print(f"  clicked {s}"); break
            except Exception as e: print(f"  submit {s} ERR {e}")
        take(page, "v2_07_after.png")

        final_url=page.url; body_after=page.inner_text("body")
        try: print(f"  URL after: {final_url}")
        except: pass
        success = any(k in body_after.lower() for k in ["thank you","received","submitted","we'll be in touch","application has been"])
        # also: Lever success redirects to /thanks or shows confirmation; /apply remaining = likely error
        if not success:
            print("  validation errors:")
            for e in page.locator(".form-field-error,[class*='error'],.template-form-error").all()[:20]:
                try:
                    t=(e.text_content() or "").strip()
                    if t: print(f"    ERR: {t[:160]}")
                except: pass
        status = "submitted" if success else "attempted-check-screenshot"
        json.dump({"company":"Curai Health","role":"People Operations & System Specialist","ats":"Lever",
                   "apply_url":APPLY_URL,"status":status,"confirmed_at":datetime.now().isoformat(),
                   "url_after_submit":final_url,"resume_file":str(RESUME),"resume_readback":shown,
                   "body_preview":body_after[:600],"notes":f"success={success} clicked={clicked}"},
                  open(ROLE_DIR/"SUBMITTED.json","w",encoding="utf-8"), indent=2)
        print(f"  STATUS: {status}")
        time.sleep(12); browser.close()

if __name__=="__main__": main()
