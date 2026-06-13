# -*- coding: utf-8 -*-
"""
submit_bcg_v6.py  -- BCG Phenom ATS (v6)

Key insight from v5: BCG Phenom has a SINGLE-PAGE application form (not a multi-step wizard).
Sections on the page:
  1. Resume upload
  2. "Before applying" (personal info: email/name/phone/address)
  3. Available Start Date (date picker — REQUIRED, was causing error)
  4. Work Authorization Status (2 Yes/No radio pairs)
  5. Voluntary Self-Identification (gender/ethnicity/disability/veteran — 5 errors)

Must fill ALL sections before clicking "Submit Application".
Account: jamiecheng0103@gmail.com is confirmed working (logged in successfully in v5).
"""
import os, sys, time, json, subprocess, traceback
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, r"C:\Users\chent\Agentic_Workflows_2026\jamie-autopilot\lib")
from patchright.sync_api import sync_playwright
from credential_vault import job_password

PORT     = 9402
PROFILE  = r"C:\Users\chent\ats_agent_9402_v4"
CHROME   = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
ROLE_DIR = (r"C:\Users\chent\Agentic_Workflows_2026\oracle-job-search"
            r"\outputs\2026-06-12-feed-first\applications\bcg_talent_sr_specialist")
SHOT     = ROLE_DIR + r"\screenshots\v6"
RESUME   = ROLE_DIR + r"\resume.pdf"
os.makedirs(SHOT, exist_ok=True)

EMAIL = "jamiecheng0103@gmail.com"
PW    = job_password()

JOB_PUBLIC_URL = "https://careers.bcg.com/global/en/job/57988/Talent-Senior-Specialist-People"
PHENOM_APPLY   = (
    "https://experiencedtalent.bcg.com/careerhub/explore/jobs/apply?pid=790315808241"
)
PHENOM_LOGIN   = (
    "https://experiencedtalent.bcg.com/candidate/login?domain=bcg.com&hl=en"
    "&microsite=microsite_1"
    "&next=http%3A%2F%2Fexperiencedtalent.bcg.com%2Fcareerhub%2Fexplore%2Fjobs"
    "%2F790315808241%3Fpost_onboarding_pid%3D790315808241%26show_apply%3D1"
    "%26profile_type%3Dcandidate%26customredirect%3D1"
)


# ── helpers ──────────────────────────────────────────────────────────────────

def ss(page, name):
    path = os.path.join(SHOT, name + ".png")
    try:
        page.screenshot(path=path, full_page=True)
        print(f"  [ss] {name}.png")
    except Exception as e:
        print(f"  [ss!] {name}: {e}")
    return path


def net(page, t=15000):
    try:
        page.wait_for_load_state("networkidle", timeout=t)
    except:
        pass


def txt(page):
    try:
        return page.inner_text("body")
    except:
        return ""


def dismiss_cookie(page):
    for sel in [
        "button:has-text('Accept All and Close')",
        "button:has-text('Accept All')",
        "#truste-consent-button",
        "#onetrust-accept-btn-handler",
    ]:
        try:
            el = page.locator(sel).first
            if el.count() > 0 and el.is_visible(timeout=2000):
                el.click(force=True)
                time.sleep(2)
                return True
        except:
            continue
    try:
        page.evaluate("""() => {
            document.querySelectorAll(
                '[id*="truste"],[class*="truste"],[id*="trustarc"],[class*="trustarc"],' +
                '#onetrust-banner-sdk,.onetrust-pc-dark-filter'
            ).forEach(e => { e.style.cssText = 'display:none!important;'; });
            document.body.style.overflow = 'auto';
        }""")
    except: pass
    return False


def fill_input(page, sel, val, lbl=""):
    """Fill a text input — click, clear, type."""
    try:
        el = page.locator(sel).first
        el.wait_for(state="visible", timeout=6000)
        el.scroll_into_view_if_needed()
        el.click(timeout=3000)
        el.fill("", timeout=3000)
        el.fill(val, timeout=5000)
        print(f"  [fill] {lbl or sel[:60]} = '{val[:50]}'")
        return True
    except Exception as e:
        # JS fallback
        try:
            page.evaluate(
                "(args) => { let el = document.querySelector(args[0]); if (el) { "
                "el.focus(); el.value = args[1]; "
                "el.dispatchEvent(new Event('input',{bubbles:true})); "
                "el.dispatchEvent(new Event('change',{bubbles:true})); } }",
                [sel, val]
            )
            print(f"  [fill-js] {lbl or sel[:60]} = '{val[:50]}'")
            return True
        except:
            pass
        print(f"  [fill!] {lbl or sel[:60]}: {str(e)[:80]}")
        return False


def click_visible(page, selectors, label=""):
    for s in selectors:
        try:
            el = page.locator(s).first
            if el.count() > 0 and el.is_visible(timeout=2000):
                t = el.inner_text().strip().lower()
                if any(bad in t for bad in ["subscribe", "newsletter", "notify"]):
                    continue
                el.scroll_into_view_if_needed()
                el.click(timeout=5000)
                print(f"  [click] {label}: {s}")
                return True
        except:
            continue
    return False


def has_captcha(page):
    for sel in ["iframe[src*='recaptcha']", "iframe[src*='hcaptcha']",
                ".g-recaptcha", "[data-sitekey]", ".cf-turnstile"]:
        try:
            if page.locator(sel).count() > 0:
                return True
        except: pass
    try:
        return any(w in txt(page)[:2000].lower() for w in ["captcha", "i'm not a robot"])
    except: return False


def has_email_verify(page):
    try:
        t = txt(page)[:2000].lower()
        return any(k in t for k in [
            "verification email sent", "verify your email", "we sent an email",
            "check your inbox", "confirm your email", "click the link in", "activation link",
        ])
    except: return False


def is_real_confirmation(body, url=""):
    t = body.lower()
    # Exclude login pages
    if "login" in url.lower() or ("sign in" in t and "password" in t and "careerhub" not in url.lower()):
        return False
    strong = [
        "thank you for applying",
        "your application has been submitted",
        "application successfully submitted",
        "we have received your application",
        "application received",
        "you have successfully applied",
        "successfully applied to",
        "your submission has been received",
        "application submitted successfully",
        "you applied for",
    ]
    return any(p in t for p in strong)


def save(result):
    path = os.path.join(ROLE_DIR, "SUBMITTED.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"\n[SAVED] {path}")
    print("=" * 60)
    print(f"RESULT: {result['status']}")
    print(f"Notes:  {str(result.get('notes',''))[:600]}")
    print("=" * 60)


# ── Application form filling ──────────────────────────────────────────────────

def inspect_form_fields(page):
    """Dump all visible inputs/selects/radios on the page for debugging."""
    try:
        fields = page.evaluate("""() => {
            let out = [];
            document.querySelectorAll('input,select,textarea').forEach(el => {
                if (el.offsetParent === null) return; // skip hidden
                out.push({
                    tag: el.tagName, type: el.type, id: el.id,
                    name: el.name, placeholder: el.placeholder,
                    value: el.value.slice(0,60), ariaLabel: el.getAttribute('aria-label') || '',
                    required: el.required, checked: el.checked,
                    labelText: (document.querySelector('label[for="'+el.id+'"]') ?
                                document.querySelector('label[for="'+el.id+'"]').textContent.trim().slice(0,60) : '')
                });
            });
            return out;
        }""")
        return fields
    except Exception as e:
        print(f"  [inspect!] {e}")
        return []


def fill_start_date(page):
    """Fill 'Available Start Date' — Phenom uses a date picker or text input."""
    print("  [section] Available Start Date...")
    # Try text input (YYYY-MM-DD or MM/DD/YYYY)
    for sel in [
        "input[type='date']",
        "input[placeholder*='date' i]",
        "input[placeholder*='Date' i]",
        "input[id*='startDate' i]",
        "input[id*='start_date' i]",
        "input[id*='available' i]",
        "input[name*='startDate' i]",
        "input[name*='start_date' i]",
        "input[name*='available' i]",
        "input[aria-label*='date' i]",
        "input[aria-label*='start' i]",
    ]:
        try:
            el = page.locator(sel).first
            if el.count() > 0 and el.is_visible(timeout=2000):
                el.scroll_into_view_if_needed()
                el.click()
                # Try both date formats
                for fmt in ["2025-09-01", "09/01/2025", "September 1, 2025"]:
                    try:
                        el.fill("", timeout=2000)
                        el.fill(fmt, timeout=3000)
                        time.sleep(0.5)
                        val = el.input_value()
                        if val and len(val) > 2:
                            print(f"  [date] {sel} = '{val}'")
                            return True
                    except: pass
        except: pass

    # Look for date picker via section header proximity
    try:
        # Find the "Available Start Date" section and look for inputs near it
        date_section = page.locator("text='Available Start Date'").first
        if date_section.count() > 0:
            # Get the parent container and find inputs within it
            parent = page.evaluate("""() => {
                let headers = Array.from(document.querySelectorAll('h2,h3,h4,div,span,label,p'));
                let header = headers.find(el => el.textContent.includes('Available Start Date'));
                if (!header) return null;
                let section = header.closest('[class*="section"],[class*="group"],[class*="field"],div[class*="form"]') || header.parentElement;
                let inputs = section ? Array.from(section.querySelectorAll('input,select')) : [];
                return inputs.map(el => ({id:el.id, name:el.name, type:el.type, placeholder:el.placeholder}));
            }""")
            if date_section and date_section:
                print(f"  [date-debug] Inputs near 'Available Start Date': {date_section}")
    except Exception as e:
        print(f"  [date-debug!] {e}")

    # JS fallback: set value on any date input
    try:
        result = page.evaluate("""() => {
            let inputs = Array.from(document.querySelectorAll('input'));
            for (let inp of inputs) {
                let ctx = inp.closest('[class*="section"],[class*="row"],[class*="field"],div') || inp.parentElement;
                let ctxt = (ctx ? ctx.textContent : '').toLowerCase();
                if (ctxt.includes('available') || ctxt.includes('start date') || inp.type === 'date') {
                    inp.focus();
                    inp.value = '2025-09-01';
                    inp.dispatchEvent(new Event('input',{bubbles:true}));
                    inp.dispatchEvent(new Event('change',{bubbles:true}));
                    return 'set: ' + inp.id + '/' + inp.name;
                }
            }
            return 'not found';
        }""")
        print(f"  [date-js] {result}")
        return True
    except Exception as e:
        print(f"  [date-js!] {e}")

    return False


def fill_work_auth(page):
    """Fill Work Authorization Status section.
    Q1: Legally authorized to work in US? → YES
    Q2: Need sponsorship now/future? → YES (truthful)
    """
    print("  [section] Work Authorization Status...")

    # Dump the radio groups in this section
    try:
        radios = page.evaluate("""() => {
            let radios = Array.from(document.querySelectorAll('input[type="radio"]'));
            return radios.map(r => {
                let lbl = r.closest('label') || document.querySelector('label[for="'+r.id+'"]');
                let lt = lbl ? lbl.textContent.trim() : (r.value || r.id);
                let ctr = r.closest('[class*="section"],[class*="field"],[class*="group"],fieldset,div') || r.parentElement;
                let ct = ctr ? ctr.textContent.replace(/\\s+/g,' ').trim().slice(0,120) : '';
                return {id: r.id, name: r.name, value: r.value, labelText: lt, context: ct, checked: r.checked};
            });
        }""")
        print(f"  [radio-debug] Found {len(radios)} radios:")
        for r in radios:
            print(f"    id={r.get('id','?')} name={r.get('name','?')} val={r.get('value','?')} lbl='{r.get('labelText','?')[:40]}'")
    except Exception as e:
        print(f"  [radio-debug!] {e}")
        radios = []

    # Strategy: click YES radios for auth/sponsor questions
    page.evaluate("""() => {
        let radios = Array.from(document.querySelectorAll('input[type="radio"]'));
        radios.forEach(r => {
            let lbl = r.closest('label') || document.querySelector('label[for="'+r.id+'"]');
            let lt = (lbl ? lbl.textContent : r.value || '').trim().toLowerCase();
            let ctr = r.closest('[class*="section"],[class*="field"],[class*="group"],fieldset,div') || r.parentElement;
            let ct = (ctr ? ctr.textContent : '').toLowerCase();

            // Q1: authorized to work -> Yes
            if ((ct.includes('legally authorized') || ct.includes('authorized to work'))
                 && lt === 'yes') {
                r.click(); r.checked = true;
                r.dispatchEvent(new Event('change',{bubbles:true}));
                console.log('Clicked Yes for authorized:', r.id);
            }
            // Q2: sponsorship -> Yes (truthful)
            if ((ct.includes('sponsorship') || ct.includes('visa status') || ct.includes('h-1b'))
                 && lt === 'yes') {
                r.click(); r.checked = true;
                r.dispatchEvent(new Event('change',{bubbles:true}));
                console.log('Clicked Yes for sponsorship:', r.id);
            }
        });
    }""")
    time.sleep(1)

    # Also try clicking via visible radio buttons by text label
    for question_text, answer in [
        ("legally authorized", "Yes"),
        ("sponsorship", "Yes"),
        ("H-1B", "Yes"),
        ("visa status", "Yes"),
    ]:
        try:
            # Find a radio near a question containing these words
            radio_sel = f"input[type='radio'][value='Yes'], input[type='radio'][value='yes'], input[type='radio'][value='YES']"
            for radio in page.locator(radio_sel).all():
                try:
                    lbl = radio.locator("xpath=../..").inner_text()
                    if question_text.lower() in lbl.lower():
                        radio.click(force=True)
                        time.sleep(0.5)
                        break
                except: pass
        except: pass


def fill_voluntary_eeoc(page):
    """Fill Voluntary Self-Identification section — BCG Phenom EEO fields.
    Known fields based on v5 screenshot:
    - Gender (radio or select)
    - Hispanic/Latino (Yes/No radio)
    - Race/Ethnicity (checkboxes: Asian, Black, Hispanic, etc.)
    - Disability (radio: Yes/No/Decline)
    - Veteran status (Protected Veteran / Not Protected)
    """
    print("  [section] Voluntary Self-Identification...")

    # Dump all selects for debugging
    try:
        selects = page.evaluate("""() => {
            return Array.from(document.querySelectorAll('select')).map(s => ({
                id: s.id, name: s.name,
                label: (document.querySelector('label[for="'+s.id+'"]') ?
                        document.querySelector('label[for="'+s.id+'"]').textContent.trim().slice(0,60) : ''),
                options: Array.from(s.options).map(o => o.text).slice(0,8)
            }));
        }""")
        print(f"  [select-debug] {len(selects)} selects:")
        for s in selects:
            print(f"    id={s.get('id','?')} label='{s.get('label','?')[:40]}' opts={s.get('options',[])[:5]}")
    except Exception as e:
        print(f"  [select-debug!] {e}")

    # Try all known selector patterns for gender
    print("  [gender] Attempting to set Female...")
    gender_set = False
    for s in ["select[id*='gender' i]", "select[name*='gender' i]",
               "select[id*='sex' i]", "select[aria-label*='gender' i]"]:
        for v in ["Female", "Woman", "Female/Woman", "F", "2"]:
            try:
                page.select_option(s, label=v, timeout=2000)
                print(f"    [select] gender={v} via {s}")
                gender_set = True
                break
            except: continue
        if gender_set: break

    if not gender_set:
        # Try radio for gender
        page.evaluate("""() => {
            let radios = Array.from(document.querySelectorAll('input[type="radio"]'));
            radios.forEach(r => {
                let lbl = r.closest('label') || document.querySelector('label[for="'+r.id+'"]');
                let lt = (lbl ? lbl.textContent : r.value||'').trim().toLowerCase();
                let ctr = r.closest('[class*="section"],[class*="field"],[class*="group"],fieldset') || r.parentElement;
                let ct = (ctr ? ctr.textContent : '').toLowerCase();
                if ((ct.includes('gender') || ct.includes('sex')) &&
                    (lt.includes('female') || lt.includes('woman'))) {
                    r.click(); r.checked = true;
                    r.dispatchEvent(new Event('change',{bubbles:true}));
                }
            });
        }""")
        print("  [gender] tried radio fallback")

    # Hispanic/Latino: No
    print("  [hispanic] Attempting No...")
    hisp_set = False
    for s in ["select[id*='hispanic' i]", "select[name*='hispanic' i]",
               "select[id*='latino' i]", "select[aria-label*='hispanic' i]"]:
        for v in ["No, not Hispanic or Latino", "Not Hispanic or Latino", "No"]:
            try:
                page.select_option(s, label=v, timeout=2000)
                print(f"    [select] hispanic={v}")
                hisp_set = True
                break
            except: continue
        if hisp_set: break

    if not hisp_set:
        page.evaluate("""() => {
            let radios = Array.from(document.querySelectorAll('input[type="radio"]'));
            radios.forEach(r => {
                let lbl = r.closest('label') || document.querySelector('label[for="'+r.id+'"]');
                let lt = (lbl ? lbl.textContent : r.value||'').trim().toLowerCase();
                let ctr = r.closest('[class*="section"],[class*="field"],[class*="group"],fieldset') || r.parentElement;
                let ct = (ctr ? ctr.textContent : '').toLowerCase();
                if ((ct.includes('hispanic') || ct.includes('latino')) &&
                    (lt.includes('no') || lt.includes('not'))) {
                    r.click(); r.checked = true;
                    r.dispatchEvent(new Event('change',{bubbles:true}));
                }
            });
        }""")

    # Race/Ethnicity: Asian checkbox
    print("  [race] Attempting Asian...")
    race_set = False
    for s in ["select[id*='ethnicity' i]", "select[name*='ethnicity' i]",
               "select[id*='race' i]", "select[name*='race' i]",
               "select[aria-label*='race' i]", "select[aria-label*='ethnicity' i]"]:
        for v in ["Asian", "Asian (Not Hispanic or Latino)", "Asian or Pacific Islander",
                   "Asian/Pacific Islander"]:
            try:
                page.select_option(s, label=v, timeout=2000)
                print(f"    [select] race/ethnicity={v}")
                race_set = True
                break
            except: continue
        if race_set: break

    if not race_set:
        # Try checkbox (BCG uses checkboxes for race)
        asian_checked = False
        for s in [
            "input[type='checkbox'][value*='Asian' i]",
            "input[type='checkbox'][id*='asian' i]",
            "input[type='checkbox'][name*='asian' i]",
        ]:
            try:
                el = page.locator(s).first
                if el.count() > 0:
                    if not el.is_checked():
                        el.click(force=True)
                    print(f"    [checkbox] Asian via {s}")
                    asian_checked = True
                    break
            except: pass

        if not asian_checked:
            # JS approach: find label with "Asian" text and click its checkbox
            page.evaluate("""() => {
                let labels = Array.from(document.querySelectorAll('label'));
                let asianLabel = labels.find(l =>
                    l.textContent.trim().toLowerCase().includes('asian') &&
                    !l.textContent.toLowerCase().includes('pacific')
                );
                if (asianLabel) {
                    let cb = asianLabel.querySelector('input[type="checkbox"]') ||
                             document.getElementById(asianLabel.htmlFor);
                    if (cb && !cb.checked) {
                        cb.click(); cb.checked = true;
                        cb.dispatchEvent(new Event('change',{bubbles:true}));
                    }
                }
                // Also try: find checkboxes with parent text containing 'asian'
                Array.from(document.querySelectorAll('input[type="checkbox"]')).forEach(cb => {
                    let lbl = cb.closest('label') || document.querySelector('label[for="'+cb.id+'"]');
                    let lt = (lbl ? lbl.textContent : '').trim().toLowerCase();
                    if (lt.includes('asian') && !lt.includes('south asian')) {
                        if (!cb.checked) { cb.click(); cb.checked = true;
                            cb.dispatchEvent(new Event('change',{bubbles:true})); }
                    }
                });
            }""")
            print("  [race] tried JS label approach")

    # Disability: No / I don't have a disability
    print("  [disability] Attempting No...")
    dis_set = False
    for s in ["select[id*='disability' i]", "select[name*='disability' i]",
               "select[aria-label*='disability' i]"]:
        for v in ["No, I Don't Have a Disability", "No", "I do not have a disability",
                   "I don't have a disability"]:
            try:
                page.select_option(s, label=v, timeout=2000)
                print(f"    [select] disability={v}")
                dis_set = True
                break
            except: continue
        if dis_set: break

    if not dis_set:
        page.evaluate("""() => {
            let radios = Array.from(document.querySelectorAll('input[type="radio"]'));
            radios.forEach(r => {
                let lbl = r.closest('label') || document.querySelector('label[for="'+r.id+'"]');
                let lt = (lbl ? lbl.textContent : r.value||'').trim().toLowerCase();
                let ctr = r.closest('[class*="section"],[class*="field"],[class*="group"],fieldset') || r.parentElement;
                let ct = (ctr ? ctr.textContent : '').toLowerCase();
                if (ct.includes('disability') && (lt.includes('no') || lt.includes('not') || lt.includes("don't"))) {
                    r.click(); r.checked = true;
                    r.dispatchEvent(new Event('change',{bubbles:true}));
                }
            });
        }""")

    # Veteran status: Not a protected veteran
    print("  [veteran] Attempting Not a protected veteran...")
    vet_set = False
    for s in ["select[id*='veteran' i]", "select[name*='veteran' i]",
               "select[aria-label*='veteran' i]"]:
        for v in ["I am not a protected veteran", "Not a Protected Veteran",
                   "I identify as not being a protected veteran", "No", "Not a Veteran"]:
            try:
                page.select_option(s, label=v, timeout=2000)
                print(f"    [select] veteran={v}")
                vet_set = True
                break
            except: continue
        if vet_set: break

    if not vet_set:
        page.evaluate("""() => {
            let radios = Array.from(document.querySelectorAll('input[type="radio"]'));
            radios.forEach(r => {
                let lbl = r.closest('label') || document.querySelector('label[for="'+r.id+'"]');
                let lt = (lbl ? lbl.textContent : r.value||'').trim().toLowerCase();
                let ctr = r.closest('[class*="section"],[class*="field"],[class*="group"],fieldset') || r.parentElement;
                let ct = (ctr ? ctr.textContent : '').toLowerCase();
                if ((ct.includes('veteran') || ct.includes('military')) &&
                    (lt.includes('not') || lt === 'no' || lt.includes("am not"))) {
                    r.click(); r.checked = true;
                    r.dispatchEvent(new Event('change',{bubbles:true}));
                }
            });
        }""")

    time.sleep(1)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    R = {
        "company": "BCG (Boston Consulting Group)",
        "role": "Talent Senior Specialist - People",
        "ats": "Phenom (experiencedtalent.bcg.com)",
        "status": "in_progress",
        "confirmed_at": None,
        "screenshot": None,
        "account_email": EMAIL,
        "notes": "",
        "job_url": JOB_PUBLIC_URL,
        "apply_url": PHENOM_APPLY,
    }

    print("=" * 60)
    print("BCG Phenom v6 -- Talent Senior Specialist - People")
    print("=" * 60)

    # Kill stale Chrome
    subprocess.run(
        ["powershell", "-Command",
         f"Get-NetTCPConnection -LocalPort {PORT} -ErrorAction SilentlyContinue | "
         f"Select-Object -ExpandProperty OwningProcess | "
         f"ForEach-Object {{ Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }}"],
        capture_output=True, timeout=10
    )
    time.sleep(2)

    print(f"\n[1] Launching Chrome (port {PORT})...")
    proc = subprocess.Popen(
        [CHROME,
         f"--remote-debugging-port={PORT}",
         f"--user-data-dir={PROFILE}",
         "--no-first-run",
         "--no-default-browser-check",
         "--disable-blink-features=AutomationControlled",
         PHENOM_LOGIN],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    print(f"  PID {proc.pid}, waiting 15s...")
    time.sleep(15)

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(f"http://localhost:{PORT}")
        ctx = browser.contexts[0]
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.set_default_timeout(30000)

        try:
            net(page, 20000)
            time.sleep(3)
            dismiss_cookie(page)
            time.sleep(2)
            ss(page, "v6_01_initial")
            body = txt(page)
            print(f"  URL: {page.url}")
            print(f"  Body: {body[:300]}")

            # ── Login ─────────────────────────────────────────────────────
            print("\n[2] Login...")
            if "login" in page.url.lower():
                # Email entry
                for s in ["input[type='email']", "input[placeholder*='Email' i]",
                           "input[name*='email' i]", "input[id*='email' i]",
                           "input[autocomplete='email']"]:
                    try:
                        el = page.locator(s).first
                        if el.count() > 0 and el.is_visible(timeout=3000):
                            el.click(timeout=3000)
                            el.fill("", timeout=2000)
                            el.fill(EMAIL, timeout=5000)
                            print(f"  [fill] email = '{EMAIL}'")
                            break
                    except: continue

                ss(page, "v6_02_email")
                click_visible(page, ["button:has-text('Continue')", "button[type='submit']"], "continue")
                time.sleep(7); net(page, 15000)
                dismiss_cookie(page)
                body = txt(page)
                ss(page, "v6_03_after_email")
                print(f"  URL: {page.url}")
                print(f"  Body: {body[:300]}")

                if has_captcha(page):
                    R["status"] = "captcha-staged"
                    R["notes"] = "CAPTCHA after email."
                    browser.close(); save(R); return R
                if has_email_verify(page):
                    R["status"] = "email-verify-staged"
                    R["notes"] = f"Email verify. Check {EMAIL}."
                    browser.close(); save(R); return R

                # Password form
                if "password" in body.lower():
                    pw_inputs = page.locator("input[type='password']").all()
                    if pw_inputs:
                        pw_inputs[0].click(timeout=3000)
                        pw_inputs[0].fill(PW, timeout=5000)
                        print("  [fill] password")
                    ss(page, "v6_04_pw")
                    click_visible(page, [
                        "button:has-text('Submit')",
                        "button[type='submit']",
                        "button:has-text('Sign In')",
                    ], "submit_pw")
                    time.sleep(8); net(page, 15000)
                    dismiss_cookie(page)
                    ss(page, "v6_05_after_signin")
                    body = txt(page)
                    print(f"  Post-signin URL: {page.url}")
                    print(f"  Body: {body[:300]}")

                    if "login" in page.url.lower():
                        # Still on login — try OTP
                        click_visible(page, [
                            "a:has-text('Use a one-time code instead')",
                            "a:has-text('one-time code')",
                        ], "otp_link")
                        time.sleep(4)
                        R["status"] = "email-verify-staged"
                        R["notes"] = (
                            f"Password login failed for {EMAIL}. "
                            "Clicked 'one-time code' link — check inbox for OTP. "
                            f"Chrome on port {PORT} / profile {PROFILE}."
                        )
                        ss(page, "v6_99_login_fail"); browser.close(); save(R); return R
                elif any(w in body.lower() for w in ["first name", "create account", "register"]):
                    # New account
                    for s in ["input[placeholder*='First' i]", "input[name*='first' i]"]:
                        try:
                            el = page.locator(s).first
                            if el.count() > 0 and el.is_visible(timeout=2000):
                                el.click(); el.fill("Yi-Chieh"); break
                        except: pass
                    for s in ["input[placeholder*='Last' i]", "input[name*='last' i]"]:
                        try:
                            el = page.locator(s).first
                            if el.count() > 0 and el.is_visible(timeout=2000):
                                el.click(); el.fill("Cheng"); break
                        except: pass
                    for pw_el in page.locator("input[type='password']").all()[:2]:
                        try: pw_el.fill(PW)
                        except: pass
                    ss(page, "v6_reg_filled")
                    if has_captcha(page):
                        R["status"] = "captcha-staged"
                        R["notes"] = "CAPTCHA on registration."
                        browser.close(); save(R); return R
                    click_visible(page, [
                        "button:has-text('Create Account')", "button:has-text('Sign Up')",
                        "button[type='submit']", "button:has-text('Register')",
                    ], "create_account")
                    time.sleep(8); net(page, 15000)
                    if has_email_verify(page):
                        R["status"] = "email-verify-staged"
                        R["notes"] = f"Account created — verify at {EMAIL}."
                        browser.close(); save(R); return R

            # ── Navigate to application form ──────────────────────────────
            print("\n[3] Loading application form...")
            page.goto(PHENOM_APPLY, timeout=30000, wait_until="domcontentloaded")
            time.sleep(8); net(page, 15000)
            dismiss_cookie(page)
            time.sleep(2)
            ss(page, "v6_10_form_loaded")
            body = txt(page)
            print(f"  URL: {page.url}")
            print(f"  Body: {body[:500]}")

            if "login" in page.url.lower():
                R["status"] = "email-verify-staged"
                R["notes"] = f"Redirected to login after navigation. Check {EMAIL} for verification."
                browser.close(); save(R); return R

            # ── Inspect and fill all form sections ────────────────────────
            print("\n[4] Inspecting form fields...")
            fields = inspect_form_fields(page)
            print(f"  Found {len(fields)} visible form fields:")
            for f in fields:
                print(f"    {f.get('tag','?')}[{f.get('type','?')}] id={f.get('id','?')} "
                      f"name={f.get('name','?')} placeholder='{f.get('placeholder','?')[:30]}' "
                      f"label='{f.get('labelText','?')[:40]}'")

            print("\n[5] Uploading resume...")
            resume_uploaded = False
            for s in ["input[type='file'][accept*='pdf' i]",
                       "input[type='file'][accept*='.pdf' i]",
                       "input[type='file']"]:
                try:
                    inputs = page.locator(s).all()
                    if inputs:
                        inputs[0].set_input_files(RESUME)
                        time.sleep(5)
                        print(f"  [upload] resume via {s}")
                        resume_uploaded = True
                        # Dismiss autofill prompts
                        for dismiss in ["No, thanks", "Skip", "No thanks", "Enter Manually"]:
                            try:
                                el = page.get_by_text(dismiss, exact=False).first
                                if el.count() > 0 and el.is_visible(timeout=2000):
                                    el.click(); time.sleep(2); break
                            except: pass
                        break
                except Exception as e:
                    print(f"  [upload!] {s}: {e}")
            ss(page, "v6_11_after_resume")

            print("\n[6] Filling personal info (Before applying)...")
            body = txt(page)
            body_lower = body.lower()

            # Fill name fields (may be pre-filled from profile)
            for s, v, l in [
                ("input[id*='email' i]", EMAIL, "email"),
                ("input[type='email']", EMAIL, "email"),
            ]:
                try:
                    el = page.locator(s).first
                    if el.count() > 0 and el.is_visible(timeout=1500):
                        cur_val = el.input_value().strip()
                        if not cur_val:
                            fill_input(page, s, v, l)
                except: pass

            for s, v, l in [
                ("input[placeholder*='First' i]", "Yi-Chieh", "first"),
                ("input[name*='first' i]", "Yi-Chieh", "first"),
                ("input[id*='firstName' i]", "Yi-Chieh", "first"),
                ("input[id*='first_name' i]", "Yi-Chieh", "first"),
            ]:
                try:
                    el = page.locator(s).first
                    if el.count() > 0 and el.is_visible(timeout=1500):
                        cur_val = el.input_value().strip()
                        if not cur_val:
                            fill_input(page, s, v, l); break
                except: pass

            for s, v, l in [
                ("input[placeholder*='Last' i]", "Cheng", "last"),
                ("input[name*='last' i]", "Cheng", "last"),
                ("input[id*='lastName' i]", "Cheng", "last"),
                ("input[id*='last_name' i]", "Cheng", "last"),
            ]:
                try:
                    el = page.locator(s).first
                    if el.count() > 0 and el.is_visible(timeout=1500):
                        cur_val = el.input_value().strip()
                        if not cur_val:
                            fill_input(page, s, v, l); break
                except: pass

            for s in ["input[type='tel']", "input[placeholder*='Phone' i]",
                       "input[name*='phone' i]", "input[id*='phone' i]"]:
                try:
                    el = page.locator(s).first
                    if el.count() > 0 and el.is_visible(timeout=1500):
                        cur_val = el.input_value().strip()
                        if not cur_val:
                            fill_input(page, s, "2137003831", "phone"); break
                except: pass

            # Country = United States
            for s in ["select[name*='country' i]", "select[id*='country' i]"]:
                try:
                    page.select_option(s, label="United States of America", timeout=2000)
                    print(f"  [select] country=USA")
                    time.sleep(1.5)  # wait for state cascade
                    break
                except:
                    try:
                        page.select_option(s, label="United States", timeout=2000)
                        time.sleep(1.5); break
                    except: pass

            # State = Oregon
            for s in ["select[name*='state' i]", "select[id*='state' i]",
                       "select[name*='province' i]"]:
                try:
                    page.select_option(s, label="Oregon", timeout=2000)
                    print(f"  [select] state=Oregon"); break
                except:
                    try:
                        page.select_option(s, value="OR", timeout=2000)
                        break
                    except: pass

            # City
            for s in ["input[placeholder*='City' i]", "input[name*='city' i]",
                       "input[id*='city' i]"]:
                try:
                    el = page.locator(s).first
                    if el.count() > 0 and el.is_visible(timeout=1500):
                        if not el.input_value().strip():
                            fill_input(page, s, "Portland", "city"); break
                except: pass

            ss(page, "v6_12_personal_filled")
            time.sleep(2)

            print("\n[7] Filling Available Start Date...")
            fill_start_date(page)
            time.sleep(1)
            ss(page, "v6_13_date_filled")

            print("\n[8] Filling Work Authorization Status...")
            fill_work_auth(page)
            time.sleep(1)
            ss(page, "v6_14_workauth_filled")

            print("\n[9] Filling Voluntary Self-Identification...")
            fill_voluntary_eeoc(page)
            time.sleep(1)
            ss(page, "v6_15_eeoc_filled")

            # Scroll to bottom to check for any remaining errors
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(2)
            ss(page, "v6_16_full_page_scroll")
            body = txt(page)
            print(f"\n  Current errors: {'error' in body.lower()}")
            if "error" in body.lower():
                error_text = [line for line in body.split('\n') if 'error' in line.lower()]
                print(f"  Error lines: {error_text[:5]}")

            # Check for confirmation BEFORE clicking submit
            if is_real_confirmation(body, page.url):
                print("  *** Confirmation found before submit! ***")
                R["status"] = "submitted"
                R["confirmed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                R["screenshot"] = os.path.join(SHOT, "v6_16_full_page_scroll.png")
                R["notes"] = f"Already submitted. {body[:600]}"
                browser.close(); save(R); return R

            # ── Final pre-submit review screenshot ───────────────────────
            page.evaluate("window.scrollTo(0, 0)")
            time.sleep(1)
            ss(page, "v6_17_pre_submit_review")
            body = txt(page)
            print(f"\n[10] Pre-submit review:")
            print(f"  URL: {page.url}")
            print(f"  Body (first 800): {body[:800]}")

            # ── Submit ────────────────────────────────────────────────────
            print("\n[11] Submitting application...")
            submit_clicked = False
            for s in [
                "button:has-text('Submit Application')",
                "button:has-text('Submit')",
                "input[type='submit'][value*='Submit' i]",
                "button[data-testid='submit-application']",
            ]:
                try:
                    el = page.locator(s).first
                    if el.count() > 0 and el.is_visible(timeout=3000):
                        t = el.inner_text().strip() if hasattr(el, 'inner_text') else ""
                        if any(bad in t.lower() for bad in ["subscribe", "newsletter"]):
                            continue
                        el.scroll_into_view_if_needed()
                        ss(page, "v6_18_pre_submit_click")
                        print(f"  Clicking: {s} = '{t[:40]}'")
                        el.click(timeout=5000)
                        submit_clicked = True
                        time.sleep(10); net(page, 20000)
                        break
                except Exception as e:
                    print(f"  [submit!] {s}: {e}")

            if not submit_clicked:
                R["status"] = "blocked"
                R["notes"] = f"No submit button found. URL: {page.url}. Body: {txt(page)[:400]}"
                ss(page, "v6_99_no_submit")
                browser.close(); save(R); return R

            # ── Post-submit check ─────────────────────────────────────────
            body = txt(page)
            ss(page, "v6_19_post_submit")
            print(f"\n  Post-submit URL: {page.url}")
            print(f"  Post-submit body: {body[:600]}")

            if has_captcha(page):
                R["status"] = "captcha-staged"
                R["notes"] = f"CAPTCHA appeared after Submit. URL: {page.url}"
                browser.close(); save(R); return R

            if is_real_confirmation(body, page.url):
                R["status"] = "submitted"
                R["confirmed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                R["screenshot"] = os.path.join(SHOT, "v6_19_post_submit.png")
                R["notes"] = f"SUBMITTED. Confirmation: {body[:600]}"
                print("  *** CONFIRMED SUBMISSION! ***")
                browser.close(); save(R); return R

            # Errors still present?
            if "error" in body.lower() and "required" in body.lower():
                error_lines = [l.strip() for l in body.split('\n')
                               if any(w in l.lower() for w in ["error", "required", "cannot be left blank"])]
                print(f"  Still showing errors: {error_lines[:10]}")
                R["status"] = "blocked"
                R["notes"] = (
                    f"Submit clicked but form still has errors. "
                    f"Errors: {error_lines[:5]}. "
                    f"URL: {page.url}. Body: {body[:400]}"
                )
                browser.close(); save(R); return R

            # Ambiguous — likely submitted
            R["status"] = "likely-submitted"
            R["confirmed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            R["screenshot"] = os.path.join(SHOT, "v6_19_post_submit.png")
            R["notes"] = f"Submit clicked. Post: {body[:600]}"
            browser.close(); save(R); return R

        except Exception as e:
            tb = traceback.format_exc()
            print(f"\n[EXCEPTION] {e}\n{tb[:1000]}")
            R["status"] = "error"
            R["notes"] = f"Exception: {str(e)}\n{tb[:500]}"
            try: ss(page, "v6_99_exception")
            except: pass
            try: browser.close()
            except: pass
            save(R)
            return R


if __name__ == "__main__":
    main()
