---
name: tailor
description: >
  Tailor Jamie's resume for a specific job description. Use when Jamie says "tailor my resume",
  "help me with my resume for this job", "which bullets should I use?", "customize resume",
  or after /evaluate recommends GO. Selects best bullet variants, suggests wording changes,
  and provides a complete recommended bullet set that fits on one page.
argument-hint: "<paste job description or reference the job just evaluated>"
---

## Stage 2: Resume Tailoring

You are helping Jamie select and fine-tune resume bullets for a specific application.

### Step 1 — Load Context

Read these files:
1. `jamie/content_library.md` — ALL bullet variants per role, self-intro versions, "what makes me stand out" blocks
2. `jamie/resume.md` — current default resume (what's on the PDF now)
3. `jamie/preferences.md` — specifically the "Resume Tailoring Rules" section
4. **If a similar company/role exists in `resume_bank/`** — read that PDF to see how Jamie
   previously tailored for a similar role. This is the best reference for her actual preferences.
   Examples: `resume_bank/Resume_...Nike.pdf` for retail/ops roles,
   `resume_bank/Resume_...L&D.pdf` for learning-focused roles,
   `resume_bank/Resume_...HR.pdf` for HRBP roles, etc.

### Step 2 — Understand the Target JD

If `$ARGUMENTS` contains a job description, use it.
If not, ask Jamie to paste it or reference which job from the current conversation.

Extract:
- **Key requirements** the JD emphasizes (ranked by prominence)
- **Keywords** that appear repeatedly (these are what ATS and hiring managers scan for)
- **Tone** of the JD (startup casual? corporate formal? mission-driven?)

### Step 3 — Select Bullet Variants

For each role in Jamie's resume, `jamie/content_library.md` has multiple variant sets:
- **Core variants** — general purpose
- **Program Management emphasis**
- **L&D/Operations emphasis**
- **Vendor/Program Management emphasis**
- **Engagement/HR emphasis**

Select the variant set per role that best matches the JD. Then within that set, pick the
4 strongest bullets (Jamie's resume has 4 bullets per role to stay on one page).

**Decision framework:**
1. Which variant set has the most natural keyword overlap with the JD?
2. Within that set, which 4 bullets demonstrate the most relevant accomplishments?
3. Do any individual bullets from OTHER variant sets fit better than the weakest bullet in the chosen set?

### Step 4 — Fine-Tune Wording

This is the critical step. Jamie's #1 complaint about AI resume help is that it sounds **too cliche**.

**Rules:**
- DO naturally incorporate 3-5 key terms from the JD into existing bullet language
- DO reorder bullets so the most relevant one comes first under each role
- DO suggest small wording tweaks (swap a verb, add a qualifier) to better align
- DO NOT rewrite bullets from scratch — these are Jamie's words about her real experience
- DO NOT stuff every JD keyword into every bullet — that's what makes it sound fake
- DO NOT use phrases like "drove strategic transformation", "spearheaded cross-functional synergies", "leveraged holistic approaches" unless she literally did that specific thing
- DO NOT make all bullets sound the same — vary sentence structure and opening verbs

**The balance:** Hit the KEY IDEAS the JD is looking for (e.g., "program management at scale",
"data-driven decision making", "stakeholder collaboration") rather than copying its exact phrases.
The reader should think "this person has done the work" not "this person copied our JD into their resume."

### Step 5 — Check One-Page Constraint

Jamie's resume MUST stay on one page. Each role gets exactly 4 bullet points.
The layout is fixed:
- Header + summary (3 lines)
- 5 roles × (title/company line + 4 bullets)
- Education (2 schools)
- Projects & Awards (3 lines)
- Skills (3 lines)

If your suggested bullets are longer than the originals, flag it:
"This bullet is ~15 chars longer than the original — may push the page. Consider trimming: [suggestion]"

### Step 6 — Deliver Recommendations

Format your response as:

```
## Resume Tailoring for: [Company] — [Job Title]

### Emphasis: [which variant set / hybrid]

### Transition Projects (OD Consultant)
1. [bullet — note if changed from current and why]
2. [bullet]

### InGenius Prep (Program Enablement Manager)
1. [bullet — note which variant set this came from]
2. [bullet]
3. [bullet]
4. [bullet]

### NextGen Healthcare (OD Intern)
1. [bullet]
...

### Vestas (HRBP Assistant)
1. [bullet]
...

### Kronos Research (HR Intern)
1. [bullet]
...

### Summary Line Suggestion
[If the JD calls for a specific emphasis, suggest a tweak to Jamie's summary paragraph]

### Self-Intro Version to Use
[Reference which self-intro from content_library.md fits best for cover letter / email]

### Changes from Current Resume
- [List each change: "InGenius bullet 3: swapped from L&D emphasis to PM emphasis because..."]
- [Total changes: X of 20 bullets modified]
```

### Step 7 — Apply Changes to HTML Resume

After presenting recommendations and getting Jamie's approval on the bullet selections,
**directly edit `jamie/resume.html`** with the changes.

**How to mark changes:**
Wrap every changed piece of text in `<span class="changed">...</span>`. This highlights
it in yellow in the browser so Jamie can see exactly what was modified.

Example:
```html
<!-- BEFORE -->
<li>Conduct needs assessments with 25+ global stakeholders to identify learning gaps and design 3 new educational programs</li>

<!-- AFTER (changed bullet, highlighted) -->
<li><span class="changed">Establish cross-functional processes and documentation for 70+ staff, streamlining operations and reducing onboarding time by 75%</span></li>
```

**What to change in the HTML:**
1. **Summary line** — update identity label, keywords, and approach per the tailoring playbook
2. **InGenius job title** — swap the title text in the `.job-title` div
3. **Bullet text** — replace `<li>` content for each swapped bullet
4. **Skills section** — update the technical skills line per the role-type recipe
5. **Location line** — update "Open to Remote" vs "Portland" vs "Seattle"
6. **Transition Projects bullets** — swap to Pair A or Pair B as appropriate

**Mark ALL changes with `class="changed"`** — even small wording tweaks. Jamie needs to
see every single modification.

**After editing, tell Jamie:**
```
Resume HTML updated with [X] changes (highlighted in yellow).

To preview:
  open jamie/resume.html    (Mac — opens in browser)

You'll see a red dashed line showing where page 1 ends.
Yellow highlights show every change I made.

→ Review the preview. Tell me if anything needs adjusting.
→ When you're happy, say "export" and I'll generate the PDF.
```

### Step 8 — Live Preview Workflow

Jamie opens `jamie/resume.html` in her browser (Chrome recommended). She will see:

1. **Yellow highlights** on every changed bullet, title, or skills line
2. **Red dashed "PAGE 1 ENDS HERE" guide** showing the one-page boundary
3. The actual layout with fonts, spacing, and formatting

**If content overflows past the red line:**
- Tell Jamie which bullet is too long and suggest trimming
- Or suggest removing a less-relevant bullet entirely
- Edit the HTML, save, and Jamie refreshes the browser to see the update instantly

**Live editing loop:**
```
Jamie: "Bullet 3 is too long, it's pushing below the line"
Claude: [trims the bullet in resume.html]
Claude: "Trimmed — refresh your browser to check"
Jamie: [refreshes] "Looks good now"
Claude: "Ready to export?"
```

VS Code users: Install the "Live Server" extension for auto-refresh on save.
Or just Cmd+R in the browser after each edit.

### Step 9 — Save Tailored Version to Resume Bank

Before exporting, save the tailored HTML as a versioned copy:

```bash
cp jamie/resume.html "resume_bank/Resume_Jamie_2026_{Company}_{Date}.html"
```

Example: `resume_bank/Resume_Jamie_2026_Notion_2026-03-27.html`

This preserves each tailored version for future reference (the playbook auto-distill
can read these later to update patterns).

### Step 10 — Export to PDF

When Jamie says "export", "looks good", or "generate PDF":

**On Mac:**
```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless --no-pdf-header-footer \
  --print-to-pdf="jamie/resume_tailored.pdf" \
  "file://$(pwd)/jamie/resume.html"
```

**On Windows:**
```bash
"/c/Program Files/Google/Chrome/Application/chrome.exe" \
  --headless --disable-gpu --no-pdf-header-footer \
  --print-to-pdf="jamie/resume_tailored.pdf" \
  "file:///$(pwd)/jamie/resume.html"
```

After export:
1. Remove all `<span class="changed">` wrappers from the HTML (clean it up)
2. Copy the PDF to resume_bank too: `resume_bank/Resume_Jamie_2026_{Company}_{Date}.pdf`
3. Show Jamie: `"PDF exported to jamie/resume_tailored.pdf — open to verify."`

### Step 11 — Iterate

Jamie WILL have feedback. Common patterns:
- "That sounds too corporate" → dial back to her original wording, just reorder
- "Can you make bullet X hit [keyword] harder?" → find a natural way to incorporate it
- "That's too long, it's past the red line" → trim without losing the metric/impact
- "I like the original better" → revert and explain why you suggested the change
- "The spacing looks off" → adjust font size or margin in the CSS (small increments: 0.1pt)

This is a back-and-forth process. Stay responsive and don't over-edit.
Each time you edit the HTML, Jamie refreshes her browser to see the result instantly.
