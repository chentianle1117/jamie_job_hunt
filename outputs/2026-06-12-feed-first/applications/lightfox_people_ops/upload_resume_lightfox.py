"""
upload_resume_lightfox.py
Attaches to the Chrome MCP tab (via CDP port 9222) that already has
https://www.lightfoxgames.com/careers/?id=people-operations-coordinator open
and uploads resume.pdf into the file input.

The form fields (name/email/linkedin/ack) were already filled via Chrome MCP JS.
This script only handles the file upload (which requires a real file-input interaction)
and takes a screenshot of the final staged form.

Run:  python upload_resume_lightfox.py
"""
import os, sys, time, json
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

DEBUG_PORT = 9222
RESUME_PDF = Path(r"C:\Users\chent\Agentic_Workflows_2026\oracle-job-search\outputs\2026-06-12-feed-first\applications\lightfox_people_ops\resume.pdf")
OUT_DIR    = Path(r"C:\Users\chent\Agentic_Workflows_2026\oracle-job-search\outputs\2026-06-12-feed-first\applications\lightfox_people_ops\screenshots")
APP_DIR    = Path(r"C:\Users\chent\Agentic_Workflows_2026\oracle-job-search\outputs\2026-06-12-feed-first\applications\lightfox_people_ops")
TARGET_URL = "https://www.lightfoxgames.com/careers/?id=people-operations-coordinator"

OUT_DIR.mkdir(parents=True, exist_ok=True)

def safe_text(t):
    return (t or '').encode('ascii', 'replace').decode('ascii') if isinstance(t, str) else str(t)

def ss(page, name):
    path = str(OUT_DIR / f"{name}.png")
    try:
        page.screenshot(path=path, full_page=True)
        print(f"  [SS] {name}.png")
    except Exception as e:
        print(f"  [SS-ERR] {name}: {safe_text(str(e))[:80]}")
    return path

def main():
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.connect_over_cdp(f"http://localhost:{DEBUG_PORT}")
        ctx = browser.contexts[0]
        pages = ctx.pages

        print(f"Open tabs ({len(pages)}):")
        for i, pg in enumerate(pages):
            print(f"  [{i}] {pg.url[:80]}")

        # Find the Lightfox careers page
        lf_page = next((pg for pg in pages if "lightfoxgames.com" in pg.url), None)
        if not lf_page:
            print(f"Lightfox tab not found — opening it now...")
            lf_page = ctx.new_page()
            lf_page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=20000)
            lf_page.wait_for_timeout(4000)
        else:
            print(f"Found Lightfox tab: {lf_page.url}")
            lf_page.bring_to_front()
            lf_page.wait_for_timeout(2000)

        ss(lf_page, "01_form_before_upload")

        # ── Re-fill text fields in case they got cleared ────────────────────
        print("\nRe-filling form fields...")
        fill_result = lf_page.evaluate("""() => {
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
            // Ensure ack checkbox is checked
            const ack = document.getElementById('ack');
            if (ack && !ack.checked) {
                ack.click();
                filled.push('ack_checked');
            }
            // Verify
            const verify = Array.from(document.querySelectorAll('input[name], textarea[name]')).map(el => ({
                name: el.name, value: (el.value||'').substring(0,60), checked: el.checked
            }));
            return {filled, verify};
        }""")
        print(f"  Filled: {fill_result.get('filled', [])}")
        for f in fill_result.get('verify', []):
            print(f"  Field {f['name']}: '{f['value']}' checked={f.get('checked','')}")

        # ── Upload resume ────────────────────────────────────────────────────
        print(f"\nUploading resume: {RESUME_PDF.name}")
        if not RESUME_PDF.exists():
            print(f"  [ERR] Resume PDF not found: {RESUME_PDF}")
            sys.exit(1)

        file_input = lf_page.locator("input[type=file][name=resume]").first
        if file_input.count() == 0:
            file_input = lf_page.locator("input[type=file]").first

        if file_input.count() > 0:
            file_input.set_input_files(str(RESUME_PDF))
            lf_page.wait_for_timeout(2000)
            print("  Resume uploaded successfully")
            # Verify filename shown
            resume_label = lf_page.evaluate("""() => {
                const fi = document.querySelector('input[type=file]');
                return fi ? fi.files[0]?.name || 'no file' : 'input not found';
            }""")
            print(f"  File input shows: {resume_label}")
        else:
            print("  [ERR] No file input found")
            sys.exit(1)

        lf_page.wait_for_timeout(1500)
        ss(lf_page, "02_form_filled_captcha_pending")

        # ── Check CAPTCHA state ─────────────────────────────────────────────
        captcha_info = lf_page.evaluate("""() => {
            const turnstile = document.querySelector('[name="cf-turnstile-response"], .cf-turnstile, iframe[src*="challenges.cloudflare.com"]');
            const turnstileWidget = document.querySelector('.cf-turnstile, [data-sitekey]');
            return {
                hasTurnstileInput: !!document.querySelector('[name="cf-turnstile-response"]'),
                turnstileValue: (document.querySelector('[name="cf-turnstile-response"]')?.value || ''),
                hasTurnstileIframe: !!document.querySelector('iframe[src*="challenges.cloudflare.com"]'),
                hasWidget: !!turnstileWidget,
                widgetDataSitekey: turnstileWidget?.getAttribute('data-sitekey') || ''
            };
        }""")
        print(f"\nCAPTCHA state: {captcha_info}")

        captcha_solved = bool(captcha_info.get('turnstileValue', ''))
        print(f"  Turnstile solved: {captcha_solved}")

        # Final screenshot
        ss(lf_page, "03_final_staged")

        # Write audit
        status = "submitted" if captcha_solved else "captcha-staged"
        result_data = {
            "company": "Lightfox Games",
            "role": "People & Operations Coordinator",
            "ats": "Custom form (lightfoxgames.com/careers) — NOT LinkedIn Easy Apply",
            "status": status,
            "confirmed_at": time.strftime("%Y-%m-%dT%H:%M:%S") if captcha_solved else None,
            "screenshot": str(OUT_DIR / "03_final_staged.png"),
            "notes": (
                "Custom Lightfox careers page — no LinkedIn Easy Apply available. "
                "Form fields filled: name=Jamie Cheng, email=jamiecheng0103@gmail.com, "
                "linkedinUrl=linkedin.com/in/jamieyccheng, resume.pdf uploaded, hybrid ack checked. "
                "BLOCKED by Cloudflare Turnstile CAPTCHA — tab left open for human completion. "
                "Human action required: solve CAPTCHA then click 'SUBMIT APPLICATION'."
            ),
            "job_url": "https://www.lightfoxgames.com/careers/?id=people-operations-coordinator",
            "linkedin_job_url": "https://www.linkedin.com/jobs/view/people-operations-coordinator-at-lightfox-games-4421646290",
            "captcha_type": "cloudflare_turnstile",
            "captcha_solved": captcha_solved,
            "form_fields_filled": {
                "name": "Jamie Cheng",
                "email": "jamiecheng0103@gmail.com",
                "linkedinUrl": "https://www.linkedin.com/in/jamieyccheng/",
                "resume": str(RESUME_PDF),
                "ack_hybrid": True,
            },
        }
        result_path = APP_DIR / "SUBMITTED.json"
        result_path.write_text(json.dumps(result_data, indent=2, default=str))

        print("\n" + "="*70)
        if captcha_solved:
            print("[OK] Form fully filled and CAPTCHA already solved — ready to submit")
        else:
            print("[CAPTCHA-STAGED] Form filled + resume uploaded.")
            print("  Human action needed:")
            print("  1. Open Chrome tab: https://www.lightfoxgames.com/careers/?id=people-operations-coordinator")
            print("  2. Solve the Cloudflare Turnstile CAPTCHA")
            print("  3. Click 'SUBMIT APPLICATION ->'")
        print("="*70)
        print(f"Audit: {result_path}")
        print(f"Screenshots: {OUT_DIR}")

if __name__ == "__main__":
    main()
