---
name: evaluate
description: >
  Evaluate whether a job is a good fit for Jamie. Use when Jamie pastes a job description,
  shares a job URL, or says "evaluate this", "is this a fit?", "should I apply?", "check this job".
  Returns a structured fit analysis with H1B status and go/stretch/pass recommendation.
argument-hint: "<paste job description or URL>"
---

## Stage 1: Job Evaluation

You are helping Jamie (Yi-Chieh) Cheng evaluate whether a specific job is worth applying to.

### Step 1 — Load Context

Read these files (in parallel if possible):
1. `jamie/preferences.md` — hard constraints, role priorities, fit scoring matrix, self-assessment
2. `jamie/h1b_verified.md` — H1B verification cache
3. `jamie/application_tracker.md` — check if she already applied to this company/role

### Step 2 — Get the Job Description

If `$ARGUMENTS` contains a URL:
- Use WebFetch to retrieve the page content and extract the JD
- If the URL is a LinkedIn job link, try to extract the job details

If `$ARGUMENTS` contains pasted text:
- Parse it directly as a job description

If neither:
- Ask Jamie to paste the job description or provide a URL

### Step 3 — Hard Constraint Check

Run through these in order. If ANY fails, it's an instant **PASS**:

1. **Already applied?** Check `jamie/application_tracker.md` for this company + similar title
2. **Visa:** Does the JD say "no sponsorship" or "must be authorized without sponsorship"? → PASS
3. **Seniority:** Is the title Senior/Director/VP/Principal/C-level? (Exception: "Senior Associate" at consulting firms is OK) → PASS
4. **Location:** Is it on-site outside Portland/Seattle/Remote? Flag it but don't auto-reject — Jamie has applied to NYC and SF roles before
5. **Hard reject roles:** Pure Sales, Pure SWE, Senior HRBP, Instructional Designer (80%+ content creation), Technical PM requiring PMP

### Step 4 — H1B Sponsorship Check

1. Check `jamie/h1b_verified.md` for the company
2. If not found, determine:
   - Is it a **cap-exempt** employer? (university, nonprofit hospital, FQHC, nonprofit research org) → GOOD
   - Is it a **Big 4 / major consulting firm**? → CONFIRMED
   - Otherwise: use WebSearch to check `site:h1bdata.info "{company name}"` for LCA filing history
3. Report: **Confirmed** / **Cap-Exempt** / **Unknown (needs verification)** / **No Sponsorship**

### Step 5 — Fit Assessment

Using the self-assessment table in `jamie/preferences.md`:

1. List each major JD requirement and map it to Jamie's strength level (3-star, 2-star, 1-star)
2. Calculate approximate match percentage
3. Apply the **remote vs. local bar**:
   - Remote roles need 80%+ match PLUS an additional advantage
   - Portland/Seattle roles need 60-70% match
4. Identify which of the 5 role priority categories this falls into (P1-P5)

### Step 6 — Deliver the Verdict

Format your response as:

```
## [COMPANY] — [JOB TITLE]

**Recommendation: GO / STRETCH / PASS**

### Quick Facts
- Location: [location + arrangement]
- H1B: [Confirmed ✅ / Cap-Exempt 🏛️ / Unknown ⚠️ / No ❌]
- Priority: P[1-5] — [category name]
- Match: ~[X]% of JD requirements
- Already applied? [Yes — skip / No]

### Why This Fits (or Doesn't)
[2-3 sentences on alignment with Jamie's experience]

### Strengths
- [bullet matching JD req → Jamie's specific experience]
- [bullet matching JD req → Jamie's specific experience]

### Gaps to Be Aware Of
- [bullet: JD requires X — Jamie has limited experience here]

### If She Applies
- Best resume variant emphasis: [L&D ops / Program Mgmt / OD / Engagement / etc.]
- Key bullets to feature from content_library.md: [brief pointer]
- Outreach angle: [alumni connection? hiring manager on LinkedIn?]
```

### Important Notes
- Be honest about gaps. Jamie's preferences.md says: "When there's a gap, say it directly."
- Don't inflate match percentage — use the self-assessment table as ground truth
- If it's a STRETCH, explain what would make it worth applying anyway (networking opportunity, dream company, cap-exempt, etc.)
- If it's a PASS, be clear and brief — don't soften it with "but maybe if..."
