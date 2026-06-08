---
name: Thesis Document Rules
description: Critical rules for maintaining thesis draft - never truncate, preserve all content, step-by-step pacing with pending prompts
type: feedback
---

NEVER truncate, summarize, or delete existing sections of the thesis document unless David explicitly says to.

**Why:** Gemini was hallucinating deletions and rolling back content. David moved to Claude Code specifically because he needs a guardian that preserves every word. Lost text = lost hours of voice-to-text synthesis work.

**How to apply:**
- Always maintain the full text when integrating new content
- Preserve all LaTeX citation syntax (`\cite{key}`)
- When adding new content, weave it in without removing surrounding text
- Git commit after every integration so changes are traceable
- Always end with a "Pending Prompt" — a targeted question asking David for his voice-to-text thoughts on the next paper/concept
- Only tackle ONE paper or concept at a time (pacing)
- Thesis files live at: `W:\CMU_Academics\2025 Fall\Thesis Demo\Thesis_Material\`
