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

## 🤖 Gemini-First Evaluation Architecture

> **Claude does NOT read Jamie's profile files directly.**
> Instead, dump everything into Gemini Pro's 1M context window — it generates grounded
> in the actual source material, eliminating hallucination of accomplishments or constraints.
> Claude's job: get the JD, build the Gemini prompt, run it, smell-test the output, present to Jamie.

### Primary path (Gemini Pro):

```bash
# Build fat context input — all relevant profile files + JD
JD_TEXT="<paste or fetched JD text>"

cat jamie/preferences.md \
    jamie/h1b_verified.md \
    jamie/profile_compact.md \
    jamie/application_tracker.md > /tmp/eval_context.txt

echo "===== JOB DESCRIPTION =====" >> /tmp/eval_context.txt
echo "$JD_TEXT" >> /tmp/eval_context.txt

cat /tmp/eval_context.txt | gemini -m gemini-2.5-pro -p "
You are evaluating a job posting for Jamie (Yi-Chieh) Cheng. All her profile context is above.

Run these checks in order:
1. HARD GATES (instant PASS if any fail): no sponsorship language, Senior/Director/VP/C-level title,
   pure sales/SWE/instructional design, already applied (check application_tracker section above)
2. H1B STATUS: check h1b_verified section. If not found: is it a university/nonprofit/hospital (cap-exempt)?
   Otherwise: Unknown — needs verification.
3. FIT ASSESSMENT: map each major JD requirement to Jamie's actual experience from preferences.md.
   Use ONLY experience described in the profile above — do not invent or extrapolate.
   Apply remote bar (80%+ match) vs local bar (60-70% match).
4. VERDICT: GO / STRETCH / PASS with honest reasoning.

Output the evaluation in this EXACT format:
## [COMPANY] — [JOB TITLE]
**Recommendation: GO / STRETCH / PASS**
### Quick Facts
- Location: [location + arrangement]
- H1B: [Confirmed ✅ / Cap-Exempt 🏛️ / Unknown ⚠️ / No ❌]
- Priority: P[1-5] — [category]
- Match: ~[X]%
- Already applied? [Yes / No]
### Why This Fits (or Doesn't)
[2-3 sentences — cite specific experience from profile above]
### Strengths
- [JD requirement → Jamie's specific experience from profile]
### Gaps
- [JD requires X — note if Jamie has limited/no experience, based only on profile above]
### If She Applies
- Resume emphasis: [variant type]
- Outreach angle: [specific to this role]
"
GEMINI_EXIT=$?
```

### Fallback chain:
```bash
if [ $GEMINI_EXIT -ne 0 ]; then
  echo "⚠️ Gemini unavailable (exit $GEMINI_EXIT) — Claude evaluating natively"
  # Claude: read profile_compact.md + preferences.md yourself and run Steps 3-6 below
fi
```

### Grounding check — cheap Grep verification (mandatory, near-zero tokens):

```bash
# If Gemini cites a specific metric or accomplishment in Strengths, grep it against profile files
# Example: Gemini says "managed 20+ vendor relationships"
grep -i "vendor" jamie/preferences.md jamie/profile_compact.md  # → found? ✅ grounded

# If Gemini cites a company name in experience (e.g. "her work at Vestas")
grep -i "vestas" jamie/preferences.md   # → found? ✅ real

# H1B status sanity check
grep -i "COMPANY_NAME" jamie/h1b_verified.md jamie/profile_compact.md
```

**If grep finds nothing for a claimed fact:** remove that claim, or re-prompt Gemini once:
`"Recheck Strengths — cite only experience explicitly stated in the profile section above. Remove any metric not found there."`

Second failure or Gemini down → Claude native fallback.

---

### Native Claude fallback (use when Gemini unavailable):

**Read only:** `jamie/profile_compact.md` — sufficient for go/pass. Escalate to `preferences.md` only for STRETCH roles needing deep fit mapping.

**Live application data** — check for duplicates via WebFetch:
- 2026 tab: `https://docs.google.com/spreadsheets/d/1tRN3KMGHOSyRMf14TRUj3wPldbM9fwDxVu9XsEH6s2E/export?format=csv&gid=1018026840`
- If WebFetch fails: use `jamie/application_tracker.md`

### Step 2 — Get the Job Description

If `$ARGUMENTS` contains a URL:
- **With Chrome:** Navigate to the URL and use `get_page_text` to read the full JD.
  This is especially important for JS-rendered ATS pages (Greenhouse, Lever, Ashby, Workday)
  that WebFetch cannot read. Also check if the posting is still live — look for
  "No longer accepting applications", 404 pages, or redirect to job board homepage.
- **Without Chrome:** Use WebFetch to retrieve the page content and extract the JD.
  If WebFetch returns a 403/redirect/empty page, ask Jamie to paste the JD text directly.
- If the URL is a LinkedIn job link, Chrome mode is strongly preferred (LinkedIn blocks WebFetch).

If `$ARGUMENTS` contains pasted text:
- Parse it directly as a job description

If neither:
- Ask Jamie to paste the job description or provide a URL

### Step 3 — Hard Constraint Check

Run through these in order. If ANY fails, it's an instant **PASS**:

1. **Already applied?** Check `jamie/application_tracker.md` for this company + similar title
2. **Visa:** Does the JD say "no sponsorship" or "must be authorized without sponsorship"? → PASS
3. **Seniority:** Is the title Senior/Director/VP/Principal/C-level? (Exception: "Senior Associate" at consulting firms is OK) → PASS
4. **Location:** Portland/Remote/Seattle is her preference but she is open to relocation if the role content and fit are genuinely strong. Flag out-of-area roles and note the location, but do NOT auto-reject on location alone. Evaluate on role fit first — if GO on content, note the location as a consideration, not a blocker.
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
