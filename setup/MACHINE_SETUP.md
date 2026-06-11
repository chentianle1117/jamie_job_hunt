# Machine Setup — running this system on a NEW computer

> **Principle:** everything machine-neutral lives in git (code, skills, docs, reference files,
> config *templates*). Only two things stay **local per machine**: (1) **secrets** and (2) **absolute
> paths**. Clone the repos → fill in the 2 local things below → you're running.
>
> This works across users/drives: machine A is `C:\Users\chent\…`, machine B is
> `C:\Users\David Chen\…`. The code never hardcodes the user — `lib/platform_utils.py` and
> `$env:USERPROFILE` resolve paths at runtime. Where an absolute path IS needed (the `.claude.json`
> MCP block), you fill it in locally from the template — don't commit it.

---

## What git carries (just `git clone`)
Clone all three as **siblings** in one folder (any user dir works):
```bash
cd ~/Agentic_Workflows_2026     # or  C:\Users\<you>\Agentic_Workflows_2026
git clone https://github.com/chentianle1117/jamie_job_hunt.git   oracle-job-search
git clone https://github.com/chentianle1117/jamie-autopilot.git  jamie-autopilot
git clone https://github.com/chentianle1117/jamie-second-brain.git
```
That brings ALL code, skills/doctrine, `jamie/` reference files, submitters, `platform_utils.py`,
the v5.0 search strategy, and these setup templates. ~90% of the system.

Then deps (once):
```bash
pip install -r jamie-autopilot/requirements.txt
python -m playwright install chromium
python -m patchright install chrome
```

---

## The 2 things that stay LOCAL (never in git)

### 1. Secrets — `~/.google_workspace_mcp/`
Holds OAuth credentials for the Google accounts + the shared `client_secret.json`. **Never committed**
(guarded in `.gitignore`). Two ways to get them on the new machine:
- **Copy** the whole `~/.google_workspace_mcp/` folder from the old PC (USB/cloud) → `C:\Users\<you>\.google_workspace_mcp\`. Fastest — keeps all accounts authorized.
- **Or re-auth fresh:** create `~/.google_workspace_mcp/`, drop in `client_secret.json` (ask David), then for each account: free port 8765 → `start_google_auth(service_name="drive", user_google_email="…")` → click the link. (Full steps: David's vault `Workflows/Skills/workspace-mcp-add-account.md`.)

### 2. MCP server config — `~/.claude.json` (the `workspace-mcp` block)
Not in git (machine-specific + points at the local secret path). Add this block to the new PC's
`~/.claude.json` under `mcpServers`, **editing the path to the new user**:
```json
"workspace-mcp": {
  "command": "uvx",
  "args": ["workspace-mcp", "--permissions", "gmail:send", "drive:full", "calendar:full"],
  "env": {
    "OAUTHLIB_INSECURE_TRANSPORT": "1",
    "WORKSPACE_MCP_PORT": "8765",
    "GOOGLE_CLIENT_SECRET_PATH": "C:\\Users\\<YOUR_USER>\\.google_workspace_mcp\\client_secret.json",
    "GOOGLE_OAUTH_REDIRECT_URI": "http://localhost:8765/oauth2callback"
  }
}
```
(On Mac, add the same block to `~/.claude.json` under `mcpServers` — see `SETUP.md` section E.)

---

## Recommended: token keepalive (so you don't re-auth hourly)
workspace-mcp stores refresh tokens but doesn't auto-refresh access tokens. `setup/workspace_mcp_refresh.ps1`
(in this repo, machine-neutral — uses `$env:USERPROFILE`) refreshes them out-of-band. Register it as a
Windows Scheduled Task every 50 min:
```powershell
$action  = New-ScheduledTaskAction -Execute "powershell.exe" `
  -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$env:USERPROFILE\Agentic_Workflows_2026\oracle-job-search\setup\workspace_mcp_refresh.ps1`""
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 50)
Register-ScheduledTask -TaskName "WorkspaceMCPTokenRefresh" -Action $action -Trigger $trigger -Description "Keep workspace-mcp Google tokens fresh"
```
(Copy `workspace_mcp_refresh.ps1` to `~/.google_workspace_mcp/` if you prefer it next to the creds —
the script reads creds from `$env:USERPROFILE\.google_workspace_mcp\credentials` regardless.)

---

## Path-sensitive client configs (additive — valid on both machines)
For anything that needs an absolute allowlist path (e.g. Claude Code `settings.json` permissions),
**add the new `C:\Users\David Chen\…` entries ALONGSIDE the existing `chent` ones** — don't replace.
A `David Chen` rule simply never matches on the `chent` PC and vice-versa, so one file works on both.

---

## Sanity check (after setup)
1. `python jamie-autopilot/lib/platform_utils.py` → prints Chrome binary, debug profile, ports, repo roots (all resolved for THIS machine).
2. Ask Claude Code: "search my Gmail inbox, 1 message, for tianlechen0324@gmail.com" → returns JSON, not an auth error.
3. Launch the debug Chrome → log into LinkedIn + Google once (the profile is per-machine, re-cloned on first run).

---

*Setup doctrine added 2026-06-08. Git = shared brain; local = secrets + absolute paths only.*
