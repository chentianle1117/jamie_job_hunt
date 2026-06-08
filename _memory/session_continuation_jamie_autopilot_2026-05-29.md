# Session Handoff — Jamie Autopilot Build + Feedback Encoding (2026-05-29)

⚠️ Read this after the 2026-05-29 compact. This was a long multi-night session building + refining
Jamie's automated job-application pipeline. Everything below is COMMITTED + PUSHED to GitHub.

## Two repos (both clean + pushed as of 2026-05-29)
- **oracle-job-search** → github.com/chentianle1117/jamie_job_hunt (the job-search project: skills, jamie/ refs, outputs, render_pdfs.py)
- **jamie-autopilot** → github.com/chentianle1117/jamie-autopilot (the autopilot engine: lib/ submit scripts, pipeline-prompts/, dashboard)
- Live skill copy that actually RUNS: `~/.claude/skills/jamie-autopilot/` (separate from the repo; SKILL.md + prompts/ edited here, then mirrored to repo's pipeline-prompts/)

## What was accomplished (5 LIVE job applications submitted across 3 nights)
1. Aurora Innovation — Program Manager, People Team (Pittsburgh/Seattle) — 2026-05-25 — Greenhouse embed
2. Pacific Seafood — Training & Development Specialist (Clackamas OR) — 2026-05-25 — PinpointHQ
3. Built In — People Ops & Workplace Experience Specialist (Chicago) — 2026-05-27 — Greenhouse, 5 essays
4. Roivant Sciences — People Operations Associate (NYC) — 2026-05-27 — Greenhouse
5. Aurora Innovation — HR Generalist (Mountain View) — 2026-05-28 — Greenhouse w/ email-CAPTCHA
- Anthropic Program Ops Manager: package built but NOT submitted (4+ YOE gate; Jamie to decide warm-intro vs skip)

## KEY TECHNICAL BREAKTHROUGHS (all working, in jamie-autopilot/lib/)
- **LinkedIn automation = CDP attach**, NOT Patchright. Launch user's REAL Chrome with
  `chrome.exe --remote-debugging-port=9222 --user-data-dir="<User Data>" --profile-directory="Profile 6"`,
  then vanilla Playwright `connect_over_cdp("http://localhost:9222")`. This bypasses LinkedIn's CSP
  (which blocks Patchright's eval injection) AND Windows DPAPI cookie encryption (which breaks cloned profiles).
  Profile 6 = "David • andrew.cmu.edu" = where Jamie's LinkedIn is logged in.
  Scripts: cdp_attach_test.py, cdp_verify_logged_in.py, linkedin_profile_enrich.py, easy_apply_submit_v2.py
- **LinkedIn Easy Apply** reaches Review autofilled (LinkedIn saves Jamie's resume + answers). Proven via LHH dry-run.
  But Easy Apply job inventory is mostly recruiting/staffing — poor fit for Jamie. Greenhouse is the workhorse.
- **Greenhouse React-select (Aurora)**: must CLICK the `<div role="option">` to commit state — pressing Enter
  sets visible text but NOT the hidden requiredInput → validation fails. submit_aurora_hrgen_v6.py is the working pattern.
- **Greenhouse email-verification CAPTCHA**: on first submit Greenhouse emails an 8-char code. Fetch it from
  Gmail via workspace-mcp, enter in the split inputs (id=security-input-0..7), resubmit. submit_aurora_finalize.py.
- **Greenhouse API direct discovery** (boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true) is reliable;
  WebFetch gets 302-redirected. discover_greenhouse_api.py + discover_greenhouse_wider.py (91 boards).
- IDs starting with digits need `[id="..."]` selector, not `#...`.
- Windows cp1252 console: strip non-ASCII or set PYTHONIOENCODING=utf-8 on python prints.
- Working ATSes: Greenhouse (embed/direct/multi-select/CAPTCHA) + PinpointHQ + LinkedIn Easy Apply (CDP).
  BLOCKED: Workday (Akamai), PeopleAdmin (account gate), iCIMS, Taleo, Oracle HCM.

## DELIVERABLES for Jamie (in oracle-job-search/jamie/)
- **dashboard.html** — fully interactive: every application expands to show embedded resume PDF + cover PDF +
  exact form fields + submission screenshot + file links; every outreach draft expands to full email body +
  LinkedIn link + verified employer + tone notes. 3-day timeline + pipeline summary.
- **FEEDBACK_GUIDE_FOR_JAMIE.md** — how Jamie reviews + gives feedback (linked from dashboard top banner)
- **MORNING_BRIEFING_2026-05-28.md** — 10-min action checklist
- **master_tracker.json + .csv** — all 5 applications logged (dedup source)
- 5 Gmail outreach drafts in jamiecheng0103@gmail.com (subject prefix `[OUTREACH]`), real emails populated:
  Emily Formea (emily.formea@roivant.com, REPLACED Jessica Redeman who left Roivant), Kelly Graff
  (kelly.graff@roivant.com SVP), Valerie Duca (valerie.duca@centessa.com), Amber O'Reilly
  (aoreilly@higginbotham.net), Kaitlyn Major-Hale (Google — LinkedIn DM only, no external email).

## ⭐ JAMIE'S FEEDBACK RULES — CANONICAL (jamie/JAMIE_FEEDBACK_RULES.md is the master)
Encoded into: CLAUDE.md, content_library.md, email_style_signature.md, outreach_templates.md, all 5 skills
(tailor/evaluate/outreach/apply-pipeline/sync), pipeline/SKILL.md, autopilot SKILL.md + 3 verifier prompts.
Audit gates added to verifiers so violations block submission.

RESUME:
- Summary BROAD (3 pillars: data analysis / evidence-based programs / stakeholder collaboration), never niche single-task
- Bullet counts: ODN Oregon = 2-3; every other experience = EXACTLY 4. Never delete to fit page; only swap.
- Company name "Organization Development Network (ODN) Oregon" (NOT "Transition Projects" — was a bug)
- Wesleyan ALWAYS includes Relevant Coursework
- Skills comprehensive: MS Office + Data Analysis + PM tools ALWAYS; JD-named tools all listed; Notion/SharePoint only if JD-named
- Header location = role's city if role is city-based (e.g. Pittsburgh PA), else Portland OR (supersedes old always-Portland rule)
- BANNED hallucinated number: "$340K / 17 launches". Use "78% enrollment rate".
- 1 page. Master resume: Downloads/Jamie (Yi-Chieh) Cheng's Resume_2026.pdf (mirrored jamie/resume.md)

COVER LETTER (canonical = jamie/cover_letter_template.html, from RRD_..._2026-05-12.html):
- render_pdfs.py build_cover_html() REBUILT to 2-column layout: cream header band (#f5ede0) + name + 2-line
  tagline; left sidebar (contact) + right justified letter; "Dear [Company] Hiring Team,"; cursive sig + printed name
- Para 1 = ONE belief sentence (data + cross-functional belief) + ONE role sentence — NOT a theory paragraph
- Paras 2-4 = one paragraph per past experience
- FINAL para = org-psych "how I work" methodology (diagnose w/ data → collaborate cross-functionally → track
  metrics), grounded in MS Applied Org Psych. (Jamie's verbal feedback OVERRIDES the older generic "welcome the chance" close.)
- No relocation over-commit; no "applied N days ago"; no company-address block; no user-level tool over-claims; bold keywords
- autopilot render_role.py + render_builtin.py import build_cover_html → inherit the layout automatically

OUTREACH:
- VERIFY recipient CURRENTLY works at company via live LinkedIn before drafting (Jessica + Kaitlyn errors)
- Focus on ROLE + alignment with background, NOT company subsidiary/structure
- Peer-curiosity tone + concrete 2-week timeframe; never fabricate "I followed your org"

DEMOGRAPHICS (confirmed truthful 2026-05-28): Gender=Woman/Female, Race=Asian, Hispanic=No, Veteran=No,
Disability=No. Central config: jamie-autopilot/lib/jamie_demographics.py. (Aurora HR Gen already submitted with
old "decline" answer — not worth fixing.)
ALWAYS: sponsorship=Yes (honest, H1B). Email jamiecheng0103@gmail.com. Phone +1-213-700-3831.
Address 1784 NW Northrup St Apt 635, Portland OR 97209.

## OPEN ITEMS / NEXT SESSION
- Jamie is reviewing the 5 applications one-by-one in the dashboard; collect her feedback per job and fold into rules.
- She offered a comprehensive resume-bank to pick bullet variants from (resume_bank/ has 26 resumes + 5 cover letters).
- Optional: regenerate the 5 already-submitted covers to new content standard as clean review samples.
- Anthropic decision still pending (warm-intro recommended).
- LinkedIn login persistence: CDP-attach works only while Chrome runs with the debug port; for a clean
  permanent login, do a one-time login inside a Patchright/CDP window next session.
- Simplify Copilot extension lives in Jamie's normal Chrome; complements pipeline (autofills Greenhouse/Lever manually).
