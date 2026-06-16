# Builder Spec — Round 2 (2026-06-15) — Jamie Cheng tailored package

You are building ONE tailored application package for Jamie Cheng. Follow this spec EXACTLY. These are hard invariants from Jamie's own feedback — violating any is a quality-degradation failure.

## Files to produce (in the role folder)
`oracle-job-search/outputs/2026-06-15-fleet/applications/<slug>/`
1. `resume.json` — clone the base schema below, tailor per role-type recipe
2. `cover_letter.md` — plain prose (see format)
3. `job.json` — metadata (see schema)
4. `JD.txt` — the full JD text you were given

## Base resume.json to CLONE
Read `oracle-job-search/outputs/2026-06-13-deep/applications/chainalysis_people_programs_lead/resume.json`. Copy it verbatim, then change ONLY:
- `meta.company`, `meta.role`, `meta.date` = "2026-06-15"
- `summary` — keep the BROAD 3-pillar structure; swap ONLY the role-identity noun (see recipe)
- bullet `{kw|text}` markup may be re-pointed to match JD keywords, but keep counts: InGenius=4, ODN=2, NextGen=4, Vestas=4, Kronos=4
- `skills` — JD-gate the tools (add LMS Canvas/Moodle for L&D; ADP/Workday for HRIS-named roles; etc.)
- `header.location` — set per role (Portland/Open to Remote, or the role's city if onsite)

## HARD INVARIANTS (never violate)
- **RULE 0 — NO FABRICATION.** Every claim traces to the base resume / content_library. Do not invent metrics, titles, or experience.
- **Canonical numbers ONLY:** 75% (onboarding time reduction), 78% (enrollment rate — default; "client conversion rate" only for L&D/consulting/sales framing), 2,000+ (employee data points), $362K (leave costs), 566% (Kronos applications), 600+ (training participants), 300+ (leave cases), 230+ students / 80+ applicants (Kronos), 20+ programs, 10+ vendors, 25+ stakeholders.
- **BANNED number:** NEVER "$340K" or "17 launches" in any form.
- **ODN = "Consultant, Organization & Talent Development"** at "Organization Development Network (ODN) Oregon". EXACTLY 2 bullets, across the TWO separate projects (Project 1 = absenteeism/$362K leave-cost diagnosis; Project 2 = NGO leadership decision-making). NEVER frame ODN as ERG / community-building / network-growth — it is OD diagnostic consulting.
- **Summary 3 pillars (keep all 3, identical wording):** (1) solving problems through data analysis, (2) developing programs grounded in evidence, (3) collaborating with stakeholders for sustainable impact. Only the role-identity noun changes.
- **Sponsorship truth:** if a cover letter or form asks, Jamie requires sponsorship = Yes (truthfully). Never claim she doesn't need it.
- **InGenius Prep is active litigation — NEVER list it as a reference or contact. It is fine as a current employer/experience on the resume.**
- Drop "97% extrovert!" ONLY for traditional consulting firms (not needed here unless the role is a Big-4/MBB consultancy).

## Role-identity noun by function (swap into summary)
- People Ops / HR generalist / lifecycle → "People Operations"
- L&D / Training / Learning Experience Design → "Learning & Development"
- OD / Employee Experience / Talent → "Organization & Talent Development"
- Program / Talent Programs → "Program Management"

## cover_letter.md format (PLAIN PROSE — no `---` dividers, no markdown headers)
```
Dear <Company> <Team or Hiring Manager>,

<Para 1: recognition of the role + genuine company/mission hook — specific to THIS JD, truthful>

<Para 2: strongest matching experience with canonical numbers — InGenius + ODN/NextGen as fits>

<Para 3: a second proof point or a candid bridge if there's a gap (disclose honestly, don't over-claim)>

<Para 4: why THIS company specifically + what she'd bring>

Warm regards,
Jamie (Yi-Chieh) Cheng
```
Keep it to ~4 paragraphs that render on ONE page. Substance over length. No `{kw|...}` markup in the cover (that's resume-only). No Drive links, no HTML, clean plain text.

## job.json schema
```json
{"company":"...","role":"...","li_url":"https://www.linkedin.com/jobs/view/<id>","job_id":"<id>","location":"...","ats":"workday|greenhouse|oracle|workable|rippling|paycor|smartrecruiters|icims","source":"linkedin_primary_2026-06-15_round2","jd_full_text":"<full JD>","hard_stop":"None","fit":"GO|STRETCH — <one line>","apply_type":"external","account_required":"True|False","form_url":"<canonical apply URL>","external_url":"<canonical apply URL>"}
```

## After writing the 3 files
Render: `cd oracle-job-search && PYTHONUTF8=1 python render_one.py outputs/2026-06-15-fleet/applications <slug>`
It must print `[OK] <slug>: resume=1p cover=1p`. If it prints BLOCKER, fix the issue (cover needs ≥3 body paragraphs after the salutation; resume autofits to 1 page) and re-render.

Return ONLY a JSON object as your final message:
{"slug":"...","built":true/false,"resume_pages":1,"cover_pages":1,"render_ok":true/false,"notes":"any caveat, e.g. gap disclosed in cover","fit_summary":"one line on why this fits Jamie"}
