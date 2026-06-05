---
name: apply-pipeline
description: >
  Run the full 4-stage job application pipeline for Jamie. Use when Jamie says "run the pipeline", "help me apply to this", "full application workflow", "go through the whole process", or pastes a JD and wants the complete treatment. Evaluates fit, tailors resume, finds contacts, drafts outreach.
---

# /apply-pipeline — (Codex)

> **Cross-tool note:** Codex copy of the `apply-pipeline` skill. The full canonical procedure lives in
> **`.claude/skills/apply-pipeline/SKILL.md`** in this repo (one source of truth, shared between Claude
> Code and Codex). Read that file and follow it exactly.

**Codex/Mac tool substitutions while following the canonical body:**
- Chains evaluate → tailor → outreach → (review). Each sub-step's Codex tool substitutions apply.
- Browser work: Patchright (headless, cross-platform) is the automation engine; the Codex Chrome extension is the interactive option for captcha/login-gated steps Jamie completes herself.
- `model: "haiku"/"sonnet"` pins are Claude-Code budget hints — ignore on Codex (one model/session).

Do not re-derive the procedure here — read `.claude/skills/apply-pipeline/SKILL.md`.
