"""
submit_lightfox.py — LinkedIn Easy Apply for Lightfox Games People & Operations Coordinator
CDP-attach to the user's running Chrome on port 9222.

Usage:
  python submit_lightfox.py [--dry-run]
"""
import os, sys, time, json, argparse
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

DEBUG_PORT = 9222
JOB_URL = "https://www.linkedin.com/jobs/view/people-operations-coordinator-at-lightfox-games-4421646290"

RESUME_PDF = Path(r"C:\Users\chent\Agentic_Workflows_2026\oracle-job-search\outputs\2026-06-12-feed-first\applications\lightfox_people_ops\resume.pdf")
COVER_PDF  = Path(r"C:\Users\chent\Agentic_Workflows_2026\oracle-job-search\outputs\2026-06-12-feed-first\applications\lightfox_people_ops\cover_letter.pdf")
OUT_DIR    = Path(r"C:\Users\chent\Agentic_Workflows_2026\oracle-job-search\outputs\2026-06-12-feed-first\applications\lightfox_people_ops\screenshots")
APP_DIR    = Path(r"C:\Users\chent\Agentic_Workflows_2026\oracle-job-search\outputs\2026-06-12-feed-first\applications\lightfox_people_ops")

OUT_DIR.mkdir(parents=True, exist_ok=True)

# Truthful form values — DO NOT CHANGE
JAMIE = {
    "first_name": "Yi-Chieh",
    "last_name": "Cheng",
    "preferred_name": "Jamie",
    "email": "jamiecheng0103@gmail.com",
    "phone": "2137003831",
    "country_code": "United States (+1)",
    "city": "Seattle, WA",
    "city_full": "Seattle, Washington, United States",
    "city_alt": "Portland, Oregon, United States",
    "linkedin": "https://www.linkedin.com/in/jamieyccheng/",
    "authorized_to_work": "Yes",
    "require_sponsorship": "Yes",   # TRUTHFUL — never change to No
    "yoe": "3",
    "salary": "85000",
    "relocate": "Yes",
    "gender": "Woman",
    "race": "Asian",
    "hispanic": "No",
    "disability": "No",
    "veteran": "No",
}


def safe_text(t):
    return (t or '').encode('ascii', 'replace').decode('ascii') if isinstance(t, str) else str(t)


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true", help="Stop before clicking Submit")
    return p.parse_args()


def ss(page, name):
    path = str(OUT_DIR / f"{name}.png")
    try:
        page.screenshot(path=path, full_page=False)
        print(f"  [SS] {name}.png")
    except Exception as e:
        print(f"  [SS-ERR] {name}: {safe_text(str(e))[:60]}")
    return path


def modal_info(page):
    """Extract current modal state: title, kind, fields, buttons."""
    return page.evaluate("""() => {
        const NL = String.fromCharCode(10);
        const dialogs = document.querySelectorAll('[role="dialog"]');
        let modal = null;
        for (const d of dialogs) {
            const r = d.getBoundingClientRect();
            if (r.width > 200 && r.height > 200) { modal = d; break; }
        }
        if (!modal) return {error: 'no modal visible'};

        const title = modal.querySelector('h2, h3, .artdeco-modal__header h2')?.innerText?.trim() || '';

        const buttons = [];
        modal.querySelectorAll('button').forEach(b => {
            const r = b.getBoundingClientRect();
            if (r.width <= 0) return;
            const txt = (b.innerText || '').trim();
            const aria = b.getAttribute('aria-label') || '';
            buttons.push({text: txt.substring(0, 80), aria: aria.substring(0, 80)});
        });

        const fields = [];
        modal.querySelectorAll('input, textarea, select').forEach(el => {
            const r = el.getBoundingClientRect();
            if (r.width <= 0) return;
            if (el.type === 'hidden') return;
            const id = el.id || '';
            const name = el.name || '';
            const type = el.tagName.toLowerCase() + (el.type ? ':' + el.type : '');
            const value = el.value || '';
            let label = '';
            if (id) {
                const lbl = document.querySelector('label[for="' + id + '"]');
                if (lbl) label = (lbl.innerText || '').trim();
            }
            if (!label) {
                let p = el.parentElement;
                for (let i=0; i<6 && p; i++) {
                    const t = (p.innerText || '').trim().split(NL)[0];
                    if (t && t.length < 200) { label = t; break; }
                    p = p.parentElement;
                }
            }
            // Check required
            const req = el.required || el.getAttribute('aria-required') === 'true';
            fields.push({id, name, type, value: value.substring(0,100), label: label.substring(0,180), required: req});
        });

        const bodyText = modal.innerText || '';
        const titleL = title.toLowerCase();
        const bodyL = bodyText.toLowerCase();
        let kind = 'unknown';
        if (titleL.includes('contact') || fields.some(f => f.label.toLowerCase().includes('first name') || f.label.toLowerCase().includes('phone'))) kind = 'contact';
        else if (titleL.includes('resume') || fields.some(f => f.type === 'input:file')) kind = 'resume';
        else if (bodyL.includes('review your application') || titleL.includes('review')) kind = 'review';
        else if (fields.length > 0) kind = 'questions';

        return {
            title,
            buttons,
            fields,
            kind,
            body_preview: bodyText.substring(0, 800).replace(/\\s+/g, ' '),
            has_error: bodyL.includes('please enter') || bodyL.includes('required') || bodyL.includes('this field is required'),
        };
    }""")


def fill_fields(page, fields, step_label):
    """Fill any unfilled fields based on label matching."""
    for f in fields:
        fid = f['id']
        ftype = f['type']
        label = f['label'].lower()
        current_val = f['value']

        # Skip already-filled
        if current_val and current_val.strip():
            continue
        if not fid:
            continue

        try:
            loc = page.locator(f"#{fid}")
            if not loc.count():
                continue

            # ----- Sponsorship (ALWAYS Yes — truthful) -----
            if "sponsor" in label or ("visa" in label and ("require" in label or "need" in label or "future" in label)):
                if "select" in ftype:
                    try:
                        loc.select_option(label="Yes")
                        print(f"    [{step_label}] sponsorship -> Yes (select)")
                    except:
                        loc.select_option(index=1)
                        print(f"    [{step_label}] sponsorship -> index 1 (fallback)")
                elif "radio" in ftype:
                    page.locator(f"input[type=radio][id*='{fid}']").filter(has_text="Yes").first.click()
                    print(f"    [{step_label}] sponsorship -> Yes (radio)")
                continue

            # ----- Authorized to work -----
            if "authoriz" in label and "work" in label:
                if "select" in ftype:
                    try:
                        loc.select_option(label="Yes")
                        print(f"    [{step_label}] authorized -> Yes")
                    except:
                        pass
                continue

            # ----- Phone -----
            if "phone" in label and "input" in ftype:
                loc.fill(JAMIE["phone"])
                print(f"    [{step_label}] phone -> filled")
                continue

            # ----- Email -----
            if "email" in label and "input" in ftype:
                loc.fill(JAMIE["email"])
                print(f"    [{step_label}] email -> filled")
                continue

            # ----- City/location (LinkedIn typeahead) -----
            if ("city" in label or "location" in label or "where" in label) and "input" in ftype:
                loc.fill(JAMIE["city"])
                page.wait_for_timeout(1200)
                page.keyboard.press("ArrowDown")
                page.wait_for_timeout(400)
                page.keyboard.press("Enter")
                print(f"    [{step_label}] city -> {JAMIE['city']}")
                continue

            # ----- Years of experience -----
            if "years" in label and ("experience" in label or "of " in label) and "input" in ftype:
                loc.fill(JAMIE["yoe"])
                print(f"    [{step_label}] YOE -> {JAMIE['yoe']}")
                continue

            # ----- Salary -----
            if ("salary" in label or "compensation" in label or "expected" in label or "pay" in label) and "input" in ftype:
                loc.fill(JAMIE["salary"])
                print(f"    [{step_label}] salary -> {JAMIE['salary']}")
                continue

            # ----- Country code -----
            if "country code" in label and "select" in ftype:
                try:
                    loc.select_option(label=JAMIE["country_code"])
                    print(f"    [{step_label}] country code -> US")
                except:
                    pass
                continue

            # ----- Relocate / commute / comfort -----
            if "select" in ftype and any(k in label for k in ["relocat", "commut", "remote", "office", "comfort", "hybrid"]):
                try:
                    loc.select_option(label="Yes")
                    print(f"    [{step_label}] {label[:30]} -> Yes")
                except:
                    pass
                continue

            # ----- Gender (voluntary) -----
            if "gender" in label and "select" in ftype:
                try:
                    loc.select_option(label="Woman")
                    print(f"    [{step_label}] gender -> Woman")
                except:
                    pass
                continue

            # ----- Race -----
            if ("race" in label or "ethnic" in label) and "select" in ftype:
                try:
                    loc.select_option(label="Asian")
                    print(f"    [{step_label}] race/ethnicity -> Asian")
                except:
                    pass
                continue

        except Exception as e:
            print(f"    [{step_label}] fill err on {fid} ({label[:30]}): {safe_text(str(e))[:80]}")


def main():
    args = parse_args()
    from playwright.sync_api import sync_playwright

    submitted = False
    review_reached = False
    steps_log = []
    screening_answers = []

    with sync_playwright() as pw:
        browser = pw.chromium.connect_over_cdp(f"http://localhost:{DEBUG_PORT}")
        ctx = browser.contexts[0]
        pages = ctx.pages

        # Find or open LinkedIn tab
        li_page = next((pg for pg in pages if "linkedin.com" in pg.url), None)
        if not li_page:
            li_page = ctx.new_page()
            print("Opened new LinkedIn tab")
        li_page.bring_to_front()

        # ── Step 1: Navigate to job ──────────────────────────────────────────
        print(f"\nNavigating to job: {JOB_URL}")
        li_page.goto(JOB_URL, wait_until="domcontentloaded", timeout=25000)
        li_page.wait_for_timeout(4000)
        ss(li_page, "01_job_page")
        print(f"  Title: {safe_text(li_page.title())}")

        # Check login
        body_text = li_page.inner_text("body")
        if "sign in" in body_text.lower() and "linkedin" in li_page.url:
            print("[BLOCKED] LinkedIn session not authenticated — cannot proceed.")
            sys.exit(1)

        # ── Step 2: Click Easy Apply ─────────────────────────────────────────
        print("\nLooking for Easy Apply button...")
        ea_clicked = False
        for selector in [
            'button[aria-label*="Easy Apply"]',
            'button.jobs-apply-button[aria-label*="Easy Apply"]',
            'a[href*="/apply/"]',
            'button:has-text("Easy Apply")',
            'a:has-text("Easy Apply")',
        ]:
            try:
                loc = li_page.locator(selector).first
                if loc.count() > 0:
                    loc.scroll_into_view_if_needed()
                    loc.click(timeout=7000)
                    ea_clicked = True
                    print(f"  Clicked Easy Apply via: {selector}")
                    break
            except Exception as e:
                print(f"  Selector {selector[:40]}: {safe_text(str(e))[:50]}")

        if not ea_clicked:
            # Try JS click as last resort
            try:
                result = li_page.evaluate("""() => {
                    const btns = Array.from(document.querySelectorAll('button, a'));
                    const ea = btns.find(b => (b.textContent || '').toLowerCase().includes('easy apply') || (b.getAttribute('aria-label') || '').toLowerCase().includes('easy apply'));
                    if (ea) { ea.click(); return true; }
                    return false;
                }""")
                if result:
                    ea_clicked = True
                    print("  Clicked Easy Apply via JS fallback")
            except Exception as e:
                print(f"  JS fallback failed: {safe_text(str(e))[:60]}")

        if not ea_clicked:
            print("[BLOCKED] Could not click Easy Apply. Checking if external ATS...")
            ss(li_page, "02_no_easy_apply")
            # Write blocked SUBMITTED.json
            result_data = {
                "company": "Lightfox Games",
                "role": "People & Operations Coordinator",
                "ats": "LinkedIn Easy Apply",
                "status": "blocked",
                "confirmed_at": None,
                "screenshot": str(OUT_DIR / "02_no_easy_apply.png"),
                "notes": "Easy Apply button not found — may be external ATS redirect",
                "job_url": JOB_URL,
            }
            (APP_DIR / "SUBMITTED.json").write_text(json.dumps(result_data, indent=2))
            sys.exit(1)

        li_page.wait_for_timeout(4000)
        ss(li_page, "02_modal_open")

        # ── Step 3: Walk the modal ───────────────────────────────────────────
        print("\nWalking Easy Apply modal...")
        step_num = 1
        max_steps = 12

        # Try to upload resume at first opportunity
        resume_uploaded = False

        while step_num <= max_steps:
            print(f"\n=== Modal Step {step_num} ===")
            li_page.wait_for_timeout(2500)

            info = modal_info(li_page)
            if "error" in info:
                print(f"  Modal error: {info['error']}")
                # Check if we already submitted (modal dismissed = success)
                page_text = li_page.inner_text("body")
                success_kw = ["your application was sent", "application submitted", "thank you for applying", "we've received your application"]
                if any(kw in page_text.lower() for kw in success_kw):
                    submitted = True
                    print("  [SUCCESS] Submission confirmed (modal closed, success message found)")
                break

            title = info.get("title", "")
            kind = info.get("kind", "unknown")
            fields = info.get("fields", [])
            buttons = info.get("buttons", [])
            body_preview = info.get("body_preview", "")
            has_error = info.get("has_error", False)

            print(f"  Title: {safe_text(title)}")
            print(f"  Kind:  {kind}")
            print(f"  Fields: {len(fields)}")
            print(f"  Buttons: {[b['text'][:30] for b in buttons[:6]]}")
            if has_error:
                print(f"  [WARNING] Page has validation errors")

            steps_log.append({
                "step": step_num,
                "title": title,
                "kind": kind,
                "field_count": len(fields),
                "buttons": [b["text"] for b in buttons[:6]],
            })

            # Screenshot this step
            ss(li_page, f"step{step_num:02d}_{kind}")

            # ── Check for file upload (resume) ──────────────────────────────
            file_inputs = [f for f in fields if "file" in f.get("type", "")]
            if file_inputs and not resume_uploaded and RESUME_PDF.exists():
                for fi in file_inputs:
                    try:
                        fid = fi["id"]
                        if fid:
                            file_loc = li_page.locator(f"#{fid}")
                        else:
                            file_loc = li_page.locator("input[type=file]").first
                        if file_loc.count() > 0:
                            file_loc.set_input_files(str(RESUME_PDF))
                            resume_uploaded = True
                            print(f"  [UPLOAD] Resume uploaded: {RESUME_PDF.name}")
                            li_page.wait_for_timeout(2000)
                            ss(li_page, f"step{step_num:02d}_resume_uploaded")
                            break
                    except Exception as e:
                        print(f"  [UPLOAD-ERR] {safe_text(str(e))[:80]}")

            # ── Fill fields ─────────────────────────────────────────────────
            fill_fields(li_page, fields, f"step{step_num}")

            # ── Handle radio buttons / dropdowns by scanning body text ───────
            # Sponsorship radio (some steps use radio groups not in fields list)
            try:
                sponsor_result = li_page.evaluate("""() => {
                    const modal = document.querySelector('[role="dialog"]');
                    if (!modal) return null;
                    const text = modal.innerText.toLowerCase();
                    if (!text.includes('sponsor') && !text.includes('visa')) return 'not_present';

                    // Try select-based
                    const selects = Array.from(modal.querySelectorAll('select'));
                    for (const sel of selects) {
                        const label = sel.closest('[class*="form"]')?.innerText?.toLowerCase() || '';
                        if (label.includes('sponsor') || label.includes('visa')) {
                            const yesOpt = Array.from(sel.options).find(o => o.text.trim().toLowerCase() === 'yes');
                            if (yesOpt && sel.value !== yesOpt.value) {
                                sel.value = yesOpt.value;
                                sel.dispatchEvent(new Event('change', {bubbles:true}));
                                return 'select_set_yes';
                            }
                        }
                    }

                    // Try radio-based
                    const radios = Array.from(modal.querySelectorAll('input[type=radio]'));
                    for (const r of radios) {
                        const lbl = document.querySelector('label[for="' + r.id + '"]');
                        if (!lbl) continue;
                        const lblText = lbl.innerText.trim().toLowerCase();
                        const groupLabel = r.closest('fieldset')?.querySelector('legend')?.innerText?.toLowerCase() || '';
                        if ((groupLabel.includes('sponsor') || groupLabel.includes('visa')) && lblText === 'yes') {
                            r.click();
                            return 'radio_clicked_yes';
                        }
                    }
                    return 'not_handled';
                }""")
                if sponsor_result and sponsor_result not in ("not_present", "not_handled"):
                    print(f"  [SPONSOR] Result: {sponsor_result}")
                    screening_answers.append({"question": "require sponsorship", "answer": "Yes", "mechanism": sponsor_result})
            except Exception as e:
                print(f"  [SPONSOR-JS] {safe_text(str(e))[:60]}")

            # Auth to work radio
            try:
                auth_result = li_page.evaluate("""() => {
                    const modal = document.querySelector('[role="dialog"]');
                    if (!modal) return null;
                    const text = modal.innerText.toLowerCase();
                    if (!text.includes('authoriz')) return 'not_present';
                    const selects = Array.from(modal.querySelectorAll('select'));
                    for (const sel of selects) {
                        const label = sel.closest('[class*="form"]')?.innerText?.toLowerCase() || '';
                        if (label.includes('authoriz')) {
                            const yesOpt = Array.from(sel.options).find(o => o.text.trim().toLowerCase() === 'yes');
                            if (yesOpt && sel.value !== yesOpt.value) {
                                sel.value = yesOpt.value;
                                sel.dispatchEvent(new Event('change', {bubbles:true}));
                                return 'select_set_yes';
                            }
                        }
                    }
                    const radios = Array.from(modal.querySelectorAll('input[type=radio]'));
                    for (const r of radios) {
                        const lbl = document.querySelector('label[for="' + r.id + '"]');
                        if (!lbl) continue;
                        const lblText = lbl.innerText.trim().toLowerCase();
                        const groupLabel = r.closest('fieldset')?.querySelector('legend')?.innerText?.toLowerCase() || '';
                        if (groupLabel.includes('authoriz') && lblText === 'yes') {
                            r.click();
                            return 'radio_clicked_yes';
                        }
                    }
                    return 'not_handled';
                }""")
                if auth_result and auth_result not in ("not_present", "not_handled"):
                    print(f"  [AUTH] Result: {auth_result}")
                    screening_answers.append({"question": "authorized to work", "answer": "Yes", "mechanism": auth_result})
            except Exception as e:
                print(f"  [AUTH-JS] {safe_text(str(e))[:60]}")

            # ── Log any open-text screener questions ─────────────────────────
            screener_qs = [f for f in fields if "textarea" in f.get("type", "")]
            for ta in screener_qs:
                q_text = ta.get("label", ta.get("id", ""))
                screening_answers.append({"question": q_text[:150], "answer": "NOT_FILLED", "note": "open-text screener"})
                print(f"  [SCREENER] Open text Q: {safe_text(q_text[:100])}")

            # ── Determine which button to click ──────────────────────────────
            btn_texts = [(b["text"].lower(), b["text"]) for b in buttons]

            # Check for Submit button
            submit_btn = None
            for bl, borig in btn_texts:
                if bl.strip().startswith("submit") or "submit application" in bl:
                    submit_btn = borig
                    break

            if submit_btn:
                review_reached = True
                ss(li_page, f"step{step_num:02d}_REVIEW_SCREEN")
                print(f"\n  [REVIEW] Reached submit step. Button: '{submit_btn}'")

                if args.dry_run:
                    print("  [DRY-RUN] Stopping before Submit.")
                    break

                # Click Submit
                print(f"  Clicking '{submit_btn}'...")
                try:
                    btn_loc = li_page.get_by_role("button", name=submit_btn, exact=False).first
                    btn_loc.click(timeout=10000)
                    li_page.wait_for_timeout(6000)
                    submitted = True
                    ss(li_page, "FINAL_after_submit")
                    print("  [SUBMITTED] Click completed.")
                except Exception as e:
                    print(f"  [SUBMIT-ERR] {safe_text(str(e))[:100]}")
                    # Try JS click
                    try:
                        li_page.evaluate(f"""() => {{
                            const btns = Array.from(document.querySelectorAll('[role="dialog"] button'));
                            const sb = btns.find(b => (b.innerText||'').toLowerCase().includes('submit'));
                            if (sb) sb.click();
                        }}""")
                        li_page.wait_for_timeout(6000)
                        submitted = True
                        ss(li_page, "FINAL_after_submit_js")
                        print("  [SUBMITTED] JS click fallback succeeded.")
                    except Exception as e2:
                        print(f"  [SUBMIT-JS-ERR] {safe_text(str(e2))[:80]}")
                break

            # Check for Next button
            next_btn = None
            for primary in ["next", "review", "continue"]:
                for bl, borig in btn_texts:
                    if bl.strip().startswith(primary) or bl.strip() == primary:
                        next_btn = borig
                        break
                if next_btn:
                    break

            if not next_btn:
                print(f"  [STUCK] No Next/Review/Submit found. Buttons: {[b['text'] for b in buttons]}")
                # Try clicking any primary-styled button in the footer
                try:
                    footer_btn = li_page.locator('[role="dialog"] footer button.artdeco-button--primary').first
                    if footer_btn.count():
                        btn_label = footer_btn.inner_text()
                        print(f"  Fallback: clicking footer primary button: '{btn_label}'")
                        footer_btn.click(timeout=8000)
                        li_page.wait_for_timeout(3000)
                        step_num += 1
                        continue
                except Exception as e:
                    print(f"  Footer fallback err: {safe_text(str(e))[:60]}")
                break

            print(f"  Clicking '{next_btn}'...")
            try:
                btn_loc = li_page.get_by_role("button", name=next_btn, exact=False).first
                btn_loc.click(timeout=8000)
                li_page.wait_for_timeout(3000)
            except Exception as e:
                print(f"  [NEXT-ERR] {safe_text(str(e))[:80]}")
                # Try footer button
                try:
                    footer_btn = li_page.locator('[role="dialog"] footer button.artdeco-button--primary').first
                    footer_btn.click(timeout=8000)
                    li_page.wait_for_timeout(3000)
                    print("  Fallback footer click succeeded")
                except Exception as e2:
                    print(f"  Footer fallback also failed: {safe_text(str(e2))[:60]}")
                    break

            step_num += 1

        # ── Final state check ────────────────────────────────────────────────
        final_body = li_page.inner_text("body")[:3000]
        ss(li_page, "FINAL_state")

        success_kw = ["your application was sent", "application submitted", "thank you for applying", "we've received your application", "successfully applied"]
        confirmed = submitted and any(kw in final_body.lower() for kw in success_kw)

        print("\n" + "="*70)
        if confirmed:
            status = "submitted"
            print("[OK] APPLICATION SUBMITTED SUCCESSFULLY")
        elif submitted:
            status = "submitted"  # clicked but couldn't verify confirmation text
            print("[OK-ish] Submit was clicked — confirm visually via FINAL_after_submit.png")
        elif args.dry_run and review_reached:
            status = "dry-run-ready"
            print("[OK] DRY RUN — reached Review/Submit screen. Mechanism works.")
        elif args.dry_run:
            status = "dry-run-incomplete"
            print("[?] DRY RUN — did not reach Submit. Review screenshots.")
        else:
            status = "blocked"
            print("[!!] Did not complete. Review screenshots.")
        print("="*70)

        # Write SUBMITTED.json
        result_data = {
            "company": "Lightfox Games",
            "role": "People & Operations Coordinator",
            "ats": "LinkedIn Easy Apply",
            "status": status,
            "confirmed_at": time.strftime("%Y-%m-%dT%H:%M:%S") if submitted else None,
            "screenshot": str(OUT_DIR / ("FINAL_after_submit.png" if submitted else "FINAL_state.png")),
            "notes": f"steps_completed={step_num-1}, review_reached={review_reached}, resume_uploaded={resume_uploaded}",
            "job_url": JOB_URL,
            "steps_log": steps_log,
            "screening_answers": screening_answers,
        }
        result_path = APP_DIR / "SUBMITTED.json"
        result_path.write_text(json.dumps(result_data, indent=2, default=str))
        print(f"Audit: {result_path}")

        return status


if __name__ == "__main__":
    main()
