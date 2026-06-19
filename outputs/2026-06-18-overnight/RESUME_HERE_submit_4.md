# ▶ RESUME HERE — submit the 4 gated saved-job packages (2026-06-19)

**State:** 4 packages are BUILT, all gates PASS (8 mechanical + auditor), auditor-PASS (sha-matched AUDIT_VERDICT.json), 1-page PDFs visually verified, committed + pushed. Ready to drive to live submit. The 5th (Housecall) already submitted earlier.

## The 4 to submit (in this order)
| Order | Role | Folder | ATS / mechanism | Notes |
|---|---|---|---|---|
| 1 | **Xenium HR — Employee Experience Representative** | `applications/Xenium_Employee-Experience-Representative/` | PrismHR — `https://xenium-resources2.prismhr-hire.com/job/1028123/employee-experience-representative` | LIVE 200. Has reCAPTCHA on form — if passive v3 → complete; if interactive checkbox/puzzle → fill to it, screenshot, leave for Jamie (hard stop). Own ATS, no LinkedIn hop = easiest. |
| 2 | **Nike — People Solutions Advisor I** | `applications/Nike_People-Solutions-Advisor-I/` | Workday (jobs.nike.com, Eightfold front-end) — account-creation lane | Beaverton, at-level, Nike sponsors. Create account w/ jamiecheng0103@gmail.com + shared pw (~/Downloads/job_password.txt); save new cred to jamie/account_registry.json (gitignored, never commit secret). |
| 3 | **Nike — Senior, Global Sales, L&D** | `applications/Nike_Senior-Global-Sales-LD/` | Workday R-85764 | +2yr stretch (at cap). Same Nike Workday account as #2 once created. |
| 4 | **RxBenefits — L&TD Specialist** | `applications/RxBenefits_Learning-Talent-Dev-Specialist/` | ATS unresolved (LinkedIn-gated; likely iCIMS/ADP) | Remote, +2yr at cap. Drive from LinkedIn id 4425318327 → follow the external Apply redirect to find the real ATS, then fill. |

## How to submit (gate-protected path)
1. Launch submit Chrome: `python jamie-autopilot/lib/stage_one.py <role_dir>` (it ensures the jamie_submit_profile Chrome on port 9400, runs ALL gates exit-4, then stages). OR drive directly via Patchright/CDP for account-lane ATSes.
2. The gates already pass — stage_one will let it through. For Greenhouse-style no-account, `submit_greenhouse_generic.py` pattern works; for Workday/PrismHR, drive the form + `set_input_files` the tailored resume.pdf/cover_letter.pdf.
3. **Truthful answers:** work-authorized = YES, sponsorship = YES, ~3yr exp, demographics Woman/Asian. Screenshot the review page BEFORE submit; verify; then submit.
4. After confirmation: write `SUBMITTED.json` + save `screenshots/04_after_submit.png`; verify the confirmation page (URL + body) by reading it back.
5. ONLY an interactive/physical CAPTCHA is a hard stop — fill to it, screenshot, leave the tab, mark captcha-staged.

## Quality system (already enforcing — don't rebuild)
- 8 mechanical gates + LLM auditor, all hard-blocking in `jamie-autopilot/lib/stage_one.py`. Full map: `jamie-autopilot/QUALITY_GATES.md`. Auditor spec: `jamie-autopilot/AUDITOR_AGENT_SPEC.md`.
- RULE -1 (content quality non-negotiable, formatting flexes) canonical in JAMIE_FEEDBACK_RULES.md + both CLAUDE.md.

## Open side-item (not blocking submits)
- **Gemini CLI:** binary alive (v0.35.3) but the free Code-Assist OAuth tier is dead. Fix = set `GEMINI_API_KEY` (AI Studio key) — needs David's key (don't create one autonomously). Until then, route large-context scans to a Claude sub-agent instead of Gemini.

## Debt
- Housecall Pro submitted earlier with pre-fix thinned bullets (corrected on disk, can't recall the sent version).
