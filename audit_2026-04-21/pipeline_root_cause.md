# Oracle Pipeline — Root Cause Analysis: Stale/Dead Links in Jamie's Notion Tracker

**Date:** 2026-04-21
**Scope:** Why "most" entries in Jamie's Notion DB (`442438a9-e372-48b7-b5f5-5f6ed8ee8e99`) are expired by the time she reviews them.
**Method:** Audit of `pipeline/SKILL.md`, `fetch_ats_jobs.py`, `jobspy_search.py`, `do_sheet.ps1`, and `skills/jamie-job-search/skill.md`, plus cross-reference with the v4.0 protocol.

Findings are ranked by estimated impact on dead-link rate.

---

## RC1 (HIGHEST IMPACT) — Greenhouse/Lever ATS API jobs are written to Notion without ever being live-verified

### Evidence
- `pipeline/SKILL.md:52` — "These jobs are **already live** (API returns only active postings) — skip Chrome verification for them"
- `pipeline/SKILL.md:368` — "**ATS API jobs skip Chrome verification** (they are confirmed live by the API)"
- `fetch_ats_jobs.py:107` — calls `https://api.greenhouse.io/v1/boards/{slug}/jobs?content=true`; if `resp.status_code == 200`, the `absolute_url` (line 123) is carried straight through to the discovery pool.
- `fetch_ats_jobs.py:130-141` — emits the URL with `source: "greenhouse_api"` and an `updated_at` stamp but no per-URL live-check.
- `pipeline/SKILL.md:590-601` — acknowledges that "Greenhouse job IDs decay fast" and that WebFetch on a stale ID silently returns a different job. Yet the API-fetch step uses the SAME `absolute_url` field and skips the title-match re-check.

### Why it fails
The ATS API returns the *current board state*, but:
1. The pipeline's own v4 guidance warns Greenhouse silently serves a fallback job when IDs expire — that exact failure can happen between the API fetch and the moment Jamie clicks the link days later.
2. The API fetch is cached to `C:/Windows/Temp/ats_jobs.json` and consumed "if < 24 hours old" (SKILL.md:362). A job that was live at fetch time may be closed 23 hours later and still get written into Notion with no re-check.
3. Lever has the same pattern (`fetch_ats_jobs.py:170`): `hostedUrl` is trusted blindly.
4. "Skip Chrome verification" also means there is no title-mismatch check, no Workday-closed check, and no re-fetch immediately before `notion-create-pages` — the ONLY guard is the API response at harvest time.

This is the single most productive path for stale links, because ATS APIs generate the largest *batch* of candidates per run — many companies × 60+ slugs — and each one bypasses the verification gate that was designed to catch decay.

### Proposed fix
- Delete the "skip Chrome verification" carve-out. Treat ATS API URLs the same as scraped URLs.
- At Notion-write time (Step 6), do a final WebFetch of the Apply URL and assert title match against the expected title captured at discovery. Only create the Notion page if it passes.
- Reduce the staleness window on `ats_jobs.json` from 24 hours to 2 hours OR re-fetch the specific URL (not the whole board) immediately before each Notion create.

---

## RC2 — Step 1c "audit all Not-started entries" is documented but has no execution guardrail; silent skip is the default failure mode

### Evidence
- `pipeline/SKILL.md:1025-1035` — describes "1c. Verify ALL 'Not started' and 'New 🆕' entries via Chrome — METICULOUS and AGGRESSIVE" and explicitly states "many existing Notion pages have dead links that were never cleaned up."
- `skills/jamie-job-search/skill.md:33-55` — the MANDATORY audit checklist explicitly requires re-verifying every Not-started entry *before* adding new roles.
- `pipeline/SKILL.md:405-408` — Chrome-missing branch says "STOP the pipeline immediately." But there is **no machine-enforced gate** — it relies on the model's adherence.
- `pipeline/SKILL.md:564-565` / `824-825` / `846-847` — quiet failure paths: WebFetch 403/timeout/blocked → mark "unknown" and continue. Chrome-blocked domains (Ashby, LinkedIn) → mark "unknown" and continue.
- No script in `pipeline/scripts/` actually performs the Not-started audit. `do_sheet.ps1` (1 line) only appends to a Google Sheet. `fetch_ats_jobs.py` and `jobspy_search.py` never touch Notion.

### Why it fails
The audit is prose-only — it lives in a 2314-line SKILL.md that the orchestrator may truncate, skip under context pressure, or reduce to a token-conservation shortcut. Observed real-world behavior Jamie reports (lots of stale entries) is consistent with the audit being routinely skipped or only applied to the top 5-10 entries rather than the full Not-started backlog.

Compounding this: LinkedIn URLs (a huge fraction of the DB) are explicitly tagged "needs manual browser check" (skill.md:44) — which in practice means they are never revalidated at all.

### Proposed fix
- Extract the Not-started audit into a dedicated script (`audit_not_started.py`) that: (a) pulls every Not-started row via Notion API, (b) HEADs the Official Link with a browser-like User-Agent, (c) for Greenhouse/Lever/Workday applies the title-match and content-pattern checks from SKILL.md:1064-1083, (d) writes back Status=Rejected/Unavailable with an "AUDIT [date]:" note.
- Make the pipeline orchestrator call this script FIRST and refuse to continue discovery until the script exits 0.
- Emit a structured report (audit_YYYY-MM-DD.json) of pass/fail counts so skipping is visible.

---

## RC3 — JobSpy (LinkedIn/Indeed/Glassdoor scrape) results have known-stale URLs and rely on the same downstream verification gate as everything else, but without enforcement they leak into Notion

### Evidence
- `jobspy_search.py:243` — `"hours_old": 72` is the ONLY freshness filter; jobspy returns what Indeed/LinkedIn serve, which can include reposts and expired listings.
- `jobspy_search.py:253-256` — `scrape_jobs` output is dumped to `C:/Windows/Temp/jobspy_results.json` with no URL liveness check.
- `jobspy_search.py:300-307` — dedup is URL-based only; a 404 URL is deduped into the pool just fine.
- `pipeline/SKILL.md:369` — "JobSpy + email alert jobs still need Chrome verification (scraped data may be stale)". This depends on RC2's verification loop, which is unreliable.
- JobSpy LinkedIn scrape returns `linkedin.com/jobs/view/{id}` URLs. LinkedIn blocks WebFetch (skill.md:44) — "LinkedIn URL (blocks crawlers) → note as 'needs manual browser check'". So the verification gate for these is essentially inert.

### Why it fails
LinkedIn-sourced URLs can't be programmatically live-checked. Per skill.md the protocol is to note them and move on — meaning LinkedIn jobs enter Notion on the strength of a jobspy scrape that is already hours-to-days old, with NO subsequent liveness check, ever. When Jamie clicks a 2-week-old jobspy LinkedIn link, it's dead more often than not.

### Proposed fix
- Before writing a LinkedIn URL into Notion, require a Chrome (Claude-in-Chrome) `get_page_text` call that confirms the JD is present and the "No longer accepting applications" banner is absent. If Chrome isn't connected, route these to a "needs_manual_verification" bucket, NOT to Notion.
- Tighten `hours_old` from 72 to 24 for LinkedIn/Glassdoor specifically.
- Prefer canonicalization: if the jobspy record includes a company ATS URL (greenhouse/lever/workday field), use THAT instead of the LinkedIn mirror as the Official Link.

---

## RC4 — Posted Date is treated as optional in practice; Urgency labels decouple from real posting age, so stale jobs look Fresh

### Evidence
- `pipeline/SKILL.md:1092-1097` — "If live → extract posted date (REQUIRED) ... If posted date cannot be determined → note 'posted date unknown'". It is called "REQUIRED" but there is a documented bail-out.
- `pipeline/SKILL.md:2244/2276` — Notion property "Posted Date (date — REAL from Chrome), Added Date (date — today)" — there is no assertion that Posted Date is non-null before Notion create.
- `skills/jamie-job-search/skill.md:57-66` — explicit rule "Never mark something 'Fresh' just because we just found it." The mere existence of this rule implies the prior behavior — mislabeling freshness — was happening.
- `fetch_ats_jobs.py:124` — Greenhouse captures `updated_at` (not `first_published`); a job "bumped" today looks fresh even if it was first posted months ago.
- `fetch_ats_jobs.py:171-176` — Lever uses `createdAt`, which IS first-post, but this value is never written into the Notion Posted Date field — the pipeline only keeps it in the JSON side-car.

### Why it fails
When Posted Date is blank, the urgency label defaults to signals based on Added Date, which is always "today" on the first run — so old jobs look fresh for 14 days in Notion. Jamie's Fresh/Urgent filter therefore shows her dead-or-dying postings.

### Proposed fix
- Make Posted Date a hard non-null field in the Notion write step. If unknown, write the URL into a separate "Needs Date" queue instead of the main tracker.
- Prefer `first_published`/`createdAt` over `updated_at` for ATS API jobs and wire it through to the Notion property.
- Compute Urgency server-side (formula property) from Posted Date only, never from Added Date.

---

## RC5 — Pipeline writes via model tool calls with no post-write sanity check; there is no "URL shape" validator guarding Notion writes against search-page URLs

### Evidence
- `pipeline/SKILL.md:660-668` — "Return ONLY direct job posting URLs"; "Do NOT return search result pages, category pages, or aggregator landing pages, LinkedIn hub pages, Glassdoor search URLs". This is a *prompt rule*, not a validator.
- `pipeline/SKILL.md:1079` — "❌ Dead (Redirect): URL redirected to generic /jobs or search results page" — detected only if the verification step actually fires (see RC1/RC2).
- `jobspy_search.py:304` — dedup key is `str(r.get("job_url", r.get("link", "")))` — accepts any URL shape silently.
- `jobs_rows.json` (present in repo) and `do_sheet.ps1` pipe rows to a Google Sheet with no URL-shape check either.
- No regex/URL-pattern gate exists in any `.py` script before emit.

### Why it fails
Prose guardrails in a 2k-line SKILL.md are easy to drift past under token pressure, especially for sub-agents running on Haiku (per CLAUDE.md: "Pure data retrieval or writes → haiku"). A Haiku write agent handed a messy discovery record will happily write `linkedin.com/jobs/hr-jobs-in-portland` or `indeed.com/jobs?q=...` into the Official Link field. Once there, it sits forever and looks "dead" to Jamie because clicking it takes her to a search, not a role.

### Proposed fix
- Add a tiny `validate_url.py` helper with per-domain regexes: Greenhouse must match `/jobs/\d+`, Lever must match `/[a-f0-9-]{36}`, Workday must match `/job/[^/]+/[^/]+_R-\d+`, LinkedIn must match `/jobs/view/\d+`, Indeed must match `/viewjob\?jk=[a-f0-9]+`. Reject anything that doesn't match at the Notion-write boundary.
- Run this validator inside the Notion MCP wrapper (or as a pre-commit pass over candidate JSON) so no sub-agent can bypass it.

---

## RC6 — Email alerts and LinkedIn "Top Picks" are marked "PRIMARY discovery source" but have the weakest freshness signal

### Evidence
- `pipeline/SKILL.md:100-103` / `342-343` — "LinkedIn 'Top Job Picks' is now the PRIMARY discovery source (v3.5). ~381 tailored recommendations."
- `pipeline/SKILL.md:96` — "These URLs still need Chrome/WebFetch verification (alerts often contain expired listings)." Acknowledged stale source promoted to primary.
- LinkedIn Top Picks recommendations routinely include roles 30-60 days old. There is no age cap or "drop if > N days" filter in the discovery logic.

### Why it fails
The pipeline's highest-volume input channel is also its stalest. Combined with RC3 (LinkedIn URLs can't be programmatically verified), every pipeline run front-loads Notion with jobs that passed LinkedIn's relevance algorithm but not LinkedIn's freshness.

### Proposed fix
- Before accepting a Top-Picks or email-alert URL into the pool, open the posting in Chrome and read the posted-date line. Drop anything > 14 days old.
- For email alerts, prefer the *ATS URL* inside the email body (when present) over the LinkedIn/Indeed redirector.

---

## Summary table

| Rank | Root cause | Dominant symptom | Fix complexity |
|------|-----------|------------------|----------------|
| RC1 | ATS API skip-verification carve-out | Silent Greenhouse expiry, fallback-job serving | Medium — add title-match at write time |
| RC2 | Audit-all-Not-started is prose-only, silently skipped | Stale backlog grows every run | High — needs a real script + orchestrator gate |
| RC3 | LinkedIn/jobspy URLs can't be revalidated | Hugely stale LinkedIn links live forever | Medium — require Chrome, prefer ATS URL |
| RC4 | Posted Date optional; Urgency defaults mislead | "Fresh" labels on month-old jobs | Low — server-side formula + non-null write |
| RC5 | No URL-shape validator at write boundary | Search URLs slip in as Official Link | Low — regex validator |
| RC6 | Stale "primary" sources (Top Picks, email) | Front-loads pool with old jobs | Low — age cap at ingest |
