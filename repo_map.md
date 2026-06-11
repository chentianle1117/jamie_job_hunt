# 🗺️ Job-Search Repo Map (single source of truth for the layout)

> Read this first if you're new to Jamie's job-search system. It explains the 3 GitHub repos,
> where each lives locally, and who owns what — so nothing gets duplicated or edited in the wrong place.
> Tooling: **Claude Code only** (the Codex/`AGENTS.md` dual-home layer was retired 2026-06-10).

## The 3 repos / 4 local folders

| Local folder | GitHub repo | Role / owns |
|---|---|---|
| `~/jamie_job_hunt` | `chentianle1117/jamie_job_hunt` | **Reference + skills repo** (one of two checkouts). Jamie's profile, resume, rules, the `/evaluate /tailor /outreach /apply-pipeline /sync` skills, tailored resumes, run packages. |
| `~/Agentic_Workflows_2026/oracle-job-search` | `chentianle1117/jamie_job_hunt` | **Same repo, second checkout** (was the macOS/Codex clone). Identical content — keep both in sync (see below). |
| `~/Agentic_Workflows_2026/jamie-autopilot` | `chentianle1117/jamie-autopilot` | **Pipeline code.** Overnight discover→tailor→audit→apply pipeline; account-creation + credential vault (`lib/`). |
| `~/Agentic_Workflows_2026/jamie-second-brain` | `chentianle1117/jamie-second-brain` | **Human-readable Obsidian vault.** Career notes, Voice & Story Bank, per-employer ground truth. Mirrors (not code). |

## ⚠️ The one gotcha: jamie_job_hunt and oracle-job-search are the SAME repo
Two local checkouts of one GitHub repo. They can silently drift if one is edited and the other isn't pulled.
**Rule: at the start of any job-search session, `git pull` in whichever checkout you're using.** Edit in one
place, push, and the other catches up on pull. Never hand-copy files between them.

## Who's the source of truth for what (no overlaps)

| Topic | Canonical file | Notes |
|---|---|---|
| Operating rules / how to help Jamie | `CLAUDE.md` (jamie_job_hunt) | RULE 0 lives at the top |
| No-fabrication + all review feedback | `jamie/JAMIE_FEEDBACK_RULES.md` | §0 is highest priority |
| Quick profile / go-pass facts | `jamie/profile_compact.md` | read FIRST; it's an excerpt |
| Ground truth on her experience | `jamie/resume.md` + `jamie/content_library.md` | "what she actually did / DON'T claim" |
| H1B sponsorship data | `jamie/h1b_verified.md` | **canonical**; profile_compact is just an excerpt |
| Autopilot pipeline runbook | `jamie-autopilot/pipeline-prompts/SKILL.md` | + `CLAUDE.md` in that repo |
| ATS accounts / passwords | macOS Keychain (`jamie-jobsearch-ats`) + `jamie-autopilot/jamie/account_registry.json` | passwords NEVER in git |
| Human-readable career notes | `jamie-second-brain/Work/Career/*` | intentional mirror of the above |

## Skills (Claude Code)
Canonical skill bodies: `~/jamie_job_hunt/.claude/skills/<name>/SKILL.md` for `evaluate, tailor, outreach,
apply-pipeline, sync`; the autopilot skill is in `~/.claude/skills/jamie-autopilot/`. (The old `.agents/skills/*`
Codex pointer copies were removed 2026-06-10.)
