---
name: tailor
description: >
  Tailor Jamie's resume for a specific job description. Use when Jamie says "tailor my resume", "help me with my resume for this job", "which bullets should I use?", "customize resume", or after /evaluate recommends GO. Selects best bullet variants, applies keyword annotations, and produces a JSON content file that the resume viewer renders.
---

# /tailor — (Codex)

> **Cross-tool note:** Codex copy of the `tailor` skill. The full canonical procedure lives in
> **`.claude/skills/tailor/SKILL.md`** in this repo (one source of truth, shared between Claude
> Code and Codex). Read that file and follow it exactly.

**Codex/Mac tool substitutions while following the canonical body:**
- Resume render → `python3 render_pdfs.py <role_dir>` (Playwright bundled Chromium; cross-platform). Verify 1-page after export.
- All NON-NEGOTIABLE rules in `jamie/JAMIE_FEEDBACK_RULES.md` apply verbatim (ODN collective, fixed bullet counts, no invented numbers, voice corpus).
- `model: "haiku"/"sonnet"` pins are Claude-Code budget hints — ignore on Codex (one model/session).

Do not re-derive the procedure here — read `.claude/skills/tailor/SKILL.md`.
