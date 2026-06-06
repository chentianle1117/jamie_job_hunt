# RUN_GUIDE — Running the Job-Search Pipeline (Jamie · Mac · Codex)

> Plain-English run guide. One-time setup once; then the "every run" routine. For the deeper
> system map see `AGENTS.md`, `SETUP.md`, and `jamie-second-brain/Work/Career/Job Search System.md`.

---

## ⚙️ ONE-TIME SETUP

**1. Confirm all three repos are cloned as siblings:**
```bash
cd ~/Agentic_Workflows_2026 && ls   # expect: oracle-job-search  jamie-autopilot  jamie-second-brain
```

**2. Pull the latest:**
```bash
cd ~/Agentic_Workflows_2026 && \
for d in oracle-job-search jamie-autopilot jamie-second-brain; do echo "── $d ──"; git -C "$d" pull origin main; done
```
If a pull complains about local changes (e.g. from an earlier test run):
```bash
git -C oracle-job-search checkout -- outputs/2026-05-25-night/state.json
git -C oracle-job-search clean -fd      # preview with `clean -n` first
```
then pull again.

**3. Install dependencies (once, or after `requirements.txt` changes):**
```bash
pip3 install -r jamie-autopilot/requirements.txt
python3 -m playwright install chromium
python3 -m patchright install chrome
```

**4. Google credential (the workspace-MCP blocker):**
- Get **`client_secret.json`** from David (shared OAuth app credential — not in any repo by design).
- Save it: `mkdir -p ~/.google_workspace_mcp` then move the file to `~/.google_workspace_mcp/client_secret.json`.

**5. Codex config:**
```bash
cp ~/Agentic_Workflows_2026/oracle-job-search/codex-config.example.toml ~/.codex/config.toml
```
Edit `~/.codex/config.toml`: set `writable_roots` to `/Users/jamiecheng/Agentic_Workflows_2026`.
It already sets `AI_BRAIN=codex` (routes fit-analysis to your ChatGPT Plus).

**6. Restart Codex, then authorize your Google:**
In `codex`, run:
```
start_google_auth(service_name="drive", user_google_email="jamiecheng0103@gmail.com")
```
Click the link → sign in → done. **If "port 8765 in use":** `lsof -ti tcp:8765 | xargs kill -9`, retry.
(Full detail: `jamie-second-brain/Work/Career/Workspace MCP — Multi-Account Google Setup (Mac, Codex).md`.)

**7. Verify:** ask Codex to "search my Gmail inbox for the last day via workspace-mcp" → JSON, not an auth error.

---

## ▶️ EVERY RUN

**1. Open Terminal → repo → pull → launch Codex:**
```bash
cd ~/Agentic_Workflows_2026/oracle-job-search
git pull origin main
codex
```
Codex auto-reads `AGENTS.md`.

**2. Start the debug Chrome** (needed for browser/apply steps) — tell Codex:
> "Launch the debug Chrome for the pipeline."
First time, log into LinkedIn + Google in that window so the session is authenticated.

**3. Run — just ask, or use a skill:**
- `/jamie-autopilot` — full round (discover → tailor → audit → package)
- `/evaluate` + paste a job link — one role's fit + H-1B check
- `/tailor` — tailor résumé for a specific JD
- `/outreach` — find contacts + draft messages
- `/sync` — commit + push your changes

**First time, always shadow first:**
> "Run the autopilot in shadow mode" — discovers + tailors + audits but **submits nothing**. Review, then decide.

**4. Review + finish:** packages land in `runs/<date>/discovered/...` + a dashboard. **You click the final Submit** on each (see caveat).

---

## ⚠️ What to expect (honest)
- **Most big companies CAPTCHA the submit button.** The pipeline fills the *whole* form, then hands you a
  ready-to-submit package — you do the captcha + click Submit (~30 sec). It will **never** fake a captcha
  or send a half-finished application.
- **Captcha-free forms** (some Greenhouse/Ashby) it submits end-to-end.
- **It's honest about fit** — ≤4 yrs required, real match, H-1B sponsor or cap-exempt — and runs an
  anti-fabrication audit before writing anything in your voice. If it says "skip," trust it.
- **Nothing is sent without you seeing it.** Emails = drafts; submissions = yours to click.

---

## 🆘 Troubleshooting
- **Workspace-MCP / OAuth error** → re-run the `start_google_auth` step (port-8765 fix above).
- **"couldn't reach a brain" / Gemini error** → confirm `AI_BRAIN=codex` is in `~/.codex/config.toml`.
- **`git pull` refuses (local changes)** → `git -C <repo> fetch && git -C <repo> reset --hard origin/main`
  (safe — you're a user of these repos, not an editor).
- **Anything else** → screenshot + send to David.
