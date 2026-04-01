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

### ⚡ Gemini Fat-Context Grounding (run BEFORE Steps 1–6)

After you have the JD text in hand (from Step 2), run Gemini to do the heavy fit analysis.
This offloads the large file reads to Gemini's fat context window and saves Claude tokens.

**How to run:**

```bash
# Write the JD to a temp file
echo "$JD_TEXT" > /tmp/jd_current.txt

# Run Gemini via Python wrapper (robust — no shell quoting issues, has timeout + retry)
python3 pipeline/gemini_run.py \
  --prompt "You are a job fit analyst for Jamie Cheng, an OD/HR professional seeking people roles in Portland OR or remote US, requiring H1B sponsorship.

Analyze the job description against Jamie's profile and return a structured evaluation with these exact sections:
1. HARD_CONSTRAINTS: list any instant-pass triggers (no sponsorship, senior title, pure sales/SWE, etc.) — or write NONE
2. H1B_STATUS: Confirmed / Cap-Exempt / Unknown / No-Sponsorship — and brief reason
3. ROLE_PRIORITY: P1/P2/P3/P4/P5 and category name
4. MATCH_SCORE: 0-100 integer
5. STRENGTHS: 3-5 bullets mapping JD requirements to Jamie's experience
6. GAPS: 2-4 bullets of honest gaps
7. RESUME_EMPHASIS: which bullet variant set fits best (L&D/PM/OD/Engagement/Vendor)
8. VERDICT: GO / STRETCH / PASS with one sentence reason

Ground your answer ONLY in the files provided. Do not invent experience Jamie does not have." \
  --context /tmp/jd_current.txt jamie/profile_compact.md jamie/preferences.md \
  --verify "MS" "USC" \
  > /tmp/gemini_output.txt 2>/tmp/gemini_err.txt

GEMINI_EXIT=$?
GEMINI_OK=$( [ $GEMINI_EXIT -eq 0 ] && echo "true" || echo "false" )
GEMINI_OUTPUT=$(cat /tmp/gemini_output.txt)
```

**Using Gemini's output:**
- If `$GEMINI_OK` = `"true"`: use `$GEMINI_OUTPUT` as the structured analysis for Steps 3–6.
  If any grounding warnings appear in `/tmp/gemini_err.txt`, drop those claims.
- If `$GEMINI_OK` = `"false"`: skip Gemini output entirely — run Steps 3–6 natively using Claude's own reads.

**Do NOT show the raw Gemini output to Jamie.** Use it as your working notes to fill in Step 6's verdict format.

---

### Step 1 — Load Context (Token-Efficient)

**Default: Read `jamie/profile_compact.md` FIRST** (~60 lines vs ~385 lines).
This contains all hard constraints, H1B quick reference, fit scoring formula, and self-assessment.
It is sufficient for Steps 3-5 (hard constraint check, H1B check, fit assessment).

**Only escalate to full files when needed:**
- Read `jamie/preferences.md` (253 lines) — only if the role is a STRETCH and you need the full
  self-assessment table, networking templates, or search query context
- Read `jamie/h1b_verified.md` (132 lines) — only if the company is NOT in profile_compact.md's
  quick reference (i.e., not in confirmed/cap-exempt/no-sponsor lists)
- **Live application data** — Use WebFetch to pull your live Google Sheet:
  - 2026 tab: `https://docs.google.com/spreadsheets/d/1tRN3KMGHOSyRMf14TRUj3wPldbM9fwDxVu9XsEH6s2E/export?format=csv&gid=1018026840`
  - 2025 tab: `https://docs.google.com/spreadsheets/d/1tRN3KMGHOSyRMf14TRUj3wPldbM9fwDxVu9XsEH6s2E/export?format=csv&gid=0`
  - If WebFetch fails, fall back to `jamie/application_tracker.md` (static snapshot)

> **Why:** Each file read costs tokens. profile_compact.md has everything for a quick
> go/pass decision at ~1/6 the token cost. Only load full files for GO/STRETCH roles
> that proceed to tailoring.

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
4. **Location:** Portland/Remote/Seattle is your preference but you are open to relocation if the role content and fit are genuinely strong. Flag out-of-area roles and note the location, but do NOT auto-reject on location alone. Evaluate on role fit first — if GO on content, note the location as a consideration, not a blocker.
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

1. List each major JD requirement and map it to your strength level (3-star, 2-star, 1-star)
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
[2-3 sentences on alignment with your experience]

### Strengths
- [bullet matching JD req → your specific experience]
- [bullet matching JD req → your specific experience]

### Gaps to Be Aware Of
- [bullet: JD requires X — you have limited experience here]

### If You Apply
- Best resume variant emphasis: [L&D ops / Program Mgmt / OD / Engagement / etc.]
- Key bullets to feature from content_library.md: [brief pointer]
- Outreach angle: [alumni connection? hiring manager on LinkedIn?]
```

### Important Notes
- Be honest about gaps. The rule is: "When there's a gap, say it directly."
- Don't inflate match percentage — use the self-assessment table as ground truth
- If it's a STRETCH, explain what would make it worth applying anyway (networking opportunity, dream company, cap-exempt, etc.)
- If it's a PASS, be clear and brief — don't soften it with "but maybe if..."
