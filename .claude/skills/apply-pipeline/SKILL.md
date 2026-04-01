---
name: apply-pipeline
description: >
  Run the full 4-stage job application pipeline for Jamie. Use when Jamie says
  "run the pipeline", "help me apply to this", "full application workflow",
  "go through the whole process", or pastes a JD and wants the complete treatment.
  Evaluates fit, tailors resume, finds contacts, drafts outreach — with dashboards
  and clear action items at each stage.
argument-hint: "<paste job description or URL>"
---

## Full Application Pipeline

You are guiding Jamie through the complete job application process. This is interactive —
you will give feedback at every stage. Listen carefully and adapt.

---

### PIPELINE OVERVIEW (show this first)

When you trigger this pipeline, immediately show this roadmap:

```
=== APPLICATION PIPELINE ===

Job: [title if known, or "analyzing..."]

  Stage 1: EVALUATE    [ ]  Fit analysis + H1B check → Go/Pass decision
  Stage 2: TAILOR      [ ]  Resume bullet selection + wording fine-tuning
  Stage 3: OUTREACH    [ ]  Find connections + draft messages
  Stage 4: APPLY       [ ]  Pre-flight checklist + application prep

  Ready? Let me start with Stage 1.
```

Update this dashboard as you complete each stage (replace `[ ]` with `[DONE]`).

---

### STAGE 1: EVALUATE

Execute the full `/evaluate` skill logic:
1. Read `jamie/preferences.md`, `jamie/h1b_verified.md`, `jamie/application_tracker.md`
2. Run hard constraint check
3. Check H1B status
4. Assess fit with match percentage
5. Deliver the structured verdict

**After Stage 1, show this dashboard:**

```
=== STAGE 1 COMPLETE: EVALUATION ===

  Company:        [name]
  Role:           [title]
  Location:       [location]
  H1B:            [status]
  Match:          ~[X]%
  Recommendation: [GO / STRETCH / PASS]
  Priority:       P[X] — [category]

  Strengths: [2-3 key strengths]
  Gaps:      [1-2 gaps]

  → Proceed to Stage 2 (Resume Tailoring)?
  → Or: ask me questions, give feedback, or say "pass" to stop here.
```

**If PASS:** Explain why briefly and stop. Don't push applying to something that's not a fit.

**If GO or STRETCH:** Wait for your confirmation before proceeding.

---

### STAGE 2: TAILOR

Execute the full `/tailor` skill logic:
1. Read `jamie/content_library.md` and `jamie/resume.md`
2. Select best variant emphasis for each role
3. Pick 4 bullets per role
4. Fine-tune wording (not cliche!)
5. Check one-page constraint

**After Stage 2, show this dashboard:**

```
=== STAGE 2 COMPLETE: RESUME TAILORING ===

  Emphasis:       [variant set chosen]
  Changes made:   [X] of 20 bullets modified
  Self-intro:     [which version recommended]

  CHANGES SUMMARY:
  • Transition Projects: [unchanged / bullet X swapped / reworded]
  • InGenius Prep:       [which emphasis set, what changed]
  • NextGen Healthcare:  [unchanged / minor tweaks]
  • Vestas:              [unchanged / minor tweaks]
  • Kronos:              [unchanged / minor tweaks]

  ACTION ITEMS FOR JAMIE:
  □ Open resume in [Google Docs / Word]
  □ Make the [X] bullet changes listed above
  □ Check it still fits on one page
  □ Export new PDF

  → Ready for Stage 3 (Outreach)?
  → Or: "this sounds too cliche", "change bullet X", "show me the full bullets"
```

**FEEDBACK LOOP:** This is where you will most likely push back. Common responses:
- "Too cliche" → revert to closer-to-original wording, just reorder bullets
- "I like bullet X better from the other set" → swap it in
- "That's too long" → trim the specific bullet
- "Show me side by side" → show current vs. proposed for each role

Stay in Stage 2 until you say you're satisfied. Don't rush to Stage 3.

---

### STAGE 3: OUTREACH

Execute the full `/outreach` skill logic:
1. Search for contacts (alumni, team members, hiring managers)
2. Check existing connections in tracker
3. Draft personalized messages
4. Build outreach sequence

**After Stage 3, show this dashboard:**

```
=== STAGE 3 COMPLETE: OUTREACH ===

  Contacts found: [X]
  Alumni:         [names or "none found"]
  Team members:   [names or "none found"]
  Hiring manager: [name or "not identified"]

  OUTREACH SEQUENCE:
  1. [Today]     → Send LinkedIn request to [Contact 1] (reason)
  2. [Today]     → Send LinkedIn request to [Contact 2] (reason)
  3. [Tomorrow]  → Submit application
  4. [Day 2-3]   → Follow up with accepted connections
  5. [Day 3-5]   → Email hiring manager with resume attached

  ACTION ITEMS FOR JAMIE:
  □ Review messages below — tell me if tone is right
  □ Send connection request to [Contact 1]
  □ Send connection request to [Contact 2]
  □ [If email] Send email to [Contact 3]

  → Ready for Stage 4 (Application Prep)?
  → Or: "rewrite message for X", "too eager", "find more people"
```

**FEEDBACK LOOP:** Messages are personal — you will want to adjust tone. Listen for:
- "Too formal" / "too casual" → adjust register
- "Don't mention X" → remove that reference
- "Can you find someone in [specific team]?" → do another targeted search
- "This sounds like I'm begging" → make it more peer-to-peer, less requesting

---

### STAGE 4: APPLICATION PREP

This is the pre-flight checklist before Jamie hits "Apply."

```
=== STAGE 4: APPLICATION PREP ===

  PRE-FLIGHT CHECKLIST:
  ✅ Job evaluated — [GO / STRETCH] with [X]% match
  ✅ Resume tailored — [X] bullets customized
  ✅ Outreach — [X] contacts identified, messages drafted
  □  Export your tailored resume as PDF
  □  Cover letter needed? [Yes — draft below / No / Optional]

  COVER LETTER (if needed):
  [Draft using content_library.md building blocks — self-intro + why this company
   + 2-3 pillars connecting your experience to JD + closing]

  APPLICATION ANSWERS (common questions):
  • Willing to relocate? → [Yes — moving to Portland / Already in Portland / Open to relocation]
  • Salary expectations? → $80K-$130K (adjust based on role level and location)
  • Visa sponsorship needed? → Yes, H1B sponsorship required
  • Years of experience? → ~3 years professional experience
  • Highest education? → MS Applied Organizational Psychology, USC (2023)

  FINAL ACTION ITEMS:
  □ Export tailored resume as PDF
  □ Send outreach messages (LinkedIn)
  □ Submit application on [company ATS]
  □ Log in Google Sheets tracker: date, company, role, status = "Applied"
  □ Set reminder: follow up in 1 week if no response

  → All done! Good luck! 🙏
```

---

## ACTIVE LISTENING & FEEDBACK PROTOCOL

Throughout the ENTIRE pipeline, watch for your feedback and adapt immediately:

### Tone Feedback
| You say | What to do |
|---|---|
| "too cliche" / "sounds fake" | Revert to original wording, reduce keyword insertion |
| "too formal" / "too corporate" | Use shorter sentences, casual vocabulary |
| "too casual" | Add more professional framing |
| "too long" | Cut to essential facts + one metric |
| "sounds desperate" | Remove urgency, make it more matter-of-fact |
| "sounds like AI wrote it" | Biggest red flag — significantly simplify, use your own phrases |

### Process Feedback
| You say | What to do |
|---|---|
| "skip to [stage]" | Jump ahead, but note what was skipped |
| "go back to [stage]" | Return and revise |
| "I don't want to apply" | Stop gracefully, no pressure |
| "just do the evaluation" | Run Stage 1 only |
| "I already have contacts" | Skip contact search, just draft messages for your contacts |

### Learning Feedback (save for future)
If you give feedback that should apply to ALL future applications (not just this one),
acknowledge it clearly: "Got it — I'll remember [X] for future applications too."
This includes preferences about tone, bullet style, types of roles you don't want, etc.

---

## MODEL SELECTION — Use the Cheapest Model That Can Do the Job (v1.1)

> This pipeline spawns background agents at Stages 1, 3, and sometimes 4.
> Always specify `model:` explicitly — unspecified defaults to Sonnet and wastes budget.

| Stage / Agent task | Model | Reason |
|---|---|---|
| H1B cache lookup (h1b_verified.md read) | `haiku` | File read + match — mechanical |
| Application tracker read/update (Notion CRUD) | `haiku` | Property writes — no judgment |
| LinkedIn contact search (name + URL extraction) | `haiku` | Structured data pull |
| Outreach message drafting | `sonnet` | Requires your voice + relationship awareness |
| Cover letter drafting | `sonnet` | Judgment-heavy, must sound like you |
| Fit evaluation / gap analysis | `sonnet` | Requires understanding of your full background |
| Orchestrator / main pipeline thread | `sonnet` | Coordinates stages — needs full capability |

**Rule:** Any agent doing pure data retrieval or writes → `haiku`. Any agent drafting words or making fit judgments → `sonnet`.

---

## TOKEN EFFICIENCY — Baked-In Rules (v1.0)

> David and Jamie share a Claude Team plan with per-seat limits (~55K tokens per 5-hour window).
> Every skill must be as token-efficient as possible without sacrificing quality.

### File Read Strategy: Compact First, Expand on Demand
| When | Read this | NOT this |
|------|-----------|----------|
| Stage 1 (evaluate) | `jamie/profile_compact.md` (~60 lines) | `preferences.md` + `h1b_verified.md` (385 lines) |
| Stage 2 (tailor) — MUST read full files | `content_library.md` + `preferences.md` | No shortcut — need full bullet text |
| Stage 3 (outreach) | `outreach_templates.md` only | NOT `content_library.md` (unless cover letter needed) |

### Session Hygiene (automatic)
- After completing a full pipeline run, suggest `/clear` to Jamie before next job
- Never carry forward stale context from a previous evaluation into a new one
- If Jamie evaluates multiple jobs in sequence, each one should be independent

### Enrichment: On-Demand Only
- Do NOT auto-generate cover letters or contact research unless Jamie asks or says "go ahead"
- Stage 3 (outreach) and Stage 4 (apply) should ask before doing expensive work:
  - "Want me to search for contacts at [Company]?" (Chrome browsing = expensive)
  - "Should I draft a cover letter?" (Sonnet generation = expensive)
- If you say "just prep the checklist" → skip contact search + cover letter, go straight to checklist

### Sub-Agent Rules
- Every spawned agent MUST specify `model: "haiku"` unless it needs voice/judgment
- Chrome navigation agents: `sonnet` (needs page understanding)
- Notion CRUD / file lookup agents: `haiku`
- If in doubt, use `haiku` — it handles 90% of mechanical tasks correctly

---

## OUTPUT PRINCIPLES

1. **Dashboards at every stage** — you should always know where you are and what's next
2. **Clear action items** — every dashboard ends with specific checkboxes for you
3. **Progress indicators** — update the pipeline overview as stages complete
4. **Summaries, not walls of text** — lead with the verdict, details below
5. **Ask before proceeding** — never auto-advance to the next stage without confirmation
6. **Be honest about gaps** — you trust directness over encouragement
