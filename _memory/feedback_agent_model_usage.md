---
name: Agent model usage — use Haiku for mechanical tasks
description: Use Haiku for scoring/auditing/CRUD agents; reserve Sonnet for judgment-heavy tasks to reduce token spend
type: feedback
---

Use the cheapest model appropriate for the task when spawning background agents.

**Rule:** Default subagents to `haiku` unless the task requires genuine judgment.

| Task | Model |
|------|-------|
| Scoring, property updates, Notion CRUD | `haiku` |
| Deduplication, auditing, batch patching | `haiku` |
| Job fit evaluation, JD analysis | `sonnet` |
| Outreach drafting, resume tailoring | `sonnet` |
| Full pipeline orchestration (top-level) | `sonnet` (orchestrator only) |

**Why:** Token spend depletes very fast when every agent defaults to Sonnet. Mechanical formula-based tasks (compute score, update Notion field) don't benefit from Sonnet's extra capability.

**How to apply:** In the Agent tool call, always set `model: "haiku"` for scoring/audit/CRUD agents. Only omit (defaults to Sonnet) for judgment tasks.
