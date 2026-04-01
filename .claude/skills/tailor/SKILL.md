---
name: tailor
description: >
  Tailor Jamie's resume for a specific job description. Use when Jamie says "tailor my resume",
  "help me with my resume for this job", "which bullets should I use?", "customize resume",
  or after /evaluate recommends GO. Selects best bullet variants, applies word-level JD keyword
  swaps, and produces a tailored HTML with diff UI (toolbar, change-log, highlights).
argument-hint: "<paste job description or reference the job just evaluated>"
---

## ⚠️ CRITICAL — Git + Working Directory Rules

**Before doing anything else:**
1. Work ONLY in `/Users/jamiecheng/jamie_job_hunt/` (main repo, `main` branch)
2. Run `git pull` before starting any tailoring session
3. Never create branches — commit directly to `main`
4. After completing: commit with descriptive message and `git push`

**Do NOT work in any worktree path.** If `pwd` contains `worktrees`, run `cd /Users/jamiecheng/jamie_job_hunt` first.

---

## 🤖 Gemini-First Architecture (PRIMARY PATH)

> Claude does NOT read Jamie's profile files directly for tailoring.
> Dump content_library + preferences + resume.md + JD into Gemini Pro's 1M context.
> Gemini can only propose bullets that exist verbatim in the files — hallucination is structurally blocked.
> Claude: build prompt → run Gemini → grep-verify every bullet → apply to HTML → present to Jamie.

### Step 1 — Get the JD + Create Tailored File

Get the JD text (from $ARGUMENTS, prior /evaluate context, or ask Jamie to paste).

Create the tailored file from the master template:
```bash
cp jamie/resume.html tailored_resumes/Company_RoleType_YYYY-MM-DD.html
```
**Never edit `jamie/resume.html` directly.** All edits go to the `tailored_resumes/` copy.
Reference: `tailored_resumes/Superhuman_WX-Coordinator_2026-03-27.html` — correctly completed example.

Check if a similar role exists in `tailored_resumes/` — if so, note the prior decisions for context.

### Step 2 — Run Gemini Tailoring Plan (fat-context)

```bash
JD_TEXT="<fetched or pasted JD>"

cat jamie/content_library.md \
    jamie/preferences.md \
    jamie/resume.md > /tmp/tailor_context.txt
echo "===== JOB DESCRIPTION =====" >> /tmp/tailor_context.txt
echo "$JD_TEXT" >> /tmp/tailor_context.txt

cat /tmp/tailor_context.txt | gemini -m gemini-2.5-pro -p "
You are tailoring Jamie Cheng's resume. Her bullet variants are in content_library above.
Her tailoring rules are in preferences above. Her current resume is in resume.md above.

CRITICAL RULES — violations will be caught by grep and rejected:
1. Every proposed bullet MUST exist verbatim (or near-verbatim) in content_library above
2. Every word-level swap original MUST exist in resume.md above
3. NO clichés: spearheaded, leveraged, drove strategic, synergies, cross-functional impact
4. Vary sentence structure — not every bullet starts the same way
5. Hit key IDEAS from JD — not exact phrases. Reader thinks 'she did this work', not 'she copied our JD'

Output EXACTLY this format:
## Resume Tailoring for: [Company] — [Job Title]
### Template Used: [name from resume_templates/]
### Emphasis: [variant set reasoning — why this set fits this JD]
### Summary: [1-line description of overall tailoring approach]

### InGenius — [variant set name]
1. [exact bullet text from content_library] — [same / swapped from X / reordered from #N]
2. [bullet] — [note]
3. [bullet] — [note]
4. [bullet] — [note]

### NextGen
1. [bullet] — [note]
2. [bullet] — [note]
3. [bullet] — [note]
4. [bullet] — [note]

### Vestas
1. [bullet] — [note]
2. [bullet] — [note]
3. [bullet] — [note]
4. [bullet] — [note]

### Skills: [proposed skills line]

### Word-level swaps:
- [Section/Role]: '[original phrase from resume.md]' → '[revised phrase]' — [JD reason in one clause]

### Changes Summary: [X] swaps 🟡 / [Y] reorders 🔵 / [Z] word swaps 🔴
"
GEMINI_EXIT=$?
```

### Step 3 — Grep Grounding Check (MANDATORY before presenting to Jamie)

Every bullet and swap must be verified against source files. Near-zero token cost.

```bash
# Verify each proposed bullet — grep a distinctive phrase from it
# Example: Gemini proposes "reduced onboarding time-to-productivity by 75%"
grep -i "75%" jamie/content_library.md          # found? ✅  not found? ❌ flag + replace

# Example: Gemini proposes "managed 20+ vendor relationships"
grep -i "vendor" jamie/content_library.md       # found? ✅  not found? ❌

# Verify each word-level swap original exists in current resume
grep -i "original phrase" jamie/resume.md       # found? ✅  not found? ❌ invented

# Cliché scan
echo "$GEMINI_OUTPUT" | grep -iE "spearhead|leverage|synerg|drove strategic|cross-functional impact|thrilled|passionate about"
# Any match → remove that phrase before presenting
```

**If grep finds no match for a bullet:**
→ Replace with nearest real variant from content_library (grep for the role section)
→ Or re-prompt once: *"Bullet '[X]' not found in content_library. Replace with a real variant from the [InGenius/NextGen/Vestas] section above."*
→ Grep-verify the replacement too

**If Gemini unavailable:** `GEMINI_EXIT != 0` → use Claude native fallback at bottom of this file.

### Step 4 — Present Plan to Jamie (chat first, before touching HTML)

Show the verified tailoring plan. Wait for Jamie's approval or "go ahead" before Step 5.

### Step 5 — Apply Changes to HTML with Full Diff System

Edit `tailored_resumes/Company_RoleType_YYYY-MM-DD.html`.

**Three change types:**

#### 🟡 Whole bullet swapped
```html
<li class="changed"
    data-original="[exact original bullet text]"
    data-reason="[why this variant fits the JD — JD reasoning, not just description]">
New bullet text here</li>
```

#### 🔵 Reordered
```html
<li class="reordered"
    data-was="[original position, e.g. 3]"
    data-reason="[why this order serves the JD]">
Same bullet text here</li>
```

#### 🔴 Word-level swap
```html
<li>...improved <span class="keyword"
    data-original="analytics"
    data-reason="JD uses exact phrase 'data analysis' 4 times — terminology alignment">
analysis</span>...</li>
```

`data-reason` must explain JD reasoning — not just describe the change:
- BAD: `data-reason="Changed 'analytics' to 'analysis'"`
- GOOD: `data-reason="JD uses exact phrase 'data analysis' 4 times — terminology alignment"`

#### JD Panel (right side):
Replace `.jd-panel` div with actual JD text. Use:
- `<span class="jd-kw" data-kwg="GROUP">keyword</span>` — color-coded keyword (groups: data/coord/cross/ex/tools/prog)
- `<mark class="jd-hl jd-swap" id="jdN">requirement</mark>` — anchor for 🟡 swap
- `<mark class="jd-hl jd-order" id="jdN">requirement</mark>` — anchor for 🔵 reorder
- `<mark class="jd-hl jd-word" id="jdN">requirement</mark>` — anchor for 🔴 word swap
- `<span class="jd-reason">→ which resume bullet connects here</span>` — Changes mode only

`id="jdN"` on JD marks must match `data-jd="jdN"` on resume bullets (connection lines).
Update `.kw-legend` to match actual keyword groups used.

**Keyword highlight CSS spec:**
- Base `.kw` tint: `#b2dfdb` / `#ffe0b2` / `#e1bee7` / `#c8e6c9` / `#f8bbd0` / `#bbdefb`
- Base `.jd-kw`: colored text + `rgba(..., 0.18)` bg tint + 2px border-bottom
- Active `.kw.kw-active`: saturated solid + `color: #fff` + `outline: 2px solid`
- Active `.jd-kw.kw-active`: `rgba(..., 0.85)` bg + `color: #fff` + `outline: 2px solid`
- Dim non-active: opacity `0.2`
- Add `transition: background 0.15s, outline 0.15s`

#### Diff Toolbar:
```html
<div class="diff-version">
  📄 Tailored for: <strong>[Company] — [Job Title]</strong>
  <span class="diff-date">[Date]</span>
</div>
```

#### Change Log table (`#change-log`):
```html
<tr><td>[Location]</td><td class="tag-swap">🟡 bullet swap</td><td class="orig">[original]</td><td class="new">[new]</td><td>[JD reason]</td></tr>
<tr><td>[Location]</td><td class="tag-order">🔵 reorder</td><td class="orig">was #N</td><td class="new">now #M</td><td>[JD reason]</td></tr>
<tr><td>[Location]</td><td class="tag-word">🔴 word swap</td><td class="orig">[old]</td><td class="new">[new]</td><td>[JD reason]</td></tr>
```

#### Additional content rules:

**Location line** (`.header .contact`):
- Portland/Beaverton/Hillsboro/Vancouver WA → `Relocating to Portland, Oregon in May 2026`
- Seattle → `Relocating to Seattle, WA in May 2026`
- Remote / other / unclear → `Open to Remote or Relocation (US-based)` ← default

**Projects & Awards:**
- Consulting roles (firms, OD consulting, human capital advisory):
  - `<b>OD Consulting Project:</b> Informed <b>Elanco Animal Health</b>...`
  - `<b>Research Consulting Project:</b> Examined non-monetary factors... for <b>YouTube</b>...`
- All other roles: keep `<b>Consulting Projects:</b>` + `<b>Master's Capstone:</b>` labels

**Formatting constants (verify every copy):**
- Summary: no border, text-align center — `.summary { padding: ...; text-align: center; }` (no `border:` rule)
- Links: visible — `.header .contact a { color: #2a6496; text-decoration: underline; }`
- LinkedIn href: `http://www.linkedin.com/in/jamieyccheng`

### Step 6 — Export to PDF

```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless --no-pdf-header-footer \
  --print-to-pdf="tailored_resumes/Company_RoleType_YYYY-MM-DD.pdf" \
  "file://$(pwd)/tailored_resumes/Company_RoleType_YYYY-MM-DD.html"
```
Also copy to: `jamie/resume_tailored.pdf`

### Step 7 — PDF Quality Gates (MANDATORY — do not skip)

```
Gate 1: Single-line bullets — warn any bullet over ~112 chars (8.8pt Calibri limit)
         Trim: remove adjectives before cutting metrics or specifics. Re-export until all pass.
Gate 2: Work sample links present as <a class="work-sample" href="...">
         NextGen: https://drive.google.com/file/d/1Pefhv22MiK30tSu2SUvNYmNRncWPMNNy/view?usp=sharing
         Vestas:  https://drive.google.com/file/d/1iyPfCA75WA6XDGx_cMzP_E5CnWZ8EmVb/view?usp=sharing
Gate 3: One page — red dashed line in browser marks page 1 boundary
```

Tell Jamie gate results:
```
PDF exported — quality gates:
✅ Work sample links: present
✅ One page: confirmed
⚠️ Bullet 3 (InGenius) at 128 chars — trimming...
```

### Step 8 — Save and Index

1. PDF already at `tailored_resumes/Company_RoleType_YYYY-MM-DD.pdf`
2. Add entry to `tailored_resumes/INDEX.md`
3. Add entry to `resume_bank/` for future reference

### Step 9 — Iterate (Gemini handles revisions too)

Jamie WILL have feedback. Route every revision through Gemini + grep-verify.

```bash
# Extract only the relevant variant block — don't pipe full context again
grep -A 30 "INGENIUSPREP\|InGenius" jamie/content_library.md > /tmp/variants.txt
echo "Current bullet: $CURRENT_BULLET" >> /tmp/variants.txt
echo "Jamie's feedback: $FEEDBACK" >> /tmp/variants.txt

cat /tmp/variants.txt | gemini -m gemini-2.5-pro -p "
Revise this resume bullet based on Jamie's feedback.
Use ONLY the variant text shown above — no new accomplishments.
No clichés. Keep her voice. Under 112 chars. Return revised bullet text only."

# Grep-verify revision before writing to HTML
grep -i "KEY_PHRASE_FROM_REVISION" jamie/content_library.md
# Found → write to HTML. Not found → re-prompt or use nearest matching variant manually.
```

| Jamie says | You do |
|---|---|
| "too corporate" | Revert to original wording, just reorder |
| "make bullet X hit [keyword] harder" | Gemini re-draft with that keyword constraint |
| "too long, past the red line" | Trim without losing metric/impact |
| "I like the original better" | Revert, note why you suggested the change |
| "sounds like AI" | RED FLAG — re-prompt Gemini with "simplify, use her exact phrasing from content_library" |

After each HTML edit, Jamie refreshes Chrome directly (Cmd+R). Do NOT reference the preview panel.

---

## ⚠️ Fallback: Claude Native (when Gemini unavailable)

```bash
if [ $GEMINI_EXIT -ne 0 ]; then
  echo "⚠️ Gemini unavailable — tailoring natively"
fi
```

Claude reads these files directly:
1. `jamie/content_library.md` — all bullet variants
2. `jamie/preferences.md` — tailoring rules, self-assessment
3. `resume_templates/TEMPLATES.md` — template → role type mapping
4. Prior tailored file for this role type (if exists in `tailored_resumes/`)

Then execute Steps 4-8 directly, applying the same rules:
- Only use bullets that exist in content_library
- No clichés, vary structure, hit key ideas not exact phrases
- Same HTML diff format, same quality gates
