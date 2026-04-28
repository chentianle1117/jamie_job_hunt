# 🐣 Oracle Job Search — Claude Skill

---
name: oracle-pipeline
description: >
  This skill should be used when the user asks to "run oracle", "find jobs for Jamie",
  "run the job search pipeline", "search jobs", "oracle job search", or "daily job digest".
  It runs the full Oracle daily job search pipeline for Jamie Cheng — searching for
  People Program Management, HR Specialist, Employee Engagement/Experience, OD/OCM,
  and entry-level Consulting roles, auditing the Notion database, enriching entries with
  cover letters and networking connections, and preparing email delivery.
version: 4.0.0
---

> Daily HR/L&D/OD/Consulting job search for Jamie (Yi-Chieh) Cheng.
> Run this skill when asked: "Run oracle", "Find jobs for Jamie", or "Run the job search pipeline"

---

## 🔄 STEP 0 — Sync Latest Updates

> **ALWAYS do this first.** Jamie's feedback and preferences may have been updated from her
> Mac sessions. Pull the latest before every run.

```bash
git pull origin main
```

Then read `jamie/profile_compact.md` — it contains all hard constraints, scoring formula,
and H1B quick reference. Only read `jamie/preferences.md` if you need the full
self-assessment table or networking templates (i.e., during enrichment, not discovery).

**After the run:** If you updated any reference files (h1b_verified.md, watchlist.md, etc.),
commit and push so Jamie's next session has the latest data.

```bash
git add jamie/ && git commit -m "Update reference files from Oracle run $(date +%Y-%m-%d)" && git push
```

---

## 🔌 STEP 0.5 — Pre-Fetch via APIs & Scripts (NEW v3.3)

> **Run BEFORE the main pipeline.** These scripts pull structured job data from public APIs
> and scraper libraries — faster, more reliable, and more exhaustive than WebSearch alone.
> Their output files are read by the main pipeline as additional discovery sources.

### 0.5a. Greenhouse + Lever API Fetch

```bash
cd "C:\Users\chent\Agentic_Workflows_2026\oracle-job-search"
python pipeline/scripts/fetch_ats_jobs.py
```

- Queries **public JSON APIs** (no auth needed) for all companies in `pipeline/ats_mapping.json`
- Greenhouse: `GET https://api.greenhouse.io/v1/boards/{slug}/jobs?content=true`
- Lever: `GET https://api.lever.co/v0/postings/{slug}?mode=json`
- Filters for People/HR/OD/L&D keywords, excludes Senior/Director/VP
- **Output:** `C:\Windows\Temp\ats_jobs.json` — read this in Step 2 as a pre-verified source
- These jobs are **already live** (API returns only active postings) — skip Chrome verification for them
- Also queries **Ashby boards** (SSR JSON API): `GET https://api.ashbyhq.com/posting-api/job-board/{slug}`
- **ATS coverage (v4.0):** 60+ Greenhouse slugs, 18 Lever slugs, 14 Ashby slugs (see `ats_mapping.json`)
- **Includes education/professional dev orgs** — ATD-affiliated companies, edtech, workforce dev
- **H1B status included per company** — `h1b: "confirmed"` entries skip manual verification

### 0.5b. JobSpy Scraper (optional — deeper LinkedIn/Indeed coverage)

```bash
# Default: 16 US search configs (P1 + P2 + P3 + local + education sector)
python pipeline/scripts/jobspy_search.py

# Education sector focus (ATD/CPTD orgs, workforce dev, edtech)
python pipeline/scripts/jobspy_search.py --edu-only

# Default + education sector
python pipeline/scripts/jobspy_search.py --include-edu

# Netherlands/EU pivot
python pipeline/scripts/jobspy_search.py --include-nl
```

- Scrapes LinkedIn, Indeed, Glassdoor concurrently using `python-jobspy`
- Indeed has **zero rate limiting** (best scraping source)
- LinkedIn caps at ~page 10 per IP (~100 results) — still catches jobs WebSearch misses
- **16 US configs** covering: P1 programs (Portland + remote), P2 OD/OCM/L&D ops, local Portland/Seattle, P3 consulting, education/CPT orgs, junior HRBP
- **Output:** `C:\Windows\Temp\jobspy_results.json` + `.csv`
- **Install once:** `pip install python-jobspy requests beautifulsoup4 pandas`

### 0.5c. Email Alerts Check (Gmail MCP — lightweight, 1 query only)

> **One quick Gmail scan at the start of each run.** Do NOT scan every email in detail.
> The goal is to catch any job alert digests from LinkedIn/Indeed/Glassdoor that might
> surface roles the pipeline would otherwise miss.
>
> ⚠️ Keep this step fast — 1 Gmail search, skim results for new URLs, add to pool and move on.
> The Google Sheet (tab "2026") is the ground truth for applied jobs — not email.
> Do NOT try to reconcile applied status from email history.

```
gmail_search_messages(q="subject:(job alert OR new jobs OR jobs for you) newer_than:2d", maxResults=5)
```

If results exist: for each email, extract job titles + URLs from the subject/snippet only.
If a title looks relevant (matches SKILL.md P1/P2 tier titles) → add URL to discovery pool.
Skip reading full email bodies — snippet is sufficient for quick triage.
These URLs still need Chrome/WebFetch verification (alerts often contain expired listings).

### 0.5d. LinkedIn "Top Job Picks" — PRIMARY Discovery Source (NEW v3.4.2)

> **This is the single highest-signal discovery source.** LinkedIn's recommendation algorithm
> already knows Jamie's profile, skills, work history, and search behavior — it pre-filters
> all 500M+ listings down to the ~381 most relevant. Use it at the start of EVERY run.

**How to access:**

1. In Chrome, navigate to:
   ```
   https://www.linkedin.com/jobs/collections/recommended/
   ```

2. This opens the **"Top job picks for you"** page — a **two-panel interface**:
   - **Left panel**: Scrollable job list, each card shows company, title, location, and H1B/PERM/E-Verify badges
   - **Right panel**: Full job description for the currently selected job — loads instantly when you click a listing
   - **URL updates** to `?currentJobId=JOBID` when you click a listing — each job has a stable permalink

3. **Scroll through the left panel** to collect all visible listings (381 results available). You can also click into individual jobs to read the full JD on the right panel WITHOUT leaving the page.

4. **To read a full JD**: Click the job title in the left panel → right panel updates with:
   - Full description (responsibilities, qualifications, company overview)
   - Hiring manager / job poster with LinkedIn profile (useful for outreach in Step 5)
   - Salary range, work type (on-site/hybrid/remote), applicant count, posting date

5. **Key filter signals visible per listing (no clicking needed):**
   - 🟢 **H1B badge** = employer confirmed H1B in LinkedIn's database — high priority for Jamie
   - **PERM badge** = employer has PERM history (likely willing to sponsor long-term)
   - **E-Verify badge** = on the federal E-Verify system (baseline for sponsorship likelihood)
   - **"X school alumni work here"** = alumni connection (USC or Wesleyan → mention in outreach)
   - **"Be an early applicant"** = posted recently, low competition — prioritize these
   - **"You'd be a top applicant"** = strong profile match — always evaluate these

**Recommended workflow per run:**
```
1. Navigate to https://www.linkedin.com/jobs/collections/recommended/
2. Scroll through left panel, noting all visible listings (title, company, location, badges)
3. Click each promising listing → read full JD in right panel
4. Copy job title, company, URL (from ?currentJobId= param or "share" button), and key JD details
5. Add all candidates to the discovery pool — treat as pre-vetted by LinkedIn's algorithm
6. These jobs still need H1B verification (check jamie/h1b_verified.md + WebSearch if unknown)
7. Proceed to Step 3 scoring as normal
```

> ⚠️ **Do NOT only screenshot the left panel.** Reading the full JD in the right panel is
> essential — the title alone won't tell you if the role requires 5+ years or if it's a fit.
> Click through each promising listing before scoring.

> ⚠️ **LinkedIn "Jobs for You" ≠ LinkedIn search results.** Do NOT use the LinkedIn search bar.
> The `/jobs/collections/recommended/` URL is the algorithm-curated feed — it surfaces roles
> specifically matched to Jamie's profile. The search bar returns generic keyword results.

### How Pre-Fetch & LinkedIn integrate with Step 2

> **LinkedIn "Top Job Picks" is now the PRIMARY discovery source (v3.5).**
> LinkedIn's algorithm already filters 500M+ listings to ~381 tailored recommendations.
> These are high-signal, pre-vetted candidates that cost zero WebSearch tokens.
>
> **Early-exit rule (v3.6 — Token Budget Optimization):**
> If LinkedIn Top Job Picks yields **5+ viable candidates** (pass hard constraints,
> worth evaluating), **skip Agents A-F WebSearch entirely.** LinkedIn already did
> the discovery work — running 6 parallel WebSearch agents on top is redundant
> and burns ~10K+ tokens for marginal yield.
>
> **Apr 3 data point:** Full secondary discovery (PSU/OHSU/Providence/Idealist/Greenhouse/Lever/
> watchlist — 3 parallel agents, 40+ searches) yielded 0 new verified picks on top of what LinkedIn
> already found. Idealist leads were all expired; Greenhouse IDs were stale; watchlist companies had
> no new openings. This validates the early-exit rule strongly.
>
> **When to run full discovery (Agents A-F):**
> - LinkedIn yields < 5 viable candidates
> - David explicitly says "run full discovery" or "deep search"
> - It's been 3+ days since the last full discovery run
> - Looking for cap-exempt roles specifically (LinkedIn doesn't filter for this well)
> - **Cap-exempt search is still worth running even with 5+ LinkedIn picks** — these are a separate
>   category LinkedIn doesn't surface well (university/hospital/nonprofit direct sites)
>
> **ATS pre-fetch** is still a supplement — run it if the Python scripts are available,
> but it's lower priority than LinkedIn.

In Step 2 discovery, BEFORE launching WebSearch agents:
1. Read `C:\Windows\Temp\ats_jobs.json` (if exists, < 24 hours old)
2. Read `C:\Windows\Temp\jobspy_results.json` (if exists, < 24 hours old)
3. Add all jobs from these files to the candidate pool
4. **ATS API jobs skip Chrome verification** (they are confirmed live by the API)
5. **JobSpy + email alert jobs still need Chrome verification** (scraped data may be stale)
6. Deduplicate by URL across all sources before proceeding to Step 3
7. **DO NOT score or pick from ATS results alone** — wait for ALL discovery agents to complete

---

## 🖥️ PREREQUISITES — Read Before Running

### Chrome Browser (REQUIRED)

> ⚠️ **CRITICAL: Claude in Chrome MUST be connected before running this pipeline.**
> Without Chrome, Claude cannot read full job descriptions or verify postings are live.
> **Proven failure mode:** In one session without Chrome, ALL 5 picks were dead jobs (0/5 success rate).
> Google search results and secondary aggregators (ZipRecruiter, WORK180, LinkedIn cached) do NOT
> update when a job closes. Only the actual job posting URL reflects true status.

**Before starting, check Chrome connection:**
```
Call: mcp__Claude_in_Chrome__tabs_context_mcp(createIfEmpty: true)
```

**If Chrome is NOT connected:**
1. STOP the pipeline immediately
2. Tell the user: "⚠️ I need your Chrome browser open with the Claude in Chrome extension connected before I can run the job search. Without it, I have no way to verify job postings are actually live — the last time I ran without Chrome, all 5 picks were dead. Please open Chrome and confirm the extension is connected, then I'll proceed."
3. Wait for user to confirm Chrome is open and extension is active
4. Re-check connection before proceeding

**Why Chrome matters — the "stale listing" problem:**
- Google search results show job postings from ZipRecruiter, WORK180, LinkedIn, and other aggregators
- These secondary sites do NOT update when the original job closes — they can show a listing as "active" for months after it's filled
- The ONLY reliable source of truth is the actual job posting URL (Greenhouse, Lever, Workday, company careers page)
- Without Chrome, I am essentially flying blind and picking from cached, potentially months-old data

**If Chrome IS connected:** Proceed with pipeline.

### User Action Required

The user (David) must have:
- Chrome browser open with Claude in Chrome extension connected
- LinkedIn logged in (for reading job postings and finding networking contacts)
- Chrome should remain open throughout the pipeline run (~15-30 minutes)

---

## 📍 Paths & Config

```
Base dir (Windows):   C:\Users\chent\Agentic_Workflows_2026\oracle-job-search\
Base dir (VM):        /sessions/*/mnt/Agentic_Workflows_2026/oracle-jamie/
Notion DB ID:         442438a9-e372-48b7-b5f5-5f6ed8ee8e99
Notion DS URL:        collection://442438a9-e372-48b7-b5f5-5f6ed8ee8e99
Notion view URL:      https://www.notion.so/ea7cccd43f7a47a6b93a196241eb8d61
Email from:           tianlechen0324@gmail.com
Email to:             jamiecheng0103@gmail.com
Google Sheet ID:      1tRN3KMGHOSyRMf14TRUj3wPldbM9fwDxVu9XsEH6s2E
Google Sheet Tab:     AI Search Bot Result
```

**Reference files** (token-efficient loading):
```
jamie/profile_compact.md    — LOAD FIRST: condensed profile, H1B cache, scoring formula (~60 lines)
jamie/watchlist.md          — 80+ target companies across 8 tiers (check every run)
jamie/h1b_verified.md       — Full H1B verification cache (only if company not in profile_compact)
jamie/outreach_templates.md — Jamie's networking style + message drafting protocol (only in Step 6)
jamie/preferences.md        — Full preferences (only if deep evaluation needed)
pipeline/ats_mapping.json   — ATS type + API slug for each watchlist company
```

**Pre-fetch data files** (generated by Python scripts before main pipeline):
```
C:\Windows\Temp\ats_jobs.json       — Greenhouse/Lever API results (fetch_ats_jobs.py)
C:\Windows\Temp\jobspy_results.json — LinkedIn/Indeed/Glassdoor scraper results (jobspy_search.py)
```

**Output files** (Claude writes these each run):
```
email_body.txt        — Bilingual email for Jamie
jobs_rows.json        — Google Sheets rows
cleanup_pages.json    — Page IDs archived this run
```

**Delivery:** Claude creates a Gmail draft directly using `gmail_create_draft` MCP tool — no script needed.

---

## 🛂 H1B vs Cap-Exempt — Critical Distinction (v3.6)

> **Cap-exempt employer ≠ H1B sponsor.** These are DIFFERENT things. NEVER conflate them.
>
> - **Cap-exempt** (501(c)(3) nonprofit / university / hospital / government) means the employer
>   can file an H1B petition at ANY time of year without the April lottery cap. BUT they still
>   must CHOOSE to sponsor — many cap-exempt employers have policies against it.
>
> - **H1B sponsor** = the employer has confirmed they will file an H1B petition for the employee.
>   This is what Jamie actually needs.
>
> **Scoring rule (v3.6):**
> - If cap-exempt status is confirmed but H1B sponsorship is unknown → tag as ❓, note "verify
>   in screening call — cap-exempt but sponsorship policy unknown"
> - Only tag 🏛️ Cap-Exempt with +10 bonus if you have EVIDENCE they sponsor (e.g., USCIS PERM
>   filings, LCA database, prior job postings mentioning sponsorship, press reports)
> - Do NOT assume cap-exempt = will sponsor. Many nonprofits explicitly do NOT sponsor H1B.
>
> **Apr 3 error:** Pathfinder Network and Benchmark Senior Living were initially tagged 🏛️ Cap-Exempt
> with +10 scoring bonus. Late Gemini verification confirmed neither sponsors H1B. Both were
> downgraded to ❓ Unknown. This cost tokens and may have inflated Jamie's expectations.

---

## 🔁 Pipeline Philosophy — Quality Over Quantity

> **Core principle: Surface ALL genuinely viable jobs each run. Let Jamie choose.**
>
> Jamie can carefully apply to 1-2 jobs per day. Each application takes 30-60 min of her real time.
> Every job surfaced must be genuinely worth that investment based on her ACTUAL experience.
>
> **Show all ⭐+ candidates. Enrich the top 3. No artificial cap.**
> It's better to send Jamie 0 jobs than to send 1 bad one. But if there are 5 good ones,
> show all 5 — she'll prioritize. The email digest ranks them; enrichment (cover letter,
> networking) only runs for the top 3 by score.
>
> **The resume exaggeration trap:**
> Jamie's resume (like most resumes) uses strong framing. When writing tailoring suggestions,
> do NOT further boost or invent on top of that framing. Look at what she literally did —
> managed 3 programs, 600+ trained, 20+ vendors, onboarding redesign — and only reword within
> that scope. If the JD requires something she hasn't done, that's a GAP, not a reframe.
>
> **Location strategy (updated v2.7) — in-person/hybrid first:**
> Remote roles attract national competition. Everyone applies remotely. Jamie's H1B status + ~3 years
> = tougher to stand out vs. a local US citizen with 5 years who applies nationally.
>
> In-person and hybrid roles have far less competition. Jamie should lean into the local advantage.
> West Coast (Portland, Seattle, Bay Area, San Diego, LA) is ideal, but any US in-person/hybrid role
> is acceptable if it's a good P1–P2 fit. Even non-West-Coast cities (Austin, Chicago, NYC, Denver)
> are on the table if the role is excellent.
>
> **Only surface remote roles if they are near-perfect P1 program management or consulting fits
> with confirmed H1B sponsorship and Oregon listed as eligible state. A decent in-person role
> anywhere in the US beats a mediocre remote role every time.**

---

## 🤖 Multi-Agent Architecture (v3.1 — VERIFY ALL)

> **The pipeline can be parallelized using Claude's Agent tool.** This dramatically
> speeds up the search by running independent workstreams simultaneously.

> ⚠️ **CRITICAL RULE (v3.1): Every candidate found by ANY agent MUST be Chrome-verified**
> **before it goes anywhere — into today's picks OR into the next_run_priority_queue.**
> **Never carry forward an unverified URL. Never defer verification to "next run".**
> A URL that hasn't been Chrome-verified (or WebFetch-verified when Chrome is blocked)
> is unknown status — it could be expired, could be Canada-only, could be 5+ yrs.
> **The priority queue must only contain verified-live candidates.**

### Ashby Board Verification — CRITICAL (learned Mar 25, updated Mar 25)
> ✅ **UPDATE (Mar 25 Run 2):** WebFetch DOES work for Ashby — Ashby uses SSR (server-side rendering) and returns
> real HTML containing `window.__appData` with `"posting":null` or `"posting":{...}`. WebFetch is now the
> preferred fast-path for Ashby verification (same signal as Chrome, no browser overhead).
>
> WebSearch and LinkedIn indexing are still STALE — they show postings as "live" weeks/months after expiration.
> Do NOT trust WebSearch/LinkedIn as final answer for Ashby.
>
> **Definitive Ashby expired signal (WebFetch or Chrome):** Response body contains `"posting":null`
> **Definitive Ashby live signal (WebFetch or Chrome):** Response body contains `"posting":{...}` with actual job data
> If `"posting":null` → job is gone. Period. Do not second-guess LinkedIn or search results.
>
> **Ashby verification checklist (use WebFetch first; fall back to Chrome if WebFetch fails/blocked):**
> 1. `WebFetch(ashby_url)` → search response for `"posting":null` or `"posting":{`
> 2. If `posting:null` → EXPIRED. If posting has content → LIVE (read YOE, location, etc. from the JSON)
> 3. If WebFetch is blocked or returns empty HTML → fall back to Chrome `get_page_text`
> 4. WebSearch results showing "LIVE" for Ashby jobs = UNRELIABLE. Always direct-verify.

### Verification Fallback (when Chrome is blocked)
Some job boards block Chrome navigation (Greenhouse, LinkedIn, Stripe). For these:
1. Try `WebFetch(url)` first — if it returns a real JD, the posting is live
2. If WebFetch also fails, use `WebSearch("site:domain.com company role name 2026")` to confirm status
3. **For Ashby specifically:** WebFetch now confirmed reliable (SSR HTML contains `posting:null` signal).
   Use WebFetch as primary; fall back to Chrome `get_page_text` only if WebFetch fails/blocked.
   Do NOT rely on WebSearch/LinkedIn indexing as final answer — they are stale by weeks/months.
4. If neither works and status is unknown → mark as "⚠️ unverified" in the queue, do NOT include in today's picks
5. Always log the verification method used (Chrome / WebFetch / WebSearch)

### Greenhouse/Lever Verification — CRITICAL (learned Apr 3 run, v3.6)
> ⚠️ **Greenhouse job IDs decay fast.** A job ID found via WebSearch may be weeks old.
> WebFetch on `job-boards.greenhouse.io/{slug}/jobs/{id}` often returns the WRONG JOB
> (another active posting at the same company) or a generic job board page — NOT the target role.
> This silently produces false "live" signals.
>
> **Reliable Greenhouse verification:**
> 1. WebFetch the specific URL → if returned content shows a DIFFERENT job title than expected → DISCARD
> 2. The job is only confirmed live if the fetched title matches the expected title exactly
> 3. If mismatched: the original job ID is expired/archived; the board is showing a fallback listing
> 4. Do NOT carry forward Greenhouse IDs from secondary agents unless title-verified
>
> **For Lever:** Same principle — WebFetch the URL, confirm title match before treating as live.
>
> **Practical implication:** WebSearch-sourced Greenhouse/Lever jobs have a HIGH stale rate.
> Only include them in today's picks if explicitly title-verified. Flag all others as ⚠️ unverified.

### Agent Decomposition

```
┌─────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR (main thread)                    │
│  Reads SKILL.md → Spawns agents → Collects results → Delivers  │
└──────────┬──────────────┬──────────────┬───────────────────────┘
           │              │              │
    ┌──────▼──────┐ ┌────▼────┐ ┌──────▼──────┐
    │  STEP 1     │ │ STEP 2a │ │ STEP 2b     │
    │  DB Audit   │ │ WebSearch│ │ Watchlist   │
    │  (Notion    │ │ Discovery│ │ Check       │
    │   MCP)      │ │ (parallel│ │ (parallel   │
    │             │ │  queries)│ │  WebSearch) │
    └──────┬──────┘ └────┬────┘ └──────┬──────┘
           │              │              │
           └──────────────┼──────────────┘
                          │
                   ┌──────▼──────────────────────────────────────┐
                   │  STEP 3 — VERIFY ALL DISCOVERED CANDIDATES  │
                   │  (main thread — Chrome + WebFetch fallback) │
                   │                                             │
                   │  For EVERY URL returned by agents A/B/C/D: │
                   │  1. Chrome navigate → get_page_text          │
                   │  2. If blocked → WebFetch(url)              │
                   │  3. If still blocked → WebSearch to confirm │
                   │  4. Record: live/expired/unknown + YOE      │
                   │  5. Apply hard gates (5+ yrs, no H1B, etc.) │
                   │                                             │
                   │  ✅ Verified live + passes gates → picks    │
                   │  ❌ Expired/blocked/fails gates → discard   │
                   │  ⚠️ Unknown → queue with "unverified" flag  │
                   └──────┬──────────────────────────────────────┘
                          │
              ┌───────────┼───────────┐
              │           │           │
        ┌─────▼────┐ ┌───▼────┐ ┌───▼────┐
        │ ENRICH   │ │ ENRICH │ │ ENRICH │
        │ Pick #1  │ │ Pick #2│ │ Pick #3│
        │ (cover   │ │        │ │        │
        │  letter, │ │        │ │        │
        │  network,│ │        │ │        │
        │  outreach│ │        │ │        │
        │  drafts) │ │        │ │        │
        └─────┬────┘ └───┬────┘ └───┬────┘
              │           │           │
              └───────────┼───────────┘
                          │
                   ┌──────▼──────┐
                   │  DELIVERY   │
                   │  Gmail +    │
                   │  Notion     │
                   └─────────────┘
```

### Parallelization Rules (v3.2 — exhaustive, auto-compact safe)

**Context auto-compact:** Claude Code automatically compacts conversation history when approaching the context limit. This applies to ALL sessions including sub-agents. The pipeline is designed to be resilient to compaction: every agent writes results to a temp file progressively (every 5 URLs), so compaction never loses work. If the main thread compacts mid-pipeline, it resumes from the last written file.

- **Step 1 (DB Audit)** can run simultaneously with **Step 2 (Discovery)** — they're independent
- **Step 0.5 (Pre-Fetch)** — run Python scripts BEFORE agents: `fetch_ats_jobs.py` (Greenhouse/Lever APIs) + `jobspy_search.py` (Indeed/LinkedIn scraper) + Gmail alerts check. Read their output JSONs into the candidate pool.
- **Step 2 Discovery** — launch ALL of the following as background agents simultaneously:
  - Agent A: LinkedIn Greenhouse/Lever site: searches (P1 batches A–H10)
  - Agent B: LinkedIn P2 batches (J–R15) + P3 consulting batches (S–X)
  - Agent C: Direct company career sites from watchlist.md Tier 1-2 (tech + gaming)
  - Agent D: Cap-exempt employers (nonprofits, hospitals, universities — Tier 3) + HigherEdJobs
  - Agent E: Alt boards (Handshake, Built In, SHRM, Idealist, Wellfound) + Remote boards (FlexJobs, WWR, Remote.co)
  - Agent F: PNW local searches (Portland/Seattle Batches Y–AF) + Greenhouse/Lever bulk WebSearch
  - Each agent returns a raw URL list + title + company. No verification — just discovery.
  - **⚠️ AGENT OUTPUT QUALITY RULES (v3.4.1):**
    - Return ONLY direct job posting URLs (containing a specific job ID or posting slug)
    - Do NOT return search result pages, category pages, or aggregator landing pages
    - Do NOT return LinkedIn hub pages (e.g., linkedin.com/jobs/hr-coordinator-jobs)
    - Do NOT return Glassdoor search URLs (e.g., glassdoor.com/Job/remote-...-jobs-SRCH_...)
    - Each result MUST have: exact job title, company name, direct apply URL
    - If a WebSearch only returns aggregator pages, note "no direct URLs found" and move on
    - Dedup within each agent: same company+title = one entry only
  - **⚠️ SKIP LIST IS COMPANY+TITLE PAIRS (v3.4.1):**
    - Do NOT skip an entire company. Only skip the exact (company, role title) pair.
    - Example: skip "Early Career PM @ Roblox" but keep "People Ops Coordinator @ Roblox"
- **⚠️ WAIT GATE: ALL discovery agents (A–F) MUST complete before Step 3 begins.**
  Do NOT start verification or scoring based on ATS pre-fetch alone. The cap-exempt
  and Portland-local roles from Agents D and F are often the best picks — they take
  longer to discover but are higher value for Jamie's specific situation.
- **Step 3 (Verification — ALL candidates, exhaustive):**
  - **Route by ATS type** (see Step 3a URL routing table)
  - **Main thread:** Ashby URLs (Chrome `get_page_text`) + LinkedIn URLs (Chrome)
  - **Parallel background agents:** all other ATSes (Greenhouse, Lever, Workday, direct sites via WebFetch)
  - Launch ceil(non-Ashby count / 15) agents in parallel — max 6 simultaneous
  - Each agent writes `verify_batch_{id}.json` progressively (every 5 URLs verified)
  - Main thread collects all batch files → merges into `verified_candidates.json`
  - **ALL candidates verified before Step 4.** No carryforward of unverified URLs.
- **Step 6 (Enrichment)** — launch 3 parallel background agents (one per pick). Each writes a complete Notion page draft, cover letter, networking contacts, outreach messages.
- **Delivery** — serial (depends on enrichment completing). Main thread only.

### Priority Queue Rules (next_run_priority_queue.md)
- **Only verified-live candidates enter the queue.** No unverified URLs.
- Every queue entry must record: `verified_date`, `verified_method` (Chrome/WebFetch/WebSearch), `live_status`, `yoe_req`, `location`.
- At the START of the next run, re-verify Tier 1 queue entries (they may expire overnight).
- Expired entries → mark as "Pass 👋" in Notion, remove from queue immediately.
- `verified_candidates.json` persists across sessions — if interrupted, resume from this file.

### When to Use Agents vs. Main Thread
- **Use Agent tool** for: discovery WebSearch batches, WebFetch verification batches, cover letter writing, networking research
- **Use main thread** for: Chrome verification (Ashby + LinkedIn), Notion MCP calls, Gmail draft, file writes, collecting agent outputs
- **Use `run_in_background: true`** for ALL discovery agents AND all WebFetch verification agents
- **Progressive writes mandatory** for any agent doing >5 sequential verifications — write partial results to file, do not hold in memory

### Model Selection — Use the Cheapest Model That Can Do the Job (v3.4.2)

> Token spend compounds fast across parallel agents. Defaulting everything to Sonnet wastes
> budget on mechanical tasks that Haiku handles perfectly. Always specify `model:` explicitly.

| Agent task | Model | Reason |
|---|---|---|
| Discovery WebSearch batches (A–F) | `haiku` | Keyword search + URL extraction — no judgment needed |
| WebFetch verification batches | `haiku` | Read page → check live/expired — mechanical |
| Notion DB audit / scoring patch | `haiku` | Formula application — pure computation |
| Notion CRUD (add/update pages) | `haiku` | Property writes — no judgment |
| Watchlist / ATS API fetch | `haiku` | Structured data pull — no judgment |
| Step 1 DB audit agent | `haiku` | Read Notion → check missing fields → update |
| Step 3 verification agents (non-Ashby) | `haiku` | WebFetch + live/expired decision |
| Step 6 enrichment agents (cover letter, outreach) | `sonnet` | Drafting requires voice + judgment |
| Fit evaluation / scoring for new roles | `sonnet` | Requires understanding of Jamie's situation |
| LinkedIn "Jobs for You" browsing + JD reading | `sonnet` | Judgment-heavy triage |
| Orchestrator / main thread | `sonnet` | Coordinates everything — needs full capability |

**Rule:** In every `Agent` tool call, set `model: "haiku"` unless the task is in the Sonnet row above.
**Never** leave model unspecified for background agents — it defaults to Sonnet and burns budget.

---

## ⚡ Urgency Scoring (v3.0)

> Jobs posted < 3 days ago at companies with fast hiring cycles get an urgency flag.

### Urgency Levels
- **⚡ URGENT — apply within 24-48 hrs**: Posted today or yesterday. Fresh listing.
- **🔶 FRESH — apply this week**: Posted 2-7 days ago. Still early in the applicant pool.
- **⏳ AGING — apply soon or skip**: Posted 8-14 days ago. Likely many applicants already.
- **💤 STALE — skip unless perfect fit**: Posted 15-30 days ago. High competition.

### In the Email Digest
Prepend urgency tag to each pick:
```
⚡ URGENT #1  Early Career PM @ Roblox  (posted yesterday!)
🔶 FRESH #2  Talent Engagement @ Flatiron  (posted 5 days ago)
```

### In Notion Page
Add urgency level to the Notes property:
```
⚡ URGENT — posted Mar 23, apply by Mar 25
```

---

## 📋 Pipeline Steps

### Step 1 — Audit Existing Notion DB

> **⚠️ CRITICAL: `notion-search` returns max 10 results per query. The DB may have 20–40+ entries.**
> You MUST run MULTIPLE search queries with varied keywords to find ALL entries before auditing.
> Never assume you've seen everything after a single search.

**1a-pre-0 — DUAL DEDUP: Read BOTH Google Sheet AND Notion before anything else (v4.0)**

> **Two sources. Different roles. Both required. Check BOTH every run.**
>
> | Source | What it contains | What it catches |
> |--------|-----------------|-----------------|
> | **Google Sheet (tab "2026")** | Every job Jamie has ever applied to, including manual apps | Jobs applied to outside this pipeline that never entered Notion |
> | **Notion DB** | Active pipeline entries + Jamie's personal decisions ("Not a fit") | Roles Jamie reviewed and rejected for reasons she may not have written down |
>
> **The relationship:** Notion is the intermediate staging area where new finds land and Jamie reviews them.
> The Google Sheet is the complete applied history. Neither is a subset of the other — you need both.
>
> Confirmed failure mode: Flatiron Health was resurfaced despite Jamie being rejected — because the
> pipeline checked Notion only (which didn't have the manually-applied role from a prior session).

**Step A — Fetch Google Sheet (tab "2026"):**

```
WebFetch(
  url="https://docs.google.com/spreadsheets/d/1tRN3KMGHOSyRMf14TRUj3wPldbM9fwDxVu9XsEH6s2E/export?format=csv&gid=1018026840",
  prompt="Extract all rows as {company, title, status} objects. Tab name is '2026'."
)
```

From this, build **Sheet Skip List** — all (company, title) pairs that have been applied to or rejected.
> If WebFetch fails: retry once. If still fails, flag to David and proceed with Notion-only — note gap in email.

**Step B — Read Notion DB (all entries, all statuses):**

Run ALL 10 batches in Step 1a (below) to collect every Notion page ID + status.
From this, build **Notion Skip List**:
- Status = "Not a fit" → **HARD SKIP** (Jamie personally reviewed and rejected — her decision, no override)
- Status = "Pass" → **HARD SKIP** (pipeline filtered or Jamie passed)
- Status = "Rejected/Unavailable" → **HARD SKIP** (company rejected Jamie or role closed)
- Status = "Applied" → **SOFT SKIP** (already submitted — don't add duplicate page)
- Status = "Not started" → **SOFT SKIP** (already in Notion pipeline — don't add duplicate page)

> ⚠️ **Since notion-search doesn't support status filters directly, use keyword batches.**
> Collect ALL pages, then check each page's Status field. See Step 1a for the 10 batch queries.

**Combined "Do Not Surface" list = Sheet Skip List + Notion Skip List.**
Log the full combined list before discovery. This is the gate for ALL new picks.

> ⚠️ **DEDUP GATE — MANDATORY BEFORE ANY NOTION PAGE CREATION (v4.0):**
> Before creating ANY new Notion page in Step 6, cross-check the company + title pair against
> the combined "Do Not Surface" list. If a match exists:
> - "Not a fit" / "Pass" / "Rejected" (from either source) → **DO NOT create page. Skip the role.**
> - "Applied" / "Not started" (from either source) → **DO NOT create duplicate. Note in email instead.**
>
> **This check happens BEFORE enrichment, cover letter, or networking research for that role.**
> Enriching a duplicate wastes budget and pollutes Notion with noise Jamie has to manually clean.
>
> **Same-company, different-title = different role = OK to add.**
> Same-company + same-title = DUPLICATE = skip, even if job IDs differ.

> **Why Notion matters even though Sheet is ground truth:**
> Jamie marks roles "Not a fit" in Notion when she's personally reviewed them — bad culture,
> wrong level, someone she knows there. These rejections may never appear in the Sheet.
> Both sources carry information the other doesn't. Check both, every time.

> ⚠️ **DEDUP BY COMPANY+TITLE PAIR, NOT BY COMPANY ALONE (v3.4.1):**
> The skip list should contain **specific (company, role title) pairs**, not entire companies.
> Jamie may have applied to "Early Career PM" at Roblox — but Roblox could post a
> "People Operations Coordinator" next week. That's a DIFFERENT role and should NOT be skipped.
>
> **Skip rule:** Only skip a discovered role if there is an EXACT or near-exact title match
> at the same company in the Google Sheet or Notion DB. "Near-exact" means the core role
> is the same (e.g., "People Ops Associate" ≈ "People Operations Associate").
> A different role at the same company is NOT skipped.
>
> **Example:**
> - Google Sheet has: Roblox — "Early Career Program Manager" → skip "Early Career PM @ Roblox"
> - Google Sheet has: Roblox — "Early Career Program Manager" → DO NOT skip "People Ops Coordinator @ Roblox"
> - Notion has: Flatiron — "TEE Associate" (Not a fit) → skip "TEE Associate @ Flatiron"
> - Notion has: Flatiron — "TEE Associate" (Not a fit) → DO NOT skip "L&D Coordinator @ Flatiron" (if it existed)
> - Notion has: Flatiron — "TEE Associate" (Pass) → skip "TEE Associate @ Flatiron"

**Combined "Do Not Surface" list = Notion "Not a fit" + Notion "Pass" + Notion "Rejected/Unavailable" + Google Sheet rejections.**
When a discovered role matches any entry on this combined list → **skip immediately, no scoring needed.**

**1a. Exhaust the full DB with multi-batch searches** — Run ALL of the following queries in sequence, collecting unique page IDs across all batches:

```
Batch 1: query="coordinator analyst"              → OD/PM/L&D coordinator and analyst roles
Batch 2: query="HR people operations"             → HR, People Ops, HRBP entries
Batch 3: query="consulting talent"                → consulting, talent management, T&O roles
Batch 4: query="program manager"                  → all program manager variants
Batch 5: query="specialist partner generalist"    → specialists, partners, generalists
Batch 6: query="Mercer Disney Ampere Instacart"   → known active companies (update each run!)
Batch 7: query="Redox Newsela Clarios"            → more active companies
Batch 8: query="pass rejected applied"            → catch Pass 👋 and other status entries
Batch 9: query="change management OCM learning"   → OCM, L&D, OD variants
Batch 10: query="experience business partner"     → HRBP and EX variants
```

⚠️ **Update Batch 6 & 7 company names each run** — replace with the actual companies currently in the DB. After each run, the companies will change. Run extra batches if DB is known to be large (30+ entries).

Deduplicate by page ID across all batches. This should surface all entries.
If a batch returns 10 results, run additional keyword-varied queries until batches return <5 new unique IDs.

**1b. Finalize skip list** — Merge the "Do Not Surface" list from step 1a-pre-0 with the Google Sheet rejections and ANY remaining Notion entries (any status) to get a complete (company, role title) dedup map. Log the full list before proceeding to discovery.

> **Status priority for the skip list:**
> - "Not a fit" = Jamie personally reviewed and rejected → HARD SKIP, highest priority
> - "Pass" = pipeline auto-filtered or Jamie passed → HARD SKIP
> - "Rejected/Unavailable" = company rejected Jamie or role closed → HARD SKIP
> - "Applied" = already submitted → SOFT SKIP (don't add duplicate Notion entry, but note if role is still open)
> - "Not started" = in Notion but not yet applied → SOFT SKIP (already tracked, don't add duplicate)

Do NOT skip entire companies — only skip the specific (company + title) pair that was tracked.

**1c. Verify ALL "Not started" and "New 🆕" entries via Chrome — METICULOUS and AGGRESSIVE (v4.0)**

> ⚠️ **Verify ALL "Not started" entries, not just new ones.** Notion accumulates stale entries
> over time because the pipeline only verified them when they were added — but jobs expire daily.
> Known problem: many existing Notion pages have dead links that were never cleaned up.
> Every run must audit the full "Not started" backlog, not just what was added today.

**Priority order for verification:**
1. **All "Not started" entries** — these are in Jamie's review queue. If the link is dead, she should NOT be spending time on it.
2. **All "New 🆕" entries added this run**
3. Other statuses (Applied, Interview) — verify only if the posting date is > 30 days old

**For EACH entry to verify:**

**DO NOT rely on tab title alone.** Always read the actual page content.

```
Step 1: navigate to the job URL
Step 2: get_page_text(tabId) — read actual text, not just screenshot
Step 3: Check content for status signals (see below)
Step 4: If expired → immediately update Notion status to "Pass 👋" with reason
```

**Status signals to look for in page TEXT:**
- ✅ Live: "Apply now", "Submit application", active application form visible
- ❌ Dead (Greenhouse): page text contains "An error occurred" OR URL has `?error=true` OR title mismatch (different job loaded)
- ❌ Dead (Lever): page returns HTTP 404 OR contains "Job not found" OR "This job is no longer available"
- ❌ Dead (Workday): page text contains "The page you are looking for doesn't exist" with a "Search for Jobs" button
- ❌ Dead (LinkedIn): text contains "No longer accepting applications" OR "This job is no longer available"
- ❌ Dead (LinkedIn — ghost listing): text shows "Reposted X months/years ago" AND applicant count is 0 or near-zero — zombie listings never removed
- ❌ Dead (Ashby): WebFetch response body contains `"posting":null`
- ❌ Dead (General): text contains "This position has been filled" OR "job has been removed" OR "position is closed"
- ❌ Dead (Redirect): URL redirected to generic `/jobs` or search results page (not a specific JD)
- ❌ Dead (ZipRecruiter/Indeed): "This job listing is no longer active"
- ❌ Visa fail: text contains "US citizens only", "no visa sponsorship", "must be authorized to work"
- ❌ No URL / bad URL: Notion entry has only a company homepage (`company.com/careers`) with no specific job ID — unverifiable → Pass immediately

**For entries on company career sites — extra verification step:**
- Greenhouse: WebFetch the URL first (fast). If title in response ≠ expected title → EXPIRED (Greenhouse silently serves a different job when the original is gone)
- Lever: WebFetch → 404 or "Job not found" = expired
- Workday: WebFetch or Chrome → "page doesn't exist" = expired
- Ashby: WebFetch → check for `"posting":null` = expired (reliable signal)
- LinkedIn: Chrome only — check for "No longer accepting applications"

**If live → extract posted date (REQUIRED):**
- Look for "Posted X days ago", "Published date", or date in the page metadata
- Record the exact or approximate posted date
- Posted > 30 days ago → mark as 💤 STALE; still keep in Notion for Jamie to decide
- If posted date cannot be determined → note "posted date unknown"

**1d. Aggressive Pass Protocol (v4.0) — act on expired entries immediately**

> ⚠️ Do NOT defer cleanup. When a link is confirmed dead, update Notion RIGHT NOW.
> Dead links sitting in "Not started" waste Jamie's review time — she clicks them and gets 404s.
> The purpose of Step 1 is to clean the deck BEFORE surfacing new picks, not after.

For every entry confirmed expired or dead:
1. Update Notion **Status** → "Pass 👋"
2. Update Notion **Notes** → reason + date (e.g., "Expired — confirmed 404 on 2026-04-03", "Greenhouse error page — original posting removed", "LinkedIn: No longer accepting applications")
3. Log it in the run summary (count of entries cleaned up)

> Do NOT delete Notion entries — preserve as historical record. Just change Status + add Notes.
> The `cleanup_pages.json` file is NO LONGER used. Skip writing it.

**Cleanup target:** The goal of each Step 1 audit is zero "Not started" entries with dead links.
If there are 10+ stale entries to clean, run a haiku-model background agent to batch the Notion updates:

```
Agent prompt: "Update these Notion pages to Status='Pass 👋' with Notes='[reason]':
  [list of page IDs + reason per page]
  Use notion-update-page for each. Model: haiku."
```

**1e. Audit summary** — At the end of Step 1, report:
- # entries verified (total checked)
- # entries marked Pass 👋 (expired/dead links cleaned up)
- # entries still active in "Not started" queue (Jamie's current review backlog)
- # entries skipped (Applied/Interview — not re-verified unless old)

Include this in the email digest so Jamie can see her Notion is clean.

### Step 2 — Discovery (cast wide, filter strict)

> **Search philosophy: scan up to ~1000 listings across all sources, surface ~20–40 candidates for closer review, pick at most 3.**
> The search effort is deliberately large. The filter is deliberately strict.
> More searching = more surface area to find the 1–3 genuinely excellent fits.
> Do not stop after the first few pages or first keyword batch.

> 🚫 **NO PARTIAL RUNS — ALL BATCHES MANDATORY (v3.1 mandate):**
> Multi-agent parallelization is for SPEED only — it must NOT reduce coverage.
> Every batch in sections 2a, 2b, 2c, 2d MUST run in every pipeline execution.
> Do NOT skip batches due to "enough candidates found" or "time constraints."
> The pipeline must complete all batches before moving to Step 3 verification.
> If token/time limits are a concern: launch more background agents, not fewer batches.
> **Minimum required: all P1 LinkedIn batches (A–H10) + all direct career sites (2b) + all watchlist checks (2c) + at least one alternative board (2d).**

#### 2a. LinkedIn (Chrome — primary platform)

Run ALL of the following search batches in LinkedIn. Use Chrome tabs in parallel where possible.
For each batch: scroll through ALL results (not just first 5), click into any JD that looks plausible.

**Base LinkedIn URL template:**
```
https://www.linkedin.com/jobs/search/?keywords={KEYWORD}&f_WT=2&f_TPR=r604800&location=United%20States&sortBy=DD
```
(Remote, past 2 weeks, sorted by date)

**LinkedIn search batches — run ALL of these:**

> **P1 PRIORITY BATCHES — run these first, always:**
```
Batch A:  "people programs manager" OR "people program manager"
Batch B:  "talent development program manager"
Batch C:  "early talent program manager" OR "early talent programs"
Batch D:  "employee experience program manager"
Batch E:  "people operations program manager" OR "HR program manager"
Batch F:  "process improvement" OR "workflow optimization" "people" OR "HR"
Batch G:  "program manager" "talent" OR "people" OR "employee experience"
Batch H:  "employee engagement" program manager OR coordinator
Batch I:  "people programs" coordinator OR specialist OR lead
Batch H2: "early career program manager" OR "university programs manager" OR "campus programs coordinator"
Batch H3: "talent and engagement" associate OR coordinator
Batch H4: "people programs associate" OR "talent programs associate"
Batch H5: "talent management" program manager OR coordinator (NOT recruiting)
Batch H6: "talent program" development OR specialist OR coordinator
Batch H7: "talent development" program coordinator OR manager (NOT instructional design)
Batch H8: "talent operations" coordinator OR manager OR specialist
Batch H9: "talent strategy" analyst OR associate OR coordinator
Batch H10: "workforce planning" coordinator OR analyst (people programs scope)
```

> **P2 BATCHES — engagement, OD, OCM:**
```
Batch J:  "employee engagement manager" OR "employee experience manager"
Batch K:  "organizational change management" OR "OCM analyst" OR "OCM specialist"
Batch L:  "change enablement" analyst OR specialist
Batch M:  "organizational development specialist" OR "OD analyst" OR "OD coordinator"
Batch N:  "culture and engagement" specialist OR manager
Batch O:  "HR transformation" analyst OR coordinator
Batch P:  "employee listening" OR "feedback programs" specialist OR manager
Batch Q:  "talent management specialist" (programs, not recruiting)
Batch R:  "learning operations" coordinator OR manager (NOT instructional design)
Batch R2: "employee insights" OR "people insights" analyst OR coordinator (program improvement focus)
Batch R3: "voice of employee" OR "feedback programs" analyst OR coordinator
Batch R4: "HR specialist" associate OR coordinator (NOT HR Manager / HRBP — Disney/entertainment type scope)
Batch R5: "service insights" OR "experience insights" analyst OR coordinator (people/program scope ONLY — not call center)
Batch R6: "workforce insights" OR "talent insights" analyst OR coordinator
Batch R7: "continuous improvement" specialist OR coordinator — people OR HR OR talent context
Batch R8: "program excellence" OR "process excellence" coordinator — people OR employee experience context
Batch R9: "CX" OR "customer experience" program coordinator — program improvement scope (verify: NOT call center ops)
Batch R10: "stakeholder feedback" OR "feedback loop" specialist — people OR talent context
Batch R11: "talent management" specialist OR coordinator (programs focus, NOT recruiting/TA)
Batch R12: "talent program" specialist OR coordinator OR analyst (program development scope)
Batch R13: "succession planning" OR "talent review" coordinator OR analyst (talent mgmt programs)
Batch R14: "talent initiatives" OR "people initiatives" coordinator OR specialist
Batch R15: "performance management" program coordinator OR specialist (NOT HRIS/system admin)
```

> **P3 BATCHES — consulting (entry/analyst level only):**
```
Batch S:  "people advisory" analyst OR associate
Batch T:  "human capital" analyst OR consultant (entry level)
Batch U:  "talent consulting" analyst OR associate
Batch V:  "organizational development" consultant analyst
Batch W:  "HR consulting" analyst OR associate
Batch X:  "workforce transformation" analyst
```

**Also run local Portland/Seattle batches (remove `f_WT=2` remote filter, add `f_WT=1%2C3` for on-site/hybrid, use `f_TPR=r2592000` for 30-day window):**

> **⚠️ EXPANDED LOCAL SEARCH MANDATE (updated Mar 2026):** Local Portland/Seattle in-person/hybrid roles must be searched thoroughly every run. On-site presence is a real competitive advantage for Jamie vs. remote applicants. Use the 30-day window (r2592000) for local searches. Broader job titles are valid locally — but still apply the 4-year max experience rule.

```
Batch Y:  "program manager" people OR HR OR talent — Portland, OR (on-site/hybrid)
Batch Z:  "employee engagement" OR "employee experience" specialist OR coordinator — Portland, OR + Seattle, WA
Batch AA: "people operations" associate OR coordinator OR specialist — Portland, OR (on-site/hybrid)
Batch AB: "organizational development" OR "OD specialist" — Portland, OR + Seattle, WA
Batch AC: "talent development" OR "learning programs" coordinator — Portland, OR + Seattle, WA (NOT instructional design)
Batch AD: "HR associate" OR "HRBP associate" OR "people coordinator" — Portland, OR + suburbs (Beaverton, Hillsboro, Vancouver WA)
Batch AE: "culture specialist" OR "engagement coordinator" OR "workforce development" — Portland, OR + Seattle, WA
Batch AF: "training coordinator" OR "training specialist" — Portland, OR + Seattle, WA (verify: program delivery focus, NOT retail/store ops)
```

**Local broader-title guidance:** For Portland/Seattle in-person roles, also accept these broader titles IF job content is strong (OD, L&D ops, employee experience, program management, engagement):
- HR Associate / People Operations Associate (early career, ≤4 yrs required)
- Training Specialist / Training Coordinator (program design/delivery focus — NOT retail store training)
- Learning & Development Specialist (if NOT instructional design / Adobe Creative Suite / e-learning authoring)
- Employee Experience Coordinator
- Workforce Development Specialist (program ops focus — NOT vocational/trade certification)
- People Coordinator / HR Coordinator (career-building content, not pure admin)

**Hard reject even for local:** Retail operations training, HRIS admin, payroll, labor/union relations, full-cycle recruiting focus, "US Person only" / no H1B, 5+ years required.

> **When LinkedIn returns mostly staffing agency results:**
> Remove `f_TPR=r604800` (date filter) to expand scope, or switch to direct career sites.
> Staffing agency noise is common for HR keywords — don't give up, switch channels.

#### 2b. Direct Company Career Sites (Chrome)

Always check these directly — they don't always appear in LinkedIn searches:

**Consulting / green-light priority (P1):**
```
careers.mercer.com → search "analyst" OR "consultant" OR "program"
jobs.aon.com → search "talent" OR "people" OR "change"
careers.kornferry.com → search "analyst" OR "associate"
deloitte.com/careers → SKIP (confirmed no H1B in current program)
mckinsey.com/careers → worth checking
bcg.com/careers → SKIP (on skip list)
```

**Tech / mid-size companies (P2-P3):**
```
instacart.careers (already added today — check for other openings)
starbucks.com/careers → search "people" OR "L&D" OR "talent"
amazon.jobs → search "people experience" OR "HR program manager"
duolingo.com/careers → search "people" OR "talent"
auditboard.com/careers → search "people" OR "HR"
stripe.com/jobs → search "people programs"
airbnb.com/careers → search "employee experience" (non-AI/non-engineer)
figma.com/careers → search "people"
notion.so/careers → search "people"
loom.com/careers → search "people"
```

**Gaming / Entertainment / Media (strong P1 potential — tech culture + people programs):**
```
careers.roblox.com → search "people" OR "talent" OR "program manager" OR "early career"
careers.riotgames.com → search "people programs" OR "talent" OR "early career"
jobs.disneycareers.com → search "HR specialist" OR "people programs" OR "talent development"
jobs.netflix.com → search "people programs" OR "talent" OR "engagement"
spotify.com/us/jobs → search "people programs" OR "talent" OR "employee experience"
ea.com/careers → search "people" OR "talent" OR "HR"
activisionblizzard.com/careers → search "people programs" OR "HR"
epicgames.com/site/en-US/careers → search "people" OR "talent" OR "program"
```
⚠️ Gaming/entertainment companies (Roblox, Disney DET, etc.) run intern programs, early career programs,
and talent/engagement programs heavily. P1 roles like Early Career PM, HR Specialist, People Programs
Associate are frequently open. These companies H1B-sponsor actively. Worth checking every run.

**Healthtech / Clinical Tech (P1-P2 potential — tech salaries, strong people programs):**
```
flatiron.com/careers → search "talent" OR "engagement" OR "people programs" OR "associate"
epic.com/careers → search "HR" OR "people" OR "training" OR "talent"
veeva.com/careers → search "people" OR "talent" OR "HR"
modernhealth.com/company/careers → search "people" OR "talent"
headspace.com/careers → search "people" OR "employee experience"
hinge.health/careers → search "people programs" OR "talent"
```

**Nonprofits / Cap-Exempt (visa advantage — lower bar):**
```
peacehealth.org/careers → check for OD/talent/change roles
providence.jobs → search HR, learning, talent, OD roles — filter Portland, OR
ohsu.edu/careers (careersat-ohsu.icims.com) → OD/talent/L&D/HR roles
legacyhealth.org/careers → HR/talent/learning roles (confirm H1B before adding)
portlandstatejobs (jobs.hrc.pdx.edu) → HR/talent/OD/L&D roles (cap-exempt university)
uportland.edu careers → HR/talent roles (cap-exempt university)
reed.edu/careers → HR/talent roles (cap-exempt college)
nonprofitoregon.org/job-board → Oregon nonprofit HR/people/talent roles
```

> ⚠️ **Cap-exempt note:** Universities, nonprofits, and hospitals are H1B cap-exempt. Jamie can receive cap-exempt H1B sponsorship at any time of year (not just the April lottery). This is a MAJOR advantage — apply to cap-exempt employers even for roles where fit is 60-65% (Portland/Seattle moderate bar), especially if the H1B advantage offsets competition.

**Education / Talent Development Sector (Jamie's preference — check every run):**
```
coursera.org/careers → "people programs" OR "talent development" OR "HR specialist"
cornerstone.com/careers → "people programs" OR "talent" OR "HR" OR "L&D"
degreed.com/careers → "people programs" OR "talent" OR "HR"
betterup.com/careers → "people programs" OR "talent" OR "HR"
guild.com/careers → "people" OR "talent" OR "HR" OR "program"
jobs.td.org → (ATD Job Bank — WebFetch: niche board)
360learning.com/careers → "people" OR "talent" OR "HR"
skillsoft.com/careers → "people programs" OR "talent development" OR "HR"
ddiworld.com/careers → "people" OR "talent" OR "consultant" OR "analyst"
```
These orgs align with Jamie's applied org psych background. Mix of cap-exempt (ATD = nonprofit)
and H1B-active (edtech companies). Lower applicant competition than LinkedIn. Check every run.

**Use WebSearch for Greenhouse/Lever bulk search:**
```
site:greenhouse.io "people programs" "program manager" posted:2weeks
site:lever.co "organizational change" OR "OCM" "analyst" posted:2weeks
site:greenhouse.io "employee experience" "program manager" remote
site:lever.co "talent development" "program manager" remote
site:greenhouse.io "change management" specialist remote
site:greenhouse.io "early career program manager" OR "talent engagement associate"
site:greenhouse.io "service insights" OR "people insights" analyst
site:lever.co "early career program" OR "university programs" coordinator OR manager
site:greenhouse.io "talent and employee engagement" associate OR coordinator
site:greenhouse.io "talent management" coordinator OR specialist OR program
site:lever.co "talent management" coordinator OR specialist OR program
site:greenhouse.io "talent development" program coordinator OR manager
site:lever.co "talent development" program coordinator OR manager
site:greenhouse.io "talent operations" coordinator OR specialist
site:greenhouse.io "talent programs" coordinator OR specialist OR associate
site:lever.co "talent programs" coordinator OR specialist OR associate
site:greenhouse.io "succession planning" OR "talent review" coordinator OR analyst
site:greenhouse.io "performance management" program coordinator -HRIS
```

#### 2c. Job Aggregators (WebSearch — secondary)

Use WebSearch (not Chrome) for these. Treat results as leads to verify in Chrome, NOT confirmed jobs.

```
WebSearch: "people programs manager" remote site:jobs.lever.co OR site:greenhouse.io
WebSearch: "OCM analyst" remote "people" hiring 2026
WebSearch: "change management program manager" remote "H1B" OR "visa sponsorship"
WebSearch: "HR transformation" "program manager" remote Portland OR Seattle
WebSearch: "employee listening" "program manager" OR "specialist" remote 2026
WebSearch: "service insights" analyst coordinator site:greenhouse.io OR site:lever.co 2026
WebSearch: "early career program manager" site:greenhouse.io OR site:lever.co 2026
WebSearch: "talent and engagement associate" OR "people programs associate" site:greenhouse.io 2026
WebSearch: "employee insights" OR "workforce insights" coordinator analyst "people" site:greenhouse.io
WebSearch: "continuous improvement" "HR" OR "people" OR "talent" specialist coordinator 2026
WebSearch: "talent management" program coordinator OR specialist site:greenhouse.io OR site:lever.co 2026
WebSearch: "talent program" development coordinator OR specialist site:greenhouse.io 2026
WebSearch: "talent development" program coordinator OR manager -"instructional design" site:greenhouse.io OR site:lever.co
WebSearch: "talent operations" coordinator OR manager "people" OR "HR" 2026
WebSearch: "succession planning" OR "talent review" coordinator analyst site:greenhouse.io 2026
WebSearch: "performance management" program coordinator specialist -HRIS -Workday site:greenhouse.io 2026
```

#### 2d. Additional Job Boards (v4.0 — non-LinkedIn sources)

> **These platforms surface roles that DON'T appear on LinkedIn.** Run every pipeline.
> Boards marked **[WebFetch-direct]** should be accessed via WebFetch to the structured URL
> (not WebSearch) — direct fetch returns curated HR-specific listings with less noise.
> Boards marked **[WebSearch]** use search because they require keyword queries.

**Built In Portland [WebFetch-direct] — PRIORITY:**
```
WebFetch: https://www.builtinportland.com/jobs?specialty=Human+Resources
WebFetch: https://www.builtinportland.com/jobs?specialty=People&q=talent+OR+programs+OR+experience
```
Portland-specific tech job board. Curated companies, almost zero staffing agency noise.
These are local employers who actively hire in PDX — Jamie's geographic advantage applies here.

**Built In Seattle [WebFetch-direct]:**
```
WebFetch: https://www.builtinseattle.com/jobs?specialty=Human+Resources
WebFetch: https://www.builtinseattle.com/jobs?specialty=People&q=talent+OR+programs+OR+experience
```
Seattle tech companies — many are H1B sponsors, accessible from Portland.

**Built In Remote HR [WebFetch-direct]:**
```
WebFetch: https://builtin.com/jobs/remote/hr?q=people+program+OR+talent+development+OR+employee+experience
```
Remote HR roles at tech companies — less LinkedIn competition than LinkedIn's remote filter.

**ATD Job Bank [WebFetch-direct] — Talent Development specialists:**
```
WebFetch: https://jobs.td.org/jobs/?q=program+manager+OR+coordinator+OR+specialist&l=Portland%2C+OR&r=50
WebFetch: https://jobs.td.org/jobs/?q=talent+development+OR+people+programs&remote=1
```
ATD (Association for Talent Development) board — employers posting here are specifically
looking for talent development professionals. Very high relevance to Jamie's background.
Many posting orgs sponsor H1B (corporate L&D teams at Fortune 500s).

**ODN Job Board [WebFetch-direct] — OD specialists:**
```
WebFetch: https://jobs.odnetwork.org/jobs/?q=organizational+development+OR+OD+OR+talent
```
Organization Development Network board — OD-specific roles. Less traffic than LinkedIn,
so lower applicant competition. Roles posted here often don't appear on LinkedIn.

**SHRM HR Jobs [WebFetch-direct]:**
```
WebFetch: https://jobs.shrm.org/jobs/?q=program+manager+OR+specialist+OR+coordinator&l=Portland%2C+OR
WebFetch: https://jobs.shrm.org/jobs/?q=people+programs+OR+talent+development&remote=1
```
HR-specific board. Different company set from LinkedIn. Less staffing agency noise.

**Education / CPT Sector [WebSearch] — Jamie's stated preference:**
```
WebSearch: "talent development" OR "L&D program manager" "workforce development" site:greenhouse.io OR site:lever.co -"instructional design"
WebSearch: "people programs" OR "HR specialist" "certification" OR "professional development" OR "corporate training" site:greenhouse.io 2026
WebSearch: "ATD" OR "SHRM" "talent development" program coordinator specialist 2026 -staffing
WebSearch: "professional development programs" coordinator OR specialist "HR" OR "people" site:greenhouse.io OR site:lever.co
WebSearch: "corporate education" OR "workforce learning" program manager OR coordinator remote 2026
```
⚠️ Education-sector and professional certification firms (ATD-affiliated, workforce dev orgs,
edtech with corporate training arms) are Jamie's stated preference. These orgs align with her
applied org psych background. Many are cap-exempt (nonprofit) or active H1B sponsors (edtech).

**HigherEdJobs [WebFetch-direct] — Universities (H1B cap-exempt ANY time of year):**
```
WebFetch: https://www.higheredjobs.com/search/advanced.cfm?JobCat=26&Region=38&Region=48&Remote=1&PosType=1&InstType=1&Keyword=HR+talent+OD+learning
```
Plus direct university career pages (use WebSearch to find job postings):
```
WebSearch: site:jobs.hrc.pdx.edu "people" OR "talent" OR "HR" OR "learning" OR "OD"
WebSearch: site:uoregon.edu/jobs "people" OR "talent" OR "HR" OR "training"
WebSearch: site:oregonstate.edu/jobs "people" OR "HR" OR "talent development"
WebSearch: site:uw.edu/jobs "people" OR "talent" OR "HR" OR "organizational development"
```

**Handshake [WebSearch] — early career roles:**
```
WebSearch: site:joinhandshake.com "people programs" OR "talent programs" OR "HR program manager"
WebSearch: site:joinhandshake.com "employee experience" OR "engagement" coordinator OR specialist
WebSearch: site:joinhandshake.com "organizational development" OR "change management" analyst
```
⚠️ Handshake is the #1 platform for entry/associate roles. Many companies post here EXCLUSIVELY
for early career positions. High signal, very low noise vs LinkedIn.

**Idealist [WebFetch-direct] — nonprofits (cap-exempt potential):**
```
WebFetch: https://www.idealist.org/en/jobs?q=people+OR+talent+OR+HR+OR+organizational+development&location=Portland%2C+OR&radius=50
```
⚠️ HIGH STALE RATE (Apr 3 data: 5/5 Idealist leads were expired). Always Chrome-verify
before adding to picks. Use WebFetch to get the page, then Chrome to verify each URL.

**Wellfound / AngelList [WebSearch] — startups:**
```
WebSearch: site:wellfound.com "people operations" OR "HR" OR "talent" OR "people programs"
```
Startups < 200 employees often have fewer applicants. Good for standing out.

**Nonprofit Oregon [WebFetch-direct]:**
```
WebFetch: https://nonprofitoregon.org/job-board
```
Oregon-specific nonprofit jobs. Cap-exempt employers. Check for HR/OD/talent roles.

**Google Jobs [WebSearch — aggregates career pages Google indexes directly]:**
```
WebSearch: "people programs manager" OR "talent programs coordinator" OR "employee experience program manager" site:careers.google.com -Google
WebSearch: "people program manager" OR "talent development coordinator" "Portland" OR "Seattle" OR "remote" 2026 -site:linkedin.com -site:glassdoor.com -site:indeed.com
WebSearch: "HR specialist" OR "talent development" OR "OD specialist" "Portland, OR" OR "Seattle, WA" OR "remote" posted 2026
```
Google Jobs aggregates company career pages differently than LinkedIn — catches jobs that
don't appear in the LinkedIn algorithm feed, especially at mid-size companies.

#### 2d-2. Watchlist Company Check (NEW v3.0)

> **Read `jamie/watchlist.md` at the start of every run.**
> Check ALL companies marked 🔄 ACTIVE in Tiers 1-3 via WebSearch or Chrome.
> Update `last_checked` dates. Add any new companies discovered during search.

**Execution:**
1. Read `watchlist.md` → get list of active companies with careers URLs
2. For Tier 1-2 (tech + gaming): WebSearch `site:{careers_url} "people" OR "talent" OR "program"`
3. For Tier 3 (cap-exempt): WebSearch or Chrome direct-navigate to careers page
4. Any hits → add to Chrome verification queue (Step 3)
5. Update `last_checked` date in watchlist.md after each company is checked

#### 2d-3. H1B Verification Cache (NEW v3.0)

> **Read `jamie/h1b_verified.md` before assessing any candidate.**
> If company is ✅ Confirmed → skip H1B verification step.
> If company is ❌ No H1B → immediate reject.
> If company is NOT in the cache → verify via myvisajobs.com + JD language, then ADD to cache.

This eliminates redundant H1B checks across runs and builds a growing knowledge base.

#### 2d-4. HigherEdJobs — Cap-Exempt Employers

> Covered in Section 2d above. Check individual university career pages via the WebSearch
> queries listed there. HigherEdJobs WebFetch URL is in `ats_mapping.json` → `niche_boards.higheredjobs_oregon`.

#### 2d-4b. Workday Direct Searches — Enterprise Companies (v4.0)

> **Nike, Starbucks, Amazon, Microsoft, Disney, Intel, Providence use Workday ATS.**
> Workday has no public API. These companies MUST be searched by navigating their career pages.
> Use WebFetch on the structured career URLs (from `ats_mapping.json → workday` section).
> These companies are high-value targets — they sponsor H1B actively and have dedicated
> people programs, talent development, and OD teams.

```
# Run ALL of these — one WebSearch per company is sufficient for discovery:
WebSearch: site:jobs.nike.com "people program" OR "talent development" OR "HR specialist" OR "employee experience"
WebSearch: site:starbucks.wd1.myworkdayjobs.com "talent" OR "people" OR "learning" OR "HR specialist"
WebSearch: site:amazon.jobs "people experience" OR "HR program manager" OR "talent development" OR "employee engagement"
WebSearch: site:careers.microsoft.com "people programs" OR "talent development" OR "HR specialist" OR "OD"
WebSearch: site:jobs.disneycareers.com "HR specialist" OR "people programs" OR "talent development" OR "learning"
WebSearch: site:jobs.intel.com "people" OR "talent" OR "OD" OR "HR specialist" Hillsboro OR Portland OR remote
WebSearch: site:salesforce.wd12.myworkdayjobs.com "people programs" OR "talent development" OR "employee experience"
WebSearch: site:tmobile.wd1.myworkdayjobs.com "people program" OR "talent" OR "HR specialist"
```

⚠️ Workday career pages are NOT indexed well by LinkedIn's algorithm — these companies'
People/Talent roles often don't appear in LinkedIn's recommended feed even when they're open.
Direct Workday searches are the only reliable way to catch them.

⚠️ For Providence Health (cap-exempt hospital): Check `providence.jobs` directly.
For OHSU (cap-exempt university hospital): Check `ohsu.edu/careers` directly.

#### 2d-5. Remote-Specific Job Boards (NEW v3.3)

> **These boards specialize in remote roles. Less noise than LinkedIn remote filters.**

```
WebSearch: site:flexjobs.com "people programs" OR "HR program manager" OR "talent development" OR "employee experience"
WebSearch: site:weworkremotely.com "people" OR "HR" OR "talent" OR "organizational development"
WebSearch: site:remote.co "people" OR "HR" OR "talent" OR "employee experience" OR "program manager"
WebSearch: site:himalayas.app "people" OR "HR" OR "talent" program manager OR specialist
```

Remote roles need 80%+ match + one advantage (per preferences.md). But these boards have
lower applicant volume than LinkedIn Remote, so competition may be more manageable.

#### 2d-6. Outcome Tracking (NEW v3.3)

> **After each pipeline run, check Jamie's Google Sheet for updates on past applications.**
> This builds a feedback loop to improve future scoring.

At the end of each run (after delivery):
1. Read the Google Sheet (2026 tab) via WebFetch CSV export
2. Look for status changes: "Applied" → "Interview" or "NGP" (Not God's Plan)
3. For any new "Interview" status: note which resume emphasis set was used, which outreach
   contacts were reached out to — this data improves future `/tailor` recommendations
4. For any new "NGP" status: note the rejection reason if available — add to dead leads
5. Update `jamie/search_strategy.md` with any new learnings

#### 2e. Job Title Reference — PRIORITY TIERS ← UPDATED v2.7

Click into JDs with ANY of these titles, even if the exact wording is slightly different.
**Accept if title fits domain; reject if JD is wrong scope.**

> ⚠️ **HARD RULE (v2.7): REJECT any role that requires more than 4 years of experience.**
> Jamie has ~3 years. Roles requiring 5+ years are too senior regardless of title.
> Check the "Required Experience" line in every JD before scoring fit.

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
P1 — BEST FIT: Talent Development + People Program Management (PRIMARY TARGET)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Jamie's SWEET SPOT = data analysis + dashboards + managing people development programs.
Always prioritize, always read full JD responsibilities (not just titles).

⚠️ CRITICAL RULE (Apr 2026): ALWAYS read the actual JD responsibilities section before
scoring. Titles can be misleading — a "Talent Development Specialist" could actually be
80% recruiting or admin. If 50%+ of duties are leave, ER, recruiting, payroll, or admin → PASS.

People Programs Manager / Coordinator / Lead
People Program Manager (any company)
Talent Development Program Manager
Early Talent Program Manager / Coordinator
Employee Experience Program Manager
HR Program Manager (if PM-heavy, NOT HRBP-heavy)
People Operations Program Manager
Workforce Development Program Manager
Talent Programs Coordinator / Specialist (if PM-scoped)
Learning Programs Manager / Coordinator (ops/logistics focus — NOT instructional design)
Employee Listening Program Manager
Feedback & Engagement Program Manager
Process Improvement / Workflow Optimization (in HR or People scope)
Program Manager, People Operations / Talent / HR (any PM role touching people/talent work)
Early Career Program Manager / Coordinator (intern/university program ops — data + events + process)
University Programs Manager / Campus Programs Coordinator (if PM-scoped, not pure recruiting)
Talent and Employee Engagement Associate / Coordinator (multi-domain: talent mgmt + L&D + EX + I&B)
People Programs Associate / Specialist (broad programs support role at tech companies)
Insights Analyst / Program Coordinator — people/EX context ONLY (see "Feedback Loop" scope pattern below)
Talent Management Program Coordinator / Specialist (programs focus — NOT recruiting/TA)
Talent Program Development Coordinator / Specialist (building/scaling talent programs)
Talent Operations Coordinator / Manager (program operations — scheduling, vendors, logistics)
Talent Strategy Analyst / Associate (if entry-level, programs-adjacent)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ NON-TRADITIONAL P1 TITLES — search for these explicitly
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
These titles don't look like obvious PM or HR roles but map directly to Jamie's sweet spot.
ALWAYS click into these — don't judge by title alone, read the scope.

Service Insights Analyst / Coordinator (TikTok-type: gather voices → find patterns → drive improvements)
Experience Insights Analyst (employee or customer experience improvement cycle)
People Insights Analyst / Coordinator
Workforce Insights Analyst (if scope = program improvement, NOT pure HR analytics/HRIS)
Employee Listening Analyst / Specialist (listening programs + action planning)
Voice of Employee (VoE) Program Manager / Coordinator
Continuous Improvement Specialist — people OR HR OR talent context
Program Analytics Coordinator — people / talent context (NOT just reporting/BI)
Feedback Programs Coordinator / Analyst
Process Excellence Coordinator — people OR employee experience context
HR Specialist (at entertainment/media/gaming companies — Disney-type scope with process improvement + data)
Operations Analyst — talent OR people OR employee experience context (if improvement-cycle scoped)

🔍 SEARCH TRICK: For these non-traditional titles, use SCOPE keywords in search rather than title:
  → "identify patterns" OR "drive improvements" + "people" OR "talent" OR "employee"
  → "feedback" + "insights" + "program" + "coordinator" OR "analyst"
  → "voice of" + "employee" OR "customer" + "program" (in people ops / EX context)
  → "stakeholder feedback" + "improvement" + "program"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🟢 "FEEDBACK LOOP" SCOPE PATTERN — P1 regardless of title
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
If a JD's core scope matches this loop, treat it as P1 even with a non-PM title:
  gather stakeholder feedback / voices / data  →
  identify patterns / friction points / trends  →
  translate into actionable improvement recommendations  →
  implement and monitor program changes
This pattern appears in: Service Insights roles (TikTok-type), Insights Analyst, CX Program
Coordinator (if HR/people context), Employee Listening Analyst. These map perfectly to Jamie's
stated interest in collecting feedback → analyzing → improving programs with data.
⚠️ ONLY in people/employee/talent context. Customer service call center ops = skip.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
P2 — GREAT FIT: Employee Experience / Engagement + OD/OCM
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Strong domain alignment with Jamie's background.
⚠️ Read JD responsibilities — skip if role is actually admin HR, leave, ER, or recruiting.

Employee Engagement Manager / Specialist / Coordinator
Employee Experience Manager / Specialist
Culture & Engagement Specialist / Manager
People Experience Specialist / Coordinator
Organizational Development Specialist / Analyst / Coordinator
OD & Learning Specialist (if NOT instructional design)
Organizational Effectiveness Analyst / Specialist
Change Enablement Analyst / Specialist (OCM scope)
Organizational Change Management (OCM) Analyst / Specialist
Change & Adoption Specialist
HR Transformation Analyst / Coordinator
Culture Specialist / Manager (engagement, not recruiting)
Talent Management Specialist (programs focus — NOT recruiting/TA)
Talent Development Specialist / Coordinator (if OD/learning program ops scope)
Learning Operations Coordinator / Manager (vendor/logistics, NOT instructional design)
Succession Planning Coordinator / Analyst (talent management programs)
Performance Management Program Coordinator (program ops — NOT HRIS/system admin)
Talent Review Coordinator / Analyst (talent calibration, reviews, program support)
Talent Initiatives Coordinator / Specialist (cross-functional talent programs)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
P3 — GOOD FIT: People/HR Consulting (ASSOCIATE / ENTRY LEVEL ONLY)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ STRICT: Only include consulting roles with "Analyst", "Associate", or "Consultant I/II".
SKIP if title contains "Senior", "Manager", "Principal", "Lead", "Director".
Consulting domains: talent management, talent development, T&D, OD, EX, people strategy.

People Advisory Services Analyst / Associate
Talent & Org (T&O) Consultant / Analyst
Human Capital Consultant / Analyst (entry level)
HR Consulting Analyst / Associate
Talent Management Consulting Analyst
Talent Development Consulting Analyst / Associate
Workforce Transformation Analyst
Organizational Development Consulting Analyst
Training & Development Consultant (entry/analyst level)
Employee Experience Consultant (entry/analyst level)
People Strategy Analyst / Associate
Talent & Rewards Consulting Analyst

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
P4 — DEPRIORITIZED: HR / HRBP (ASSOCIATE or ASSISTANT ONLY)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ STRICT (updated Apr 2026): Jamie has only 10 months direct HRBP experience (Vestas).
ONLY consider HRBP roles at assistant/associate level. Skip anything above associate.
Skip if role is admin-heavy, leave-focused, ER-heavy, or recruiting-heavy.
Jamie wants to AVOID going deeper into operational HR — she prefers talent dev + programs.
Mid-level HR Generalist and HRBP roles are OUT.

HR Associate / HR Assistant
HRBP Associate / HR Business Partner Associate
People Operations Associate / Coordinator
HR Coordinator (only if career-development focused, not pure admin)
People Coordinator
Associate People Partner / HR Partner

NOT acceptable at P4:
HR Generalist (mid-level — unless explicitly "Associate HR Generalist" or ≤2 yrs required)
HR Business Partner (unless "Associate HRBP" or "HRBP I")
HR Manager, People Manager, HR Director

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REJECT IMMEDIATELY — do not click in, do not assess:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"Instructional Designer", "Curriculum Developer", "Content Developer",
"eLearning Developer", "Learning Designer", "Training Developer",
"Recruiter", "Talent Acquisition", "Sourcer", "Recruiting Coordinator",
"HRIS", "Workday Admin", "HR Systems", "HR Technology",
"Payroll", "Benefits Analyst", "Compensation Analyst",
"Employee Relations Manager", "Labor Relations",
"Senior Consultant", "Manager, Consulting", "Principal Consultant",
"HR Generalist" (unless explicitly Associate/entry with ≤2 yrs required),
"HR Business Partner" (unless explicitly Associate/entry level),
"Director", "VP", "Head of", "Senior Manager",
Any JD requiring 5+ years of experience
```

#### 2f. Quality Gate Before Chrome Verification

Before spending Chrome verification time on a candidate, quick-check:
- **Does JD require more than 4 years?** → SKIP immediately. Check "Required" or "Minimum Qualifications" for "X years of experience". 5+ = skip.
- **No hard company skip list** — ALWAYS read the full JD to determine fit. A company you'd expect to be bad (TikTok, DoorDash, BCG, Deloitte, etc.) may have an excellent role that fits Jamie perfectly. Company reputation does NOT justify skipping — only the actual JD content determines fit.
  - Nike HQ is Beaverton, OR (Portland metro) — always check careers.nike.com for current HR/L&D/Talent/OD openings.
- Is the seniority clearly too high? (Director, VP, Senior Manager, 5+ years required) → skip
- Is it an HR/HRBP role that isn't explicitly associate/assistant/entry-level? → skip (mid-level HR generalist and HRBP roles are out per v2.7)
- Is it a consulting role at senior/manager/principal level? → skip (only analyst/associate consulting roles)
- Is it a staffing agency posting? (Insight Global, TEKsystems, Randstad, Robert Half, Apex Group) → skip the agency listing; if the client company is visible, search for the direct posting instead
- Is it clearly instructional design / ER / payroll / recruiting? → skip
- Is it contract/temp? → skip (H1B problematic)

**🟢 JD GREEN FLAG SIGNALS — if you see these phrases in the JD body, it's likely a strong fit:**
These patterns appear in all 4 of Jamie's "optimal JD" examples (Roblox, Flatiron, Disney, TikTok):
```
✅ "identify inefficiencies" / "recommend improvements" / "process improvements"
✅ "gather / collect feedback" + "drive improvements" / "translate into actionable"
✅ "continuously improving programs based on feedback and outcomes"
✅ "data-driven" / "maintain trackers or databases" / "run reports" / "dashboards"
✅ "project manage the operational details" of a people/talent program
✅ "stakeholder coordination" or "stakeholder management" in people/talent context
✅ "intern / early career programs" operations (not just recruiting)
✅ "employee engagement" + "analytics" / "program outcomes"
✅ "exposure to automation, tooling, or systems improvements" / "basic automation"
✅ "budget tracking" / "vendor coordination" in a people programs context
✅ "compliance training" / "onboarding facilitation" / "employee recognition programs"
✅ "voice of customer/employee" / "insights" + program improvement cycle
```
A JD body with 3+ of these signals = almost certainly a P1 fit regardless of the exact title.
Escalate these to full Chrome verification immediately.

Everything else → proceed to Chrome verification in Step 3.

> **QUALITY BAR — VERY HIGH STANDARD:**
> Only surface jobs that Jamie actually WANTS and is genuinely QUALIFIED for based on what she has done.
> - Do NOT include roles that lean on her ★☆☆ areas (instructional design, payroll, ER, HRIS systems)
> - Do NOT include roles where salary is too low for H1B prevailing wage
> - Do NOT include contract/temporary roles (H1B problematic)
> - **Do NOT stretch Jamie's experience — no forced connections between her background and the JD**
> - 0 picks is always better than 1 bad pick

**No Forced Connections Rule:**
> If you find yourself writing "Jamie's experience with X could translate to..." or "while not directly..."
> or "her background in X gives her a foundation for..." → STOP. That's a forced connection.
> The experience must be DIRECT AND HONEST. If it's a stretch, say so in the gaps section.
> Jamie's credibility depends on this.

**Skip list** — always re-query Notion at runtime.

---

### 🎯 Section 2g — Reference JD Profiles (Jamie's Optimal Roles)

> These are 4 real JDs that Jamie identified as near-perfect fits. Use them as calibration templates
> when assessing new candidates. If a new JD reminds you of one of these four — surface it.

---

**REF-1: Roblox — Early Career Program Manager** (San Mateo, CA | in-person Tue-Thu | $91K-$122K)
- **Why optimal:** Pure P1 — program management in early talent/campus space at a tech company.
  Data-oriented (maintain trackers, run reports), systems-minded (identify workflow inefficiencies,
  implement automation), events execution (intern events, campus programming), stakeholder management
  (Legal, People Ops, Facilities, Immigration). "Continuously improving programs based on feedback."
- **Key language to match:** "data oriented", "systems minded", "identify inefficiencies and manual
  workflows", "recommend improvements", "process enhancements", "basic automation", "program outcomes"
- **Find-alikes by searching:** "early career program manager", "university programs coordinator",
  "campus programs", "intern program manager" at tech companies

---

**REF-2: Flatiron Health — Talent and Employee Engagement Associate** (NY | hybrid 3 days | $88K-$121K)
- **Why optimal:** P1/P2 hybrid — one role spanning ALL people domains: talent management + L&D +
  inclusion & belonging + employee experience. "Associate" level = right seniority (3+ yrs req ✅).
  Scope includes: program coordination, project management, onboarding facilitation, engagement survey
  admin, LMS admin, systems analytics, budget tracking, internal comms, vendor coordination.
- **Key language to match:** "project management support across the team's work", "programmatic
  and project management support", "systems & program analytics", "reporting and analyses",
  "highly organized", "proactive", "talent management, L&D, I&B, and employee experience"
- **Find-alikes by searching:** "talent and engagement associate", "people programs associate",
  "employee engagement associate", at healthtech/oncology tech/mission-driven companies

---

**REF-3: Disney Entertainment Television — HR Specialist** (LA area | in-person | Disney campus)
- **Why optimal:** P4 at a dream employer — an HR Specialist role below HRBP level with
  genuine process improvement + data analysis scope embedded. "Administer and evaluate onboarding
  and offboarding processes end to end, including recommending and implementing process improvements
  to enhance the overall experience." Runs talent dashboards and reports. Workday/SAP experience valued.
  Multi-function exposure (OD, ER, TA, L&D, comp) = perfect learning ground.
- **Key language to match:** "implementing process improvements", "run and utilize reports and talent
  dashboards", "project management experience", "Experience advising on HR programs", "analytical
  skills to interpret data, identify trends, and recommend solutions"
- **Find-alikes by searching:** "HR Specialist" at entertainment/media/gaming (NOT "HR Generalist"
  mid-level). Also: "People Coordinator", "HR Associate" at Disney, Netflix, Spotify, EA, Nintendo.
  In-person/hybrid only for this archetype.

---

**REF-4: TikTok Shop — Service Insights (Feedback Loop role)** (US-based, 2026 new grad hire)
- **Why optimal:** Non-traditional P1 — title is ambiguous but scope is pure "Feedback→Improvement"
  loop work: gather customer/stakeholder voices → identify patterns and friction → translate to
  actionable improvement initiatives → cross-functional collaboration → monitor effectiveness.
  This maps EXACTLY to Jamie's stated goal of "collect feedback → improve programs → data analysis."
  Entry-level/new grad scope = right seniority.
- **Key language to match:** "gather and analyze customer feedback", "identify patterns and trends",
  "areas of friction and opportunities for improvement", "translate insights into actionable
  improvement initiatives", "monitor the effectiveness of implemented solutions"
- **Find-alikes by searching:** In HR/people context: "employee insights analyst", "people insights
  coordinator", "employee listening analyst", "HR continuous improvement". Also "service insights"
  at tech companies with large customer/employee programs (TikTok, Shopify, Salesforce, HubSpot).
  ⚠️ Must be in people/employee context — not customer service call center operations.

---

**Cross-reference: Common strengths valued across all 4 JDs:**
| Skill / Quality | How Jamie demonstrates it |
|---|---|
| Data analysis & reporting | Tracked program KPIs, 600+ trained, 20+ vendors managed |
| Process improvement mindset | Redesigned onboarding process, identified workflow gaps |
| Stakeholder management | Worked across HR, managers, vendors, cross-functional teams |
| Project/program coordination | PM role managing 3 concurrent programs with timelines/deliverables |
| Communication (written + verbal) | Internal comms, program documentation, presentations |
| Events execution | Coordinated learning events, culture activations, program workshops |
| Systems curiosity | Interest in automation, tooling improvements (per preferences.md) |

---

### Step 3 — Verification (MANDATORY — ALL candidates, exhaustive parallel approach v3.2)

> ⚠️ **EVERY candidate from ALL discovery agents MUST be verified before it goes anywhere.**
> This includes future-queue entries, not just today's picks.
> **An unverified URL must never enter the priority queue. Verify now or discard.**
>
> **Context window note:** Auto-compact fires automatically when context approaches its limit.
> The pipeline continues correctly after compaction because state is written to files progressively.
> Do NOT hold results in memory waiting to write at the end — write after every batch.

#### 3a. URL Routing — Split by ATS Type (do this FIRST)

Collect ALL URLs from Step 2. Route into buckets:

| Bucket | ATS / Domain | Method | Who handles it |
|--------|-------------|--------|---------------|
| **A** | `jobs.ashbyhq.com` | Chrome `get_page_text` — check for `"posting":null` | Main thread only |
| **B** | `job-boards.greenhouse.io`, `boards.greenhouse.io` | WebFetch — 404 / error page = expired | Parallel agents |
| **C** | `jobs.lever.co` | WebFetch — full JD returned = live, 404 = expired | Parallel agents |
| **D** | Workday (`wd5.myworkdayjobs.com`, etc.) | WebFetch — "page doesn't exist" = expired | Parallel agents |
| **E** | Direct company sites (Nike, Roblox, Stripe, HubSpot, etc.) | WebFetch first, Chrome fallback | Parallel agents |
| **F** | LinkedIn URLs | Chrome only — check for "No longer accepting applications" | Main thread |

#### 3b. Launch Parallel Verification (background agents — start immediately)

> **For batches B-E: launch background agents NOW while main thread handles Ashby (A) and LinkedIn (F).**
> Each agent receives 12-15 URLs, verifies all via WebFetch, writes results to a temp file, exits.
> Use `run_in_background: true` so main thread continues with Chrome work.

**Agent prompt template for WebFetch verification batches:**

```
You are a job posting verification agent for Jamie Cheng's job search pipeline.

Your task: verify whether each of the following job postings is live or expired.

METHOD for each URL:
1. Call WebFetch(url) — read the response
2. For Greenhouse: expired if response contains "An error occurred" or URL has "?error=true"
3. For Lever: expired if response is a 404 or contains "Job not found" or "This job is no longer available"
4. For Workday: expired if response contains "The page you are looking for doesn't exist"
5. For company sites: expired if response is a generic careers/search page (no specific JD), 404, or "position has been filled"
6. If live: extract from the response — (a) YOE required, (b) location, (c) salary range if present, (d) any "no sponsorship" language, (e) posting date if visible

For each URL, also apply hard gates immediately:
- REJECT if YOE required > 4 years
- REJECT if "no visa sponsorship" / "US citizens only" / "must be authorized to work"
- REJECT if contract/temp only
- REJECT if outside US (unless explicitly remote with no state restrictions)

PROGRESSIVE WRITE RULE: After verifying every 5 URLs, append results to the output file below.
Do NOT wait until all URLs are done — write partial results immediately. This ensures results
are not lost if context compacts mid-run.

Write results to: C:\Users\chent\Agentic_Workflows_2026\oracle-job-search\job-search\verify_batch_{BATCH_ID}.json

Format:
[
  {
    "url": "https://...",
    "status": "live" | "expired" | "unknown",
    "yoe_req": "2-3 years" | "not stated" | "5+ years (REJECT)",
    "location": "Portland OR (hybrid)" | "Remote" | "NYC (on-site)" | "unknown",
    "salary": "$70-90K" | "not stated",
    "h1b_flag": "no sponsorship language (ok)" | "REJECT: explicit no sponsorship",
    "posting_date": "2026-03-20" | "unknown",
    "notes": "brief note on what you saw"
  }
]

If WebFetch fails (403, timeout, blocked), mark status "unknown" and note the error.
Do NOT retry more than once per URL.

URLs to verify:
{LIST OF 12-15 URLS}
```

**How many agents to launch:**
- Up to 100 candidates → launch ceil(non-Ashby-count / 15) agents (max 6)
- Example: 60 Greenhouse/Lever/Direct URLs → launch 4 agents of 15 each
- Name batch files: `verify_batch_greenhouse1.json`, `verify_batch_lever1.json`, `verify_batch_direct1.json`, etc.

#### 3c. Main Thread: Ashby Verification (Chrome)

While background agents run, main thread verifies Ashby URLs one by one:

```
For each Ashby URL:
  1. navigate(url)
  2. get_page_text(tabId)
  3. Search output for "posting":null
     - Contains "posting":null → EXPIRED
     - Contains "posting":{...} with actual data → LIVE
       Extract: YOE req, location, salary, posting date from the JSON
  4. Apply hard gates (5+ yrs, no sponsorship, contract)
```

Write Ashby results progressively (every 5 URLs) to:
`C:\Users\chent\Agentic_Workflows_2026\oracle-job-search\job-search\verify_batch_ashby.json`

Same format as agent batches above.

> ⚠️ If Chrome blocks `jobs.ashbyhq.com` ("This site is blocked"): mark status "unknown — chrome blocked".
> Do NOT include unknown-status Ashby URLs in today's picks.
> DO add them to the priority queue with "⚠️ ashby-unverified" flag for manual check.

#### 3d. Main Thread: LinkedIn Verification (Chrome)

For any LinkedIn job URLs:
```
1. navigate(linkedin_url)
2. Run JS to expand JD: document.querySelectorAll('button').forEach(b => {
     if (b.innerText.includes('Show more') || b.innerText.includes('See more')) b.click();
   });
3. get_page_text(tabId)
4. Check for:
   - "No longer accepting applications" → EXPIRED
   - "This job is no longer available" → EXPIRED
   - "Reposted X years ago" with 0 applicants → EXPIRED (zombie listing)
   - Active apply button + full JD → LIVE
5. Extract YOE, location, salary, posting date from expanded text
```

#### 3e. Collect All Results

After all background agents complete AND Chrome work is done:

1. Read all `verify_batch_*.json` files
2. Merge into a single verified candidates list
3. Apply final deduplication (same role may appear in multiple batches)
4. Sort: live passes (ordered by urgency/freshness) → unknowns → expired

**Write merged results to:**
`C:\Users\chent\Agentic_Workflows_2026\oracle-job-search\job-search\verified_candidates.json`

Format:
```json
{
  "run_date": "2026-03-25",
  "total_verified": 87,
  "live_passes": 23,
  "expired": 58,
  "unknown": 6,
  "candidates": [
    {
      "url": "...",
      "company": "...",
      "title": "...",
      "status": "live",
      "yoe_req": "2-3 years",
      "location": "SF hybrid",
      "salary": "$83-118K",
      "h1b_flag": "ok",
      "posting_date": "2026-03-21",
      "freshness": "🔶 FRESH",
      "verified_method": "Chrome Ashby",
      "verified_date": "2026-03-25"
    }
  ]
}
```

This file persists across sessions — if the pipeline is interrupted and resumed in a new session,
start Step 4 from this file rather than re-verifying.

#### 3f. Per-Candidate JD Read (live passes only)

For each candidate with `status: "live"`, read the full JD to extract enrichment data.
WebFetch verification already gives partial data. Fill in any missing fields:
- State eligibility restrictions (search JD for "eligible states", "authorized to work in")
- If Oregon excluded → flag "⚠️ Oregon NOT listed as eligible state"
- Confirm exact posting date from the page (not Google/search results)
- Note any sponsorship language explicitly stated

> **Freshness rule:** REJECT if posted > 30 days ago. Prefer < 14 days.

### Step 3c — Structured JD Skill Extraction (NEW v4.0 — run BEFORE Step 4 fit assessment)

> **Extract required skills from each verified-live JD before scoring.** This prevents
> accidental score inflation by making skill gaps visible upfront, not discovered mid-scoring.
> Takes ~30 seconds per JD — cheap compared to the cost of enriching a bad fit.

For each verified-live candidate, extract these fields from the JD text:

```
REQUIRED skills (★★★ — "required" / "must have" / "minimum qualification"):
  - List each one: [ ] skill / experience area

PREFERRED skills (★★☆ — "preferred" / "nice to have" / "plus"):
  - List each one: [ ] skill / experience area

Experience required: X years (required) / Y years (preferred)
Location type: Remote / Hybrid X days / On-site | Location: [city, state]
Visa language: [quote exact text if "no sponsorship" or "must be authorized"]
Salary range: [if stated]
```

Then rate Jamie's match against each REQUIRED skill:
- ✅ Direct match (she has done exactly this)
- ⚠️ Partial match (adjacent experience — needs honest framing)
- ❌ Gap (she hasn't done this; would need to learn on the job)

**Auto-flag rules:**
- If 3+ REQUIRED skills are ❌ → mark as `SKIP` before proceeding to full Step 4 assessment
- If JD contains a ★★★ required skill that is in Jamie's ★☆☆ self-assessment areas
  (instructional design, payroll, ER, HRIS admin) → mark as `SKIP`
- If YOE required > 4 years anywhere in required qualifications → `SKIP` immediately

This structured extraction feeds directly into Step 4 (fit %) and Step 5 (scoring).
Log it as a compact block in the pick dashboard — it's the evidence behind the fit score.

---

### Step 4 — Honest Fit Assessment

> **Be Jamie's honest advisor, not her hype machine.**

For each verified-live candidate, assess against Jamie's ACTUAL experience from `resume.md`:

> ⚠️ **HARD EXPERIENCE RULE (v2.7):** If the JD requires more than 4 years of experience anywhere in the posting (required qualifications, "minimum X years"), **REJECT immediately**. Jamie has ~3 years. Do not assess fit further for 5+ year roles.

**4a. In-person / Hybrid (ANY US location) — PREFERRED, MODERATE bar (65%+ actual JD match):** ← NEW v2.7
- In-person/hybrid roles are now the primary target — less national competition, local presence = real advantage
- West Coast (Portland, Seattle, Bay Area, LA, San Diego) preferred but other US cities are acceptable if role fits
- JD must align with P1–P3 priority tiers (program management, engagement/OD, consulting)
- Do NOT surface roles where JD leans on ★☆☆ areas (instructional design, payroll, ER, HRIS)
- **⚠️ If eligible-states restriction applies and Oregon is excluded → flag it, but this is less critical for in-person roles**

**4b. Remote — HIGH bar (85%+ actual JD match), only if genuinely exceptional:** ← UPDATED v2.7
- Remote roles attract national competition. Jamie's H1B status + 3 years = tougher sell than a local US citizen.
- Only surface a remote role if ALL of the following are true:
  - 85%+ honest JD match (near-perfect fit)
  - At least one of: confirmed H1B sponsor, networking connection, cap-exempt employer, P1 consulting
  - Role is clearly P1 or P2 tier (program management or consulting)
  - Oregon is listed as eligible state (or no state restriction exists)
- If ANY condition is missing → SKIP the remote role, don't pick it over a local alternative
- **Bottom line: a decent local role beats a great remote role.**

**4c. Portland / Seattle / Pacific Northwest — STILL best if available:**
- Local Pacific Northwest presence = lowest competition + H1B cap-exempt university/hospital advantage
- Accept 60%+ fit for Portland/Seattle in-person if P1–P2 tier
- JD should not lean heavily on ★☆☆ areas

**4c-2. Education Sector / Professional Development Orgs — Jamie's stated preference:**
- Companies in the talent development, workforce training, CPT/CPTD certification, and edtech
  corporate training space are a strong cultural fit given Jamie's applied org psych background
- Accept 65%+ fit for these orgs even if remote, because domain alignment matters
- Examples: ATD (Association for Talent Development), organizations developing CPTD-related programs,
  workforce development nonprofits (cap-exempt advantage), edtech with corporate L&D divisions
  (Coursera, Degreed, 360Learning, Cornerstone OnDemand), consulting firms that focus on
  talent and learning (DDI, Korn Ferry, Mercer, Right Management / ManpowerGroup)
- ⚠️ Still apply H1B check — not all ed-sector orgs sponsor. Cap-exempt nonprofit advantage applies.

**4d. Check against self-assessment in preferences.md:**
- If role leans on ★☆☆ areas (instructional design, payroll, ER) → probably not a fit

**4e. Company quality check ← NEW v2.4:**
- Always search Glassdoor for every company before adding to Notion
- Glassdoor < 3.0/5 → immediate reject (toxic culture, not worth Jamie's time)
- Glassdoor 3.0–3.4/5 → flag as ⚠️ Caution; only proceed if everything else is outstanding
- Glassdoor 3.5+/5 → OK (note any relevant culture issues in the Notion entry)
- If Glassdoor review mentions: mass layoffs (< 6 months ago), hostile management, "promote then fire", "toxic" culture → add as ⚠️ flag even at 3.5+

**4f. Explicit gap analysis for each candidate:**
- ✅ What Jamie genuinely matches (with evidence from actual work)
- ⚠️ Where she's a stretch (developing skills positioned as strong)
- ❌ What she's missing (hard requirements she doesn't meet)
- If ❌ list has more than 1-2 hard requirements → SKIP

### Step 5 — Score and Present ALL Viable Candidates

**Scoring (weight order):**
1. **Visa certainty** (cap-exempt > confirmed H1B sponsor > unknown)
   - **🏛️ Cap-exempt bonus (+10%):** Universities, nonprofits (501(c)(3/4)), and hospitals
     are H1B cap-exempt — no lottery, no timing constraint, year-round sponsorship.
     This is Jamie's strongest visa path. Cap-exempt employers get a +10% scoring bonus.
   - Cap-exempt + Portland/Seattle = best possible combination. Prioritize these above all.
2. **Honest fit score** — real JD match percentage based on actual experience
3. **Role-priority tier** (P1 > P2 > P3 > P4)
4. **Location** (Portland/Seattle in-person > Other US in-person/hybrid > Remote-exceptional-fit only)
5. **Freshness** (< 7 days > 7-14 > 14-30)

> **Cap-exempt discovery is the highest-value activity in this pipeline.**
> Tech companies found via ATS APIs are useful but secondary. The Portland cap-exempt
> roles from Agent D (HigherEdJobs, Idealist, university career sites) and Agent F
> (PNW local searches) are often harder to find but far more actionable for Jamie.

> ⚠️ **EXPERIENCE GATE:** Any role requiring 5+ years → automatic disqualification before scoring.

**Present ALL candidates that pass the HARD CONSTRAINTS. Do NOT over-filter.**
Jamie will decide which to apply to. She benefits from seeing the full landscape.
The pipeline's job is to FIND and VERIFY roles, not to gatekeep them.

**Hard constraints (auto-reject):**
- Requires 5+ years experience
- Explicitly says "no sponsorship" / "US citizens only"
- Non-US location
- Senior/Director/VP/C-level title

**Everything else gets included in the email digest**, even if it's a stretch.
For each role, provide enough info for Jamie to decide:
- Posted date, salary, YOE requirement, location, H1B status
- 1-2 sentence honest assessment of fit and gaps
- Cap-exempt status clearly marked

Enrichment (cover letter, networking) is done for the top 3, but all viable roles
appear in the email digest ranked by score with full details.

**Fit Score formula (v3.4.1) — compute a 0-100 numerical score for EVERY candidate:**

```
Base score = JD match % (honest assessment vs Jamie's actual experience)
  +10 if cap-exempt employer (hospital/university/501c3 nonprofit)
  +5  if confirmed H1B sponsor (per h1b_verified.md or JD states it)
  +5  if Portland or Seattle in-person/hybrid
  +3  if P1 or P2 role priority tier
  -10 if remote-only (national competition, harder for H1B)
  -5  if requires 3-4 yrs experience (Jamie has ~3, borderline)

Cap at 100. Round to nearest whole number.
Store this number in the Notion "Fit Score" property (0-100).
```

**JD match % guidelines (the Base score):**
- 80-100%: Jamie hits every core requirement with direct experience
- 65-79%: Strong on 3-4 core requirements, 1-2 gaps that are learnable
- 55-64%: Hits the theme but missing 2+ core requirements or lacks direct examples
- Below 55%: Auto-skip (don't add to Notion)

**Rating (star bracket — derived from Fit Score):**
- ⭐⭐⭐ Perfect = Fit Score ≥ 80
- ⭐⭐ Good = Fit Score 65–79
- ⭐ Worth reviewing = Fit Score 55–64

**Urgency tag (v3.4.1) — stored in Notion "Urgency" select AND shown in email:**
- 🚨 Urgent = posted < 7 days ago — flag in email: "apply within 24-48 hrs!"
- 🔶 Fresh = posted 7-14 days ago — flag in email: "apply this week"
- ⏳ Aging = posted 14-30 days ago — still worth applying, note in email
- 💤 Stale = posted 30+ days ago — only if Fit Score ≥ 80, otherwise skip

### Step 6 — Add to Notion (honest content)

> ⚠️ **DEDUP CHECK BEFORE EVERY PAGE CREATION (v3.5.1):**
> Before creating a Notion page for any pick, verify it is NOT already in the dedup list from Step 1a-pre-0.
> - If status is "Not a fit" or "Pass" → DO NOT add. Remove from picks entirely. Don't enrich it.
> - If status is "Applied" or "Not started" → DO NOT add a duplicate page. Mention in email only.
> - Same company + same title at same org with different job IDs → verify they are genuinely separate openings before adding.
> **Failure to check this wastes enrichment tokens and pollutes Notion with duplicates.**

For each pick (max 3), create a Notion page in DB `442438a9-e372-48b7-b5f5-5f6ed8ee8e99`.

**Properties** (match schema exactly):
- Job Title (title), Company (text), Location (text)
- Category (select: Consulting, Program Management, L&D, HR/HRBP, OD/OCM/EX, Others)
- userDefined:URL (url), Company URL (url), Notes (text — empty or one-line)
- LinkedIn Link (url) — **REQUIRED**: Always include the LinkedIn job posting URL when available. LinkedIn is the primary search platform.
- Official Link (url) — The company's direct careers page URL for this role (e.g., Greenhouse, Lever, Workday, company site)
- Posted Date (date — REAL from Chrome), Added Date (date — today)
- H1B Friendly (select: ✅ Confirmed, 🏛️ Cap-Exempt, ❓ Unknown, ❌ No Sponsorship)
- Rating (select: ⭐⭐⭐ Perfect, ⭐⭐ Good, ⭐ Near-miss)
- Fit Score (number — 0-100, computed via formula above — REQUIRED v3.4.1)
- Urgency (select: 🚨 Urgent, 🔶 Fresh, ⏳ Aging, 💤 Stale — based on posted date — REQUIRED v3.4.1)
- Status = "Not started" (Notion native status field — pipeline adds new roles as "Not started"; Jamie moves to "Applied" when she submits)

**Page Content — use EXACT PAGE FORMAT from template below.**

**CRITICAL content rules:**
- **Resume tailoring:** ONLY reword things Jamie actually did. Never invent experience.
- **Cover letter:** Honest pitch. Say "I'm building skills in X" rather than claiming expertise she doesn't have.
- **Fit table:** MUST include ⚠️ Gaps section. Never skip it.
- **Networking:** Use Chrome to find REAL LinkedIn profiles with actual URLs.

---

### 📄 EXACT PAGE FORMAT — OPERATIONAL STANDARD (v3.1)

> ⚠️ **CONTENT QUALITY RULE:** Every Notion page must be immediately actionable.
> Jamie should be able to open a page and start working — no lookup steps needed.
> - All LinkedIn URLs must be real, working URLs found via search (not placeholders)
> - All outreach messages must be fully written in Jamie's voice, ready to copy-paste
> - All resume bullet swaps must cite the SPECIFIC content_library.md variant name + full text
> - Cover letter must be complete 250-350 word final draft, not instructions
> - Interview prep items must be role-specific (company name, actual news, actual JD requirement)
> - If you can't find a real LinkedIn URL for a contact, write "URL not found" — never write a fake URL
>
> **The email and the Notion page should have the same operational quality.**
> The Notion page is Jamie's prep workbook. It must be richer than the email, not sparser.

```markdown
## ⚡ Quick Action Summary

| Action | Priority | Status |
|---|---|---|
| Send LinkedIn message to {Contact 1 full name} | 🔴 Do First | [ ] |
| Swap resume bullets (see tailoring below) | 🟡 Before Applying | [ ] |
| Submit application at {direct apply URL} | 🟡 After networking | [ ] |
| Follow up with {Contact 2} in 3 days | 🟢 Day 3+ | [ ] |

**Apply URL:** {direct application link — Greenhouse/Lever/Ashby/company site}
**Deadline signal:** {urgency tag — ⚡ apply today / 🔶 apply this week / ⏳ apply soon / 💤 ok to wait}

---

## 🎯 Why This Role Fits Jamie

| Jamie's Actual Experience | {Company} JD Requirement | Fit |
|---|---|---|
| {specific thing she ACTUALLY did with numbers — from resume.md} | {exact JD requirement text} | ✅ Direct match — {brief reason} |
| {another specific experience — e.g., "redesigned onboarding, -75% time"} | {JD requirement} | ✅ Direct match — {reason} |
| {developing experience or adjacent} | {JD requirement} | 🟡 Stretch — {honest assessment} |

### ⚠️ Gaps to Consider

| JD Requirement | Jamie's Reality | Risk Level |
|---|---|---|
| {requirement she doesn't fully meet — be specific} | {what she actually has — honest} | 🟡 Stretch / 🔴 Hard Gap |

**Should she apply?** {1-2 sentence honest recommendation with specific reasoning}

---

## 🏢 About {Company}

| Aspect | Details |
|---|---|
| **Headquarters** | {city, state} |
| **Industry** | {sector + 1-line what they do} |
| **Stage / Size** | {startup/growth/public — employee count — recent funding or revenue} |
| **Glassdoor** | {X.X}/5 — {2-3 word sentiment, e.g., "fast-paced, collaborative"} |
| **H1B** | {✅ Confirmed (N LCAs FY2025) / 🏛️ Cap-Exempt / ❓ Unknown / ❌ No} |
| **Salary** | {range from posting or Glassdoor estimate} |

**Culture signals:** {2-3 specific Glassdoor pros/cons relevant to Jamie's work style}

**Recent news (last 6 months):** {one specific thing — funding round, acquisition, leadership, layoffs — with source}

**Why this company matters for the interview:** {1-2 sentences — what Jamie should know to show she did research}

---

## ✏️ Resume Tailoring

**JD keywords Jamie CAN credibly claim:** {5-8 keywords from JD that map to real experience}
**JD keywords to OMIT (Jamie doesn't have this):** {1-3 gaps — don't stretch}

**Bullet swaps — use these specific content_library.md variants:**

SWAP 1 — InGenius Prep / primary role bullet:
- CURRENT: "{exact text from resume.md}"
- USE THIS VARIANT: "{complete reworded bullet — specific text, not a description of what to write}"
- WHY: {which JD phrase this targets, e.g., "matches 'identify workflow inefficiencies' requirement"}

SWAP 2 — InGenius Prep / second bullet:
- CURRENT: "{exact text}"
- USE THIS VARIANT: "{complete reworded bullet}"
- WHY: {JD phrase it targets}

SWAP 3 — Transition Projects / Vestas / NextGen (if relevant):
- CURRENT: "{exact text}"
- USE THIS VARIANT: "{complete reworded bullet}"
- WHY: {JD phrase it targets}

---

## 📝 Cover Letter (complete draft — ready to send)

Dear {Hiring Manager name if known, otherwise "Hiring Manager"},

{Full 250-350 word cover letter — COMPLETE FINAL TEXT, not instructions.
 Opening must name the company and role.
 Body: 2 specific InGenius/Transition Projects experiences with numbers.
 One honest gap acknowledgment if appropriate.
 Close with genuine enthusiasm for this company specifically.
 Signed: Jamie (Yi-Chieh) Cheng | Portland, OR | jamiecheng0103@gmail.com}

---

## 🤝 Networking Contacts

**Outreach order:** Message Contact 1 first. Wait 3 days, then Contact 2.

### Contact 1: {Full Name} — {Exact Title} at {Company}
**Connection type:** {Hiring Manager / People Team / Recruiter / USC Alum / Wesleyan Alum}
**LinkedIn:** {ACTUAL URL — e.g., https://www.linkedin.com/in/firstname-lastname-abc123/}
**Why reach out:** {specific reason — adjacent to hiring, USC alum, posted about this topic}

**Message (copy-paste into LinkedIn — under 300 chars):**
"Hi {First Name}, this is Jamie! {1-2 sentences specific to this person/role}. Would love to connect!"

---

### Contact 2: {Full Name} — {Exact Title} at {Company}
**Connection type:** {type}
**LinkedIn:** {ACTUAL URL}
**Why reach out:** {reason}

**Message (copy-paste into LinkedIn):**
"Hi {First Name}, {personalized message different from Contact 1 — references something specific about their background or work}."

---

## ✅ H1B & Sponsorship Notes

| Factor | Details |
|---|---|
| **Status** | {✅ Confirmed / 🏛️ Cap-Exempt / ❓ Unknown / ❌ No} |
| **Evidence** | {e.g., "47 LCAs filed FY2025, 98% approval rate" or "501c3 nonprofit" or "no evidence found"} |
| **Action** | {e.g., "Safe to apply — confirm eligibility in screening call" or "Verify before applying"} |

---

## 📋 Interview Prep

- [ ] Research **{specific thing about this company}** — {why it matters, e.g., "Roblox's intern program scope and timeline"}
- [ ] Prepare STAR story for **"{exact JD requirement phrase}"** — lead with {which experience}
- [ ] Prepare STAR story for **"{second JD requirement}"** — lead with {which experience}
- [ ] Prepare STAR story for **"{third JD requirement}"** — lead with {which experience}
- [ ] Know **{company}'s product/mission** at user level — {what to know specifically}
- [ ] Review Glassdoor concern: **"{specific con from Glassdoor}"** — prepare for culture question
- [ ] {Role-specific item — e.g., "Be ready to discuss gaming industry" or "Understand ESOP model"}
- [ ] Prepare questions: {2-3 specific questions for THIS company/role}
- [ ] Practice H1B framing: {confirm Roblox/etc. sponsors this role category}

---

## 🔗 Sources

| Resource | Link |
|---|---|
| **Job Posting (apply here)** | {direct URL} |
| **Company Careers** | {careers page URL} |
| **Glassdoor** | {glassdoor URL} |
| **LinkedIn Company Page** | {linkedin.com/company/...} |
| **H1B Data** | {h1bgrader.com or myvisajobs.com URL} |
| **Recent News** | {news article URL if found} |
```

### Step 7 — Bible Verse

Rotate through 7 verses (day-of-week index, 0=Sun):
0: Joshua 1:9 | 1: Jeremiah 29:11 | 2: Philippians 4:13 | 3: Isaiah 41:10
4: Romans 15:13 | 5: Psalm 73:26 | 6: Isaiah 40:31

Get Chinese + English text from `jamie/bible_verses.md`.

### Step 8 — Write email_body.txt

> **v3.0: The email is now a SELF-CONTAINED ACTION SHEET.**
> Jamie should be able to read the email and start networking + applying
> without needing to open Notion first. Every pick includes full networking
> contacts with LinkedIn URLs and draft outreach messages.

```
🌸✨ 每日工作小汇报 · Daily Job Digest ✨🌸

Dear Jamie, 👋💕

📖 今日经文 · Today's Verse 📖
————————————————————————
🇨🇳 {CHINESE_VERSE}

🇺🇸 {ENGLISH_VERSE}

— {VERSE_REFERENCE}
————————————————————————

💼 今日精选机会 · Today's Top Picks 💼

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{URGENCY_TAG} #1  {JOB_TITLE}  @  {COMPANY}
📍 {LOCATION}  |  📅 Posted: {DATE}
🏷️ Category: {CATEGORY}  |  ⭐ Rating: {STARS}
💰 Salary: {SALARY_RANGE} (if known)
🛂 H1B: {CONFIRMED / CAP-EXEMPT / UNKNOWN}
💬 Why this fits you: {2-3 sentences — honest, specific to Jamie's experience}
🔗 Apply here: {DIRECT_URL}
🔗 LinkedIn posting: {LINKEDIN_URL}

👥 Networking Contacts:

   1. {CONTACT_NAME} — {TITLE} at {COMPANY}
      🏷️ {Hiring Manager / Team Member / Alumni / Recruiter / Chief of Staff}
      🔗 {FULL_LINKEDIN_PROFILE_URL}
      📝 Draft message:
      "{Personalized outreach message in Jamie's voice — ready to copy-paste.
       References something specific about this contact's work.}"

   2. {CONTACT_NAME} — {TITLE}
      🏷️ {connection type}
      🔗 {FULL_LINKEDIN_PROFILE_URL}
      📝 Draft message:
      "{Another personalized message — different from #1}"

   (3. if available)

✏️ Resume Tailoring for This Role:

   📌 Key JD keywords to weave in: {5-8 keywords from JD that Jamie can credibly claim}

   🔄 Suggested bullet swaps (from jamie_content_library.md):
   • InGenius role → use "{EMPHASIS}" variant:
     CURRENT: "{exact current bullet from resume.md}"
     SWAP TO: "{specific variant from content_library.md that better matches this JD}"
     WHY: {1 sentence — what JD language this aligns with}

   • InGenius role → swap another bullet:
     CURRENT: "{current bullet}"
     SWAP TO: "{better variant}"
     WHY: {alignment reason}

   • Vestas / Transition Projects / NextGen → adjust if relevant:
     CURRENT: "{current bullet}"
     SWAP TO: "{better variant}"
     WHY: {alignment reason}

   ⚠️ Gaps — do NOT add these to resume (Jamie doesn't have this experience):
   • {JD requirement she can't credibly claim — e.g., "PMP certification"}
   • {Another gap — e.g., "5 years people analytics with Visier/Tableau"}

   💡 Prompt for Jamie to paste into another AI for further refinement:
   "I'm applying for {JOB_TITLE} at {COMPANY}. Here's the JD: {JD_URL}.
    My current resume is attached. Please help me:
    1. Reword these bullets using the JD's language: {list the 2-3 bullets to swap}
    2. Add these keywords naturally: {keyword list}
    3. Keep my experience honest — don't invent metrics I don't have.
    4. Gaps I should NOT try to cover: {gap list}
    5. Suggest a 2-sentence summary/objective line tailored to this role."

📋 Quick Action Checklist:
   □ Send connection request to {Contact 1 name} (highest priority — {reason})
   □ Swap resume bullets as suggested above (or paste prompt into AI)
   □ Submit application via {platform}
   □ Follow up with {Contact 2} in 2-3 days

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

(repeat full enriched block for top 3 by score)
(URGENCY_TAG: ⚡ URGENT / 🔶 FRESH / ⏳ AGING / 💤 STALE)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 Additional Viable Roles (scored but not fully enriched):

| # | Company | Role | Location | H1B | Rating | Key Note |
|---|---------|------|----------|-----|--------|----------|
| 4 | {Co.} | {Role} | {Loc} | ✅/🏛️/❓ | ⭐⭐ | {one-line why} |
| 5 | {Co.} | {Role} | {Loc} | ✅/🏛️/❓ | ⭐ | {one-line why} |
(include ALL candidates that pass the ⭐+ threshold — no cap)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🧹 Database Cleanup: {N} expired entries marked as Pass today.
{Brief list of what was cleaned and why, e.g., "TEECOM — expired posting"}

📊 全部已存入 Notion (cover letters, full tailoring, interview prep) ✅
https://www.notion.so/ea7cccd43f7a47a6b93a196241eb8d61

🙏 愿神带领你找到祂为你预备的那份工作！
加油，你是最棒的！💪🌈

最爱你的鼠鼠 🐹❤️
```

> **CRITICAL EMAIL RULES:**
> - **ALL URLs must be clickable** — write them as full `https://...` URLs on their own line.
>   Gmail auto-links plain URLs. Do NOT use markdown `[text](url)` — Gmail doesn't render it.
>   LinkedIn profile URLs must be full URLs like `https://www.linkedin.com/in/sarahkim/`
>   so Jamie can click directly from the email to open the profile.
> - Every networking contact MUST have their full clickable LinkedIn URL
> - Every draft message MUST be personalized to the contact (reference their work/title/background)
> - Draft messages must be ≤ 300 characters for LinkedIn connection requests
> - **Resume tailoring section per pick is MANDATORY** — include specific bullet swaps from
>   `jamie_content_library.md`, JD keywords, gaps to avoid, and a ready-to-paste AI prompt
> - The email alone should give Jamie everything she needs to:
>   1. Click a link and apply
>   2. Click a LinkedIn profile and send a connection request with the draft message
>   3. Know exactly which resume bullets to swap and which keywords to add
>   4. Paste a prompt into another AI for further resume refinement
> - Notion has the DEEP content (cover letter, full company research, interview prep)
> - The email has the ACTION content (who to contact, what to say, where to apply, how to tailor)

### Step 9 — Write jobs_rows.json

```json
[
  ["{URL}", "{DATE}", "{JOB_TITLE}", "{COMPANY}", "{CATEGORY}", "{LOCATION}", "", "{ONE_LINE_WHY}"],
  ...
]
```

### Step 11 — Create Gmail Draft

Use `gmail_create_draft` to jamiecheng0103@gmail.com with subject "🌸✨ 每日工作小汇报 · Daily Job Digest ✨🌸" and body from email_body.txt.

> **URL clickability:** Use `contentType: "text/plain"` (default). Gmail auto-links all plain-text
> URLs (https://...) so Jamie can click directly. Do NOT use HTML or markdown link syntax.
> Every URL in the email (job posting, LinkedIn profiles, Notion link) must be a full
> `https://` URL on its own line so Gmail renders it as a clickable blue link.

### Step 12 — Pipeline Complete

Note: Archiving/deletion is NO LONGER performed. Expired entries are marked "Pass 👋" directly in Notion during the audit step, preserving all records.

---

### Step 13 — Terminal Run Summary (MANDATORY — output as one complete block)

> **Always output this after Step 12 — and again after all late background agents finish.**
> This is David's single checkpoint to verify the run is complete and correct.
> Never fragment it across messages. One clean block, every time.

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🐣 ORACLE PIPELINE — RUN COMPLETE
Run {N} · {Date} · {Day of Week}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📧 EMAIL
   Status:  ✅ Gmail draft created (Draft ID: {id})
   To:      jamiecheng0103@gmail.com
   Picks:   {N} new picks included

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🆕 TODAY'S PICKS

| # | Company | Role | H1B | Urgency | Notes |
|---|---------|------|-----|---------|-------|
| 1 | {Co.} | {Role} | ✅/🏛️/❓ | ⚡/🔶/⏳ | {e.g., "NYC hybrid — relocation decision needed"} |
| 2 | {Co.} | {Role} | ✅/🏛️/❓ | ⚡/🔶/⏳ | {e.g., "Apr 17 deadline, cap-exempt"} |

⚠️ ACTION ITEMS — DO TODAY:
   □ {Highest urgency — e.g., "US Mobile: decide NYC relocation, then apply (⚡ 2 days old)"}
   □ {Second action — e.g., "GlossGenius: message Alyssa Holden for H1B pre-screen"}
   □ {Third if any}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🗂️ NOTION
   New pages created:  {N} ({company names})
   Status fixes:       {N} ({e.g., "Notion Labs, Mercer, Swinerton → Applied ✅"})
   Marked Pass 👋:     {N} (expired or gate-failed)
   DB snapshot:        ~{N} total · {N} Applied ✅ · {N} New 🆕 · {N} Pass 👋

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔜 RUN 4 QUEUE (verified live, not yet picked)

| Company | Role | Why Not Today | Action |
|---------|------|---------------|--------|
| {Co.} | {Role} | {e.g., "H1B unverified, onsite Bay Area"} | {e.g., "Verify H1B + confirm Jamie open to relocation"} |

(Empty = nothing queued)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❌ TOP GATE FAIL REASONS THIS RUN
   • {N} roles — 5+ YOE required
   • {N} roles — Explicit no H1B sponsorship
   • {N} roles — Expired on ATS direct check (~{X}% expiry rate)
   • {N} roles — Contract/temp or location mismatch

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 STATS
   Discovered: ~{N} | Verified live: {N} | Gate passes: {N} | Picks: {N}
   Expiry rate: ~{X}%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

> **When background agents arrive late (after Step 13 already ran):**
> - Acknowledge each arriving agent in 1–2 lines (confirmed expired / gate fail / new live pick)
> - If a new live candidate passes all gates → add to email draft, Notion, and queue; note it
> - Once ALL late agents are processed → re-output the full Terminal Summary above, marked "UPDATED"
> - Never leave David with a fragmented view — always close with the complete block

---

## 📁 Reference Files

```
jamie/resume.md              — Jamie's resume (GROUND TRUTH for tailoring)
jamie/preferences.md         — Role priorities, fit criteria, search queries
jamie/bible_verses.md        — Verses with Chinese translations
jamie/watchlist.md            — 80+ target companies across 7 tiers (NEW v3.0)
jamie/h1b_verified.md        — H1B verification cache (NEW v3.0)
jamie/outreach_templates.md  — Networking style guide + message drafting (NEW v3.0)
jamie/content_library.md — MASTER content library: resume bullet variants, self-intros,
                                       recruiter emails, cover letter blocks, "why company" templates (NEW v3.1)
```

---

## ⚠️ Known Issues & Workarounds

### VM Egress Proxy Blocks
Many domains blocked from VM: linkedin.com, glassdoor.com, indeed.com, greenhouse.io, lever.co, workday sites. **Workaround: Chrome browser handles all direct job page access.** VM WebSearch still works for Google queries.

### `notion-update-page` MCP Tool
`update_properties` works for simple changes. For complex content updates or if it fails with bug #153, create a REPLACEMENT entry and add OLD page ID to `cleanup_pages.json`.

### Gmail Draft
Use `gmail_create_draft` MCP tool to create the draft. Subject: "🌸✨ 每日工作小汇报 · Daily Job Digest ✨🌸", To: jamiecheng0103@gmail.com, body from email_body.txt.

---

## 🎓 Lessons Learned — v4.1 (Apr 19, 2026 Deep Run)

> Recorded from a 21-agent / 600+-query / full-DB-audit run. These are concrete failure modes
> observed today; treat them as hard rules in v4.1+ runs.

### Verification & Discovery

1. **WebSearch-sourced LinkedIn URLs are ~90% ghost listings.**
   Out of 39 direct LinkedIn `/jobs/view/{id}` URLs returned by WebSearch agents, the ones we
   sampled in Chrome (Envoy, Lattice) were "Reposted 1–3 years ago, No longer accepting
   applications." LinkedIn keeps stale postings indexed even when closed. **Rule: never include
   a WebSearch-sourced LinkedIn URL in today's picks without Chrome-verifying it first.**

2. **Greenhouse/Lever public APIs returned 403/404 from this VM during this run.**
   Both `api.greenhouse.io/v1/boards/{slug}/jobs/{id}` and `jobs.lever.co/{slug}/{id}?mode=json`
   were unreachable. WebFetch on the same URLs also returned 404 even for live jobs. **Rule:
   when ATS APIs are 403/404, downgrade those agent results to "unverified" and surface only
   if Chrome can navigate them. Do not present as today's picks.**

3. **Chrome `mcp__Claude_in_Chrome__navigate` is restricted to a domain allowlist.**
   `jobs.lever.co`, `job-boards.greenhouse.io`, and most ATS hosts are blocked ("Navigation to
   this domain is not allowed"). Only LinkedIn, Idealist, big-co careers pages reliably work.
   **Rule: Plan for ATS verification to require WebFetch only; if WebFetch is also failing
   (today's pattern), mark as ⚠️ unverified and DO NOT inflate confidence.**

4. **LinkedIn `get_page_text` only returns the LEFT panel (search list), not the JD detail
   right panel.** To read a JD, you must navigate directly to the canonical
   `linkedin.com/jobs/view/{id}` URL. The collections/recommended URL with `?currentJobId=`
   does not surface the right panel via `get_page_text`. **Rule: when LinkedIn surfaces
   promising results, immediately deep-link to each `/jobs/view/{id}` for verification.**

5. **WebSearch returns far more category/hub pages than direct job URLs.** Agents A–F returned
   roughly 30–50% hub pages (`/jobs/people-operations-jobs-portland-oregon-metropolitan-area`),
   which are useless for verification. **Rule: filter agent outputs to require at least one
   numeric job ID or posting slug in the URL path. Reject `/jobs/{keyword}-jobs-{location}`
   patterns automatically — they are search aggregations, not jobs.**

### Audit & Dedup

6. **The Notion DB accumulates ~40% dead links if not audited every run.** Today's audit found
   6 dead links among the "Not started" / high-score queue (Greenlight America cap-exempt,
   EY Portland 92/100, PeaceHealth, Palantir, J&J, PwC) — all marked Pass after verification.
   **Rule: Step 1 audit MUST run every pipeline. Verify every "Not started" with active
   deadlines AT THE TOP OF THE RUN before any new discovery, so deadline-window picks don't
   sit stale.**

7. **`Status` field is a Notion select — value must be exactly "Pass", NOT "Pass 👋".**
   Several update_properties calls failed with `validation_error` because the Notion select
   options are: `Not started, Applied, Not a fit, Rejected/Unavailable, Pass`. The 👋 emoji
   that lives in our prose is NOT part of the value. **Rule: when calling notion-update-page,
   set `properties.Status = "Pass"` (no emoji). Use Notes to record the audit reason.**

8. **The skip list must be (company, title) pairs not just company.** Confirmed: Spotify and
   Notion both have multiple HR roles open simultaneously; skipping the whole company because
   Jamie applied to one role would have lost real opportunities. **Rule already documented in
   v3.4.1; reinforced today.** Cross-check the Sheet AND Notion before adding any new page.

### Discovery Yield

9. **Cap-exempt employers without explicit H1B evidence cannot be tagged ✅ or +10 bonus.**
   Today's deep search confirmed 12+ cap-exempt structures (universities, hospitals, foundations)
   but ZERO had explicit sponsorship language in JDs. Agent S finding 7 nonprofits all carried
   ❓ Unknown. **Rule: tag cap-exempt structure ≠ sponsorship willingness. Mark as ❓ and note
   "must verify in first screening call" — never +10 bonus without filing-history evidence.**
   Kaiser Permanente confirmed NO H1B (zero LCAs 2021–2023) — explicit no-go despite cap-exempt.

10. **Mega-keyword LinkedIn agents (50+ batches) produce ~3× more category-hub pages and only
    ~10–15% direct-URL increase over a focused 25-batch run.** Diminishing returns sharply
    after batch count exceeds 30. **Rule: cap LinkedIn agent batches at 25–30. Spend extra
    parallel agent budget on direct ATS / niche board / cap-exempt direct-portal searches
    instead — those have higher signal-to-noise.**

11. **JobSpy (Indeed scraping) is the highest-yield single source.** 360 deduped Indeed/LinkedIn
    results in one run; 22 passed strict filters and ~5 reached today's picks. Indeed's lack of
    rate limiting makes it the cleanest discovery channel today. **Rule: always run JobSpy
    `--include-edu` at the start. Treat its output as primary, not supplemental.**

12. **LinkedIn "Top Job Picks" feed (`/jobs/collections/recommended/`) was today's single best
    source by yield-per-token.** It surfaced AskBio, UnitedLex, Oliver Wyman (rejected for no
    H1B), Spotify HR Specialist patterns, and PitchBook in <500 tokens of Chrome reads. The
    LinkedIn algorithm has already pre-filtered to Jamie's profile. **Rule: in Step 2, the
    main thread MUST scroll Top Job Picks before launching discovery agents. If Top Picks
    yields 5+ live candidates, drop the WebSearch agent count by 50%.**

### Operational

13. **Pre-fetch scripts must be the FIRST action in every run.** They take 1–2 min each in
    background and provide ~360 candidate jobs before any agent spawns. Today's
    `fetch_ats_jobs.py` returned 43 jobs (43% Stripe Bengaluru noise — needs filter); JobSpy
    returned 360. **Rule: trigger both Python scripts as background processes in the very
    first message of the pipeline. Don't gate on their completion.**

14. **Audit agents need explicit page-batch lists.** When given a generic "audit all Not
    started" prompt, the haiku agent only got through 25–30 entries before context-budgeting
    out. Splitting into explicit batches (20 IDs per agent call) reliably gets through 100+
    entries across multiple agents. **Rule: after fetching the full Notion ID list, partition
    into batches of 20 and spawn one haiku audit agent per batch. Do not ask one agent to
    "audit everything."**

15. **The `ats_mapping.json` Stripe slug returns 35+ Bengaluru jobs that flood the candidate
    pool.** Almost every run, ATS pre-fetch is dominated by Stripe India. **Rule: filter
    Stripe results to US-only locations during ingest. Add this to `fetch_ats_jobs.py` as a
    location filter.**

16. **Discovery agent type spec ("general-purpose" vs custom) must be exactly correct.**
    Typoed `general-puroose` failed silently and required relaunch. **Rule: always use
    `subagent_type: "general-purpose"` exactly — no creative spellings.**

### What to do differently next run

- **Start with Top Picks + JobSpy + audit in parallel; defer WebSearch agents** until those
  three are exhausted (5+ unverified candidates) — saves ~50% token budget.
- **Cap LinkedIn WebSearch agents at 25 batches each.** Spend the extra parallelism on direct
  ATS portals and cap-exempt employer career pages.
- **Hard-require numeric job ID in URL** during agent post-filtering. Drop hub pages.
- **Verify ALL active-deadline "Not started" entries at audit step 1**, not just new ones.
- **Pre-emptively mark cap-exempt-without-evidence as ❓**, never +10 bonus.

---

## 🎨 Emoji Key

| Symbol | Meaning |
|--------|---------|
| 🐣     | Oracle / the search agent |
| 🐹     | Sign-off in email ("最爱你的鼠鼠 🐹❤️") |
| 🌟     | Top picks (all picks use 🌟 now — max 3) |

---

*v4.1.0 — Apr 19, 2026: DEEP-RUN LESSONS LEARNED. Added new "Lessons Learned — v4.1" section near the end of SKILL.md capturing 16 concrete failure modes from a 21-agent / 600+-query / full-DB-audit run. Highlights: (1) WebSearch-sourced LinkedIn URLs are ~90% ghost listings — must Chrome-verify before today's picks. (2) Greenhouse/Lever public APIs returned 403/404 from this VM — downgrade unverified. (3) Chrome navigation allowlist excludes most ATS hosts — plan WebFetch-only for them. (4) LinkedIn `get_page_text` returns left-panel only — must deep-link `/jobs/view/{id}` for JD detail. (5) Reject hub-page URLs `/jobs/{kw}-jobs-{loc}` automatically. (6) Audit Step 1 every run; Notion DB accumulates ~40% dead links otherwise. (7) Notion Status select option is "Pass" not "Pass 👋" — emoji breaks update_properties. (8) Cap-exempt structure ≠ sponsorship — never +10 bonus without LCA evidence. (9) Cap LinkedIn agents at 25–30 batches; spend extra parallelism on direct portals. (10) JobSpy + LinkedIn Top Picks are highest-yield single sources — run first. (11) Audit agents need explicit batch-of-20 page-ID lists. (12) Stripe India floods ATS results — filter `fetch_ats_jobs.py` to US-only at ingest.*

*v3.1.0 — Mar 24, 2026: CONTENT LIBRARY + EXPANDED SEARCH. (1) JAMIE CONTENT LIBRARY: Created `jamie_content_library.md` — master file with all resume bullet variants (PM/L&D/EX/vendor emphasis per role), 6 self-intro versions, 6 recruiter/hiring manager email templates, "why company" building blocks, "what makes me stand out" paragraphs, remote work statement, HRIS/tools statement, and work sample description. Pipeline now pulls from pre-written content variants instead of generating from scratch. (2) TALENT MANAGEMENT SEARCH EXPANSION: Added 6 new P1 LinkedIn batches (H5-H10): talent management program, talent program development, talent development program, talent operations, talent strategy, workforce planning. Added 5 new P2 batches (R11-R15): talent management specialist, talent program specialist, succession planning, talent initiatives, performance management program. Added 7 new WebSearch queries and 10 new Greenhouse/Lever site: queries for talent management/development. Added 4 new P1 titles (Talent Management Program Coordinator, Talent Program Development Coordinator, Talent Operations Coordinator, Talent Strategy Analyst) and 4 new P2 titles (Succession Planning Coordinator, Performance Management Program Coordinator, Talent Review Coordinator, Talent Initiatives Coordinator). (3) EMAIL AS ACTION SHEET: Email digest now includes full networking contacts with LinkedIn URLs, draft outreach messages (copy-paste ready), connection type (recruiter/alumni/hiring manager/team), salary range, H1B status, urgency tag, and per-pick action checklist. Jamie can start outreach directly from the email without opening Notion. (4) OUTREACH FORMAT SELECTION: Each networking contact now specifies the right outreach format — LinkedIn connection request (short), recruiter email (medium), hiring manager email (long), or alumni connection — drawn from the appropriate template source.*

*v3.0.0 — Mar 24, 2026: MAJOR ARCHITECTURE UPGRADE. (1) MULTI-AGENT PIPELINE: Added Agent decomposition diagram and parallelization rules — Step 1+2 run simultaneously, discovery uses parallel background agents, enrichment per-pick parallelized. (2) EXPANDED JOB BOARDS: Added Handshake (early career — Jamie's exact tier), Built In PDX/Seattle/SF (curated tech), SHRM JobBoard (HR-specific), Idealist (nonprofits/cap-exempt), Wellfound (startups), Google for Jobs. (3) COMPANY WATCHLIST: Created `watchlist.md` with 80+ target companies across 7 tiers — checked systematically every run with `last_checked` tracking. (4) H1B VERIFICATION CACHE: Created `h1b_verified.md` — eliminates redundant H1B checks. 27 confirmed sponsors, 14 cap-exempt, 2 confirmed no-H1B cached from day 1. (5) NETWORKING OUTREACH PROTOCOL: Created `outreach_templates.md` with Jamie's real message samples, personalization formula, and contact-finding protocol. Every Notion pick now includes personalized draft messages referencing specific details from contact's LinkedIn profile. (6) URGENCY SCORING: Added ⚡URGENT/🔶FRESH/⏳AGING/💤STALE tags based on posting age. Email digest now shows urgency prominently. (7) CAP-EXEMPT DEDICATED LOOP: Tier 3 of watchlist ensures Portland/Seattle hospitals, universities, nonprofits are checked every single run.*

*v2.8.1 — Mar 20, 2026: NON-TRADITIONAL TITLE EXPANSION. Added explicit "Non-Traditional P1 Titles" block covering: Service Insights Analyst, Experience Insights Analyst, People Insights Analyst, Workforce Insights Analyst, Employee Listening Analyst, Voice of Employee (VoE) Program Coordinator, Continuous Improvement Specialist (people context), Feedback Programs Coordinator, Process Excellence Coordinator, HR Specialist (Disney-type scope), Operations Analyst (people/EX context). Added scope-keyword search trick for finding these roles when title-based search fails. Added 5 new LinkedIn batches (R5–R10): service insights, workforce insights, continuous improvement, program excellence, CX program coordinator, stakeholder feedback. Added 5 new WebSearch queries and 4 new Greenhouse/Lever site: queries for these non-traditional titles.*

*v2.8 — Mar 20, 2026: JD CALIBRATION UPDATE based on 4 optimal JDs from Jamie (Roblox Early Career PM, Flatiron Talent & Engagement Associate, Disney HR Specialist, TikTok Shop Service Insights). (1) NEW P1 TITLES: "Early Career Program Manager", "Talent and Employee Engagement Associate", "People Programs Associate", "University Programs Coordinator" added to P1 tier. (2) NEW "FEEDBACK LOOP" SCOPE PATTERN: Any JD whose core scope is gather-feedback → identify-patterns → translate-to-improvements → monitor is treated as P1 regardless of title. (3) NEW GREEN FLAG SIGNALS: Added explicit JD language signals (e.g., "identify inefficiencies", "continuously improving programs based on feedback", "exposure to automation/tooling") that strongly predict fit. (4) NEW COMPANY SECTORS: Added Gaming/Entertainment (Roblox, Disney, EA, Netflix, Spotify, Epic Games) and Healthtech (Flatiron, Epic, Veeva, Modern Health) to direct site checklist. (5) NEW LINKEDIN BATCHES: H2 "early career program manager", H3 "talent and engagement associate", H4 "people programs associate", R2 "employee insights analyst", R3 "voice of employee feedback", R4 "HR specialist associate". (6) NEW SECTION 2f: Reference JD Profiles — detailed calibration guides for all 4 optimal JDs with find-alike search strategies.*

*v2.7 — Mar 20, 2026: Major strategy update. (1) PRIORITY TIER OVERHAUL: P1 = People Program Management (primary target — PM skills + people/talent/HR domain); P2 = Employee Engagement/Experience + OD/OCM; P3 = People/HR Consulting (associate/analyst ONLY — no senior/manager consulting); P4 = HR/HRBP Associate or Assistant ONLY (mid-level HR Generalist and HRBP are OUT). (2) EXPERIENCE GATE: Any JD requiring 5+ years = automatic reject at quality gate. Max 4 years required. (3) LOCATION FLIP: In-person/hybrid is now the primary target — less competition, real local advantage. Remote only if near-perfect P1 fit + confirmed H1B + Oregon eligible. West Coast preferred but any US in-person role is fine. (4) LinkedIn search batches reorganized into P1/P2/P3 priority groups with PM-heavy searches leading. (5) Reject list expanded: HR Generalist (mid-level), HRBP (non-associate), senior consulting, any 5+ yr requirement.*

*v2.6 — Mar 4, 2026: Completely rewrote Step 2 (Discovery). New philosophy: scan ~1000 listings across all sources, surface ~20–40 for review, pick max 3. Added 18 LinkedIn search batches (A–U) with exact URL templates. Added direct company career site checklist (Mercer, Aon, Korn Ferry, Starbucks, Amazon, Duolingo, AuditBoard, Stripe, Figma, Notion, PeaceHealth, Providence, etc.). Added WebSearch Greenhouse/Lever bulk query templates. Added full expanded job title list (accept/reject by domain). Added 2e Quality Gate to skip obvious rejects before Chrome verification.*

*v2.6 — Mar 5, 2026: (1) New dead-signal patterns: Workday "page doesn't exist" = expired; LinkedIn "Reposted X years ago + 0 applicants" = zombie ghost listing; company homepage URL with no job ID = unverifiable. (2) ALL "Pass 👋" entries MUST be archived each run. (3) CRITICAL: public/nonprofit cap-exempt employers may still explicitly say "no visa sponsorship" — always READ the full job posting for sponsorship language even for cap-exempt orgs. PCC (Portland Community College) posted "not currently able to provide visa sponsorship" despite being cap-exempt. DELETE any posting with explicit no-sponsorship language regardless of org type. (4) Updated SKILL.md Notion search batch keywords to include known active companies. Lesson: Mar 4-5 audit removed 11 entries total across two runs — exhaustive multi-pass Chrome verification is mandatory.*

*v2.5 — Mar 4, 2026: Added 0/5 dead-job failure story to Chrome prerequisites section (the "stale listing" problem — aggregators don't update when jobs close). Added resume exaggeration trap warning to Pipeline Philosophy. Added "why remote is harder" context. Chrome is now the MANDATORY verification backbone, not optional.*

*v2.4 — Mar 4, 2026: (1) Meticulous Chrome-verify: use `get_page_text` not just screenshot/tab-title; explicit status signals for Greenhouse/Lever/LinkedIn/ZipRecruiter dead-page patterns. (2) JD-Expansion Protocol: expanded search titles (OCM, Change Enablement, Employee Listening, People Experience, etc.); pivot to direct career sites when LinkedIn returns staffing agency noise; click into JD even if title doesn't match keywords. (3) No Forced Connections Rule: if you're bridging unrelated experience → stop, flag it as a gap. (4) Remote state-eligibility check: always scan JD for eligible-states list; Oregon exclusion = immediate flag/reject. (5) Archive-Not-Pass: write rejected roles to cleanup_pages.json instead of marking "Pass 👋" in Notion. (6) Company Quality Check: Glassdoor < 3.0 = reject; 3.0–3.4 = caution flag.*

*v2.3 — Mar 4, 2026: Step 1 DB audit now runs 10+ keyword-batched notion-search queries to find all 20–40+ entries (not just top 10). cleanup_pages.json format updated to use `id` field (matching run_oracle.ps1). v2.2: LinkedIn-first search, quality bar reinforced, LinkedIn Link + Official Link columns, Gmail draft via MCP.*
