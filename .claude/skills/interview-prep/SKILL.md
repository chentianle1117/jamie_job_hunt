---
name: interview-prep
description: >
  Build a paste-ready interview-prep doc for Jamie ahead of a recruiter screen, hiring-manager
  interview, or panel. Use when Jamie says "prep me for [company]", "I have an interview",
  "build interview prep", "help me get ready for [interviewer]", or pastes a JD and names an
  interview type/date. Produces the standard 7-section prep grounded in her real profile + STAR bank.
argument-hint: "<company / role / interview type / interviewer(s) / date — or paste a JD>"
---

## Interview Prep — the deliverable is a paste-ready prep doc (not a resume)

You are preparing Jamie (Yi-Chieh) Cheng for an interview. The **deliverable is one Markdown
prep doc per interview**, formatted for Google Docs, following the 7-section template. Resumes and
cover letters in this repo are *reference material* — a source of truth for her real experience —
not the thing you produce here.

> 🚨 **RULE 0 applies in full.** Truth beats fit. Never invent experience, metrics, interviewer
> facts, or company news. Every claim traces to `jamie/resume.md`, `jamie/content_library.md`,
> `jamie/profile_compact.md`, or the company notes doc. When unsure, ASK Jamie in plain text.
> See `jamie/JAMIE_FEEDBACK_RULES.md` §0.

---

### Step 0 — Gather inputs

From `$ARGUMENTS` (or by asking Jamie in plain text — no menus):
- **Company** and **role title**
- **Interview type:** recruiter screen / hiring-manager / panel — this sets the depth (Step 4)
- **Interviewer name(s)** if known
- **Date** and any **notes from earlier conversations** with the company
- The **JD** (pasted, a URL, or a file)

If the JD is a URL, read it with Chrome `get_page_text` (ATS pages) or WebFetch; if blocked, ask
Jamie to paste it.

---

### Step 1 — Check the repo for existing intel (DO THIS FIRST)

Jamie's prior call notes and partial preps live in `jamie/interview_prep/`:
- `intake/` — original `.docx`/`.pdf`/`.pptx` (named `Company, Interviewer.docx`)
- `extracted/` — the same docs as `.txt` (read these; they're token-cheap)
- `STATUS.md` — the manifest diff: which companies have FULL / PARTIAL / RAW notes
- `TEMPLATE.md` — the canonical 7-section template
- `CONSISTENCY.md` — resolved canonical facts (title, revenue, counts, location, work-auth)

**Always check `STATUS.md` first.** If this company already has a notes doc, READ the extracted
`.txt` — it usually holds real intel Jamie gathered live: interviewer names, round structure,
in-office days, comp, culture notes, recruiter-stated facts. Build *on top of* that; don't discard it.

If the doc is classified FULL → you're refining. PARTIAL → fill the missing sections. RAW → build
from scratch but keep every real fact in the notes.

---

### Step 2 — Pull Jamie's canonical profile + STAR bank

- `jamie/profile_compact.md` — constraints, H1B, self-assessment (always)
- `jamie/interview_prep/CONSISTENCY.md` — the resolved canonical facts (title = **Program
  Enablement Manager**; **$316K** = team-high BD revenue, **$115K** = program revenue; **600+** =
  webinar participants, **70+** = cross-functional staff; home base **Portland, OR**; work-auth line)
- `jamie/resume.md` + `jamie/content_library.md` — ground truth for any experience claim and her
  real STAR variants (read when drafting Section 5)
- `jamie-second-brain/Work/Career/Voice & Story Bank.md` — her actual phrasing + STAR stories
- Per-employer ground truth in `jamie-second-brain/Work/Projects/*.md` (ODN = pro bono OD diagnostic
  consulting — NGO leadership + HR leave-cost — NOT community/ERG)

Match STARs to the role from the bank (Section 6 of TEMPLATE.md lists the mapping).

---

### Step 3 — Research the company (web; current — do NOT rely on training data)

Search the web for:
- What they do · core products · industry & market position
- **Recent news** — funding, M&A, leadership change, launches (this is how the Brex prep caught the
  Capital One acquisition context and BOC's post-ICBC regulatory environment). Always web-verify.
- Culture & values — official site + an employee-review reality check (Glassdoor/Blind)
- The team and **how it ladders to company goals**
- Regulatory / industry context when relevant (finance, healthcare, regulated sectors)

Cite what you find in Section 2. If you can't verify a fact, say so — don't assert it.

---

### Step 4 — Fit & positioning (then calibrate depth)

1. **Classify fit:** core fit / reasonable stretch / long shot — be honest.
2. **Strengths to lead with** + **honest gaps to prepare for** (never paper over a gap; acknowledge
   briefly, pivot to a real strength).
3. **Pick the positioning angle that matches THIS role** — don't reuse one generic pitch:
   - enablement / sales-adjacent → lead with BD + enablement build (40+ leads, 78% conversion)
   - governance / compliance / risk → lead with process/ops/vendor mgmt + compliance-sensitive coordination
   - L&D / talent dev → lead with onboarding redesign + program build + needs assessment
   - people-program / culture → lead with OD method + engagement/data + global program scaling
4. **Flag consistency landmines** against `CONSISTENCY.md` — title, revenue figure, participant
   counts, location. If a notes doc states a number that conflicts, use the canonical one and flag it.

**Calibrate depth by interview type:**
- **Recruiter screen** — lighter: must-haves, motivation/why-now, logistics, 1–2 light STARs
- **Hiring manager** — deeper: 4–6 STARs, role-specific Q&A, scope/impact detail
- **Panel** — map likely questions to each interviewer's angle; group Section 4 by interviewer

---

### Step 5 — Build the prep doc (the deliverable)

Use the 7-section template in `jamie/interview_prep/TEMPLATE.md`. Write it to
`jamie/interview_prep/{Company}_{Role}_Interview-Prep_{YYYY-MM-DD}.md`.

The 7 sections:
1. **Header** — role, company, interview type, interviewer name(s), date
2. **Company Info** — what they do · products · industry & market · **news (web-verified)** · culture
   & values · org & department · core requirement → how Jamie matches
3. **Self-Introduction & opening responses** — conversational bulleted intro hitting beats in order;
   "why looking / why now"; reframed gap answers — in Jamie's natural spoken voice
4. **Anticipated questions + drafted answers** — derived from the JD, each with a grounded answer.
   **This is a standing requirement — always include it.** Group by interviewer for panels.
5. **STAR examples** — Situation/Task/Action/Result, role-matched from the bank
6. **Questions to ask** — grouped (Team & org / Role & fit / Process & logistics) + blank lines for her own
7. **Logistics to have ready** — comp, location/relocation, work auth, consistency + tone notes

**Voice & format rules:**
- Conversational, warm, direct — the way Jamie actually speaks, not prose-on-a-page
- Paste-ready Markdown: `###` headers, **bold the beats** so they're glanceable on a live call
- Honesty first; calibrate by type; match positioning to the employer every time

---

### Step 6 — Surface the critical few in chat (not just in the doc)

In your chat reply, lead with the headline items Jamie must see before the call:
- The **headline** (e.g., an acquisition, a regulatory event, a reorg)
- The **honest gaps** and how she'll handle them
- **Decisions she must make before the call** — relocation, comp target, work authorization timing

Then point her to the saved doc.

---

### Step 7 — Offer to iterate

Offer (don't auto-run):
- Refine specific lines (intro, gap answers) into her natural spoken voice with bolded beats
- A **mock interview** (you ask, she answers; you coach)
- A **JD jargon decoder**
- Deeper **STAR build-out** for the likely-heaviest questions

---

### Reference — example trace (how the Brex prep ran)
JD + "recruiter screen tomorrow" → checked repo (`Brex, Diane`) → web research surfaced the
acquisition context → fit = stretch (no SDR quota) → built 7-section doc → flagged acquisition +
gaps + relocation/comp/work-auth decisions in chat → iterated the intro into spoken voice with
bolded beats.

### Model selection (per CLAUDE.md)
- File reads / extraction / classification of notes docs → spawn `haiku` sub-agents
- Drafting the doc, intro, gap answers, STARs (judgment + Jamie's voice) → `sonnet` (or the main thread)
