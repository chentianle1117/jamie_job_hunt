# AGENTS.md — Jamie's Job Search (oracle-job-search)

> **Entry file for OpenAI Codex** (Codex reads `AGENTS.md`; Claude Code reads `CLAUDE.md`).
> This repo runs on **both** Windows (David / Claude Code) and macOS (Jamie / Codex) from the
> SAME codebase. One source of truth; no fork.

## 0. Read this first
- **The canonical operating rules — Jamie's profile, the NON-NEGOTIABLE resume rules, outreach
  rules, file-naming, location rules, spacing rules, tone, feedback loops — live in `CLAUDE.md`
  in this repo.** Read `CLAUDE.md` and follow it exactly. It is tool-neutral; everything in it
  applies to Codex too, with the substitutions in §3 below.
- **The most important rule:** anything written in Jamie's voice (resume bullets, cover letters,
  outreach, essays) follows `jamie/JAMIE_FEEDBACK_RULES.md` + `jamie/jamie_voice_corpus.md` —
  her real phrasing, her real stories, never invented or inflated. Truth over polish.

## 1. Skills (how Jamie triggers work)
Codex skills live in `.agents/skills/<name>/SKILL.md` and are invoked with `/<name>` or `$<name>`:
- `/evaluate` — paste a JD/URL → fit analysis + H1B check + go/stretch/pass
- `/tailor` — tailor resume bullets + render PDF for a specific JD
- `/outreach` — find + draft networking messages
- `/apply-pipeline` — full evaluate→tailor→outreach chain
- `/sync` — commit + push
- `/jamie-autopilot` — overnight discovery+tailor+audit+package pipeline (in the **jamie-autopilot** repo)

Each Codex skill is a thin pointer to the canonical `.claude/skills/<name>/SKILL.md` body — read
that body and follow it. (Dual-home, shared body: editing the canonical body updates both tools.)

## 2. Run the pipeline (tool-neutral)
The mechanical stages are plain Python that any agent (or Jamie by hand) can run. The judgment
stages (fit, bullet selection, cover/outreach drafting, the adversarial audit) are done by the
agent per the skill bodies. Key scripts:
- `pipeline/gemini_run.py` — Gemini grounding (large-context fit analysis; cross-platform).
- `render_pdfs.py` — resume/cover PDF render (Playwright bundled Chromium; cross-platform; verify 1-page).
- `build_master_dashboard.py` — the review dashboard.
- Submitters + Patchright browser engine live in the sibling `jamie-autopilot/lib/`.

## 3. Codex / macOS substitutions (when following CLAUDE.md or a skill body)
- **Browser / "With Chrome" / get_page_text** → use the **Codex Chrome extension** (reads
  Jamie's logged-in Chrome: LinkedIn/Gmail/ATS) for interactive reads; `WebFetch`/`requests`
  for static pages. For automated submission use the **Patchright** engine in `jamie-autopilot/lib/`
  (headless, cross-platform) — NOT a Claude_in_Chrome MCP (no Codex equivalent).
- **Live application tracker** → the Google Sheet (single source of truth) via `workspace-mcp`
  (Gmail/Drive/Sheets), registered in `~/.codex/config.toml`. Jamie auths her OWN Google account
  (`jamiecheng0103@gmail.com`) — replace any hardcoded `david@hilos.studio`.
- **Paths** → never hardcode. Use `jamie-autopilot/lib/platform_utils.py` helpers; everything is
  repo-relative or `Path.home()`-anchored and OS-branched.
- **`model: "haiku"/"sonnet"` pins** anywhere in the docs are Claude-Code budget hints — **ignore
  on Codex** (one model per session). Push mechanical work into Python so the model only does judgment.
- **CAPTCHA** → never solve/bypass (prohibited). The submitter detects captcha and routes the role
  to a human-submit package. Most large-employer ATS forms are captcha-gated.

## 4. Setup on a new machine
See `SETUP.md` (cross-platform) for the full first-run checklist (Python deps, Gemini CLI,
Patchright browsers, Chrome debug profile, MCP registration, git auth).

## 5. Cross-platform invariants
- Windows stays exactly as it is for David (Claude Code, `.claude/`).
- Mac runs the identical repo under Codex (`.agents/`, `AGENTS.md`, `~/.codex/config.toml`).
- The `.claude/` and `.agents/` skill bodies share ONE canonical source — keep them in sync by
  editing the `.claude/skills/<name>/SKILL.md` body (the `.agents` copies just point at it).
