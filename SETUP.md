# SETUP.md — First-run checklist (macOS · Claude Code)

The pipeline runs from ONE codebase. Both `~/jamie_job_hunt` and
`~/Agentic_Workflows_2026/oracle-job-search` are checkouts of the same GitHub repo
(`chentianle1117/jamie_job_hunt`). Keep both pulled/synced.

For a full system-layout overview see `repo_map.md`.

---

## A. Clone the repos
```bash
# both repos must be SIBLINGS (platform_utils derives paths from that)
cd ~/Agentic_Workflows_2026
git clone https://github.com/chentianle1117/jamie_job_hunt.git oracle-job-search
git clone https://github.com/chentianle1117/jamie-autopilot.git jamie-autopilot
```

## B. Python + dependencies
```bash
# macOS: use system python3 (brew install python3 if missing)
python3 -m pip install -r jamie-autopilot/requirements.txt

# ONE-TIME browser binaries (NOT pulled by pip — required for render + submit):
python3 -m playwright install chromium
python3 -m patchright install chrome
```
Verify: `python3 jamie-autopilot/lib/platform_utils.py` → should print the correct Chrome binary,
debug-profile dir, and repo roots for THIS machine.

## C. Chrome debug profile (for auto-submit / browser automation)
Chrome 136+ refuses `--remote-debugging-port` on the DEFAULT profile, so we use a dedicated profile.
Launch it via the helper:
```bash
python3 -c "import sys; sys.path.insert(0,'jamie-autopilot/lib'); import platform_utils as u; u.launch_debug_chrome()"
```
- macOS binary: `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`
- profile dir (Mac): `~/Library/Application Support/Google/Chrome/autopilot_debug_profile`
- debug port: 9333 (override with `AUTOPILOT_DEBUG_PORT`)

First launch: log into LinkedIn / Google in that window so the session is authenticated.
For interactive captcha or login steps, use Claude Code with the Claude-in-Chrome MCP.

If Jamie's everyday Chrome profile is not "Profile 4", set `export AUTOPILOT_PROFILE_NAME="Default"`
(or whichever) before running profile-clone steps.

## D. git auth
```bash
gh auth login        # or configure a git credential helper
```
The `.claude/settings.json` has an auto-push hook; push is also available via the `/sync` skill.

## E. Google credential (workspace-MCP — Gmail / Drive / Sheets)
- Get **`client_secret.json`** from David (shared OAuth app credential — never in git).
- `mkdir -p ~/.google_workspace_mcp` and move the file to `~/.google_workspace_mcp/client_secret.json`.
- Passwords and sensitive credentials are managed via macOS Keychain through `jamie-autopilot/lib/credential_vault.py` — never stored in git.

Add the `workspace-mcp` block to `~/.claude.json` under `mcpServers`:
```json
"workspace-mcp": {
  "command": "uvx",
  "args": ["workspace-mcp", "--tools", "gmail", "drive", "calendar"],
  "env": {
    "OAUTHLIB_INSECURE_TRANSPORT": "1",
    "WORKSPACE_MCP_PORT": "8765",
    "GOOGLE_CLIENT_SECRET_PATH": "/Users/jamiecheng/.google_workspace_mcp/client_secret.json",
    "GOOGLE_OAUTH_REDIRECT_URI": "http://localhost:8765/oauth2callback"
  }
}
```

First workspace-mcp call triggers Google OAuth → approve Gmail + Drive (drive:full).
Sign in as **jamiecheng0103@gmail.com** (her own account).
**If "port 8765 in use":** `lsof -ti tcp:8765 | xargs kill -9`, retry.

## F. Claude Code skills
Claude Code reads `CLAUDE.md` (repo root) automatically and loads skills from `.claude/skills/<name>/SKILL.md`.
The `jamie-autopilot` pipeline skill lives at `~/.claude/skills/` (user-level).
No extra configuration needed — just `cd oracle-job-search && claude`.

## G. Trigger the pipeline
In Claude Code (run from the repo dir):
- Just ask: "run the autopilot pipeline in shadow mode", or
- `/jamie-autopilot` (skill), `/evaluate`, `/tailor`, `/outreach`, `/sync`.

---

## H. Per-machine secrets (each person sets their own)
- workspace-mcp Google token — per machine; Jamie's own Google account.
- `gh`/git credentials — per machine.
- Optional `.env` (Notion/Telegram) — only if those delivery channels are used.
- **No API keys are committed.** Everything is OAuth or env-var, per machine.
