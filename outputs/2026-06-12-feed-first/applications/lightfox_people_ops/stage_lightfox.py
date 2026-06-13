"""
stage_lightfox.py
Navigate to the Lightfox careers form in the CDP browser,
fill all text fields, upload resume.pdf, and leave staged for human CAPTCHA solve.
"""
import sys, json, time
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

RESUME_PDF = Path(r"C:\Users\chent\Agentic_Workflows_2026\oracle-job-search\outputs\2026-06-12-feed-first\applications\lightfox_people_ops\resume.pdf")
OUT_DIR    = Path(r"C:\Users\chent\Agentic_Workflows_2026\oracle-job-search\outputs\2026-06-12-feed-first\applications\lightfox_people_ops\screenshots")
APP_DIR    = Path(r"C:\Users\chent\Agentic_Workflows_2026\oracle-job-search\outputs\2026-06-12-feed-first\applications\lightfox_people_ops")
TARGET_URL = "https://www.lightfoxgames.com/careers/?id=people-operations-coordinator"
OUT_DIR.mkdir(parents=True, exist_ok=True)

FILL_SCRIPT = """
(function() {
    const inputs = document.querySelectorAll('input, textarea');
    const filled = [];
    for (const el of inputs) {
        const name = el.name || '';
        if (name === 'name' && !el.value) {
            el.value = 'Jamie Cheng';
            el.dispatchEvent(new Event('input', {bubbles:true}));
            el.dispatchEvent(new Event('change', {bubbles:true}));
            filled.push('name');
        } else if (name === 'email' && !el.value) {
            el.value = 'jamiecheng0103@gmail.com';
            el.dispatchEvent(new Event('input', {bubbles:true}));
            el.dispatchEvent(new Event('change', {bubbles:true}));
            filled.push('email');
        } else if (name === 'linkedinUrl' && !el.value) {
            el.value = 'https://www.linkedin.com/in/jamieyccheng/';
            el.dispatchEvent(new Event('input', {bubbles:true}));
            el.dispatchEvent(new Event('change', {bubbles:true}));
            filled.push('linkedinUrl');
        }
    }
    const ack = document.getElementById('ack');
    if (ack && !ack.checked) { ack.click(); filled.push('ack'); }
    return filled;
})()
"""

VERIFY_SCRIPT = """
(function() {
    const f = {};
    document.querySelectorAll('input[name], textarea[name]').forEach(function(el) {
        var v = el.type === 'file' ? (el.files[0] ? el.files[0].name : 'empty') : (el.value || '');
        f[el.name] = v.substring(0, 80);
    });
    var ack = document.getElementById('ack');
    f['ack_checked'] = ack ? ack.checked : false;
    var token = document.querySelector('[name="cf-turnstile-response"]');
    f['turnstile_len'] = token ? token.value.length : 0;
    return f;
})()
"""

def safe(t):
    return (t or '').encode('ascii', 'replace').decode('ascii') if isinstance(t, str) else str(t)

def ss(page, name):
    path = str(OUT_DIR / (name + '.png'))
    try:
        page.screenshot(path=path, full_page=True)
        print(f"  [SS] {name}.png")
    except Exception as e:
        print(f"  [SS-ERR] {name}: {safe(str(e))[:80]}")
    return path

def main():
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.connect_over_cdp("http://localhost:9222")
        ctx = browser.contexts[0]
        pages = ctx.pages

        print(f"CDP tabs ({len(pages)}):")
        for i, pg in enumerate(pages):
            print(f"  [{i}] {pg.url[:90]}")

        # Find or navigate to Lightfox page
        lf_page = next((pg for pg in pages if "lightfoxgames.com" in pg.url), None)
        if lf_page:
            print(f"\nFound Lightfox tab: {lf_page.url}")
            lf_page.bring_to_front()
            # Reload to get a fresh form with a fresh Turnstile
            print("Reloading for fresh form + fresh Turnstile token...")
            lf_page.reload(wait_until="domcontentloaded")
            lf_page.wait_for_timeout(5000)
        else:
            print(f"\nNo Lightfox tab — opening new one...")
            lf_page = ctx.new_page()
            lf_page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=20000)
            lf_page.wait_for_timeout(5000)

        ss(lf_page, "01_fresh_form")

        # Fill text fields
        print("\nFilling text fields...")
        filled = lf_page.evaluate(FILL_SCRIPT)
        print(f"  Filled: {filled}")
        lf_page.wait_for_timeout(800)

        # Upload resume
        print(f"\nUploading resume: {RESUME_PDF.name}")
        if not RESUME_PDF.exists():
            print(f"  [ERR] File not found: {RESUME_PDF}")
            sys.exit(1)

        # Make the file input visible if needed, then upload
        lf_page.evaluate("""
            (function() {
                var fi = document.querySelector('input[type="file"][name="resume"]');
                if (fi) {
                    fi.style.display = 'block';
                    fi.style.visibility = 'visible';
                    fi.style.opacity = '1';
                    fi.style.position = 'relative';
                    fi.style.width = '100px';
                    fi.style.height = '30px';
                }
            })()
        """)
        lf_page.wait_for_timeout(300)

        file_loc = lf_page.locator('input[type="file"][name="resume"]').first
        if file_loc.count() == 0:
            file_loc = lf_page.locator('input[type="file"]').first

        if file_loc.count() > 0:
            file_loc.set_input_files(str(RESUME_PDF))
            lf_page.wait_for_timeout(2000)
            fname = lf_page.evaluate("""
                (function() {
                    var fi = document.querySelector('input[type="file"]');
                    return fi && fi.files[0] ? fi.files[0].name : 'no file';
                })()
            """)
            print(f"  File input shows: {fname}")
        else:
            print("  [WARN] No file input found on page")

        lf_page.wait_for_timeout(1000)

        # Wait for Turnstile to auto-solve (it often auto-solves in real browsers)
        print("\nWaiting up to 15s for Turnstile auto-solve...")
        for i in range(15):
            token_len = lf_page.evaluate("""
                (function() {
                    var t = document.querySelector('[name="cf-turnstile-response"]');
                    return t ? t.value.length : 0;
                })()
            """)
            if token_len > 0:
                print(f"  Turnstile solved! Token length: {token_len}")
                break
            print(f"  [{i+1}/15] Waiting... token_len={token_len}")
            lf_page.wait_for_timeout(1000)

        # Verify final state
        state = lf_page.evaluate(VERIFY_SCRIPT)
        print(f"\nFinal form state: {json.dumps(state, indent=2)}")

        ss(lf_page, "06_staged_final")

        turnstile_solved = state.get('turnstile_len', 0) > 0
        resume_ok = state.get('resume', 'empty') not in ('empty', '')
        name_ok = bool(state.get('name', ''))
        email_ok = bool(state.get('email', ''))

        print(f"\nReadiness: name={name_ok}, email={email_ok}, resume={resume_ok}, captcha={turnstile_solved}")

        if turnstile_solved and resume_ok and name_ok and email_ok:
            # All good — try auto-submit
            print("\nAll fields ready including Turnstile! Attempting auto-submit...")
            lf_page.wait_for_timeout(500)
            submit_btn = lf_page.locator('button:has-text("SUBMIT")').first
            if submit_btn.count() == 0:
                submit_btn = lf_page.locator('button[type="submit"]').first

            submit_btn.scroll_into_view_if_needed()
            lf_page.wait_for_timeout(800)
            ss(lf_page, "07_pre_submit")
            submit_btn.click(timeout=10000)
            lf_page.wait_for_timeout(7000)
            ss(lf_page, "08_after_submit")

            final_text = lf_page.inner_text("body")[:2000]
            success_kw = ["thank you", "application received", "submitted", "we'll be in touch",
                          "application sent", "received your application", "we received"]
            confirmed = any(kw in final_text.lower() for kw in success_kw)
            print(f"  Submission confirmed: {confirmed}")
            print(f"  Page preview: {final_text[:300]}")

            status = "submitted" if confirmed else "submitted_unconfirmed"
            screenshot_key = "08_after_submit.png"
        else:
            status = "captcha-staged"
            screenshot_key = "06_staged_final.png"
            print("\n[CAPTCHA-STAGED] Turnstile not yet solved.")
            print("  Human action required:")
            print(f"  1. Look at Chrome tab: {TARGET_URL}")
            print("  2. Solve the Cloudflare Turnstile CAPTCHA widget")
            print("  3. Click 'SUBMIT APPLICATION ->'")

        # Write SUBMITTED.json
        result = {
            "company": "Lightfox Games",
            "role": "People & Operations Coordinator",
            "ats": "Custom form (lightfoxgames.com/careers) — NOT LinkedIn Easy Apply",
            "status": status,
            "confirmed_at": time.strftime("%Y-%m-%dT%H:%M:%S") if "submitted" in status else None,
            "screenshot": str(OUT_DIR / screenshot_key),
            "notes": (
                "LinkedIn job uses 'Apply on company website' redirect — NOT Easy Apply. "
                "Redirects to lightfoxgames.com custom careers form with Cloudflare Turnstile CAPTCHA. "
                f"Form fields filled: name=Jamie Cheng, email=jamiecheng0103@gmail.com, "
                f"linkedinUrl=linkedin.com/in/jamieyccheng, resume={'uploaded' if resume_ok else 'MISSING'}, "
                f"hybrid ack={'checked' if state.get('ack_checked') else 'UNCHECKED'}. "
                f"Turnstile: {'solved' if turnstile_solved else 'NOT solved — human must complete'}. "
                f"Status: {status}."
            ),
            "job_url": TARGET_URL,
            "linkedin_job_url": "https://www.linkedin.com/jobs/view/people-operations-coordinator-at-lightfox-games-4421646290",
            "captcha_type": "cloudflare_turnstile",
            "captcha_solved": turnstile_solved,
            "form_fields_verified": state,
            "human_action_required": None if "submitted" in status else
                f"Open {TARGET_URL}, solve Cloudflare Turnstile CAPTCHA, click SUBMIT APPLICATION",
        }
        result_path = APP_DIR / "SUBMITTED.json"
        result_path.write_text(json.dumps(result, indent=2, default=str))
        print(f"\nAudit written: {result_path}")
        print(f"Status: {status}")

if __name__ == "__main__":
    main()
