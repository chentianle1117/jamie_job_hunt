#!/usr/bin/env python3
"""Generate Codex .agents/skills/<name>/SKILL.md pointer files for the oracle repo — thin
Codex copies that point at the canonical .claude/skills/<name>/SKILL.md body (one source of
truth, no drift). Cross-platform tool substitutions noted inline."""
import os
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent  # oracle-job-search
AGENTS_SKILLS = REPO / ".agents" / "skills"

SKILLS = {
    "tailor": {
        "desc": ('Tailor Jamie\'s resume for a specific job description. Use when Jamie says "tailor my resume", '
                 '"help me with my resume for this job", "which bullets should I use?", "customize resume", or after '
                 '/evaluate recommends GO. Selects best bullet variants, applies keyword annotations, and produces a '
                 'JSON content file that the resume viewer renders.'),
        "subs": ("- Resume render → `python3 render_pdfs.py <role_dir>` (Playwright bundled Chromium; cross-platform). "
                 "Verify 1-page after export.\n"
                 "- All NON-NEGOTIABLE rules in `jamie/JAMIE_FEEDBACK_RULES.md` apply verbatim (ODN collective, "
                 "fixed bullet counts, no invented numbers, voice corpus)."),
    },
    "outreach": {
        "desc": ('Find networking contacts and draft outreach messages for a job Jamie is applying to. Use when Jamie '
                 'says "who should I reach out to?", "find connections", "draft outreach", "help me network for this '
                 'role", or after /tailor is complete. Identifies alumni, hiring managers, and team members, then '
                 'drafts personalized messages.'),
        "subs": ("- LinkedIn contact verification → use the **Codex Chrome extension** against Jamie's logged-in "
                 "LinkedIn (the canonical body's 'verify recipient CURRENTLY works there' rule is mandatory).\n"
                 "- Drafts go to Jamie's Gmail via `workspace-mcp` (registered in `~/.codex/config.toml`)."),
    },
    "sync": {
        "desc": ('Commit and push all current changes to main. Use when Jamie says "sync", "push everything", '
                 '"commit", "save my work", or "push to GitHub". Stages all files (including PDFs), writes a '
                 'descriptive commit message, and pushes to origin/main.'),
        "subs": ("- `git` is identical cross-platform. Jamie needs `gh auth login` (or a git credential helper) once "
                 "on her Mac. Same add/commit/push sequence as the canonical body."),
    },
    "apply-pipeline": {
        "desc": ('Run the full 4-stage job application pipeline for Jamie. Use when Jamie says "run the pipeline", '
                 '"help me apply to this", "full application workflow", "go through the whole process", or pastes a JD '
                 'and wants the complete treatment. Evaluates fit, tailors resume, finds contacts, drafts outreach.'),
        "subs": ("- Chains evaluate → tailor → outreach → (review). Each sub-step's Codex tool substitutions apply.\n"
                 "- Browser work: Patchright (headless, cross-platform) is the automation engine; the Codex Chrome "
                 "extension is the interactive option for captcha/login-gated steps Jamie completes herself."),
    },
}

POINTER = '''---
name: {name}
description: >
  {desc}
---

# /{name} — (Codex)

> **Cross-tool note:** Codex copy of the `{name}` skill. The full canonical procedure lives in
> **`.claude/skills/{name}/SKILL.md`** in this repo (one source of truth, shared between Claude
> Code and Codex). Read that file and follow it exactly.

**Codex/Mac tool substitutions while following the canonical body:**
{subs}
- `model: "haiku"/"sonnet"` pins are Claude-Code budget hints — ignore on Codex (one model/session).

Do not re-derive the procedure here — read `.claude/skills/{name}/SKILL.md`.
'''

for name, info in SKILLS.items():
    d = AGENTS_SKILLS / name
    d.mkdir(parents=True, exist_ok=True)
    (d / "SKILL.md").write_text(
        POINTER.format(name=name, desc=info["desc"], subs=info["subs"]),
        encoding="utf-8",
    )
    print(f"[wrote] .agents/skills/{name}/SKILL.md")
print("done — Codex skill pointers generated (evaluate already written by hand).")
