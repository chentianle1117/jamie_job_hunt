---
name: sync
description: >
  Commit and push all current changes to main. Use when Jamie says "sync",
  "push everything", "commit", "save my work", or "push to GitHub".
  Stages all files (including PDFs), writes a descriptive commit message, and pushes to origin/main.
argument-hint: "<optional: short description for commit message>"
---

## Sync All Changes to GitHub

Run this sequence in the jamie_job_hunt repo:

### Step 1 — Stage everything

```bash
cd /Users/jamiecheng/jamie_job_hunt
git add -A
```

### Step 2 — Check what's staged

```bash
git status
git diff --cached --stat
```

Report to Jamie what's being committed (file names + rough summary).

### Step 3 — Commit with a descriptive message

Use `$ARGUMENTS` if provided as the commit description. Otherwise, infer from the staged files:
- If resume files changed → "Update resume for [company] [date]"
- If jamie/ files changed → "Update [file] — [what changed]"
- If skills changed → "Update [skill] skill"
- If multiple types → "Update resume, content library, and tracker [date]"

```bash
git commit -m "[descriptive message based on what changed]"
```

### Step 4 — Push

```bash
git push origin main
```

### Step 5 — Confirm

Report: `"Pushed X files to main: [list of files]"`
