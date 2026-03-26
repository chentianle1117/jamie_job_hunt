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

### Step 7 — Iterate

Jamie WILL have feedback. Common patterns:
- "That sounds too corporate" → dial back to her original wording, just reorder
- "Can you make bullet X hit [keyword] harder?" → find a natural way to incorporate it
- "That's too long" → trim without losing the metric/impact
- "I like the original better" → revert and explain why you suggested the change

This is a back-and-forth process. Stay responsive and don't over-edit.
