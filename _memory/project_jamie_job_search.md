---
name: jamie-job-search-context-strategy
description: "Jamie (Yi-Chieh) Cheng's HR/People Strategy job search — sponsorship barrier, realistic strategy, and oracle pipeline support"
metadata: 
  node_type: memory
  type: project
  originSessionId: 1cc5945f-7f76-42d1-8cb4-acad5c9bc387
---

**Jamie's background:** USC Applied Organizational Psychology MS. Wants People Strategy / OD / L&D / EX roles. NOT interested in going back to traditional HR/TA operations.

**The hard constraint:** Needs H1B sponsorship. Most People Strategy / HR roles at US companies explicitly do not sponsor, especially for non-STEM mid-level roles. This is a systemic barrier, not a performance issue.

**Current state (as of 2026-03-28):**
- On FMLA leave from a toxic company (leave runs through ~June 2026)
- Has been job-searching 2-3 hrs/day for 2-3 years with minimal return
- ~30-40 applications total, very few screening calls, ~1 second-round ever
- Even roles where hiring manager liked her → no sponsorship at company policy level
- Actively considering Netherlands Orientation Year visa as primary Plan B

**Revised strategy (agreed with David):**
- Cap time-box at **1-1.5 hrs/day max** — quality over quantity, no more 2-3 hr days
- Prioritize **cap-exempt employers**: universities, nonprofits, research institutes (H1B outside the lottery cap — no April roulette)
- Filter aggressively: use MyVisaJobs to verify past sponsorship history; skip any JD with "must be authorized without future sponsorship"
- Begin surfacing **Dutch/European listings** — Amsterdam, Rotterdam companies with Recognised Sponsor status
- Treat each rejection as a system bug, not personal failure

**Oracle pipeline role:** The oracle job search agent runs daily and surfaces leads, writes cover letters, and delivers a digest. David built this to reduce Jamie's emotional load from manual searching. The networking contacts (like today's Providence + Disney HRBP research) are part of this pipeline.

**Why:** Jamie has sacrificed geographically (LA → Houston → Pittsburgh → Portland) for David's career. The job search burden is compounding mental health strain. Reducing friction and redirecting toward realistic paths (cap-exempt US + EU) is higher ROI than continued full-effort US corporate spraying.

**How to apply:** When oracle pipeline outputs come up, flag EU/NL roles as high priority. When discussing Jamie's job search, assume 1-hr/day budget and sponsorship-first filtering.

---

## UPDATE 2026-05-29 — Automated application pipeline is LIVE
- Built `/jamie-autopilot` (github.com/chentianle1117/jamie-autopilot) — auto-discovers, tailors, submits
  applications + drafts outreach. 5 live submissions done across 3 nights (Aurora x2, Pacific Seafood,
  Built In, Roivant). Auto-apply works on Greenhouse + PinpointHQ + LinkedIn Easy Apply (via CDP attach to
  user's real Chrome on port 9222 — NOT Patchright, which LinkedIn CSP blocks).
- **CANONICAL RULES doc:** `oracle-job-search/jamie/JAMIE_FEEDBACK_RULES.md` — read this before any resume/
  cover/outreach work. Encodes Jamie's detailed feedback from reviewing the first 5 applications.
  Cover template = `jamie/cover_letter_template.html` (2-column, render_pdfs.py build_cover_html produces it).
- **Demographics now truthful:** Woman + Asian (was "decline"). Config: jamie-autopilot/lib/jamie_demographics.py
- **Full handoff:** session_continuation_jamie_autopilot_2026-05-29.md (read FIRST for technical detail).
- Jamie reviews applications via `oracle-job-search/jamie/dashboard.html` (interactive, expandable cards).
