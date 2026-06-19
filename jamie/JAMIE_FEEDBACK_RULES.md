# 🎯 Jamie's Feedback Rules — CANONICAL (from 2026-05-28 review of first 5 applications)

> **This is the master rules doc.** Every skill (`/evaluate`, `/tailor`, `/outreach`, `/apply-pipeline`, autopilot)
> and every audit agent MUST follow these. Jamie reviewed the first 5 auto-submitted applications and
> gave detailed feedback. These are her words, encoded. When in doubt, this file wins.

---

## 🔓 ACCESS LEVEL — FULL SUBMISSION AUTHORITY (David, 2026-06-15, STANDING)

> David granted full, standing authorization to DRIVE APPLICATIONS TO ACTUAL SUBMIT (not just stage).
> Applies to every run + every skill until David revokes it. **Goal: SUBMIT eligible roles, end-to-end.**

**AUTHORIZED autonomously (no asking):**
- **Create accounts** on any ATS using Jamie's email (`jamiecheng0103@gmail.com`) + the shared password in
  `~/Downloads/job_password.txt`. If a site needs different rules, alter the pw AND **save the new
  credential** (vault / `jamie/account_registry.json`; never commit the secret).
- **Log into** existing accounts; **type the password** into login/signup fields (explicitly authorized).
- **Email verification / OTP** — read the code from Jamie's Gmail via `workspace-mcp` and complete it.
- **Bypass passive bot-protection** — "protected by reCAPTCHA" badges, invisible reCAPTCHA v3 — proceed.
- **Click the final Submit** once the form is filled + screenshot-verified.

**THE ONE HARD STOP — interactive/physical CAPTCHA only:** an "I'm not a robot" checkbox you must tick,
an image-grid/slider/press-and-hold puzzle. Fill up to it, screenshot, leave for the human. Everything
short of an actively-operated bot-gate is authorized.

**BE RELENTLESSLY PERSISTENT (David 2026-06-15):** if one fill method fails, try another — different
selectors, the Apply-CTA click, the direct ATS API, type-to-filter+Enter on react-selects, **and
Claude-in-Chrome (browser MCP) for custom dropdowns / account / iframe forms** where blind CDP selectors
fail. Don't give up at the same quality bar. Quality gates below still bind (no fabrication, tailored
resume, truthful sponsorship=Yes, screenshot-review before Submit, write SUBMITTED.json + confirmation).

## 📍 DISCOVERY PRIORITY #1 — PORTLAND-LOCAL OR REMOTE (David, 2026-06-15, STANDING)

> When searching for NEW roles, **Portland-local (Portland/Beaverton/Hillsboro/Vancouver WA metro) OR
> fully-remote-US roles are the ABSOLUTE highest priority** — rank them first, surface them first,
> build them first. Seattle/relocation roles are secondary; onsite-elsewhere is lowest. This outranks
> the prior tier ordering for discovery. (Sponsorship + truth rules still gate everything.)
>
> **Canonical source files Jamie confirmed:**
> - Master resume: `Downloads/Jamie (Yi-Chieh) Cheng's Resume_2026.pdf` (mirrored in `jamie/resume.md`)
> - Canonical cover letter template: `resume_bank/Cover Letter_Jamie (Yi-Chieh) Cheng_Roblox.pdf`
> - Resume base HTML: `resume_bank/Resume_Base_Template_2026-03-27.html`
> - 26 tailored resume variants + 5 cover letters in `resume_bank/`

---

## 0. 🚨 NO FABRICATION — TRUTH IS THE TOP PRIORITY (Jamie feedback 2026-06-10 — OVERRIDES EVERYTHING)

> This rule outranks every other rule, including keyword-matching and fit-maximizing. A weaker-but-true
> application always beats a stronger-but-false one. Jamie reviews every package; a single invented claim
> destroys her trust and could cost her credibility in an interview. When forced to choose between
> "matches the JD better" and "is true," **TRUE WINS, every time.**

### The rule (applies to resumes, cover letters, outreach, essays, form answers — EVERYTHING)
1. **Never write a claim Jamie cannot back up.** Every accomplishment, responsibility, metric, skill,
   relationship, and framing must trace to a real, verifiable source: `jamie/resume.md`,
   `jamie/content_library.md`, or `jamie/profile_compact.md`. If it is not in those files, Jamie did not
   tell us she did it — do **not** assert it.
2. **Do not re-describe a real experience as something it isn't to fit the JD.** The classic failure
   (2026-06-10, Cambia): ODN Oregon is **pro bono OD diagnostic consulting** — a team of professionals
   helping NGOs with leadership structure, decision-making, people-culture, and strategic-plan issues
   via interviews + data analysis. It is **NOT** "community building," **NOT** "ERG management," **NOT**
   "member events / volunteer-leader coordination / professional-network growth." Stretching the *true
   description* of a job into JD-flavored language you can't source is fabrication, even when the
   employer name and dates are correct.
3. **Adjacent ≠ same.** Program management, OD consulting, and engagement-data work are adjacent to
   ERG/community/culture-program work, but they are different. Name the real skill; do not relabel it as
   the JD's skill.
4. **Honesty about gaps is mandatory and good.** If the JD's core asks for experience Jamie lacks
   (e.g., direct ERG management), say so plainly to Jamie. Surfacing a gap is a feature, not a failure —
   it is what keeps her out of interviews she'd be caught flat in. The `/evaluate` honest-match score
   must reflect real overlap, not keyword overlap.
5. **When unsure, ASK — never guess.** If you cannot confirm from the source files whether Jamie did a
   thing, do not write it. Stop and ask Jamie a direct question (plain text, no menus). "I'm not sure
   whether X is true of your experience — did you do X?" is always the right move. Guessing to keep the
   pipeline moving is never acceptable.
6. **Banned-content list still applies** (see §2): the "$340K / 17 launches" composite is hallucinated —
   never use it. Default metric is "78% program enrollment rate."
7. **The skills/tools section contains ONLY what Jamie actually has (Jamie 2026-06-18).** Tailoring =
   surfacing what Jamie *truly has* in the canonical files (`resume.md` / `content_library.md`), re-angled
   toward the role. The rule is simple and general: a tool/skill belongs on the resume **if and only if it
   is in Jamie's canonical skills vocabulary** — if she genuinely used it, it belongs; if it isn't there,
   leave it out. The violation is **inventing** a tool to match a JD keyword, never the tool itself. For
   example, **Jira** does not appear in `content_library.md`, so adding "Jira" to match a JD is fabrication
   and must be removed — but Jira is just an instance of the rule, not a special-cased blacklist: the same
   logic applies to any tool not in her vocabulary. If a JD names a tool/skill Jamie doesn't have, you LEAVE
   IT OUT — do not invent a new line, bullet, or skill to satisfy a JD. Adding anything genuinely new to her
   vocabulary requires asking Jamie first — every time.
8. **NO clichés, NO JD-copy-paste (Jamie 2026-06-18 — applies to summary, bullets, cover, outreach).**
   Do not lift the JD's phrasing and paste it into Jamie's materials, and do not use clichés. That is lazy,
   fake-sounding tailoring and Jamie can spot it instantly. Instead: look at what Jamie *actually* has in the
   canonical source and **gracefully adapt it** toward the role in her own voice. Hit the JD's underlying
   IDEAS using HER real words — never mirror its vocabulary to seem like a fit. Truth + her voice over
   surface keyword-matching, always.

### The fact-check gate (HARD — every agent and the orchestrator must run it)
Before ANY resume / cover letter / outreach / essay / form-answer is written to disk or shown to Jamie,
the writer AND a reviewer must verify, claim by claim:

- [ ] **Every sentence is sourced.** For each claim, name the source file + the real experience it comes
      from. If a claim cannot be sourced, delete it or flag it to Jamie — do not ship it.
- [ ] **No experience is mislabeled.** ODN = OD diagnostic consulting (two separate projects, see §0.2 &
      §2). InGenius = program/L&D enablement. NextGen/Vestas = work-sample HRBP/OD. Kronos = HR intern.
      Each is described as what it actually was.
- [ ] **No invented relationships or activities** (no "coordinated volunteer leaders," "built a
      community," "ran ERGs," "managed a team," "led M&A integration," etc. unless `resume.md` supports it —
      most of these are explicitly flagged as DON'T-claim in `resume.md`).
- [ ] **Metrics are real** (only `content_library.md` figures; banned composite absent).
- [ ] **Gaps are disclosed**, not papered over with JD vocabulary.

If the gate fails, the orchestrator sends the work back to the agent with the specific failing claims and
the true source text, and re-checks. Nothing ships until the gate passes.

### How the orchestrator (main model) must operate this
- **Brief first:** When dispatching any sub-agent that writes Jamie-voice content, the dispatch prompt MUST
  include this §0 rule and the relevant true descriptions from `resume.md` — quote the "What Jamie actually
  does" + "DON'T claim" notes for every experience the agent will touch. Do not assume the agent will read
  the files; hand it the ground truth.
- **Quality-gate after:** When agent results return, the orchestrator does NOT trust them. Read the actual
  produced text (open the .md / .json), run the fact-check gate above against `resume.md`/`content_library.md`,
  and only then show Jamie. If any claim fails, send it back to the agent with the correction, or fix it
  directly, and re-verify. The main model is the last line of defense before Jamie sees anything.
- **This is self-imposed and non-negotiable.** "The agent said it was done" is not verification. Reading the
  output and checking it against source is verification.

---

## 1. RESUME SUMMARY (top intro) — KEEP IT BROAD

❌ **WRONG (too niche):** "ensuring HRIS data accurate," "managing LMS systems," any single narrow task.
Niche framing makes Jamie look like she can do ONE thing, not her full skill set.

✅ **RIGHT (broad + high-level):** Capture her general skill set. Use the master-resume summary as the anchor:

> "I'm Jamie—a curious, people-loving (97% extrovert!) **Organization & Talent Development** professional who thrives on **solving problems through data analysis**, **developing programs grounded in evidence**, and **collaborating with stakeholders for sustainable impact**. Expect me to always be seeking ways we can improve people experience—through human-centered, data-driven approaches."

**Tailoring rule:** Swap the role-title noun to match the JD's function — but keep the THREE broad pillars:
1. solving problems through **data analysis**
2. developing programs **grounded in evidence**
3. **collaborating with stakeholders** for sustainable impact

### ⭐ CLOSING SENTENCE — only the "we can ___" verb phrase flexes (Jamie 2026-06-18)
Keep the stem and the tail FIXED: *"Expect me to always be seeking ways we can ___ — through human-centered,
evidence-based approaches."* **Customize ONLY the "we can ___" clause** to fit the team/role, truthfully:
- People Ops / EX → "improve the people experience"
- Ops-heavy role → "optimize operational work"
- OD role → "achieve organizational effectiveness"
- L&D / talent development → "support people's growth" / "enable people to do their best work"
- Sales Enablement → "enable sales teams to succeed"
- …or any honest fit for that team. The tail ("through human-centered, evidence-based approaches") never changes.
(Do NOT swap the whole sentence — only the verb phrase after "we can". This is the §0.8 graceful-adapt rule applied.)

### ⭐ "97% extrovert!" — KEEP IT (Jamie 2026-06-18)
The "(97% extrovert!)" parenthetical stays in the summary by default — it shows her personality and is true.
Only drop it in a rare special case where the role clearly wouldn't want it (e.g. a very formal/conservative
context) — and FLAG that to Jamie first rather than silently cutting. Default = keep.

### ⭐ TITLE NOUN MUST STAY A BROAD UMBRELLA (Jamie feedback 2026-05-29 — applies to ALL future resumes)
The self-title Jamie gives herself must be a **big-umbrella term**, never a niche single-function label.
- ❌ TOO NICHE: "Employee Experience professional," "HRIS Analyst," "LMS Administrator," "Learning Coordinator"
- ✅ BROAD UMBRELLA — pick the ONE that best fits the JD (the *title itself* stays broad; just choose the most JD-relevant broad term):
  - **People & Organizational Development professional** (broadest — People/HR/OD/L&D roles)
  - **Strategic Program Manager** (product/program-PM-framed roles)
  - **People Program Manager** (bridges her real title + People target; strong all-rounder)
  - Or a new broad umbrella if it fits better — but it must read as an umbrella, not a single task.
- **Rule of thumb:** if the noun describes ONE function or ONE task, it's too niche — widen it.

Built In's summary ("building the infrastructure that lets employees trust the company") is the model
of good breadth — Jamie explicitly approved it. Aurora's "analytical organizer with a growth mindset"
opener is also the gold standard for the cover letter closer (see §6).

### ⭐ AGGRESSIVE KEYWORD SWAPPING (Jamie feedback 2026-05-29 — applies to ALL future resumes)
Scan the JD for its operative keywords and work them into bullets where TRUTHFUL and relevant. Common ones
to watch for and Jamie's truthful hooks for each:
- **operations / logistics** → InGenius "program logistics … and operations"
- **communication / communication strategy** → InGenius "refining communication strategies"; Vestas HR newsletter
- **new hires / onboarding** → Vestas "Optimize onboarding processes for new hires" (KEEP the phrase "new hires")
- **delivery / program positioning / value proposition** → InGenius "delivery strategy," "program positioning/value proposition"
- **cross-functional teams** → InGenius: she works with **Marketing, Tech, and Sales** teams — name them when the JD values cross-functional work
- **documentation / SOPs** → InGenius "creating documentation," "hosting" materials
Use the exact JD phrasing when Jamie genuinely did the thing. Never invent; these are all real to her work.

---

## 2. EXPERIENCE BULLETS — COUNT IS FIXED

| Experience | Bullet count | Notes |
|---|---|---|
| ODN Oregon (Organization Development Network) | **2-4 bullets** | TWO separate projects (see below) — may use 3-4 if both projects need coverage. |
| InGenius Prep (Program Enablement Manager) | **exactly 4** | |
| NextGen Healthcare | **exactly 4** | NEVER delete bullets to save space |
| Vestas Wind Systems | **exactly 4** | |
| Kronos Research | **exactly 4** | |

**HARD RULE:** Never drop a bullet point to fit the page. Always 4 for every experience except ODN.
If space is tight, tighten wording — do NOT delete bullets.
**Only SWAP a bullet** when you have a more JD-relevant variant from `content_library.md`. Swapping ≠ deleting.

### ⭐ BULLET REORDERING BY RELEVANCE (Jamie feedback 2026-05-29 — all future resumes)
Within each experience, **lead with the most JD-relevant bullet.** E.g. for People/EX roles, put
"Analyze 2,000+ employee experiences…" FIRST at NextGen because it reads most relevant. Reorder freely;
the bullet set is fixed but the ORDER should surface the strongest-matching accomplishment first.

### ⭐ ODN = TWO SEPARATE PROJECTS — NEVER MIX THEM IN ONE BULLET (Jamie feedback 2026-05-29)
ODN Oregon work spans **two distinct, unrelated projects.** Each bullet must stay within ONE project —
do NOT blend sentences/metrics across the two.
- **Project 1 — Absenteeism / leave-cost diagnosis (HR client):** Facilitated CEO/HR discovery + stakeholder
  interviews to diagnose absenteeism drivers; **upskilled/empowered the HR team to analyze and quantify
  leave data** (audited 300+ leave cases, ~$362K in leave costs) to refute cost assumptions and drive
  policy redesigns + first-aid training.
- **Project 2 — NGO leadership decision-making & accountability (completely different client):** Working with
  a leadership/direction team at NGOs facing confusion + glitches in cross-functional processes. Ran **focus
  groups + 1:1 semi-structured interviews** to understand the problems; **analyzed qualitative data to surface
  themes around decision-making and accountability**; used deep-dive diagnosis to address process ambiguity
  and inefficiency and challenge the team to change.
- You MAY use 3-4 ODN bullets total to cover both projects (e.g. 2 per project), or add a focus-group bullet
  if relevant to the JD. Just keep each bullet about ONE project only.

### Specific bullet feedback:
- **InGenius engagement research:** Fine to mention, but do NOT over-emphasize — it was a small side project.
- **InGenius real scope (use these keywords when JD-relevant):** the programs she runs involve **communication
  strategies, working with Marketing / Tech / Sales teams, program logistics, delivery, operations, program
  positioning / value proposition,** and creating + hosting documentation. Name the specific teams when the JD
  values cross-functional collaboration. All truthful — use freely.
- **Company name:** It is **"Organization Development Network (ODN) Oregon"** — NOT "Transition Projects"
  and NOT "ODN Oregon" alone in a way that loses the full name.

---

## 3. EDUCATION — Wesleyan ALWAYS includes Relevant Coursework

- **USC:** MS in Applied Organizational Psychology (GPA 3.95) + Relevant Coursework line
- **Wesleyan University:** BA in Psychology and Education Studies (GPA 4.00) + **ALWAYS include the
  Relevant Coursework line** (Educational Psychology, Practicum in Education Studies, Psychological Testing,
  Learning and Motivation). Earlier runs sometimes dropped Wesleyan coursework — never do that.

---

## 4. SKILLS — COMPREHENSIVE, grouped, JD-aware

**Principle:** List MORE than the JD requires (shows breadth), but remove genuinely irrelevant niche tools.

**Always list (foundational — regardless of JD):**
- Microsoft Office (Word, PowerPoint, Excel)
- Data Analysis (Excel, Google Sheets, SPSS)
- Project Management tools (Asana, Airtable)

**List only if JD mentions or it's relevant:**
- Niche knowledge-mgmt tools like **Notion, SharePoint** — ONLY if the JD names them (not foundational, so don't pad with them)
- HRIS specifics (SAP, Rippling, ADP), ATS (Greenhouse), LMS (Canvas, Moodle) — match to JD

**Canonical skills block (from master resume) — grouped into 5 lines:**
```
HR Systems: HRIS (SAP, Rippling, ADP) · ATS (Greenhouse) · LMS (Canvas, Moodle)
Data & PM Tools: Data Analysis (Excel, Google Sheets, SPSS) · Project Management (Asana, Airtable) · CRM (HubSpot)
Productivity: Knowledge Management (SharePoint, Notion) · AI Tools (ChatGPT, Gemini) · Microsoft Office (Word, PowerPoint)
Languages: English (fluent) · Mandarin Chinese (native) · Spanish (basic)
Certifications: HRCI Human Resource Associate Certificate (in progress)
```

**Rule:** Cross-reference the JD's required tools and make sure every one Jamie HAS is listed. Don't under-list.

---

## 5. LOCATION IN HEADER — match the role's office city

**Decision rule:**
- If the role's office is **Portland/remote** → header reads `Portland, OR (Open to Remote or Relocation)`
- If the role's office is in a **specific city (e.g., Pittsburgh, PA for Aurora Program Manager)** →
  header reads `Pittsburgh, PA` (the role's city), so recruiters see her as local/in-area.
- Pick whichever of {Portland, OR | the role's city} makes the recruiter believe she'll be in the area.

**This is a CHANGE from the old "always Portland, OR" rule.** Now: location follows the role's base city
when the role is clearly tied to one office. (ODN + InGenius work-location stays `Remote, USA` in the
experience entries themselves — that rule is unchanged.)

---

## 6. COVER LETTER — use the CANONICAL TEMPLATE (confirmed 2026-05-29)

**CANONICAL FORMAT FILE:** `jamie/cover_letter_template.html` (saved from the newest real letter,
`tailored_resumes/RRD_..._Cover-Letter_2026-05-12.html`). The pipeline renderer `render_pdfs.py →
build_cover_html()` now reproduces this exact layout. Older `resume_bank/*Roblox.pdf` etc. confirm the
same structure but the RRD HTML is the authoritative current format.

**VISUAL LAYOUT (the renderer produces this automatically):**
- Cream header band (#f5ede0), centered "Jamie Cheng" + 2-line tagline
- Two-column body: left sidebar (phone / Portland, OR / Open to Relocation / email / LinkedIn) + right justified letter
- "Dear [Company] Hiring Team," salutation (company name in salutation OK; NO full address block)
- Cursive signature ("Jamie Cheng") + printed name ("Jamie (Yi-Chieh) Cheng")
- Tagline line 2 varies by role: "Dedicated to Driving Individual and Organizational Development" (OD/L&D)
  vs "Dedicated to Improving People/Employee Experience" (EX/People Ops)

**CLOSING PARAGRAPH (confirmed 2026-05-29 — Jamie's verbal feedback wins over the older generic close):**
The final paragraph is the **org-psych "how I work" methodology** (see below in this section), NOT the
older generic "I would welcome the chance to bring my skills..." close. This is Jamie's differentiator.

### Structure (follow exactly):
**Header block (centered):**
```
Jamie Cheng
A Solution-focused, Data-driven, and People-oriented Professional
Dedicated to Improving People Experience
```
**Left sidebar / contact:** phone · "Remote, open to relocation" (or role city if local) · email · LinkedIn

**Date** → **"Dear Hiring Team,"**
- ❌ Do NOT write the company name + city as a physical address block. Just date + "Dear Hiring Team," (or "Dear Hiring Manager,").
- ❌ Do NOT list "Chicago, IL" or any company location in the letter.

**Paragraph 1 (opener) — ONE belief sentence + bridge to role:**
- Open with the signature pattern: "**[Domain]** isn't just about **[surface-level thing]**—from my experience,
  it's about **[Jamie's real belief: a continuous cycle of collecting insights, analyzing data, and refining
  solutions through cross-functional collaboration]**."
- Jamie's actual belief to weave in: *many problems are solved through a closer look at data + more
  cross-functional collaboration.* Tie that belief to what the role is really about (e.g., "it's not just
  about keeping the system updated — it's about building people strategy driven by real data, constant
  analysis, and cross-functional collaboration").
- Then ONE quick sentence on her background + what she brings, ending with the role + company.
- ❌ Do NOT write a full paragraph theorizing about what the role is. ONE quick sentence about the role/function, then pivot to her background.

**Paragraphs 2-4 — ONE paragraph per past experience (her preferred structure):**
- One paragraph each for the most relevant 2-3 experiences (e.g., Vestas → NextGen → current InGenius role).
- Each paragraph tells that job's story: what she did + the skill it showcased. Bold the key skill phrases.
- Keep it grounded in what the JD actually values.

**Final paragraph — the org-psych "how I work" close (Jamie's signature differentiator):**
- This is the paragraph Jamie specifically wants. Frame her **MS in Applied Organizational Psychology** as the
  lens for HOW she works — the scientific method applied to people problems:
  1. She uses **data collection + analysis** to diagnose what's actually wrong in operations / where people struggle
  2. She uses **people + stakeholder-collaboration skills** to propose cross-functional solutions
  3. She continues using **data skills to track key metrics** to ensure progress + success
- Frame: "This is how I approach work — uniquely grounded in my background in organizational psychology (MS, USC)."
- Optionally end with the approved closer style: "As an **analytical organizer with a growth mindset**, [company]'s
  mission to [X] and the [role challenge] are both draws..." (the Aurora closer Jamie loved — broad, ties to
  mission without being cliché or over-flattering).

**Bold formatting:** Bold the high-value keyword phrases throughout (like the Roblox sample does).

### Relocation / commitment language:
- ❌ Do NOT write "I am fully committed to relocating to [city]" or over-commit.
- ✅ Either say something light ("I'm excited about the opportunity") OR just rely on the "open to relocation"
  checkbox in the application form. Don't belabor relocation in the letter.
- ❌ Do NOT say "I applied to N roles N days ago" or reference prior applications — not relevant, drop it.

### Role-specific phrasing:
- Don't highlight a tool/task Jamie only used at user-level (e.g., "managing LMS systems"). Use a broader
  framing instead (e.g., "managing learning systems to support employee growth").

---

## 7. OUTREACH EMAILS — role-focus, verified recipients, real timeframe

### Recipient verification (HARD RULE — we got this wrong twice):
- **ALWAYS verify the person CURRENTLY works at the company** via their live LinkedIn before drafting.
  - Jessica Redeman had left Roivant (caught). Kaitlyn Major-Hale does NOT work at Built In (she's at Google) —
    so do not frame her as a Built In contact. Match the person to the right company/context.
- If you can't confirm current employment, don't draft outreach for that person.

### Tone + content (from Jamie's edits):
- ✅ Open by noting she applied to the role and wanted to personally reach out. Good.
- ❌ Do NOT talk about the company's subsidiary/holding-company structure. Jamie doesn't know it well and it feels impersonal/researched-but-fake.
- ✅ Focus on **what the role does and how it aligns with her background**, grounded in what the JD actually says.
  Example: "I was particularly drawn to the employee-relations complexity that requires careful handling and
  cross-functional collaboration — it reminds me of the work I did at Vestas."
- ✅ Peer-curiosity framing: "As a fellow People Operations practitioner, I'd love to hear what it looks like
  day-to-day on your team — what are some exciting opportunities and some of the challenges?"
- ✅ Offer a concrete timeframe: "If you're open to a brief chat, I'd really appreciate it — I have some time
  in the next two weeks if you're free."
- ❌ Do NOT fabricate that Jamie "followed how the organization has..." — she didn't. Never claim research/following she didn't do.

### Senior-leader (e.g., Head of People) version:
- Lead with: she's a People + OD professional with a background in [X], and she's drawn to organizations
  where People is a strategic lever, not just operational — "and it sounds like that's the case at [company]."
- "I would be honored to connect — no agenda beyond learning about [the team's challenges and exciting opportunities]."
- Offer the 2-week timeframe. Keep it shorter and more deferential than peer outreach, but still NOT about org structure.

---

## 8. PERSONAL INFO / DEMOGRAPHICS (confirmed 2026-05-28)

- **Gender identity:** Female / Woman
- **Racial/ethnic background:** Asian
- **Hispanic/Latino:** No
- **Veteran status:** Not a protected veteran
- **Disability:** No
- **Work authorization:** Yes
- **Sponsorship required:** Yes (HONEST — always; never lie)
- **Email:** jamiecheng0103@gmail.com · **Phone:** +1-213-700-3831

(Central config: `jamie-autopilot/lib/jamie_demographics.py`)

---

## 9. AUDIT-AGENT CHECKLIST (every application must pass before submit)

Audit agents MUST verify ALL of these and flag any failure.

**🚨 GATE 0 — TRUTH (run FIRST, see §0; a failure here blocks the whole package):**
- [ ] Every claim in resume/cover/outreach/essays is sourced to `resume.md` / `content_library.md` / `profile_compact.md`
- [ ] No experience is mislabeled (ODN = OD diagnostic consulting, NOT community/ERG/network-building)
- [ ] No invented relationships, activities, team management, or metrics
- [ ] **No invented skill/tool** added to match the JD (§0.7). The skills section = ONLY tools in Jamie's
      canonical vocabulary (`content_library.md`). Grep the resume/cover for any tool NOT in that vocabulary —
      if present and unsourced, remove it. (Jira is the known example: not in `content_library.md`, so it must
      never appear — but the check is general, any out-of-vocabulary tool fails.)
- [ ] **No clichés, no JD-phrasing copy-pasted** (§0.8). Read the summary/bullets/cover: does any line mirror
      the JD's vocabulary or read as a cliché? If yes, rewrite in Jamie's real words from the canonical source.
- [ ] Gaps vs the JD's core are disclosed to Jamie, not hidden behind JD keywords
- [ ] Orchestrator has READ the actual output (not just trusted the agent) and checked it against source

**Resume:**
- [ ] Summary is BROAD (no niche single-task framing) + uses the 3 pillars (data / evidence-based programs / stakeholder collaboration)
- [ ] Company name "Organization Development Network (ODN) Oregon" is correct (NOT "Transition Projects")
- [ ] ODN has 2-3 bullets; every other experience has exactly 4 bullets (none deleted)
- [ ] Wesleyan includes the Relevant Coursework line
- [ ] Skills are comprehensive: Microsoft Office + Data Analysis + PM tools always present; JD-named tools all listed; no irrelevant padding (Notion/SharePoint only if JD-named)
- [ ] Header location = role's city if role is city-based, else Portland OR
- [ ] No invented numbers (only content_library.md figures; the "$340K / 17 launches" composite is BANNED)
- [ ] The 78% metric reads **"78% program enrollment rate"** by DEFAULT. Use "78% client conversion rate" ONLY when the role is product/sales-focused (Jamie feedback 2026-05-29).
- [ ] Self-title is a BROAD umbrella (People & Organizational Development professional / Strategic Program Manager / People Program Manager), never a niche single-function label.
- [ ] ODN bullets keep the two projects separate (absenteeism-diagnosis vs NGO-leadership-accountability) — never blended.
- [ ] JD keywords (operations, logistics, communication, new hires, delivery, etc.) swapped in where truthful.
- [ ] One page

**Cover letter:**
- [ ] Header = "Jamie Cheng" + tagline; "Dear Hiring Team," (NO company address/city block)
- [ ] Para 1 = ONE belief sentence (data + cross-functional) + ONE role sentence, not a theory paragraph
- [ ] Paras 2-4 = one paragraph per past experience
- [ ] Final para = org-psych scientific-method "how I work" (diagnose w/ data → collaborate on solution → track metrics)
- [ ] Bold keywords throughout
- [ ] No relocation over-commitment, no "applied N days ago"
- [ ] No user-level tool over-claims (no "managing LMS systems" as a headline)

**Outreach:**
- [ ] Recipient CURRENTLY works at the company (LinkedIn-verified)
- [ ] Role-focused, NOT company-structure
- [ ] Peer-curiosity tone + concrete 2-week timeframe offer
- [ ] No fabricated "I followed your org" claims

---

## 10. CHANGELOG

- **2026-05-28:** Initial creation from Jamie's review of first 5 applications (Aurora People PM, Pacific Seafood,
  Built In, Roivant, Aurora HR Gen). Demographics switched to truthful. Cover template anchored to Roblox sample.
  Location-by-role-city rule added. ODN naming bug documented. Bullet-count rule fixed.
- **2026-06-10:** Added **§0 NO FABRICATION** (top-priority rule) + **Gate 0 — TRUTH** to §9, after the Cambia
  package re-described ODN Oregon as "ERG / community building." Codified: every claim must be sourced; adjacent
  ≠ same; disclose gaps; ask-don't-guess; orchestrator must brief agents with ground truth up front AND read +
  fact-check agent output against source before Jamie sees it (self-imposed quality gate). Mirrored into
  `CLAUDE.md` and `jamie-autopilot/CLAUDE.md`. (Codex `AGENTS.md` layer retired 2026-06-10.)
