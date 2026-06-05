---
name: evaluate
description: >
  Evaluate whether a job is a good fit for Jamie. Use when Jamie pastes a job description,
  shares a job URL, or says "evaluate this", "is this a fit?", "should I apply?", "check this job".
  Returns a structured fit analysis with H1B status and go/stretch/pass recommendation.
---

# /evaluate — Job fit evaluation (Codex)

> **Cross-tool note:** This is the Codex copy of the `evaluate` skill. The full, canonical
> procedure lives in **`.claude/skills/evaluate/SKILL.md`** in this same repo (one source of
> truth, shared between Claude Code and Codex). Read that file and follow it exactly.

**On Codex/Mac, apply these tool substitutions while following the canonical body:**
- "With Chrome / get_page_text" → use the **Codex Chrome extension** to read JS-rendered ATS
  pages (LinkedIn/Greenhouse/Lever/Ashby/Workday); fall back to `WebFetch`/`requests` for
  static pages. Same goal: get the full JD text + confirm the posting is still live.
- Gemini grounding step → run `python3 pipeline/gemini_run.py ...` exactly as written
  (cross-platform; Gemini CLI is the same `gemini` binary on Mac).
- Live application tracker → the Google Sheet via `workspace-mcp` (registered in
  `~/.codex/config.toml`) or the CSV-export WebFetch fallback. Single source of truth.
- `model: "haiku"/"sonnet"` pins in the canonical body are **Claude-Code budget hints — ignore
  on Codex** (one model per session).

Everything else (Step 0 timeline overlay, hard-constraint check, H1B verification on
h1bdata.info, the 9 scoring guardrails, verdict format) applies verbatim. Do not re-derive it
here — read `.claude/skills/evaluate/SKILL.md`.
