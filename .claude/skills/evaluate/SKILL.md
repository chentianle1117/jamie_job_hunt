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

---

## 🤖 Gemini-First Architecture (PRIMARY PATH)

> Claude does NOT read Jamie's profile files directly.
> Dump all profile files into Gemini Pro's 1M context in one shot.
> Gemini generates grounded in the actual source — hallucination of experience is structurally prevented.
> Claude: get the JD → build the prompt → run Gemini → grep-verify → present to Jamie.

### Step 1 — Get the Job Description

If `$ARGUMENTS` contains a URL:
- **With Chrome:** Navigate and `get_page_text` — required for JS-rendered ATS (Greenhouse, Lever, Ashby, Workday) and LinkedIn (blocks WebFetch). Also verify posting is still live (no "No longer accepting" or 404).
- **Without Chrome:** WebFetch the URL. If 403/redirect/empty → ask Jamie to paste JD directly.

If `$ARGUMENTS` contains pasted text: use it directly.
If neither: ask Jamie to paste the JD or provide a URL.

### Step 2 — Run Gemini Evaluation (fat-context)

```bash
# On Jamie's Mac: repo is at /Users/jamiecheng/jamie_job_hunt/
# Store JD text in a temp var or file first
JD_TEXT="<fetched or pasted JD text>"

cat jamie/preferences.md \
    jamie/h1b_verified.md \
    jamie/profile_compact.md \
    jamie/application_tracker.md > /tmp/eval_context.txt
echo "===== JOB DESCRIPTION =====" >> /tmp/eval_context.txt
echo "$JD_TEXT" >> /tmp/eval_context.txt

cat /tmp/eval_context.txt | gemini -m gemini-2.5-pro -p "
You are evaluating a job posting for Jamie (Yi-Chieh) Cheng. All her profile context is above.
Run these checks in order:

1. HARD GATES (instant PASS if any fail):
   - JD says 'no sponsorship' or 'must be authorized without sponsorship' → PASS
   - Title is Senior/Director/VP/Principal/C-level (exception: 'Senior Associate' at consulting) → PASS
   - Pure Sales, Pure SWE, Instructional Designer (80%+ content creation), Technical PM w/ PMP req → PASS
   - Already applied — check application_tracker section above for this company + similar title → PASS

2. H1B STATUS: check h1b_verified section above. If not found:
   - University/nonprofit hospital/FQHC/nonprofit research org → Cap-Exempt 🏛️
   - Big 4 / major consulting firm → Confirmed ✅
   - Otherwise → Unknown ⚠️ (needs verification)

3. FIT ASSESSMENT: map each major JD requirement to Jamie's ACTUAL experience from preferences.md above.
   Use ONLY experience described in the profile above — do not invent or extrapolate.
   Remote bar: 80%+ match + additional advantage. Local/Portland/Seattle bar: 60-70%.
   Identify priority tier: P1 (Program Mgmt), P2 (Engagement/OD), P3 (HR Generalist/HRBP),
   P4 (Consulting), P5 (Adjacent/stretch)

4. VERDICT: GO / STRETCH / PASS with honest reasoning.

Output in this EXACT format — no deviations:
## [COMPANY] — [JOB TITLE]
**Recommendation: GO / STRETCH / PASS**
### Quick Facts
- Location: [location + arrangement]
- H1B: [Confirmed ✅ / Cap-Exempt 🏛️ / Unknown ⚠️ / No ❌]
- Priority: P[1-5] — [category name]
- Match: ~[X]%
- Already applied? [Yes / No]
### Why This Fits (or Doesn't)
[2-3 sentences — cite specific experience from profile above, no invented metrics]
### Strengths
- [JD requirement] → [Jamie's specific experience from profile above]
- [repeat for top 3]
### Gaps
- [JD requires X — Jamie has limited/no experience here, based only on profile above]
### If She Applies
- Resume emphasis: [variant type from content_library]
- Outreach angle: [alumni? hiring manager? specific angle]
"
GEMINI_EXIT=$?
```

### Step 3 — Grep Grounding Check (mandatory, near-zero tokens)

Before presenting to Jamie, verify every specific claim in Strengths against source files:

```bash
# Verify any cited metric or experience snippet exists in profile files
# Examples:
grep -i "vendor" jamie/preferences.md jamie/profile_compact.md        # "managed vendor relationships"
grep -i "600" jamie/preferences.md jamie/profile_compact.md           # "600+ employees"
grep -i "onboarding" jamie/preferences.md jamie/profile_compact.md    # onboarding program claim
grep -i "COMPANY_NAME" jamie/h1b_verified.md jamie/profile_compact.md # H1B status check

# Cliché check on the full output
echo "$GEMINI_OUTPUT" | grep -iE "spearhead|leverage|synerg|drove strategic|cross-functional impact|thrilled|passionate about"
# Any match → remove that phrase before presenting
```

**If grep finds no match for a claimed fact:**
→ Remove the claim from Strengths
→ Re-prompt Gemini once: *"Recheck Strengths — cite only experience explicitly in the profile section above. Remove any metric not found there."*
→ If second attempt fails or Gemini is down → Claude native fallback below

### Step 4 — Present to Jamie

Output the verified evaluation. Add at the bottom:

```
---
💡 Next steps:
  /tailor — tailor resume for this role
  /outreach — find contacts + draft messages
  /clear — start fresh before next evaluation
```

---

## ⚠️ Fallback: Claude Native (when Gemini unavailable)

```bash
# Gemini unavailable if: exit code != 0, rate limit, CLI not found
if [ $GEMINI_EXIT -ne 0 ]; then
  echo "⚠️ Gemini unavailable — evaluating natively"
fi
```

**Claude reads directly:**
1. `jamie/profile_compact.md` — hard constraints, H1B quick reference, fit scoring (~60 lines, sufficient for go/pass)
2. `jamie/preferences.md` — only if STRETCH and need full self-assessment table
3. `jamie/h1b_verified.md` — only if company not in profile_compact.md quick reference

**Live application dedup** — WebFetch Jamie's Google Sheet:
- 2026: `https://docs.google.com/spreadsheets/d/1tRN3KMGHOSyRMf14TRUj3wPldbM9fwDxVu9XsEH6s2E/export?format=csv&gid=1018026840`
- 2025: `https://docs.google.com/spreadsheets/d/1tRN3KMGHOSyRMf14TRUj3wPldbM9fwDxVu9XsEH6s2E/export?format=csv&gid=0`
- If WebFetch fails: `jamie/application_tracker.md`

**Then run hard constraint check, H1B check, fit assessment, and deliver verdict in the same output format above.**

---

## Important Notes (apply in both paths)
- Be honest about gaps. Jamie's preferences.md says: "When there's a gap, say it directly."
- Don't inflate match % — use the self-assessment table as ground truth
- STRETCH: explain what makes it worth applying anyway (networking, dream company, cap-exempt)
- PASS: be clear and brief — don't soften with "but maybe if..."
- Location is NOT an auto-reject — flag it, evaluate role fit first
