---
name: workspace-mcp OAuth — add new account
description: How to authorize a new Google account in workspace-mcp when port 8765 is blocked
type: reference
originSessionId: 7275d610-ad8c-48e9-ad55-d5d52c6a0d9d
---
## Problem
`start_google_auth` always errors "Port 8765 already in use" because the workspace-mcp server owns that port permanently.

## Fix (3 steps)
1. Kill the workspace-mcp process: `netstat -ano | findstr ":8765"` → `Stop-Process -Id <PID> -Force`
2. Immediately call `start_google_auth(service_name="gmail", user_google_email="<email>")`
3. Click the link Claude returns → sign in → done

Credentials saved to: `C:\Users\chent\.google_workspace_mcp\credentials\<email>.json`

## Full how-to
See [[Workflows/Skills/workspace-mcp-add-account]] in vault.

## Token auto-refresh
Windows Task Scheduler task `WorkspaceMCPTokenRefresh` runs `refresh.ps1` every **50 min**.
Refreshes any token expiring within 10 min. Covers all credential files automatically.
Log: `C:\Users\chent\.google_workspace_mcp\refresh.log`
This is a keepalive — not an inbox poller.

## Permission scopes
Config in `~/.claude.json` mcpServers.workspace-mcp.args:
- `gmail:send` — read + compose + send drafts
- `drive:full` — read + write (create folders, copy files, upload). **Updated 2026-05-13** from `drive:readonly`.
- `calendar:full` — read + write events
**Note:** Each individual account's OAuth token must be re-issued (kill PID 8765 → start_google_auth) AFTER the config change to pick up new scopes. Old tokens retain old scopes. Use `service_name="drive"` (not "gmail") in the re-auth call to ensure Drive scopes are requested.

## Authorized accounts (as of 2026-05-13)
- david@hilos.studio
- davidch2@andrew.cmu.edu
- tianlechen0324@gmail.com
- ycheng72@usc.edu
- jamiecheng0103@gmail.com ← added 2026-05-13
