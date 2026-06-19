# Saved-Jobs Build/Submit Status (2026-06-19)

Driving the 5 in-bounds NOT-yet-applied saved roles to submit/stage.

| # | Role | ATS | Build | Gates | Render(1pg) | Visual | Submit |
|---|---|---|---|---|---|---|---|
| 1 | **Housecall Pro — Sr Associate, Training** | Greenhouse (no-acct) | ✅ done | ✅ resume+cover+truth PASS | ✅ 1p+1p (autofit 0.97) | ✅ both verified clean | ✅ **SUBMITTED + CONFIRMED** ("Thank you for applying!" page, screenshot-verified, tailored PDFs attached, sponsorship=YES) |
| 2 | Nike — People Solutions Advisor I | Workday (account) | ⏳ | | | | |
| 3 | Xenium HR — EE Representative | PrismHR (job/1028123) | ⏳ | | | | |
| 4 | Nike — Sr Global Sales L&D (5+yr, +2 cap) | Workday (account) | ⏳ | | | | |
| 5 | RxBenefits — L&TD Specialist (5yr, +2 cap) | LinkedIn-gated ATS | ⏳ | | | | |

## Housecall package facts (truth-checked)
- YOE asked: **2+ yrs** → Jamie's ~3yr clears cleanly (no stretch).
- Fit: facilitation + development of training + analytical process-improvement = her InGenius (600+ webinars, 78%, 75%, 70+) + NextGen L&D + ODN data work. RULE-0 clean, no invention.
- Sponsorship: Greenhouse form asks it ("case by case — will you require sponsorship?") → answer **YES** truthfully. Work-auth → YES.
- Resume re-angled summary noun to "Learning & Development", lifted training/facilitation bullet to top of InGenius. All metrics + bullet counts (ODN=3, rest=4) preserved.

## Renderer note (fixed)
jamie-autopilot `lib/render_role.py` does a SINGLE fixed-size render with NO autofit → reports 2 pages.
The autofit loop lives in `oracle-job-search/render_pdfs.py` (`render_role`, scales 1.0→0.86, 1-page hard gate).
Wrapper `oracle-job-search/_render_one.py` points APPS_DIR at the run folder and renders one role with autofit.
**Use `_render_one.py` for rendering this batch.** (Both Amazon base + Housecall rendered 2pg under the lib renderer; 1pg under the oracle renderer.)
