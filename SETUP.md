# SETUP.md — First-run checklist (Windows + macOS)

The pipeline runs from ONE codebase on either OS. Below: the macOS / Codex path (Jamie) and the
Windows / Claude Code path (David). Most steps are identical; OS-specific bits are marked.

---

## A. Clone the repos (both OSes)
```bash
# pick a home; the two repos must be SIBLINGS (platform_utils derives paths from that)
cd ~/Agentic_Workflows_2026            # macOS    (or  C:\Users\<you>\Agentic_Workflows_2026 on Windows)
git clone https://github.com/chentianle1117/jamie_job_hunt.git oracle-job-search
git clone https://github.com/chentianle1117/jamie-autopilot.git jamie-autopilot
```

## B. Python + dependencies (both OSes)
```bash
# macOS: use system python3 (brew install python3 if missing) — NO conda needed
# Windows: your existing python is fine
python3 -m pip install -r jamie-autopilot/requirements.txt

# ONE-TIME browser binaries (NOT pulled by pip — required for render + submit):
python3 -m playwright install chromium
python3 -m patchright install chrome
```
Verify: `python3 jamie-autopilot/lib/platform_utils.py` → should print the correct Chrome binary,
debug-profile dir, and repo roots for THIS machine.

## C. Gemini CLI (both OSes)
```bash
npm i -g @google/gemini-cli          # needs Node (macOS: brew install node)
gemini auth login                    # sign in as davchen1117@gmail.com (Google One AI Pro)
gemini -m gemini-2.5-flash -p "OK"   # smoke test → should print OK
```

## D. Chrome debug profile (both OSes — for auto-submit / browser automation)
Chrome 136+ refuses `--remote-debugging-port` on the DEFAULT profile on BOTH OSes, so we use a
dedicated profile. Launch it cross-platform via the helper:
```bash
python3 -c "import sys; sys.path.insert(0,'jamie-autopilot/lib'); import platform_utils as u; u.launch_debug_chrome()"
```
- macOS binary: `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`
- profile dir (Mac): `~/Library/Application Support/Google/Chrome/autopilot_debug_profile`
- debug port: 9333 (override with `AUTOPILOT_DEBUG_PORT`)
First launch: log into LinkedIn / Google in that window so the session is authenticated.
If Jamie's everyday Chrome profile is not "Profile 4", set `export AUTOPILOT_PROFILE_NAME="Default"`
(or whichever) before running profile-clone steps.

## E. git auth (both OSes)
```bash
gh auth login        # or configure a git credential helper
```
(The Windows `.claude/settings.json` has an auto-push hook; on Codex, push is an explicit step or
the `/sync` skill.)

---

## F. macOS / Codex ONLY — make Codex behave like Claude Code

### F1. Codex reads AGENTS.md automatically
`AGENTS.md` (repo root) + `.agents/skills/` are picked up when Jamie runs `codex` in the repo dir.
Nothing to configure — just `cd oracle-job-search && codex`.

### F2. Register MCP servers — `~/.codex/config.toml`
Copy `codex-config.example.toml` (in this repo) to `~/.codex/config.toml` and adjust. Minimum:
```toml
[mcp_servers.workspace-mcp]          # CRITICAL: Gmail + Drive + Google Sheets tracker
command = "uvx"
args = ["workspace-mcp", "--tools", "gmail", "drive", "calendar"]
env = { OAUTHLIB_INSECURE_TRANSPORT = "1", WORKSPACE_MCP_PORT = "8765" }

sandbox_mode = "workspace-write"
approval_policy = "on-request"
[sandbox_workspace_write]
network_access = true                # REQUIRED: ATS APIs, JobSpy, Gemini, git, Patchright
writable_roots = ["/Users/jamiecheng/Agentic_Workflows_2026", "/private/tmp"]
```
First workspace-mcp call triggers Google OAuth → approve Gmail + Drive (drive:full).
Sign in as **jamiecheng0103@gmail.com** (her own account).

### F3. Codex Chrome extension (optional but recommended)
Install the **Codex** extension from the Chrome Web Store. It lets Codex read/act on Jamie's
logged-in sites (LinkedIn/Gmail/ATS) for the interactive verification + the human-in-the-loop
captcha submits. The automated submission engine remains Patchright (headless).

### F4. Trigger the pipeline
In `codex` (run from the repo dir):
- Just ask: "run the autopilot pipeline in shadow mode", or
- `/jamie-autopilot` (skill), `/evaluate`, `/tailor`, `/outreach`, `/sync`.

---

## G. Windows / Claude Code (David) — unchanged
Existing `.claude/` skills + `CLAUDE.md` keep working exactly as before. The new `.agents/` files
and `platform_utils.py` are additive and don't change the Windows experience.

## H. Per-machine secrets (each person sets their own)
- Gemini OAuth (`gemini auth login`) — per machine.
- workspace-mcp Google token — per machine; Jamie's own Google account.
- `gh`/git credentials — per machine.
- Optional `.env` (Notion/Telegram) — only if those delivery channels are used.
- **No API keys are committed.** Everything is OAuth or env-var, per machine.
