---
name: sync
description: >
  Commit and push all current changes to main. Use when Jamie says "sync", "push everything", "commit", "save my work", or "push to GitHub". Stages all files (including PDFs), writes a descriptive commit message, and pushes to origin/main.
---

# /sync — (Codex)

> **Cross-tool note:** Codex copy of the `sync` skill. The full canonical procedure lives in
> **`.claude/skills/sync/SKILL.md`** in this repo (one source of truth, shared between Claude
> Code and Codex). Read that file and follow it exactly.

**Codex/Mac tool substitutions while following the canonical body:**
- `git` is identical cross-platform. Jamie needs `gh auth login` (or a git credential helper) once on her Mac. Same add/commit/push sequence as the canonical body.
- `model: "haiku"/"sonnet"` pins are Claude-Code budget hints — ignore on Codex (one model/session).

Do not re-derive the procedure here — read `.claude/skills/sync/SKILL.md`.
