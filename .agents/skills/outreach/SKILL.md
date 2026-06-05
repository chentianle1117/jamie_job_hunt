---
name: outreach
description: >
  Find networking contacts and draft outreach messages for a job Jamie is applying to. Use when Jamie says "who should I reach out to?", "find connections", "draft outreach", "help me network for this role", or after /tailor is complete. Identifies alumni, hiring managers, and team members, then drafts personalized messages.
---

# /outreach — (Codex)

> **Cross-tool note:** Codex copy of the `outreach` skill. The full canonical procedure lives in
> **`.claude/skills/outreach/SKILL.md`** in this repo (one source of truth, shared between Claude
> Code and Codex). Read that file and follow it exactly.

**Codex/Mac tool substitutions while following the canonical body:**
- LinkedIn contact verification → use the **Codex Chrome extension** against Jamie's logged-in LinkedIn (the canonical body's 'verify recipient CURRENTLY works there' rule is mandatory).
- Drafts go to Jamie's Gmail via `workspace-mcp` (registered in `~/.codex/config.toml`).
- `model: "haiku"/"sonnet"` pins are Claude-Code budget hints — ignore on Codex (one model/session).

Do not re-derive the procedure here — read `.claude/skills/outreach/SKILL.md`.
