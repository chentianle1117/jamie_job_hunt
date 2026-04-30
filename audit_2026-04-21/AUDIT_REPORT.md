# Oracle Job Search — Comprehensive Audit

**Date:** 2026-04-21
**Trigger:** Jamie reports most job links in the Notion tracker are expired or months old; she doesn't trust the pipeline.
**Scope:** Notion DB (`collection://442438a9-e372-48b7-b5f5-5f6ed8ee8e99`) + `/jamie-job-search` pipeline code + `skills/jamie-job-search/skill.md`.

---

## TL;DR

Jamie's perception is **directionally right but numerically off**. The Notion tracker itself is mostly clean — of 82 pages audited, only 9 are actually in `Not started` status, and of those 9 only 1 is confirmed LIVE (Adyen HRBP). The real failure modes are:

1. **Pipeline writes search-page URLs as Official Link** (3 of 9 Not-started entries — UnitedLex, Spotify, PitchBook). These are the entries Jamie clicks and gets nothing. This is the most *visible* trust-breaker.
2. **LinkedIn URLs never get revalidated** (3 of 9 Not-started — KalVista, Genentech, Benchmark). The pipeline explicitly tags them "needs manual browser check" and then never actually checks. They age into Jamie's "Fresh" view as dead links.
3. **Freshness labels drift from reality** (Genentech labeled 🔶 Fresh despite being 17 days old with no Posted Date). Fresh means "added recently", not "posted recently".
4. **Greenhouse/Lever ATS jobs skip live-verification at write time** — pipeline trusts the API fetch. Silently stale IDs serve fallback jobs that pass as "live".

Five Notion entries were immediately cleaned up today; six structural pipeline fixes are proposed below.

---

## Part 1 — State of the Notion Tracker

Audited 82 unique page IDs across categories Consulting, L&D, OD/OCM/EX, HR/HRBP, Program Management. Results:

| Bucket | Count |
|---|---|
| Already triaged (Applied / Pass / Not a fit / Rejected) | 73 |
| Confirmed LIVE | 1 |
| Search-URL-only (unusable link) | 3 |
| LinkedIn — needs manual check | 3 |
| UNCLEAR (SPA / bot-blocked) | 2 |

### The 9 active Not-started entries

| Company | Title | Verdict | Link issue |
|---|---|---|---|
| **Adyen** | HR Business Partner | ✅ LIVE | Apply now — this is the one Jamie should act on |
| Affirm | Talent Management Specialist II | UNCLEAR | Greenhouse URL resolves to list view; manually verify |
| EY Seattle | People Consulting – HR Transactions – Senior | CLOSED → updated to Pass | Posted ~165 days ago; duplicate of Portland variant |
| UnitedLex | HR Specialist – EX | SEARCH URL → updated to Pass | Official Link was a LinkedIn search query |
| Spotify | HR Specialist | SEARCH URL → updated to Pass | Official Link was `lifeatspotify.com/jobs` root |
| PitchBook | HR Specialist | SEARCH URL → updated to Pass | Official Link was `pitchbook.com/about/careers` root |
| KalVista | HR Specialist, HRBP & L&D | Needs manual | LinkedIn — open in browser |
| Genentech | L&D Specialist | Needs manual + urgency fixed | LinkedIn + mislabeled Fresh at 17d |
| Benchmark Senior Living | L&D Coordinator | Needs manual | LinkedIn — open in browser |

### Updates applied to Notion today

- UnitedLex → Status=Pass, AUDIT note
- Spotify → Status=Pass, AUDIT note
- PitchBook → Status=Pass, AUDIT note
- EY Seattle (duplicate 165d old) → Status=Pass, Urgency=Stale, AUDIT note
- Genentech L&D → Urgency downgraded 🔶 Fresh → ⏳ Aging with AUDIT note

After these updates, Jamie's active Not-started queue is **4 entries**: Adyen (LIVE, apply), Affirm (needs manual), KalVista / Benchmark (LinkedIn, browser-check).

---

## Part 2 — Why Jamie's experience is worse than the numbers suggest

The audit shows the tracker is 89% already-triaged, but the *experience* is driven by the 11% that's still Not-started, and within that the worst offenders are all recent additions (past 3 weeks). Every new pipeline run adds more noise of the same kinds:

- **Search URLs** → Jamie clicks, lands on a careers homepage, can't find the role, loses trust
- **LinkedIn URLs** → Jamie clicks, gets a "this job is no longer accepting applications" banner, loses trust
- **Stale Fresh labels** → Jamie filters for Fresh, sees Genentech, opens it, role is 17 days old, loses trust

The pipeline's audit protocol (skill.md:33-55) was *designed* to catch all of this, but it's prose-only — nothing enforces it.

---

## Part 3 — Root causes (detail in `pipeline_root_cause.md`)

Ranked by impact on Jamie's experience:

| Rank | Root cause | Fix complexity |
|---|---|---|
| RC1 | ATS API jobs skip live-verification at write time | Medium |
| RC2 | "Audit all Not-started" is prose, no script, no gate | **High** |
| RC3 | LinkedIn/JobSpy URLs never revalidated | Medium |
| RC4 | Posted Date optional → Urgency decoupled from actual age | Low |
| RC5 | No URL-shape validator before Notion write | **Low — immediate win** |
| RC6 | Stale "primary" sources (LinkedIn Top Picks, email alerts) | Low |

---

## Part 4 — Recommended workflow changes

### Do these now (low-effort, high-impact)

**1. Add `validate_url.py` at the Notion-write boundary.** Regex per domain:
```
greenhouse: job-boards.greenhouse.io/[^/]+/jobs/\d+
lever:      jobs.lever.co/[^/]+/[a-f0-9-]{36}
workday:    myworkdayjobs.com/.+_R-\d+
linkedin:   linkedin.com/jobs/view/\d+
indeed:     indeed.com/viewjob\?jk=[a-f0-9]+
ashby:      jobs.ashbyhq.com/[^/]+/[a-f0-9-]{36}
```
Reject anything else at write time. Would have blocked today's UnitedLex / Spotify / PitchBook entries.

**2. Make Urgency a Notion formula, computed from Posted Date.**
- 🚨 Urgent: posted ≤ 3 days OR deadline ≤ 7 days
- 🔶 Fresh: posted ≤ 14 days
- ⏳ Aging: posted 15–30 days
- 💤 Stale: posted > 30 days OR Posted Date blank and Added Date > 14 days

Remove manual setting. This kills the "Fresh because just added" failure mode.

**3. Cap ingest age at 14 days for LinkedIn Top Picks and email-alert sources.** They're the stalest primary inputs and can't be revalidated later.

**4. Prefer the ATS URL over the LinkedIn mirror.** If a JobSpy record has `greenhouse_url` or `lever_url` alongside `linkedin_url`, write the ATS one. ATS URLs are verifiable; LinkedIn URLs aren't.

### Do these next (structural)

**5. Build `audit_not_started.py` and gate the pipeline on it.**
- Pulls every `Status=Not started` row via Notion MCP
- WebFetch / browser-verify each Official Link
- Writes back Status=Rejected/Unavailable with `AUDIT [date]:` prefix
- Orchestrator must call it FIRST and refuse to continue discovery until it exits 0
- Emits `audit_YYYY-MM-DD.json` so skips are visible

**6. At Notion-write time, re-fetch the Apply URL and assert title match.** Closes the Greenhouse "silent fallback" gap. Adds one WebFetch per new role — cheap insurance.

### Update the skill docs

- `skills/jamie-job-search/skill.md:33-55` should reference the new `audit_not_started.py` script by name instead of describing the protocol in prose.
- `pipeline/SKILL.md:52,368` — remove the "ATS API jobs skip Chrome verification" carve-out.
- Add a "URL shape requirements" section with the regex table so every sub-agent sees it.

---

## Part 5 — What to tell Jamie

> "Audited 82 tracker pages. The DB is cleaner than it feels — 89% is already triaged. What's breaking trust is **a small number of really bad recent additions**: LinkedIn search URLs, careers-homepage URLs, and Fresh labels on 17-day-old jobs. Cleaned up 5 of those today. The one role worth her attention right now is **Adyen HRBP on Greenhouse — confirmed live**.
>
> Pipeline has 6 root causes for why bad entries keep appearing. The biggest immediate win is a URL-shape validator that would have blocked today's UnitedLex/Spotify/PitchBook writes. The biggest structural fix is turning the 'audit Not-started entries' protocol into a real script with a hard gate instead of a paragraph in SKILL.md."

---

## Artifacts

- `pipeline_root_cause.md` — full 6-RC analysis with file:line evidence
- `link_health_A.json`, `link_health_B.json` — per-page verdicts for all 82 audited IDs
- `candidate_ids.txt`, `batch_A.txt`, `batch_B.txt` — working files
