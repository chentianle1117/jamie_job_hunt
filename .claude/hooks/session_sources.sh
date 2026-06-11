#!/usr/bin/env bash
# SessionStart hook — inject Jamie's job-search source-of-truth checklist into context.
#
# Why: agents have fabricated/mislabeled Jamie's experience (e.g. ODN -> "ERG/community")
# because they acted before reading the canonical sources. This makes the source list
# unmissable at the very start of every session, so RULE 0 (no fabrication) can actually
# be followed. Output goes back to the model as additionalContext (not shown as a secret).
#
# It only fires the full checklist when this looks like the job-search workspace.

set -euo pipefail

JH="/Users/jamiecheng/jamie_job_hunt"
SB="/Users/jamiecheng/Agentic_Workflows_2026/jamie-second-brain"
AP="/Users/jamiecheng/Agentic_Workflows_2026/jamie-autopilot"

# Only inject if the job-search repo is present on this machine.
if [[ ! -d "$JH" ]]; then
  echo '{}'
  exit 0
fi

read -r -d '' CTX <<'EOF' || true
📋 JAMIE JOB-SEARCH SESSION — READ SOURCES BEFORE ACTING (this is RULE 0 territory)

If this session is about Jamie's job search (evaluating/tailoring/applying/outreach/essays),
you MUST ground yourself in the canonical sources BEFORE writing anything in her voice or
making a go/pass call. Fabrication and mislabeling happen when an agent skips these.

START HERE (cheap, always):
• jamie/profile_compact.md         — constraints, H1B cache, scoring, self-assessment
• jamie/JAMIE_FEEDBACK_RULES.md §0 — NO FABRICATION rule + the self-quality-gate (highest priority)

GROUND TRUTH for any claim about her experience (read the relevant ones before tailoring/cover/outreach):
• jamie/resume.md                  — "What Jamie actually does / ✅ CAN claim / ⚠️ STRETCH / ❌ DON'T claim" notes
• jamie/content_library.md         — her real bullet variants, self-intros, templates
• jamie-second-brain/Work/Career/Voice & Story Bank.md  — her actual phrasing + STAR stories
• jamie-second-brain/Work/Career/Master Profile.md      — canonical facts
• jamie-second-brain/Work/Projects/*.md                 — per-employer ground truth (ODN, InGenius, Vestas, NextGen, Kronos)
  ⮑ KEY: ODN Oregon = pro bono OD diagnostic consulting (NGO leadership + HR leave-cost), NOT community/ERG.

PIPELINE / APPLICATION MECHANICS (read when applying or automating):
• jamie-second-brain/Work/Career/Job Search System.md
• jamie-second-brain/Work/Career/ATS Accounts & Credential Vault.md  — Keychain creds, CAPTCHA=manual rule
• jamie-autopilot/lib/{credential_vault,account_registry,account_creator,apply_orchestrator,h1b_prefilter}.py
• jamie-autopilot/AGENTS.md  + this repo's CLAUDE.md (RULE 0)

HARD RULES (do not violate): truth beats fit; adjacent ≠ same; disclose gaps; when unsure ASK (plain text);
never bypass a CAPTCHA; passwords live in Keychain, never in git; Jamie clicks/confirms outward actions.
EOF

# Emit as additionalContext via SessionStart hookSpecificOutput.
python3 - "$CTX" <<'PY'
import json, sys
ctx = sys.argv[1]
print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": ctx
    }
}))
PY
