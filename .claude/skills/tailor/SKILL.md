---
name: tailor
description: >
  Tailor Jamie's resume for a specific job description. Use when Jamie says "tailor my resume",
  "help me with my resume for this job", "which bullets should I use?", "customize resume",
  or after /evaluate recommends GO. Selects best bullet variants, applies keyword annotations,
  and produces a JSON content file that the resume viewer renders with diff UI.
argument-hint: "<paste job description or reference the job just evaluated>"
---

## CRITICAL — Git + Working Directory Rules

**Before doing anything else:**
1. Run `git pull` before starting any tailoring session
2. Never create branches — commit directly to `main`
3. After completing a session: commit with a descriptive message and `git push`

---

## NEW ARCHITECTURE: JSON Content + Unified Viewer

The resume system uses a **single HTML viewer** (`resume_viewer.html`) that loads JSON content
files. The agent edits ONLY the JSON (~80 lines) — never the viewer HTML.

```
resume_viewer.html          ← THE viewer app (never edited during tailoring)
resume_data/base.json       ← default resume content (starting point for new tailoring)
tailored_resumes/*.json     ← one JSON per tailored resume (what the agent edits)
tailored_resumes/index.json ← manifest for the dropdown selector
```

---

## Step 0 — Start the Preview Server (if not already running)

Jamie needs a local server to preview resumes. Start it automatically:

```bash
# Check if server is already running on port 8080
lsof -i :8080 > /dev/null 2>&1 || python3 -m http.server 8080 &
```

This runs in the background. Jamie never needs to do this manually.

---

## Step 1 — Load Context

Read these files:
1. `jamie/content_library.md` — bullet variants per role + the **Tailoring Playbook** section
2. `jamie/preferences.md` — Resume Tailoring Rules + Strict Fit Scoring Rules
3. **If a similar role exists in `tailored_resumes/*.json`** — read it for prior tailoring decisions

---

## Step 2 — Create the JSON Content File

Copy the base template and name it per the convention:

```bash
cp resume_data/base.json "tailored_resumes/Company_Jamie (Yi-Chieh) Cheng_Role-Title_YYYY-MM-DD.json"
```

Example: `tailored_resumes/Nike_Jamie (Yi-Chieh) Cheng_Store-Ops-Specialist_2026-04-05.json`

---

## Step 3 — Select Bullet Variants Using the Tailoring Playbook

Read the **Tailoring Playbook** section in `jamie/content_library.md`. It has decision rules
for 7 role types. For the target JD:

1. Identify the role type (L&D, PM, HR/HRBP, Consulting, Talent Mgmt, Ops, Tech)
2. Apply ALL dimensions from the playbook simultaneously:
   - Summary identity + keywords + approach
   - InGenius job title
   - Bullet emphasis set (A–H)
   - Transition Projects pair (A or B)
   - Vestas/NextGen/Kronos variants
   - Technical skills line
   - Location line

---

## Step 4 — Edit the JSON

Edit the JSON file with:

### Bullet text
Replace bullet `text` fields with the selected variants. Add `{kwg|keyword}` inline markup
for keywords that should be highlighted in the viewer.

**Keyword markup syntax:**
- `{data|data analytics}` → renders as highlighted "data analytics" in the Data/Analytics color
- Groups: `data`, `coord`, `cross`, `ex`, `tools`, `prog` (or custom per JD)

### Change metadata
For each modified bullet, add:
- `"change": "swap"` — bullet was replaced from a different variant set
- `"change": "reorder"` — bullet was moved to a different position (add `"was": 3`)
- `"change": "word"` — specific words were swapped within the bullet
- `"original"` — the text before the change (shown in Changes mode)
- `"jd"` — array of JD requirement IDs this bullet addresses (e.g., `["jd1", "jd2"]`)
- `"reason"` — why this change was made (shown in Changes mode)

### JD panel
Populate the `jd` section with:
- `meta` — company, role, location, salary
- `sections` — structured JD content with `{kwg|keyword}` markup
- Each requirement gets an `id` (jd1, jd2...) and `changeType` that links to resume bullets

### Change log
Write the `changeLog` array with all modifications documented.

### Keyword groups
Update `keywordGroups` labels to match the JD's emphasis areas.

---

## Step 5 — Update the Index Manifest

Add the new JSON to `tailored_resumes/index.json`:

```json
{"file": "Company_Jamie (Yi-Chieh) Cheng_Role-Title_YYYY-MM-DD", "label": "Company — Role (Date)"}
```

---

## Step 6 — Give Jamie the Preview Link

Tell Jamie:

```
Resume tailored — [X] bullets modified, [Y] reordered.
Preview: http://localhost:8080/resume_viewer.html?resume=Company_Jamie%20(Yi-Chieh)%20Cheng_Role-Title_YYYY-MM-DD

Open this link in Chrome. You'll see:
  • Keywords mode (default): colored highlights showing JD keyword coverage
  • Changes mode: yellow/blue/red highlights showing what was modified + why
  • Clean mode: plain resume for final review
  • Red dashed line: page 1 boundary — content below it overflows

Tell me if anything needs adjusting.
```

---

## Step 7 — Iterate on Feedback

Jamie will give feedback. Edit the JSON (not the viewer HTML).

Common feedback and responses:
- "Too cliche" → revert to closer-to-original wording in the JSON
- "Bullet X is too long" → trim the text in the JSON, Jamie refreshes browser
- "I like the original better" → restore the original text, remove the `change` metadata
- "Spacing looks off" → adjust `meta.pageMargins` in the JSON (per-resume override)

Each edit is ~1 line in the JSON. Jamie refreshes browser to see the update instantly.

---

## Step 8 — Export to PDF

When Jamie says "export" or "looks good":

**On Mac:**
```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless --no-pdf-header-footer \
  --print-to-pdf="tailored_resumes/Company_Jamie (Yi-Chieh) Cheng_Role-Title_YYYY-MM-DD.pdf" \
  "http://localhost:8080/resume_viewer.html?resume=Company_Jamie%20(Yi-Chieh)%20Cheng_Role-Title_YYYY-MM-DD"
```

**On Windows:**
```bash
"/c/Program Files/Google/Chrome/Application/chrome.exe" \
  --headless --disable-gpu --no-pdf-header-footer \
  --print-to-pdf="tailored_resumes/Company_Jamie (Yi-Chieh) Cheng_Role-Title_YYYY-MM-DD.pdf" \
  "http://localhost:8080/resume_viewer.html?resume=Company_Jamie%20(Yi-Chieh)%20Cheng_Role-Title_YYYY-MM-DD"
```

**HARD REQUIREMENT:** The exported PDF must have consistent margins on all four sides
(top, bottom, left, right). Verify after export. If margins are uneven, adjust
`meta.pageMargins` in the JSON and re-export.

After export, tell Jamie where the PDF is saved.

---

## Formatting Rules (from CLAUDE.md — apply to ALL resumes)

- **Consistent margins:** Top/bottom/left/right must be even and balanced. Default: 0.35in 0.45in 0.35in 0.45in
- **Section headers:** `border-bottom: 1px solid #000` only — NO `border-top`
- **Font sizes:** body 9.5pt, bullets 9.2pt, summary 9pt
- **One page rule:** MUST fit on exactly one page — the viewer shows a red zone for overflow
- **Bullet characters:** Use literal `•` text nodes (the viewer adds these automatically)
- **No bullet wrapping:** Every bullet must stay on a single line. If it wraps, trim it.
- **Keyword padding:** `padding: 0 !important` on `.kw, .jd-kw` in print CSS (already in viewer)

---

## Anti-Cliche Rules (CRITICAL)

- DO NOT try to 100% match every keyword in the JD
- DO NOT use phrases like "drove strategic transformation" unless she actually did
- DO NOT over-choreograph — hit key IDEAS, not exact JD phrases
- When in doubt, keep Jamie's original wording — it's already strong
- The `{kwg|keyword}` markup highlights coverage without changing the wording
