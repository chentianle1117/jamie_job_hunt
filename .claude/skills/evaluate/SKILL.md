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

### ⏰ Step 0 — Check Active Context Window (DO FIRST)

Before doing anything else, read the top of `jamie/preferences.md` and check whether a
**"Timeline-Adjusted Overlay"** section is currently active. As of May 12, 2026, Jamie is
in an H1B-runway window (~11 weeks to land a new sponsor) and the overlay broadens criteria.

**If the overlay is ACTIVE** (the section exists and is not marked "reverted"):
- Use the overlay's match thresholds (Portland 55-65%, Seattle 60-65%, Remote 70%+ at sponsor, Relocation 65%+ at sponsor)
- Include **P1b** roles (Education Program Manager, Curriculum Program Manager, Learning Program Manager, EdTech Program Manager, Higher Ed Program Manager, Student Success Program Manager) as P1-equivalent
- Treat relocation roles as in-scope (not flag-only) at confirmed H1B sponsors
- **Cap-exempt orgs (universities, hospitals) are the highest-leverage lane** — fastest H1B path
- **ALWAYS verify h1bdata.info** for the company's NON-TECH filings before approving a remote or relocation role. A company that sponsors only senior SWE is not a sponsor for Jamie.
- **Stay strict** on: AVOID list (recruiting/TA, payroll, leave, ER, HRIS admin, instructional design as primary, pure tactical coordinator/admin roles)

**If the overlay is INACTIVE** (Jamie has landed and it's been removed/marked reverted):
- Use the v2.0 strict defaults below (Portland 60-70%, Seattle 65-70%, Remote 80%+ + edge required, Relocation flag-only)

In either case, after Step 0 continue to Step 1.

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

---

### Step 5b — Truthful Scoring Guardrails (Added May 13, 2026)

> **Calibration learning:** The May 11-13 sweeps systematically over-scored leads. Below are the
> guardrails to prevent that. Apply these BEFORE finalizing any score above 70.

#### Guardrail 1 — Cap-Exempt Modifier Is CONDITIONAL

`+10` cap-exempt bonus applies ONLY when the role's hiring department actually sponsors at this grade.
Many universities and hospitals have explicit "no sponsorship at admin/specialist staff levels" policies.

**Apply the full +10 ONLY if:**
- The JD or careers page explicitly mentions sponsorship-eligibility, OR
- h1bdata.info confirms LCA filings at this specific job title / grade level in past 2 years, OR
- The institution is on the verified short-list of sponsor-friendly cap-exempt employers
  (UCLA Health, Columbia at L14+, Johns Hopkins at L4+, Kaiser NW, Providence — confirmed historically)

**Apply +5 cap-exempt with sponsorship-flag-pending if:**
- The institution is cap-exempt by classification but sponsorship pattern at this grade is uncertain.
- Examples that often DON'T sponsor at IC/Specialist grade: Harvard FCU, MIT admin staff, Stanford GSE staff,
  smaller universities and community colleges.

**Apply +0 if:**
- The JD explicitly states "no sponsorship" or "must be authorized without sponsorship."

#### Guardrail 2 — Consulting Exception Is CONDITIONAL ON SCOPE

`+3` consulting exception (for Senior/Manager titles at Big4/MBB) applies ONLY when the role's
actual scope is in Jamie's experience domain.

**Apply the +3 ONLY if:**
- Big4/MBB Senior Associate OR Senior Consultant OR Manager, AND
- Scope is People Advisory / Talent Strategy / Org Design / Change Management / People Programs, AND
- Jamie's actual experience covers the core scope (not just title fit)

**DO NOT apply the +3 if:**
- Scope is HR M&A Transactions / Due Diligence (Jamie has none)
- Scope is HRIS Implementation (Workday/SAP/Oracle — Jamie has no platform exp)
- Scope is Sales/Revenue Operations consulting (off-profile)
- Scope is Tax Advisory / Risk / Audit (off-profile)

**Reason:** Big4 hiring managers screen for relevant project experience FIRST. The title-exception
gets the resume past the bot filter but doesn't help at the human-screen stage if the core scope
doesn't match.

#### Guardrail 3 — Hard YOE Gaps Cannot Be "Offset" By Warm Intros

If JD states minimum YOE (e.g., "5 years required") and Jamie's actual YOE is 2+ years below that minimum,
**do not score above 60** regardless of:
- USC alumni warm intro availability
- Cap-exempt status
- Perfect title fit
- Personal connection at the company

**Warm intros help get a resume read** when YOE is within 1 year of stated minimum.
**Warm intros do NOT override** a 2+ year YOE gap at most companies (utilities, hospitals, regulated
industries, government, established corporates). At small startups and rapidly-growing scale-ups
YOE flexibility is higher, but those rarely sponsor H1B for non-tech roles.

#### Guardrail 4 — ★☆☆ Required Skills As Primary Function = Auto-PASS Signal

Per `preferences.md`: when a JD lists any of these as a **REQUIRED** (not preferred) qualification,
it's a strong PASS signal — even if other parts of the JD seem like a fit:

- Multi-state employment compliance
- Payroll administration
- Benefits administration as primary function
- HRIS platform management (Workday/SAP/Oracle HCM admin/implementation)
- Employee relations casework as primary function
- Investigation skills as primary function
- Compensation/total rewards as primary function
- Recruiting/TA as primary function
- Change management requiring Prosci/ADKAR cert

**Auto-cap score at 65 if any ★☆☆ skill appears as required primary function.**
**Auto-cap score at 60 if 2+ ★☆☆ skills appear as required.**
**Auto-PASS (max score 55) if 3+ ★☆☆ skills appear as required.**

Do NOT soft-pedal these as "learnable" or "stretch." Competing candidates WILL have these skills,
and Jamie's H1B-runway window cannot afford applications where she's screened out at the
resume-review stage.

#### Guardrail 5 — Reposted/100+ Applicants Rule (Apr 30) Still Applies

Per `preferences.md` LinkedIn Competition Filter:
- Reposted (any version) = HARD SKIP unless H1B-confirmed AND honest skill match ≥70%
- 100+ applicants (single signal) = HARD SKIP
- Remote + 1 other signal = HARD SKIP
- 2+ of 3 signals = HARD SKIP

The May 12 timeline overlay allows "1 signal OK if H1B-confirmed AND skill match ≥70%" — but the
≥70% threshold must be the HONEST match per the guardrails above, not the inflated match.

#### Guardrail 6 — Verdict Mapping

Final score after all modifiers (cap 100, floor 0):

| Score | Verdict | Action |
|-------|---------|--------|
| 85+ | GO | Apply this week; tailor resume + outreach |
| 70-84 | STRETCH | Apply only with referral OR if H1B-confirmed AND strong scope match |
| 60-69 | STRETCH-borderline | Apply only if cap-exempt + warm intro + scope match all true |
| <60 | PASS | Do not apply; would waste runway. Note as monitor-weekly if title is otherwise good. |

#### Guardrail 7 — Sanity Check Before Reporting

Before delivering the verdict, ask yourself:
1. If I read this JD without knowing the score, would I genuinely tell Jamie "you're a strong fit"?
2. Would the hiring manager's first-pass resume screen actually advance Jamie to phone screen?
3. Is the score driven by the ROLE/SCOPE fit, or by score-modifiers (cap-exempt, H1B-confirmed, alumni)?

If #3 is "by score-modifiers," subtract 10 from the final score. Score-modifiers should support a
real scope fit, not manufacture one.

---
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
