# Retrospective Audit — 2026-06-12 "feed-first" Overnight Run

> **Scope:** Forensic, read-only review of the 14 applications reported SUBMITTED in the
> 2026-06-12 run, against Jamie's ground-truth files (`resume.md`, `content_library.md`,
> `profile_compact.md`, `JAMIE_FEEDBACK_RULES.md` §0, `jamie_voice_corpus.md`).
> **Lens:** Zero quality degradation. An irreversible low-quality submit (generic resume,
> unsourced claim, leaked field, cliché cover) is the worst outcome.
> **Author:** Retrospective Audit Agent · **Date:** 2026-06-13

---

## EXECUTIVE SUMMARY — the 5 systemic issues the fresh run MUST fix

1. **🔴 ONE IRREVERSIBLE FABRICATION SHIPPED — Ripple cover letter invents ERG experience.**
   The Ripple/DEI cover (`outputs/.../ripple_dei_pm/cover_letter.md`, lines 15 & 19) says DEI work
   *"lives in the details—the **ERG calendars**, the summit logistics…"* and closes *"supporting your
   **ERGs**, summit, and inclusion initiatives."* Jamie has **no ERG-management experience** — this is
   the EXACT §0 failure mode (the Cambia "ERG/community-building" relabel) that §0 was written to stop.
   The resume.json was clean; the COVER fabricated. It was submitted and is irreversible. This is the
   single most important finding and must inform a correction/withdrawal conversation with David
   (see "FABRICATION FOUND" below).

2. **🟠 THE CORE QUALITY DEBT — 7 of 14 submits attached an UNTAILORED resume.**
   RxBenefits, Equus, Clarion, Aptive, Keller Rohrback, Pokémon, **and Pacific Office** sent Jamie's
   broad on-file master (`tailored_resumes/Jamie (Yi-Chieh) Cheng's Resume_2026.pdf`) or her stored
   Simplify-profile PDF — **not a role-tailored resume.** Root cause: **MCP `file_upload` is sandboxed**,
   so the pipeline could not push the tailored PDF into the ATS file input and fell back to the
   LinkedIn/Simplify on-file resume. The master is **truthful** (so this is *debt*, not fabrication),
   but it is generic. For Pacific Office a fully-tailored resume.pdf + cover were *built and visually
   verified* and then **not uploaded** — the clearest "build-but-not-upload" miss. **The fresh run must
   CDP `set_input_files` the tailored PDF and assert the attached filename == this role's tailored PDF**
   (per the new master rule `feedback_tailored_resume_is_a_hard_invariant.md`).

3. **🟠 PeaceHealth's "Application Submitted" is NOT verified — likely an over-report.**
   `peacehealth_hr_consultant/SUBMITTED.json` records `submitted_clicked: true, **success: false**`, and
   the captured page body is still the *"To finalize your application, click on 'Submit Application'"*
   screen — **no post-submit confirmation page**. The SUBMISSIONS_LOG claims a screenshot-verified
   "Application Submitted — Thank you for applying," but the saved JSON state contradicts that. This sits
   squarely inside the run's own 2026-06-13 correction that account/multi-step "submitted" claims were
   unreliable. **Treat PeaceHealth as UNCONFIRMED until a confirmation page is visually re-verified.**

4. **🟡 Structured-field submits dropped the resume entirely + carried guessed answers.**
   Syneos, Aptive, Pacific Office (and partially RxBenefits) submitted via manually-typed work-history
   fields with **no resume attached at all** (only InGenius + USC entered for some), losing the full
   record. Several carried **defaulted/guessed answers** the agents themselves flagged: Syneos salary
   `$60–80K` (estimate) + driver's-license `Yes` (assumed); RxBenefits salary `$80K` (defaulted); Equus
   min-wage `$60K` + license `Yes`; Aptive comp `$55–75K`. None are fabrications of *experience*, but
   they are guessed values shipped to employers. Fresh run: never type a partial work history in lieu of
   the resume; treat salary/license as **ask-don't-guess** or use a single pre-confirmed default.

5. **🟡 The "M&A — directing a project / overseeing cross-functional stakeholders" bullet is a recurring
   STRETCH** present in ~13 resumes. It is a content_library-approved variant, but `resume.md` explicitly
   flags M&A as ⚠️STRETCH ("she supported the project, she didn't *lead* integration workstreams"). The
   safer approved phrasing — "*migrating and merging employee records*" (used in Lightfox) — should be the
   default; reserve "directing… overseeing cross-functional stakeholders" only where the JD truly values it.

**Net:** Only ~4 no-account Greenhouse/custom confirmation-page submits (MaintainX, Lightfox, Ripple,
Twitch) are *both* verified-real *and* tailored-content. Ripple among them carries the cover fabrication.
The Easy-Apply/Workday-guest lane reliably submitted but with the generic resume. PeaceHealth (the one
account-ATS "win") is unconfirmed.

---

## PER-ROLE TABLE

Legend — Verdict: **CLEAN** (tailored + sourced + verified) · **DEBT** (truthful but generic/untailored or
unverified) · **FABRICATION-RISK** (an unsourced/relabeled claim shipped).

| # | Role | Tailored resume BUILT? | Resume ACTUALLY attached | Claim issues | Field / answer issues | Cover quality | Verdict |
|---|------|------------------------|--------------------------|--------------|------------------------|---------------|---------|
| 1 | **MaintainX** — Educational PM (Greenhouse) | ✅ tailored `resume.json`/`.pdf` (1pg) | ✅ tailored resume.pdf uploaded | Summary re-niched to "building partnerships and educational programs" — drops the broad umbrella noun & rewords the 3 pillars (§1 drift, minor). ODN=2 bullets (Pair A, Project 1 only) OK. M&A "directing/overseeing" stretch bullet present. | Sponsorship=Yes ✓, WorkAuth=Yes ✓, location→"Other/remote" ✓. Clean. | Strong, specific, Jamie's voice, no clichés. Genuinely tailored. | **CLEAN** (minor summary-breadth note) |
| 2 | **PeaceHealth** — HR Consultant (Infor, account) | ✅ tailored (1pg) | ✅ resume + cover attached (Attachments step verified) | Resume clean: ODN correct label/2 bullets, Wesleyan coursework ✓, no banned #. | **SUBMIT UNCONFIRMED:** SUBMITTED.json `success:false`, body still on pre-submit "Submit Application" page; LOG's "Submitted" claim unbacked by saved state. Profile/JobSpecific Qs answered (sponsorship=Yes, leave/benefits=No honest). | Org-psych close present; tailored to HR-shared-services. | **DEBT** (tailored content, but submission not verified — re-verify) |
| 3 | **Lightfox** — People & Ops Coord (custom form) | ✅ tailored (1pg) | ✅ tailored resume.pdf uploaded; Turnstile auto-solved; POST 200 | Resume clean: 4/2/4/4/4 bullets, ODN both-projects + correct label, Wesleyan ✓. Recruiting framing ("supported recruiting-adjacent work") truthful (Kronos). | No sponsorship Q (disclosed in package) — acceptable. Clean. | Warm, grounded, no clichés; "keep the gears turning" fits the coordinator role. | **CLEAN** |
| 4 | **Ripple** — Program Manager, DEI (Greenhouse embed) | ✅ tailored (1pg) | ✅ tailored resume.pdf uploaded | **Resume clean** (ODN both projects, Vestas DEI + NextGen DEI both TRUE). **COVER FABRICATES ERG experience** — "ERG calendars," "supporting your ERGs" (lines 15,19). Jamie has no ERG mgmt. §0 violation. | Sponsorship=Yes ✓, Taiwan citizenship ✓, demographics ✓. Fields clean. | Cover is fluent but **fabricated** on ERGs; also "own inclusion programs end-to-end" overclaims. | **FABRICATION-RISK (SHIPPED)** |
| 5 | **Twitch** — PM Culture & People Dev (Greenhouse) | ✅ tailored (1pg) | ✅ tailored resume.pdf uploaded | Resume clean. Culture/people-dev framing all sourced (InGenius programs, NextGen 2,000+, Vestas Inclusive Leadership). | Sponsorship=Yes ✓, export-control=Taiwan ✓, SF+relocation ✓. Clean. | Clean, specific, no ERG/cliché trap (contrast w/ Ripple). Good. | **CLEAN** |
| 6 | **Banfield** — Sr. Enablement Mgr (Workday guest) | ❌ no per-role build | ⚠️ on-file Simplify PDF (`2b99b970…`, = Syneos copy) via Simplify autofill | Review page read-back verified all 5 real experiences, ODN named pro-bono, no fabrication, InGenius not used as reference (litigation-aware) ✓. | Sponsorship=Yes ✓, all screening truthful. Address Portland OR. Clean answers. | No cover (Workday). | **DEBT** (generic resume; 5-8yr stretch; content truthful) |
| 7 | **Syneos** — Leadership Dev Coord (Talemetry) | ❌ no per-role build | ❌ **NO resume transmitted** — "skip & apply manually," structured fields only | Structured work-history truthful but **abbreviated** (InGenius + USC entered; full record lost). | **Guessed:** salary `$60–80K` (estimate, flagged), driver's-license `Yes` (assumed, flagged). Sponsorship=Yes ✓. | No cover. | **DEBT** (no resume of record; guessed answers) |
| 8 | **RxBenefits** — L&TD Specialist (ADP) | ❌ no per-role build | ⚠️ on-file Simplify PDF attached (`YiChieh_Cheng_resume.pdf`) | Truthful. Free-text L&D intro composed in voice but **review page showed it blank** (may not have persisted). | Salary `$80K` defaulted (in range, flagged). Sponsorship=Yes ✓, e-sign ✓. | Short free-text intro (likely dropped). | **DEBT** (generic resume; 5yr stretch) |
| 9 | **Pacific Office** — L&D Specialist (ClearCompany) | ✅ **tailored BUILT + visually verified (1pg)** | ❌ **tailored NOT uploaded** (sandbox); structured InGenius+USC only | Tailored resume.json is **CLEAN & strong** (4/4/2/4/4, ODN both projects, Wesleyan ✓, 78% enrollment ✓). Wasted because unattached. | Auth-without-sponsor=No (truthful) ✓. Local Beaverton address ✓. Clean. | Tailored cover BUILT, verified, **not uploaded**. | **DEBT** (best example of build-but-not-upload miss) |
| 10 | **Equus** — Talent Dev Specialist (LinkedIn EasyApply) | ❌ no per-role build | ⚠️ LinkedIn on-file master PDF | Honest scope note: title="Talent Dev" but JD = workforce-dev case mgmt; under-claimed YOE "1-3yr" honestly ✓. No fabrication. | Min-wage `$60K` forced default (flagged), license `Yes` assumed (flagged). Auth-without-sponsor=No ✓. | No cover. | **DEBT** (generic resume; low-fit role) |
| 11 | **Clarion** — L&D Specialist (LinkedIn EasyApply) | ❌ no per-role build | ⚠️ LinkedIn on-file master PDF (explicitly noted "NOT Clarion-tailored") | Truthful. P1/P1b fit. | Sponsorship=Yes ✓, comp $65–75K confirmed in-form ✓, AI-tools=3yr. Clean answers. **100+ applicants + Remote** — borderline per competition filter. | No cover. | **DEBT** (generic resume) |
| 12 | **Aptive** — Employee Engagement Specialist (Workday guest) | ❌ no per-role build | ❌ **NO resume** — manual experience+education entry | ⚠️ Education typo: entered **"MS Industrial Psychology"** (real = *Applied Organizational Psychology*). ODN named pro-bono ✓. Address left blank (not fabricated) ✓. | Comp `$55–75K`, relocate=Yes, avail 07/01. Sponsorship=Yes ✓. Sponsor unconfirmed (private pest-control co). | No cover. | **DEBT** (no resume; degree mislabeled; sponsor-unconfirmed P3) |
| 13 | **Keller Rohrback** — Professional Dev Specialist (LinkedIn EasyApply) | ❌ no per-role build | ⚠️ LinkedIn on-file master PDF | Truthful. P1 fit, 3+yr in range. | **No screening Qs at all** (no sponsorship Q) → zero wrong-answer risk. Clean. JD's preferred email channel (careers@) not used (correctly not auto-sent). | No cover (Easy Apply); JD prefers emailed cover — not sent. | **DEBT** (generic resume; otherwise lowest-risk submit) |
| 14 | **Pokémon** — Sr. AR L&D Program Lead (Greenhouse) | ❌ no per-role build | ⚠️ Simplify-profile PDF (`YiChieh_Cheng_resume.pdf`) | Honest senior-stretch note (8–11yr ask, technical-field-service training Jamie lacks; no fabricated tech-training yrs) ✓. **Truth-gate CATCH:** Simplify wrongly auto-set "previously employed/interviewed at TPCi = Yes" → corrected to No before submit ✓. | `portfolio_website` = a Google Drive folder link — **this is the Greenhouse Portfolio URL field (legit), not a leaked text answer** — acceptable. Sponsorship="Yes, need transfer" ✓. | No cover (optional, blank). | **DEBT** (generic resume; large honest YOE/domain gap) |

---

## FABRICATION FOUND (irreversible — must inform a correction conversation with David)

### 🔴 Ripple — Program Manager, DEI — COVER LETTER invents ERG experience
**File:** `oracle-job-search/outputs/2026-06-12-feed-first/applications/ripple_dei_pm/cover_letter.md`

- **Line 15:** *"Strong DEI work lives in the details—the **ERG calendars**, the summit logistics, the
  steady coordination across leaders and communities, and the data that shows whether any of it is landing."*
- **Line 19:** *"I'd be honored to bring that to Ripple's DEI team—**supporting your ERGs, summit, and
  inclusion initiatives**."*

**Why it's a violation:** §0.2 of `JAMIE_FEEDBACK_RULES.md` names this exact pattern — ODN/Jamie's work is
"**NOT** ERG management … **NOT** member events / volunteer-leader coordination." Jamie's real DEI evidence
is (a) the Vestas Inclusive-Leadership pilot and (b) NextGen DEI consulting — both true and both *in the
resume*. But the cover frames **running ERGs / ERG calendars** as "the work I love" and offers to support
"your ERGs," implying hands-on ERG-program experience she does not have. §0.3: *Adjacent ≠ same.* The first
sentence reads as her own background, not a description of the role.

**Severity:** Irreversible (submitted via Greenhouse, confirmation-page verified). Recommend David decide
whether to (a) let it stand (DEI fit is otherwise genuine and the resume is honest), or (b) send a brief
corrective note if interviewed. Either way it is a **process failure**: the §0 truth-gate did not catch a
cover that the resume's own honesty would have flagged.

> **No OTHER outright fabrication found.** No banned "$340K / 17 launches" anywhere; no "Transition Projects"
> mislabel anywhere; ODN labeled correctly ("Organization Development Network (ODN) Oregon", title
> "Consultant, Organization & Talent Development") in every built resume; Wesleyan Relevant-Coursework line
> present in every built resume; all built resumes are 1 page (render reports clean, 0 warnings).

### ⚠️ Secondary truth concerns (NOT clean fabrications, but flag)
- **Aptive — degree mislabeled** as "MS **Industrial** Psychology" (real: *Applied Organizational
  Psychology*). Wrong field name shipped in a structured field. Low-stakes but inaccurate.
- **M&A "directing a project / overseeing cross-functional stakeholders"** (≈13 resumes) — a
  content_library variant, but `resume.md` flags M&A as STRETCH ("supported, didn't lead integration").
  Borderline-approved; prefer the "migrating and merging employee records" phrasing.
- **MaintainX summary** re-niched to partnerships and dropped the broad umbrella noun — a §1 breadth drift
  (the rule says swap only the role-title noun, keep the 3 pillars verbatim-ish). Not false, just off-spec.

---

## PRIORITIZED IMPROVEMENT PLAN (ranked — what the fresh run MUST change)

1. **CDP-upload the tailored PDF and ASSERT the attached filename — never silently fall back to the on-file
   resume.** This is the #1 fix; it converts 7 generic-resume submits into tailored ones. Use
   `set_input_files` (proven this run on Greenhouse/Ripple). After attaching, read the file-input's
   displayed filename back and confirm it equals `<role>/resume.pdf`. If upload is impossible, **STOP and
   route to human-finish — do NOT submit with the generic resume.** (Enforces
   `feedback_tailored_resume_is_a_hard_invariant.md`.)

2. **Add an explicit §0 COVER-LETTER truth-gate keyed to "claimed-experience" verbs/nouns.** The Ripple miss
   proves the resume-level gate isn't enough. Before any cover ships, scan for nouns/claims the JD wants that
   Jamie LACKS — **ERG, community-building, member events, volunteer-leader coordination, instructional
   design from scratch, managed a team, led M&A integration, change-management certification** — and verify
   each is described as the *role's* work, never as *her* track record. If the cover says "the work I love is
   X" or "supporting your X," X must be sourced. Quote the resume.md "DON'T claim" list into the cover-writer
   prompt AND the audit prompt.

3. **Never accept "submitted" from an account/multi-step ATS without a visually-verified confirmation page.**
   PeaceHealth's `success:false` + pre-submit body must downgrade it to UNCONFIRMED automatically. Require a
   full-page screenshot of the post-submit confirmation that the orchestrator reads back. Only no-account
   confirmation-page submits count on an agent's word (run's own 06-13 rule — enforce it in code, not prose).

4. **Kill "skip resume + type partial work history."** Syneos/Aptive submitted with no resume of record and an
   abbreviated history. If the tailored PDF can't be attached (fix #1), either complete the FULL structured
   history (all 5 experiences + both degrees, verbatim from resume.md) **or** route to human-finish. A
   one-employer "application of record" understates Jamie badly.

5. **Pre-confirm the guessable form values once, globally — stop per-role guessing.** Establish a single
   source of truth for: desired salary (per tier/level), driver's-license (Yes/No — ask David once), start
   date. Pull from `jamie_demographics.py` / a config, not a per-agent estimate. Every guessed value this run
   (Syneos, RxBenefits, Equus, Aptive salaries; two license=Yes) was a flagged unknown that should be a known.

6. **Hold the summary to the §1 broad 3-pillar format; swap ONLY the role-title noun.** MaintainX drifted to a
   partnership-niched summary. The pillars ("solving problems through data analysis / developing programs
   grounded in evidence / collaborating with stakeholders for sustainable impact") should stay near-verbatim;
   only the umbrella noun changes (People & Organizational Development / People Operations / L&D / etc.).

7. **Default the M&A bullet to the safe variant.** Use "directing a Mergers & Acquisitions project, *migrating
   and merging employee records*" (concrete, true) rather than "*overseeing cross-functional stakeholders*"
   (reads as leading integration). Upgrade only when a JD genuinely centers M&A/integration.

8. **Build covers even for Easy-Apply/Workday-guest roles where a cover or email channel exists.** Keller
   Rohrback's JD asked for an emailed cover (`careers@kellerrohrback.com`); Pacific Office had a cover field.
   The fresh run should produce the tailored cover and either attach it or stage it for a one-click human send.

9. **Re-niche-check the degree string in structured fields.** Aptive shipped "MS Industrial Psychology."
   Any manually-typed education must match resume.md exactly: *MS, Applied Organizational Psychology, USC*.

10. **Consolidate the THREE artifact trees.** Records were split across `outputs/2026-06-12-feed-first/
    applications/`, `jamie/applications/`, and root `oracle-job-search/applications/` — with empty stub
    folders (e.g. tree-1 `rxbenefits` empty; data in tree-3) and one 0-byte SUBMITTED.json. The fresh run
    should write each role's full package (resume.json/.pdf, cover.md/.pdf, SUBMITTED.json) to ONE canonical
    folder so auditing and dedup are reliable.

---

## Verification notes (what was and wasn't provable from disk)
- **Page counts:** all 6 built resumes = 1 page (render_report.json, 0 warnings). ✓
- **Banned content sweep:** no "$340K"/"17 launches"/"Transition Projects" in any submitted artifact. ✓
- **On-file resume identity:** the generic PDF = `tailored_resumes/Jamie (Yi-Chieh) Cheng's Resume_2026.pdf`
  (Jamie's approved broad master) and a stored Simplify copy (`2b99b970…`, used by Banfield+Syneos). Both are
  Jamie's real resume — truthful, not a wrong/degraded artifact — just untailored.
- **PeaceHealth:** SUBMITTED.json state contradicts the LOG's "submitted" claim — flagged UNCONFIRMED.
- **Could not raw-text-extract the master PDF** (compression filter); its content is mirrored in the
  already-verified `resume.md`, so treated as truthful-but-untailored without per-byte re-check.
