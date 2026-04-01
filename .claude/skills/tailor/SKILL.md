---
name: tailor
description: >
  Tailor Jamie's resume for a specific job description. Use when Jamie says "tailor my resume",
  "help me with my resume for this job", "which bullets should I use?", "customize resume",
  or after /evaluate recommends GO. Selects best bullet variants, applies word-level JD keyword
  swaps, and produces a tailored HTML with diff UI (toolbar, change-log, highlights).
argument-hint: "<paste job description or reference the job just evaluated>"
---

## ⚠️ CRITICAL — Git + Working Directory Rules (HIGH PRIORITY)

**Before doing anything else:**
1. Work ONLY in `/Users/jamiecheng/jamie_job_hunt/` (main repo, `main` branch)
2. Run `git pull` before starting any tailoring session
3. Never create branches — commit directly to `main`
4. After completing a session: commit with a descriptive message and `git push`

**Do NOT work in any worktree path** (e.g. `.claude/worktrees/...`)

**Check your working directory:** If `pwd` returns anything containing `worktrees` or a branch name,
you are in the wrong place. Run `cd /Users/jamiecheng/jamie_job_hunt` to fix it before proceeding.

**The interface may show a branch name (e.g. "claude/objective-elbakyan")** — this is the worktree
the session was started in, not where files should be edited. Always confirm you are writing files
to `/Users/jamiecheng/jamie_job_hunt/` and not a worktree copy.

## ⚡ Token Efficiency Rules

1. **Read `jamie/profile_compact.md` first** — ~60 lines with all hard constraints, H1B quick
   reference, and fit scoring. Only read `preferences.md` or `h1b_verified.md` if compact is insufficient.
2. **`content_library.md` — let Gemini read it.** When `$GEMINI_OK = "true"`, do NOT read
   `content_library.md` yourself — Gemini has already processed it. Only read it directly
   if Gemini failed (`$GEMINI_OK = "false"`).
3. **Read the tailored file once before editing** — don't re-read the full HTML after each edit.

---

## Stage 2: Resume Tailoring

### Step 1 — Load Context

Read these files:
1. `jamie/content_library.md` — ALL bullet variants per role, self-intro versions
2. `jamie/preferences.md` — Resume Tailoring Rules section
3. `resume_templates/TEMPLATES.md` — which template maps to which role type
4. **If a similar role exists in `tailored_resumes/`** — read that HTML to see prior tailoring decisions

### Step 2 — Create the Tailored File

**`jamie/resume.html` is the source of truth for the full diff UI.**
It contains the complete three-mode toolbar (Changes / Keywords / Clean), change log, split-pane
JD panel, SVG connection lines, keyword group highlighting, and click-to-pin interaction.
**Never rebuild the UI from scratch.** Always copy from this file.

Create the tailored version:
```bash
cp jamie/resume.html tailored_resumes/Company_RoleType_YYYY-MM-DD.html
```

**Do NOT edit `jamie/resume.html` directly during tailoring.** All edits go to the `tailored_resumes/` copy.
The Superhuman version (`tailored_resumes/Superhuman_WX-Coordinator_2026-03-27.html`) is the reference
for a correctly completed tailored file.

### ⚡ Gemini Fat-Context Grounding (run AFTER Step 2, BEFORE Step 4)

After copying the tailored file, run Gemini with the full content library + JD.
This offloads the 10,000-token content_library.md read to Gemini's fat context window — saving Claude tokens and getting better bullet recommendations in one shot.

**How to run:**

```bash
# Write the JD to a temp file
echo "$JD_TEXT" > /tmp/jd_current.txt

# Run Gemini via Python wrapper (robust — no shell quoting issues, has timeout + retry)
python3 pipeline/gemini_run.py \
  --prompt "You are a resume tailoring assistant for Jamie Cheng, an OD/HR professional.

Using ONLY the bullet variants in content_library.md, recommend the best bullet selections for this job description.

Return these exact sections:
1. TEMPLATE: which template to use (base / EX-WX / PM / LD / HR-HRBP) and why
2. INGENIUS_VARIANT: which variant set (core / PM / L&D / vendor / engagement) and why
3. ODN_BULLETS: list 2 bullets to use (exact text from content_library.md)
4. INGENIUS_BULLETS: list 4 bullets to use (exact text from content_library.md), in recommended order
5. NEXTGEN_BULLETS: list 4 bullets to use (exact text from content_library.md), in recommended order
6. VESTAS_BULLETS: list 4 bullets to use (exact text from content_library.md), in recommended order
7. WORD_SWAPS: up to 5 specific word-level swaps (format: 'original phrase' -> 'new phrase' | reason: JD uses X)
8. SKILLS_LINE: recommended Technical Skills line content
9. SUMMARY: one summary sentence in Jamie's voice (no cliches)
10. GAPS: honest gaps between this JD and Jamie's experience

Rules:
- ONLY use bullet text that appears verbatim in content_library.md. Never invent bullets.
- WORD_SWAPS must be small changes (1-4 words), not full rewrites.
- SUMMARY must sound like Jamie, not a robot." \
  --context /tmp/jd_current.txt jamie/content_library.md jamie/preferences.md \
  --verify "audit 300+" "InGenius" \
  --cliche-check \
  > /tmp/gemini_output.txt 2>/tmp/gemini_err.txt

GEMINI_EXIT=$?
GEMINI_OK=$( [ $GEMINI_EXIT -eq 0 ] && echo "true" || echo "false" )
GEMINI_OUTPUT=$(cat /tmp/gemini_output.txt)
# Note: exit 2 means cliché found but output still printed — check stderr and fix SUMMARY manually
```

**Using Gemini's output:**
- If `$GEMINI_OK` = `"true"` (exit 0): use `$GEMINI_OUTPUT` as the bullet selection plan for Steps 4–5.
  If exit was 2 (cliché): output is still usable — just revert the SUMMARY to the closest self-intro from `content_library.md`.
  Spot-check 2–3 recommended bullets exist verbatim in `content_library.md`. If not found, fall back to Claude's own selection for that role only.
- If `$GEMINI_OK` = `"false"` (exit 1): skip Gemini entirely — read `content_library.md` directly and select bullets yourself.

**Do NOT skip Step 6 (present plan to Jamie before touching HTML)** even when using Gemini output.

---

### Step 3 — Understand the Target JD

Extract:
- **Key requirements** ranked by prominence
- **Keywords** that appear repeatedly (ATS + hiring manager scan targets)
- **Tone** (startup casual? corporate formal? mission-driven?)

### Step 4 — Select Bullet Variants

The chosen template already has a good starting set. Review each role and decide:
1. Does the template's InGenius variant set match this JD, or should you switch?
2. Should any bullets from a different variant set replace the weakest bullet?
3. What reordering within each role would put the most JD-relevant bullet first?

**Decision framework:**
1. Which variant set has the most natural keyword overlap with the JD?
2. Within that set, which 4 bullets demonstrate the most relevant accomplishments?
3. Do any individual bullets from OTHER variant sets fit better than the weakest?

### Step 5 — Fine-Tune Wording (Word-Level Swaps)

This is critical. Jamie's #1 complaint: **AI resume help sounds too cliche**.

**Rules:**
- DO naturally incorporate 3-5 key terms from the JD into existing bullet language
- DO reorder bullets so the most relevant one comes first
- DO suggest small wording tweaks (swap a verb, add a qualifier)
- DO NOT rewrite bullets from scratch — these are Jamie's words
- DO NOT stuff every JD keyword into every bullet
- DO NOT use "drove strategic transformation", "spearheaded cross-functional synergies", etc.
- DO NOT make all bullets sound the same — vary sentence structure

**Goal:** Hit the KEY IDEAS the JD looks for, not copy exact phrases. Reader should think
"this person has done the work" not "this person copied our JD."

### Step 6 — Deliver Recommendations (Chat First)

Present the tailoring plan before touching the HTML:

```
## Resume Tailoring for: [Company] — [Job Title]

### Template Used: [template name]
### Emphasis: [which variant set / hybrid]

### Summary: [proposed change]

### InGenius — [variant set used]
1. [bullet] — [note: same / swapped from X / reordered from #N]
2. [bullet]
3. [bullet]
4. [bullet]

### NextGen
1–4. [bullets with notes]

### Vestas
1–4. [bullets with notes]

### Skills
[proposed skills line]

### Changes Summary
- [X] bullet swaps (🟡)
- [Y] reorders (🔵)
- [Z] word-level swaps (🔴)
```

### Step 7 — Apply Changes to HTML with Full Diff System

After Jamie approves (or auto-proceed if she said "go ahead"), edit the tailored file
`tailored_resumes/Company_RoleType_YYYY-MM-DD.html` (NOT `jamie/resume.html`).

**Three change types — use the correct class for each:**

#### 🟡 Whole bullet swapped (different variant from content_library)
```html
<li class="changed"
    data-original="[exact original bullet text]"
    data-reason="[why this variant fits the JD better]">New bullet text here</li>
```

#### 🔵 Reordered (same text, moved to different position)
```html
<li class="reordered"
    data-was="[original position number, e.g. 3]"
    data-reason="[why this order serves the JD better]">Same bullet text here</li>
```

#### 🔴 Word-level JD keyword swap (verb/noun changed to match JD language)
```html
Before: <li>...improved <span class="keyword" data-original="analytics" data-reason="JD uses exact phrase 'data analysis'">analysis</span>...</li>
```

**IMPORTANT:** Every `data-reason` must explain the JD reasoning, not just describe the change.
- BAD: `data-reason="Changed 'analytics' to 'analysis'"`
- GOOD: `data-reason="JD uses exact phrase 'data analysis' 4 times — terminology alignment"`

#### Build the JD Panel (right side):

Replace the `.jd-panel` div content with the actual job description. Use these classes:
- `<span class="jd-kw" data-kwg="GROUP">keyword</span>` — color-coded keyword on JD side (same groups: data/coord/cross/ex/tools/prog)
- `<mark class="jd-hl jd-swap" id="jdN">requirement text</mark>` — anchor for swap change type (🟡)
- `<mark class="jd-hl jd-order" id="jdN">requirement text</mark>` — anchor for reorder change type (🔵)
- `<mark class="jd-hl jd-word" id="jdN">requirement text</mark>` — anchor for word swap (🔴)
- `<span class="jd-reason">→ explanation of which resume bullet this connects to</span>` — visible in Changes mode only

The `id="jdN"` on JD marks must match `data-jd="jdN"` on the corresponding resume bullets — this is what makes connection lines work.

Also update the `.kw-legend` to match the actual keyword groups used for this role.

**Keyword highlight CSS spec (use this exact spec — do NOT use the old faint pastel version):**
- Base `.kw` tint (always visible): `#b2dfdb` / `#ffe0b2` / `#e1bee7` / `#c8e6c9` / `#f8bbd0` / `#bbdefb`
- Base `.jd-kw`: colored text + `rgba(..., 0.18)` background tint + 2px border-bottom
- Active `.kw.kw-active`: saturated solid color with `color: #fff` (e.g. `#26c6da`, `#ffa726`, `#ab47bc`, `#66bb6a`, `#ec407a`, `#42a5f5`) + `outline: 2px solid`
- Active `.jd-kw.kw-active`: `rgba(..., 0.85)` background + `color: #fff` + `outline: 2px solid`
- Dim opacity on non-active: `0.2` (not `0.25`)
- Add `transition: background 0.15s, outline 0.15s` to both `.kw` and `.jd-kw`

#### Also update the Diff Toolbar at top of HTML:
```html
<div class="diff-version">
  📄 Tailored for: <strong>[Company] — [Job Title]</strong>
  <span class="diff-date">[Date]</span>
  ...
</div>
```

#### And build the Change Log table (`#change-log`):
```html
<tr><td>[Location]</td><td class="tag-swap">🟡 bullet swap</td><td class="orig">[original]</td><td class="new">[new]</td><td>[JD reason]</td></tr>
<tr><td>[Location]</td><td class="tag-order">🔵 reorder</td><td class="orig">was #N</td><td class="new">now #M</td><td>[JD reason]</td></tr>
<tr><td>[Location]</td><td class="tag-word">🔴 word swap</td><td class="orig">[old word]</td><td class="new">[new word]</td><td>[JD reason]</td></tr>
```

#### Additional content rules per tailoring:

**Location line** (in `.header .contact`):
- Role in Portland, OR (or suburbs: Beaverton, Hillsboro, Vancouver WA) → `Relocating to Portland, Oregon in May 2026`
- Role in Seattle, WA → `Relocating to Seattle, WA in May 2026`
- Remote / other relocation / unclear → `Open to Remote or Relocation (US-based)` ← default

**Projects & Awards section**:
- Consulting-related roles (consulting firms, OD consulting, human capital advisory): use two consulting project labels:
  - `<b>OD Consulting Project:</b> Informed <b>Elanco Animal Health</b>...` (NOT "Enhanced", NOT "Consulting Projects:")
  - `<b>Research Consulting Project:</b> Examined non-monetary factors... for <b>YouTube</b>...` (NOT "Master's Capstone:")
- All other roles: keep `<b>Consulting Projects:</b>` + `<b>Master's Capstone:</b>` labels as-is

**Formatting constants (verify on every tailored copy)**:
- Summary: **no border**, text-align: center — `.summary { padding: ...; text-align: center; }` (no `border:` rule)
- Links: **visible hyperlinks** — `.header .contact a { color: #2a6496; text-decoration: underline; }`
- LinkedIn `<a href="http://www.linkedin.com/in/jamieyccheng">` must be present with correct href

### Step 8 — Export to PDF

Export from the **tailored file** (not `jamie/resume.html`):

```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless --no-pdf-header-footer \
  --print-to-pdf="tailored_resumes/Company_RoleType_YYYY-MM-DD.pdf" \
  "file://$(pwd)/tailored_resumes/Company_RoleType_YYYY-MM-DD.html"
```

Also copy to: `jamie/resume_tailored.pdf` (for quick access)

### Step 9 — PDF Quality Gates (MANDATORY after every export)

Run these checks after every export. Do NOT skip.

#### Gate 1: Single-line bullets
Every bullet must fit on ONE line in the PDF. Run a character-count check:
```python
# Warn any bullet over ~112 chars (approximate single-line limit at 8.8pt Calibri)
```
If any bullet is too long → trim it, re-export, check again. Iterate until all pass.

**Trimming priority:** Remove adjectives before cutting metrics or specifics.

#### Gate 2: Work sample hyperlinks
`(Work Sample)` text on NextGen and Vestas must be clickable `<a>` tags:
- NextGen: `https://drive.google.com/file/d/1Pefhv22MiK30tSu2SUvNYmNRncWPMNNy/view?usp=sharing`
- Vestas: `https://drive.google.com/file/d/1iyPfCA75WA6XDGx_cMzP_E5CnWZ8EmVb/view?usp=sharing`

Verify these are present in the HTML as `<a class="work-sample" href="...">` before exporting.

#### Gate 3: One page
Check that the resume doesn't overflow. The red dashed line in the browser shows page 1 boundary.

**Tell Jamie the gate results:**
```
PDF exported — quality gates:
✅ Work sample links: present
✅ One page: confirmed
⚠️ Bullet 3 (InGenius) at 128 chars — may wrap. Trimming...
```

### Step 10 — Save and Index

1. Copy PDF to `tailored_resumes/Company_RoleType_YYYY-MM-DD.pdf`
2. Add entry to `tailored_resumes/INDEX.md`
3. Add entry to `resume_bank/` (for reference in future tailoring)

### Step 11 — Iterate

Jamie WILL have feedback. Stay responsive and don't over-edit.

| She says | You do |
|----------|--------|
| "too corporate" | Revert to original wording, just reorder |
| "make bullet X hit [keyword] harder" | Find natural way to incorporate it |
| "too long, past the red line" | Trim without losing the metric/impact |
| "I like the original better" | Revert, note why you suggested the change |
| "sounds like AI" | RED FLAG — significantly simplify, use her own phrases |

After each HTML edit, Jamie refreshes her browser (Cmd+R) to see the result.
Do NOT tell Jamie to check the preview panel — she refreshes Chrome directly.
