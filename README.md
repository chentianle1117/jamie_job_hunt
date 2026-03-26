# Jamie's Job Search Assistant

An AI-powered job application toolkit built on [Claude Code](https://claude.com/claude-code) that helps Jamie (Yi-Chieh) Cheng find, evaluate, and apply to HR/OD/L&D roles. Combines automated job discovery with interactive application support — resume tailoring, networking outreach, and fit analysis.

---

## How It Works

```
                    TWO WORKFLOWS
                    ═════════════

  ┌─────────────────────────┐     ┌──────────────────────────────┐
  │   ORACLE PIPELINE       │     │   APPLICATION ASSISTANT       │
  │   (automated discovery) │     │   (interactive, on-demand)    │
  │                         │     │                               │
  │   David runs daily on   │     │   Jamie runs on her Mac       │
  │   Windows. Searches     │     │   when she finds a job she    │
  │   80+ job boards,       │     │   wants to apply to.          │
  │   filters by H1B/fit,   │     │                               │
  │   populates Notion DB,  │     │   /evaluate → fit analysis    │
  │   sends email digest.   │     │   /tailor   → resume bullets  │
  │                         │     │   /outreach → find contacts   │
  │   Trigger:              │     │   /apply-pipeline → all 4     │
  │   /jamie-job-search     │     │                               │
  └────────────┬────────────┘     └──────────────┬───────────────┘
               │                                  │
               └──────────┐    ┌──────────────────┘
                          ▼    ▼
                  ┌──────────────────┐
                  │  Google Sheets   │
                  │  (ground truth)  │
                  │                  │
                  │  Jamie updates   │
                  │  status, tracks  │
                  │  all apps here   │
                  └──────────────────┘
```

---

## Setup on Mac (Jamie)

### Prerequisites

- **Node.js 18+** — [download](https://nodejs.org/)
- **Google Chrome** — for browser-powered features
- **Anthropic account** — Pro, Max, Teams, or Enterprise plan
- **Git** — comes preinstalled on Mac

### Installation

```bash
# 1. Install Claude Code
npm install -g @anthropic-ai/claude-code

# 2. Clone this repo
git clone https://github.com/chentianle1117/jamie_job_hunt.git
cd jamie_job_hunt

# 3. Start Claude Code
claude
```

That's it. Claude automatically reads `CLAUDE.md` and knows who you are, where your files are, and how to help.

### Enable Chrome Browser Control (recommended)

This lets Claude navigate LinkedIn, read job postings from ATS pages, and help with applications directly in your browser.

```bash
# 1. Install "Claude in Chrome" extension from Chrome Web Store
#    https://chromewebstore.google.com/detail/claude/fcoeoabgfenejglbffodgkkbkcdhcgfn

# 2. Log into LinkedIn in Chrome (Claude uses your logged-in session)

# 3. Start Claude Code with Chrome enabled
claude --chrome
```

**Requirements:** Claude Code v2.0.73+, Chrome extension v1.0.36+, paid Anthropic plan.

**What Chrome mode enables:**
- Read full job descriptions from JS-rendered ATS pages (Greenhouse, Lever, Ashby, Workday)
- Browse LinkedIn People pages to find alumni and hiring managers
- Read LinkedIn profiles for personalized outreach
- Potentially fill application forms (Jamie reviews and submits)

Without `--chrome`, Claude still works — it just uses WebSearch instead of direct browser access.

---

## Skills (Slash Commands)

### `/evaluate` — Is this job a good fit?

Paste a job description or URL. Claude will:
1. Check hard constraints (H1B, seniority, location)
2. Verify sponsorship status against the H1B cache or via web search
3. Score fit against Jamie's self-assessment matrix
4. Return a **GO / STRETCH / PASS** recommendation with reasoning

```
> /evaluate
> [paste job description]

=== EVALUATION ===
Company:   Notion
Role:      Early Career People Projects
H1B:      Unknown ⚠️ — needs verification
Match:     ~72%
Verdict:   STRETCH — strong PM fit but remote role needs 80%+ match
```

### `/tailor` — Customize resume for this job

Selects the best bullet variants from Jamie's expanded resume library and fine-tunes wording:
- Picks from multiple emphasis sets (L&D, PM, HR, OD, Consulting)
- Adjusts summary line, job titles, skills section
- Checks against past tailored resumes in `resume_bank/`
- Ensures one-page fit
- **Never sounds cliche** — this is the #1 rule

```
> /tailor
> [reference the job just evaluated]

=== RESUME TAILORING ===
Emphasis:     Program Management
Changes:      7 of 20 bullets modified
Self-intro:   V3 — OD/EX Focus

ACTION ITEMS:
□ Open resume in InDesign
□ Swap InGenius bullets to PM emphasis set
□ Update skills line: add Asana, Airtable
□ Export new PDF
```

### `/outreach` — Find connections and draft messages

Searches for networking contacts and drafts personalized messages in Jamie's voice:
- Finds USC / Wesleyan alumni at the company
- Identifies hiring managers and team members
- Drafts LinkedIn connection requests (under 300 chars)
- Drafts follow-up emails using Jamie's actual templates
- With `--chrome`: can browse LinkedIn directly

```
> /outreach Nike

=== OUTREACH PLAN ===
Contact 1: Amanda Steele — Store Ops (LinkedIn)
  → Connection request drafted (287 chars)
Contact 2: [USC alum found via search]
  → Alumni template drafted
Sequence: Send requests today → Apply tomorrow → Follow up Day 3
```

### `/apply-pipeline` — Full 4-stage workflow

Runs all stages end-to-end with dashboards and checkboxes at each step:

```
=== APPLICATION PIPELINE ===

Job: Early Career People Projects @ Notion

  Stage 1: EVALUATE    [DONE]  GO — 78% match, P2 role
  Stage 2: TAILOR      [DONE]  7 bullets customized, PM emphasis
  Stage 3: OUTREACH    [DONE]  2 contacts found, messages drafted
  Stage 4: APPLY       [    ]  Pre-flight checklist ready

  → Review checklist and submit when ready.
```

---

## Repository Structure

```
jamie_job_hunt/
├── CLAUDE.md                        ← Auto-loaded every session (who Jamie is, how to help)
├── README.md                        ← You are here
│
├── jamie/                           ← Jamie's profile & reference files
│   ├── preferences.md               ← Hard constraints, role priorities, fit scoring
│   ├── content_library.md           ← Expanded resume bullets (multiple variants per role)
│   ├── resume.md                    ← Current resume (markdown)
│   ├── resume.pdf                   ← Current resume (formatted PDF)
│   ├── resume.html                  ← Editable HTML resume template
│   ├── outreach_templates.md        ← LinkedIn/email message templates in Jamie's voice
│   ├── h1b_verified.md              ← H1B sponsorship cache (50+ companies)
│   ├── watchlist.md                 ← 80+ target companies across 7 tiers
│   ├── search_strategy.md           ← Search queries by role priority
│   ├── application_tracker.md       ← Live Google Sheets URLs + static fallback
│   └── bible_verses.md              ← Daily encouragement verses
│
├── resume_bank/                     ← Past tailored resumes (20) + cover letters (5)
│   ├── Resume_..._Nike.pdf
│   ├── Resume_..._Roblox.pdf
│   ├── Resume_..._Mercer.pdf
│   ├── Cover Letter_..._Jamf.pdf
│   └── ...
│
├── .claude/skills/                  ← Claude Code skills (auto-discovered)
│   ├── evaluate/SKILL.md            ← /evaluate command
│   ├── tailor/SKILL.md              ← /tailor command
│   ├── outreach/SKILL.md            ← /outreach command
│   └── apply-pipeline/SKILL.md      ← /apply-pipeline command
│
├── pipeline/                        ← Oracle discovery pipeline (David's machine)
│   ├── SKILL.md                     ← Full 13-step pipeline definition
│   ├── run_oracle.ps1               ← Email + Telegram delivery script
│   └── scripts/                     ← Helper scripts
│
└── docs/                            ← Architecture & workflow documentation
    ├── ARCHITECTURE.md              ← Multi-agent pipeline architecture
    └── WORKFLOW_GUIDE.md            ← Operational guide
```

---

## Data Flow

### Live Application Tracker

Jamie's Google Sheet is the single source of truth for all applications:

```
Google Sheets "Job Search 2026"
        │
        │  WebFetch (live CSV export)
        ▼
Claude reads at start of /evaluate and /apply-pipeline
        │
        │  Checks: already applied? contacts? outreach status?
        ▼
Uses live data for duplicate detection and context
```

- **2026 tab** (gid=1018026840): Current year applications
- **2025 tab** (gid=0): Historical applications
- **Fallback**: Static snapshot in `jamie/application_tracker.md` if offline

### Resume Bank

When Jamie applies to a new job and creates a tailored resume:
1. She saves the PDF to `resume_bank/` with the company name
2. Next session, Claude detects the new file
3. Claude reads it and updates the tailoring playbook patterns
4. Future `/tailor` suggestions reference how Jamie actually adapts (not just guesses)

---

## Agent Behavior — Feedback Loop

Claude actively listens for Jamie's corrections and adapts in real time:

| Jamie says | Claude does |
|---|---|
| "too cliche" / "sounds fake" | Reverts to original wording, reduces keyword stuffing |
| "too formal" / "too corporate" | Shorter sentences, warmer vocabulary |
| "sounds desperate" / "too eager" | Removes urgency, more matter-of-fact |
| "sounds like AI wrote it" | Significantly simplifies, uses Jamie's own phrases |
| "I like the original better" | Reverts immediately, doesn't push |
| "skip to outreach" | Jumps ahead, notes what was skipped |
| "go back" | Returns to previous stage |
| "I don't want to apply" | Stops gracefully, no pressure |

**Key principle:** Every stage waits for Jamie's confirmation before advancing. Claude never auto-proceeds to the next step.

---

## Key Design Decisions

**Why not fully automate resume editing?**
Jamie uses InDesign for final layout with precise typographic control. Claude suggests specific text changes; Jamie makes the edits. An HTML resume template (`jamie/resume.html`) exists as an experimental alternative.

**Why Google Sheets over Notion for tracking?**
Jamie already updates Google Sheets for every application. It captures jobs from both the Oracle pipeline AND jobs she finds on her own. Claude reads it live via WebFetch.

**Why not auto-send LinkedIn messages?**
Outreach is personal. Claude drafts messages in Jamie's voice; she reviews and sends. The Chrome integration can pre-fill the message box, but Jamie always controls the send button.

**Why separate skills instead of one monolith?**
Jamie sometimes just wants to evaluate a job (30 seconds) without committing to the full pipeline. Individual skills let her use exactly what she needs. `/apply-pipeline` chains them when she wants the full treatment.

---

## For David (Pipeline Operator)

The Oracle discovery pipeline runs on David's Windows machine and requires:
- Notion MCP (for database access)
- Gmail MCP (for email delivery)
- Environment variables: `NOTION_TOKEN`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`

See `pipeline/SKILL.md` and `docs/ARCHITECTURE.md` for the full multi-agent architecture.

Trigger: `/jamie-job-search` (user-level skill, not in this repo)

---

Built with [Claude Code](https://claude.com/claude-code) by David & Claude
