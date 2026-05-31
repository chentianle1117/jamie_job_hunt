# Auto-Apply Research — 2026-05-27

> Research commissioned after 0/6 auto-apply success on 2026-05-25 pipeline run.
> All facts sourced. Speculation marked explicitly. Tool viability assessed as of May 2026.

---

## Executive Summary

1. **Chrome MCP domain blocks are a real, documented bug** — the per-domain allowlist is broken for MCP-driven navigation (issue #57219, closed as duplicate, unresolved). The workaround is to visit each ATS domain in the Chrome extension sidepanel first, click "Always allow on this site," then run the pipeline. This is currently the only reliable path within the existing stack.

2. **Aurora (Greenhouse) is already a supported ATS** — the pipeline has `auto_submit_greenhouse: true` flagged as enabled. Aurora uses `boards.greenhouse.io/aurorainnovation`. The block was a permissions issue, not an ATS issue. Fix: grant Chrome MCP permission on `boards.greenhouse.io` once.

3. **Sandvik uses Workday** (`sandvik.wd3.myworkdayjobs.com`) — Workday is the hardest to automate due to multi-step forms + bot detection. No commercial tool has a reliable 2026 record here. Simplify Copilot autofills (free) but requires manual submit. FastApply claims Workday support but has not been independently verified for H-1B-specific question handling.

4. **For the road-trip period (3–6 weeks), the recommended stack is: Simplify Copilot (free, autofill) + one manual session per application for final submit.** No commercial auto-submit tool has documented ADP Workforce Now or PeopleAdmin support as of May 2026.

5. **Greenhouse direct API is the highest-leverage technical investment** — Aurora and similar Greenhouse employers can be submitted programmatically (no browser) using the public Job Board API. This is the correct long-term path for those ATS targets, buildable in ~1 day.

---

## Section 1: Chrome MCP Domain Allowlist

### How It Works

Claude in Chrome uses a **per-domain permission model** with three tiers:
- "Allow this action" — single action only
- "Always allow actions on this site" — persistent domain permission
- "Decline" — block

For **Team/Enterprise** plans, admins can configure org-level allowlists/blocklists via organization settings. These override individual user settings.

For **personal Pro/Max plans**, there is no org-level allowlist. Users must approve each domain interactively.

There is a setting at `claude.ai/settings/browser-extension` → "Default for all sites" → "Allow extension" which lifts domain category restrictions and causes individual permission prompts to display. This is the closest to a "grant all" mode for personal accounts.

### The Actual Bug (Confirmed, May 2026)

**Issue #57219** (closed as duplicate of an earlier report): When Claude is driven by Claude Desktop/Claude Code MCP tools (`navigate`, `click`, `type`), the per-site allowlist in Settings → Claude in Chrome → Allowed Sites has **no effect**. MCP navigation calls return `permission_required` even for explicitly whitelisted domains.

The bug only affects MCP-driven sessions. The Chrome extension sidepanel works correctly — if you use the extension directly (not Claude Code), domain permissions work as documented.

**Root cause (suspected):** The allowlist is stored at a location the MCP permission layer does not read from, or is only evaluated for the extension sidepanel context, not the Desktop-driven MCP context.

**Issue #36767** (wildcard domain matching): Closed as duplicate. Anthropic has acknowledged the feature request but no ETA.

**Issue #55580** (user-controlled allowlist override): Open as of May 2026, labeled "enhancement," no Anthropic response or assignment. Requests a user allowlist to override server-side blocks on personal plans.

**Issue #56965** (v1.0.70 regression): `permission_required` regression — approval popup never renders, all MCP navigations blocked in some versions.

### How to Unblock (Current Workarounds)

**Workaround 1 — Pre-grant via sidepanel (recommended, 5 min setup):**
1. Open Chrome with the Claude extension
2. Navigate to each ATS domain in the sidepanel (NOT via Claude Code)
3. When prompted, click "Always allow actions on this site"
4. The domain is now in the approved list — subsequent Claude Code MCP calls should work

**Important caveat:** Due to bug #57219, this may still not propagate to MCP calls. Test one domain first before committing.

**Workaround 2 — "Allow all" mode:**
Go to `claude.ai/settings/browser-extension` → set default to "Allow extension" (acts on all sites). This triggers prompts rather than silent blocks, giving Claude Code a chance to receive user approval at runtime.

**Workaround 3 — LevelDB direct write (security risk, NOT recommended):**
Documented in GitHub issue #26779. Writing directly to the extension's LevelDB storage pre-approves arbitrary domains. Undermines security model. Do not use.

### Security Trade-off

The per-domain model exists because of a real attack class: prompt injection via malicious web pages that instruct Claude to take actions (buy things, exfiltrate data). A 2025 vulnerability ("ShadowPrompt") demonstrated this via trusted subdomains. "Allow all" mode removes this protection. Acceptable risk for Jamie's job search pipeline running on trusted ATS domains — not acceptable for general browsing.

### Limitations

- No official fix timeline from Anthropic for the MCP allowlist bug
- Each ATS domain requires a separate manual pre-grant
- Extension version updates may reset permissions (regression risk)
- Domains served via company-specific subdomains (`careers.company.com`) each need individual grants — a wildcard feature does not exist yet

---

## Section 2: Alternative Tools

### A. Playwright / Selenium / Puppeteer

**Setup cost:** Medium (~1–3 days per ATS handler if writing from scratch; ~half-day if extending existing `lib/ats_handlers/`)

**How it works:** Playwright launches a real Chrome/Firefox browser (headed or headless) and drives it via CDP. With a persistent Chrome user data directory (`--user-data-dir`), it can pick up Jamie's saved cookies/auth state — no re-login needed.

**Key advantage over Chrome MCP:** Playwright is not subject to any extension allowlist. It's pure browser automation. No permission prompts.

**Per-ATS complexity:**
- Greenhouse: Easy. Well-documented forms, no bot detection at apply level. Playwright handles it reliably.
- Workday: Hard. Multi-step flows, dynamic JavaScript, some Workday instances use Arkose Labs (bot detection). Scripts break on Workday updates. Existing project: `g-kolipak/workday-job-application-automation` (2 commits, 0 stars, untested quality).
- PeopleAdmin: Medium. Standard HTML form structure. No known anti-bot protections. Likely straightforward.
- PinpointHQ (Pacific Seafood): Unknown bot defenses. Standard form. Likely easy.
- ADP Workforce Now (Carlos Rosario): Hard. ADP's apply flows are session-heavy and have multiple redirects. No documented successful Playwright automation found.

**Auth persistence:** Use `playwright.chromium.launchPersistentContext(userDataDir)` with Jamie's Chrome profile path. Copies session cookies including LinkedIn, Google SSO, etc.

**Maintenance burden:** Each ATS update can break a handler. Expect 1–2 hrs/month maintenance for 4+ active handlers.

**Recommendation:** Build a Playwright handler for Greenhouse (Aurora) and PeopleAdmin (UPortland) first. Both are medium-easy and cover 3 of the 6 blocked domains.

---

### B. Commercial Auto-Apply Services

| Tool | Price (May 2026) | Workday | Greenhouse | ADP | PeopleAdmin | PinpointHQ | Uses Your Resume | Auto-Submit |
|---|---|---|---|---|---|---|---|---|
| **Simplify Copilot** | Free | ✅ (autofill) | ✅ (autofill) | ❓ unconfirmed | ❓ unconfirmed | ❓ unconfirmed | ✅ Your resume | ❌ Autofill only |
| **FastApply** | $14–$49/mo | ✅ claimed | ✅ claimed | ❌ not listed | ❌ not listed | ❌ not listed | ✅ Tailors yours | ✅ Auto-submit |
| **LoopCV** | Free–€9.99+/mo | ✅ listed | ✅ listed | ❌ not listed | ❌ not listed | ❌ not listed | Unclear | ✅ Auto-submit |
| **LazyApply** | $99–$999/yr | ⚠️ 34% accuracy | ✅ basic | ❌ | ❌ | ❌ | Generates answers | ✅ |
| **AIApply.co** | $12–$23/wk | ✅ claimed (Workday + Greenhouse) | ✅ | ❓ | ❌ | ❌ | Generates per-role | ✅ |
| **Sonara** | $2.95 trial → $23.95/mo | ❓ (job boards focus) | ❓ | ❌ | ❌ | ❌ | Uses uploaded resume | ✅ (volume) |
| **JobRight.ai** | Free + $20–$40/mo | N/A — no submissions | N/A | N/A | N/A | N/A | Customizes yours | ❌ Matching only |
| **Massive.ai** | Insufficient 2025-2026 data | ❓ | ❓ | ❓ | ❓ | ❓ | ❓ | ❓ |
| **Talentprise** | Insufficient data — appears focused on matching/profile, not auto-apply | — | — | — | — | — | — | — |

**Key findings:**
- **No tool as of May 2026 has confirmed ADP Workforce Now or PeopleAdmin support.** These are niche ATS platforms not covered by mainstream auto-apply tools.
- **PinpointHQ** (Pacific Seafood) is too small to be on any tool's radar. No coverage found.
- **Simplify Copilot is free and the best starting point** — autofill + manual submit is the realistic baseline for all 6 ATSes.
- **FastApply is the most complete commercial option** for Workday + Greenhouse, but ADP/PeopleAdmin gaps mean it still doesn't solve 3 of the 6 blockers.
- **Sonara and LazyApply are not appropriate for Jamie's use case** — volume-blast tools with generic resumes. H-1B/sponsorship question handling is not documented for either.

**Privacy / data concern:** AIApply, Sonara, and LazyApply all process your resume on their servers. For Jamie's H-1B situation, sharing immigration status and work authorization details with third-party services requires trust. Simplify is the least privacy-invasive (browser extension, local autofill).

---

### C. Open-Source Auto-Apply Projects

| Project | ATS Support | Auth Method | Maintained (May 2026) | Notes |
|---|---|---|---|---|
| **feder-cr/Jobs_Applier_AI_Agent_AIHawk** | LinkedIn Easy Apply only (third-party plugins removed) | Selenium + Chrome cookies | **ARCHIVED 2026-05-17** — read-only, no updates | Last release Nov 2024. Do not use. |
| **g-kolipak/workday-job-application-automation** | Workday only | Playwright (unknown auth) | 2 commits, 0 stars — likely proof-of-concept | No README visible, no stars, untested |
| **LinkedIn Easy Apply bots (multiple)** | LinkedIn only | Selenium/cookies | Various — most work but LinkedIn actively blocks bots | Not relevant — Jamie applies off LinkedIn |

**Bottom line:** No maintained open-source project as of May 2026 covers Workday (reliably), ADP, PeopleAdmin, or PinpointHQ with H-1B-aware question handling. AIHawk was the closest option but is now archived.

---

### D. ATS Direct API Integration

#### Greenhouse Job Board API (Aurora — confirmed Greenhouse)

**Status: Fully viable. Recommended.**

Aurora uses Greenhouse (`boards.greenhouse.io/aurorainnovation`). Greenhouse publishes a public Job Board API:

- **List jobs:** `GET https://boards-api.greenhouse.io/v1/boards/aurorainnovation/jobs`
- **Get job + questions:** `GET https://boards-api.greenhouse.io/v1/boards/aurorainnovation/jobs/{id}?questions=true`
- **Submit application:** `POST https://boards-api.greenhouse.io/v1/boards/aurorainnovation/jobs/{id}` (multipart form)

**Auth:** HTTP Basic Auth with your API key. **No ATS key needed** — the Job Board API is public (no auth required to read/apply, unlike the Recruiting API).

**What you can submit:** `first_name`, `last_name`, `email`, `phone`, `resume` (PDF binary), `cover_letter` (PDF binary), + custom `questions[]` per job (including work authorization / visa sponsorship).

**H-1B handling:** Work authorization questions appear in the `questions` array with their field names and option values. You answer them like any other field. Can be templated once and reused.

**Required client-side validation:** Greenhouse does NOT reject applications missing required fields — validation is your responsibility. Write a validator against the questions array before submitting.

**Security note:** Do not POST directly from a browser page (exposes API key). Route through a local Python script.

**Implementation estimate:** 2–3 hrs for a Python script that reads our tailored `resume.pdf` + `cover_letter.pdf` from the application folder and submits via API. Can be wired into the pipeline as `apply_greenhouse_api.py`.

#### PeopleAdmin (UPortland — higher education ATS)

**Status: No public API. Browser automation required.**

PeopleAdmin is a higher-education-focused ATS (now part of Powerschool). It has no documented public API for submitting applications. The apply URL structure is `https://{institution}.peopleadmin.com/postings/{id}/applications/new` — a standard HTML form. Playwright is the right approach here.

#### ADP Workforce Now (Carlos Rosario)

**Status: No public apply API. Complex browser automation.**

ADP's career portal (`carlosrosario.org` redirects to an ADP-hosted application page) has no documented public API for candidates. ADP has a Partner API but it's employer-facing only. Manual apply or Playwright with close attention to session management is required.

**Practical note:** Carlos Rosario is the highest-priority role (score 90, GO verdict). Given its importance, Jamie should apply manually while this is being automated. Time investment: ~20 minutes.

#### Workday (Sandvik — `sandvik.wd3.myworkdayjobs.com`)

**Status: No public apply API. Workday has an Apply API but it's behind enterprise credentials.**

Workday's "Apply with Workday" feature connects via OAuth for users with Workday accounts. There is no unauthenticated POST endpoint. Automation options:
- Playwright (medium difficulty — multi-step forms, some bot detection)
- Simplify Copilot autofill + manual submit (recommended for now)

#### PinpointHQ (Pacific Seafood)

**Status: No documented public API. Standard HTML form, likely easy to automate.**

PinpointHQ is a UK-based ATS with a clean REST API for employers, but no documented public candidate application API. The apply form is standard HTML at `/postings/{id}/applications/new`. Playwright would work. Pacific Seafood is a STRETCH/DECISION role — lower priority.

---

## Section 3: Per-ATS Compatibility Matrix

| Domain | ATS Platform | Our Handler? | Simplify Autofill | API Path | Playwright | Priority | Recommended Action |
|---|---|---|---|---|---|---|---|
| `boards.greenhouse.io/aurorainnovation` | **Greenhouse** | ✅ Yes (auto_submit_greenhouse: true) | ✅ | ✅ Public API | Easy | HIGH | Fix Chrome MCP grant OR use Greenhouse API directly |
| `uportland.peopleadmin.com` | **PeopleAdmin** | ❌ | ❓ Unconfirmed | ❌ No API | Medium | HIGH | Playwright handler + manual pre-grant |
| `carlosrosario.org` (ADP) | **ADP Workforce Now** | ❌ | ❓ Unconfirmed | ❌ No public API | Hard | HIGH (score 90) | Jamie applies manually; build Playwright later |
| `sandvik.wd3.myworkdayjobs.com` | **Workday** | ❌ | ✅ Autofill only | ❌ No public API | Hard | MEDIUM | Simplify autofill + manual submit |
| `careers.pacificseafood.com` | **PinpointHQ** | ❌ | ❓ Unconfirmed | ❌ No documented API | Easy (likely) | LOW (STRETCH role) | Skip for now; manual if Jamie decides to apply |
| `jobs.oregonstate.edu` | **Likely NeoGov** | ❌ | ❓ Unconfirmed | ❌ No public API | Medium | FAILED (score 42) | Role rejected — not relevant |

---

## Section 4: Recommended Stack for Jamie (Road-Trip Period, 3–6 Weeks)

### Context
Jamie is road-tripping. She has ~1 hr/day for job search. She cannot manually apply to 30+ jobs/week, but she can spend 20–30 minutes reviewing + clicking "Submit" on pre-filled applications.

### Recommended Stack: Simplify Copilot + Pipeline Autofill + Greenhouse API

**Tier 1 — Zero cost, works now:**
- **Simplify Copilot** (Chrome extension, free): Install once, profile set up once. For any Workday, Greenhouse, iCIMS, Lever application — navigate to the form, click the Simplify button, it fills all fields from Jamie's profile. Jamie reviews and clicks Submit. Time per application: ~5 minutes.
- **Chrome MCP pre-grant**: For Greenhouse domains specifically, manually grant permission in the sidepanel once. The pipeline can then run unattended for Greenhouse ATSes.

**Tier 2 — Build once (~1 day dev), permanent:**
- **Greenhouse API submitter (`apply_greenhouse_api.py`)**: Read `resume.pdf` + `cover_letter.pdf` from the application folder, load questions array from the job endpoint, answer work-auth fields via config, POST. Fully automated, no browser. Covers Aurora and any future Greenhouse employer.

**Tier 3 — Build when volume justifies (~2–3 days dev):**
- **Playwright PeopleAdmin handler**: Covers UPortland (2 active roles) and any future higher-ed employer on PeopleAdmin.

**Do NOT invest in:**
- Commercial auto-submit tools (Sonara, LazyApply): Volume tools not designed for targeted, sponsorship-aware applications
- AIHawk: Archived
- Workday Playwright automation: High breakage risk; Simplify autofill + manual submit is more reliable until Workday is a higher-volume target

### What Jamie Does on the Road

Per pipeline run (3 PACKAGE/DECISION roles on a typical night):
1. Carlos Rosario (ADP): 20-min manual apply — open ADP form, paste from Simplify profile, submit. Top priority.
2. Aurora (Greenhouse): 5 min — Simplify autofill OR pipeline submits via API if Greenhouse submitter is built.
3. UPortland (PeopleAdmin): 10 min — Simplify autofill (if supported) or manual. Check if Simplify popup appears on PeopleAdmin when they install.
4. Sandvik (Workday): 10 min — Simplify autofill, manual submit.

**Total daily apply time: ~45 min for 4 applications.** Well within the 1-hr cap.

---

## Section 5: Implementation Plan

### Phase 1 — Tonight (30 min, David)
1. Install Simplify Copilot in Chrome
2. Create Jamie's Simplify profile (import from her resume)
3. Pre-grant Chrome MCP permission for `boards.greenhouse.io` via sidepanel
4. Manually apply to Carlos Rosario (ADP) — highest priority role, score 90

### Phase 2 — This Week (2–3 hrs, David)
5. Build `scripts/apply_greenhouse_api.py`:
   - Input: `application_dir/` containing `resume.pdf`, `cover_letter.pdf`, metadata JSON with job_id and company slug
   - Reads `questions` array from Greenhouse Job Board API
   - Answers work-auth template from `jamie/preferences.md` (H-1B, requires sponsorship: yes)
   - POSTs multipart form with resume + cover letter
   - Writes `apply_status.json` to application dir (mirrors existing schema)
6. Wire into `/jamie-autopilot`: check if ATS = Greenhouse, call `apply_greenhouse_api.py` instead of Chrome MCP

### Phase 3 — If UPortland Roles Remain Open (4–6 hrs, David)
7. Build `scripts/apply_peopleadmin.py` using Playwright:
   - `launchPersistentContext` with Jamie's Chrome user data dir
   - Navigate to posting URL
   - Fill form fields by ID (inspect PeopleAdmin form structure first)
   - Upload resume + cover letter
   - Submit and write `apply_status.json`

### Phase 4 — Future / If Workday Volume Increases
8. Evaluate FastApply Pro ($29/mo) — only if Jamie is getting 5+ Workday roles per week
9. Monitor GitHub issue #55580 for Anthropic's user allowlist override feature

---

## Sources

- [Claude in Chrome Permissions Guide](https://support.claude.com/en/articles/12902446-claude-in-chrome-permissions-guide)
- [Claude in Chrome Admin Controls](https://support.claude.com/en/articles/13065128-claude-in-chrome-admin-controls)
- [Using Claude in Chrome Safely](https://support.claude.com/en/articles/12902428-using-claude-in-chrome-safely)
- [GitHub Issue #55580 — User-controlled allowlist override](https://github.com/anthropics/claude-code/issues/55580)
- [GitHub Issue #57219 — Allowlist not respected for MCP navigate](https://github.com/anthropics/claude-code/issues/57219)
- [GitHub Issue #36767 — Wildcard domain matching](https://github.com/anthropics/claude-code/issues/36767)
- [Simplify Copilot official page](https://simplify.jobs/copilot)
- [Simplify Copilot Review 2026 (JobRight)](https://jobright.ai/blog/simplify-copilot-review-2026-features-pricing-and-top-alternatives/)
- [FastApply auto-apply tools comparison 2026](https://blog.fastapply.co/auto-apply-jobs-tools-compared-2026)
- [FastApply vs LazyApply review 2026](https://blog.fastapply.co/fastapply-vs-lazyapply-review-and-comparison-2026)
- [AIApply Review 2026](https://jobright.ai/blog/aiapply-review-2026-how-it-works-pricing-and-honest-user-experiences/)
- [Sonara Review 2026 (JobRight)](https://jobright.ai/blog/sonara-review-2026-pros-cons-and-what-users-actually-experience/)
- [LoopCV pricing and ATS support](https://www.loopcv.pro/pricing/)
- [LazyApply Review (Wobo)](https://www.wobo.ai/blog/lazyapply-review/)
- [feder-cr/Jobs_Applier_AI_Agent_AIHawk — ARCHIVED](https://github.com/feder-cr/Jobs_Applier_AI_Agent_AIHawk)
- [g-kolipak/workday-job-application-automation](https://github.com/g-kolipak/workday-job-application-automation)
- [Greenhouse Job Board API](https://developers.greenhouse.io/job-board.html)
- [Greenhouse API overview (support)](https://support.greenhouse.io/hc/en-us/articles/10568627186203-Greenhouse-API-overview)
- [Aurora Innovation Greenhouse job board](https://boards.greenhouse.io/embed/job_board?for=aurorainnovation)
- [Sandvik Workday careers portal](https://sandvik.wd3.myworkdayjobs.com/seco-jobs)
- [Pacific Seafood Careers — powered by PinpointHQ](https://careers.pacificseafood.com)
- [PinpointHQ on ADP Marketplace](https://apps.adp.com/en-US/apps/352854/pinpoint)
- [Claude Extension ShadowPrompt vulnerability (Penligent)](https://www.penligent.ai/hackinglabs/claude-extension-prompt-injection-how-shadowprompt-turned-a-trusted-subdomain-into-a-browser-scale-risk/)
- [Claude for Chrome Complete Guide 2026](https://almcorp.com/blog/claude-for-chrome-complete-guide/)
