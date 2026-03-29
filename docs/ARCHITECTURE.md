# Oracle Pipeline v3.0 — Multi-Agent Architecture

## Overview

The Oracle pipeline can be decomposed into **5 agent workstreams** that run partially
in parallel. The main bottleneck is Chrome (serial — one tab group), but everything
else can be parallelized aggressively.

**Estimated runtime:** 15-20 min (down from 25-35 min in v2.x monolithic mode)

---

## Agent Topology

```
                    ┌──────────────────────────┐
                    │      ORCHESTRATOR         │
                    │   (main Claude thread)    │
                    │                           │
                    │  1. Reads SKILL.md        │
                    │  2. Spawns agents         │
                    │  3. Collects results      │
                    │  4. Chrome verification   │
                    │  5. Coordinates delivery  │
                    └────────┬─────────────────┘
                             │
            ┌────────────────┼────────────────────┐
            │                │                     │
   ┌────────▼────────┐ ┌────▼──────────┐ ┌───────▼────────┐
   │  AUDIT AGENT    │ │ DISCOVERY     │ │ WATCHLIST       │
   │  (background)   │ │ AGENT POOL    │ │ AGENT           │
   │                 │ │ (background)  │ │ (background)    │
   │  • Notion MCP   │ │               │ │                 │
   │  • Multi-batch  │ │ ┌───────────┐ │ │ • Reads         │
   │    search       │ │ │ Agent A   │ │ │   watchlist.md  │
   │  • Status check │ │ │ LinkedIn  │ │ │ • WebSearch     │
   │  • Build skip   │ │ │ GH/Lever  │ │ │   each Tier 1-3 │
   │    list         │ │ │ WebSearch │ │ │   company       │
   │                 │ │ ├───────────┤ │ │ • Returns new   │
   │  Returns:       │ │ │ Agent B   │ │ │   candidates    │
   │  • skip_list[]  │ │ │ Alt boards│ │ │                 │
   │  • cleanup[]    │ │ │ Handshake │ │ │ Returns:        │
   │  • active[]     │ │ │ Built In  │ │ │ • candidates[]  │
   │                 │ │ │ SHRM      │ │ │ • updated dates │
   └────────┬────────┘ │ ├───────────┤ │ └───────┬────────┘
            │          │ │ Agent C   │ │          │
            │          │ │ Cap-Exempt│ │          │
            │          │ │ OHSU, PSU │ │          │
            │          │ │ etc.      │ │          │
            │          │ └───────────┘ │          │
            │          └────┬──────────┘          │
            │               │                     │
            └───────────────┼─────────────────────┘
                            │
                     ALL RESULTS MERGED
                     Deduplicated by URL
                     Filtered through skip_list
                            │
                   ┌────────▼──────────┐
                   │  CHROME VERIFY    │
                   │  (main thread —   │
                   │   SERIAL)         │
                   │                   │
                   │  For each URL:    │
                   │  1. navigate      │
                   │  2. get_page_text │
                   │  3. Check live    │
                   │  4. Read full JD  │
                   │  5. Extract date  │
                   │                   │
                   │  Returns:         │
                   │  • verified[]     │
                   │    (live + JD)    │
                   └────────┬──────────┘
                            │
                   ┌────────▼──────────┐
                   │  FIT + SCORE      │
                   │  (main thread)    │
                   │                   │
                   │  Read resume.md   │
                   │  Read h1b_cache   │
                   │  Score each       │
                   │  Pick top 3       │
                   │  Add urgency tags │
                   └────────┬──────────┘
                            │
              ┌─────────────┼─────────────┐
              │             │             │
        ┌─────▼─────┐ ┌────▼────┐ ┌─────▼─────┐
        │ ENRICH #1 │ │ ENRICH  │ │ ENRICH #3 │
        │ (bg agent)│ │ #2 (bg) │ │ (bg agent)│
        │           │ │         │ │           │
        │ • Cover   │ │ • Cover │ │ • Cover   │
        │   letter  │ │   letter│ │   letter  │
        │ • Resume  │ │ • Resume│ │ • Resume  │
        │   tailor  │ │   tailor│ │   tailor  │
        │ • Find    │ │         │ │           │
        │   contacts│ │         │ │           │
        │   (Chrome)│ │         │ │           │
        │ • Draft   │ │         │ │           │
        │   outreach│ │         │ │           │
        │ • Company │ │         │ │           │
        │   research│ │         │ │           │
        │ • Notion  │ │         │ │           │
        │   page    │ │         │ │           │
        └─────┬─────┘ └────┬────┘ └─────┬─────┘
              │             │             │
              └─────────────┼─────────────┘
                            │
                   ┌────────▼──────────┐
                   │  DELIVERY         │
                   │  (main thread)    │
                   │                   │
                   │  1. Write files   │
                   │  2. Gmail draft   │
                   │  3. Telegram      │
                   │  4. Update        │
                   │     watchlist.md  │
                   │     h1b_cache     │
                   │  5. Summary       │
                   └───────────────────┘
```

---

## Agent Specifications

### 1. Audit Agent
- **Type:** `general-purpose` (background)
- **Tools needed:** Notion MCP (search, fetch, update-page)
- **Input:** Notion DB ID, search batch keywords
- **Output:** `{ skip_list: string[], active_entries: Entry[], cleanup_count: number }`
- **Duration:** ~3-5 min (10 search batches + status verification)
- **Can run simultaneously with:** Discovery agents

### 2. Discovery Agent Pool (3 parallel agents)
- **Type:** `general-purpose` (background)
- **Tools needed:** WebSearch only (no Chrome — Chrome is reserved for main thread)
- **Agent A — LinkedIn/Greenhouse/Lever:**
  - Runs all `site:greenhouse.io` and `site:lever.co` WebSearch queries
  - Runs local Portland/Seattle WebSearch queries
  - Returns: `{ candidates: [{url, title, company, source}] }`
- **Agent B — Alternative Boards:**
  - Runs Handshake, Built In, SHRM, Idealist, Wellfound WebSearch queries
  - Returns: `{ candidates: [{url, title, company, source}] }`
- **Agent C — Cap-Exempt Employers:**
  - Reads watchlist.md Tier 3
  - WebSearch each cap-exempt employer's careers page
  - Returns: `{ candidates: [{url, title, company, source}] }`
- **Duration:** ~2-4 min each (running in parallel)

### 3. Watchlist Agent
- **Type:** `general-purpose` (background)
- **Tools needed:** Read (file), WebSearch
- **Input:** `watchlist.md` file
- **Process:**
  1. Read watchlist.md
  2. For each Tier 1-2 company with `last_checked` > 3 days ago:
     - WebSearch: `site:{careers_url} "people" OR "talent" OR "program"`
  3. Return any new candidates found
  4. Return updated `last_checked` dates
- **Output:** `{ candidates: [...], watchlist_updates: [{company, last_checked}] }`
- **Duration:** ~3-5 min

### 4. Enrichment Agents (1 per pick, max 3)
- **Type:** `general-purpose` (background)
- **Tools needed:** WebSearch, Read (resume.md, outreach_templates.md), Notion MCP (create page)
- **⚠️ Chrome contention:** Networking contact search requires Chrome. Options:
  - Option A: Main thread handles all Chrome networking searches sequentially, passes contacts to enrichment agents
  - Option B: Enrichment agents use WebSearch (`site:linkedin.com/in`) as fallback (less accurate but parallel)
  - **Recommended: Option A** — main thread does Chrome networking, enrichment agents handle writing
- **Input per agent:** `{ jd_text, company, resume_md, outreach_templates_md, contacts[] }`
- **Output per agent:** Full Notion page content (cover letter, resume tailoring, outreach drafts, interview prep)
- **Duration:** ~2-3 min each (running in parallel)

### 5. Delivery (main thread)
- **Tools needed:** Write (file), Gmail MCP, Bash (Telegram)
- **Process:** Sequential — write files → create Gmail draft → Telegram → summary
- **Duration:** ~1-2 min

---

## Timing Comparison

| Phase | v2.x (Serial) | v3.0 (Parallel) |
|-------|----------------|------------------|
| DB Audit | 5 min | 5 min (background) |
| Discovery | 10 min | 4 min (3 parallel agents) |
| Chrome Verify | 8 min | 8 min (serial — bottleneck) |
| Fit Assessment | 2 min | 2 min |
| Enrichment | 9 min (3 × 3 min) | 3 min (3 parallel agents) |
| Delivery | 2 min | 2 min |
| **TOTAL** | **~36 min** | **~19 min** |

Audit and Discovery overlap → saves ~5 min.
Enrichment parallelized → saves ~6 min.
Net savings: ~17 min per run (47% faster).

---

## Implementation Notes

### Claude Agent Tool Usage
```python
# Spawn audit + discovery simultaneously
Agent(description="audit notion db", prompt="...", run_in_background=True)
Agent(description="search greenhouse lever", prompt="...", run_in_background=True)
Agent(description="search alt job boards", prompt="...", run_in_background=True)
Agent(description="check watchlist companies", prompt="...", run_in_background=True)

# Wait for all to complete, merge results
# Then Chrome verify (serial, main thread)

# Spawn enrichment per pick
for pick in top_3:
    Agent(description=f"enrich {pick.company}", prompt="...", run_in_background=True)

# Wait, then deliver
```

### Chrome Bottleneck Mitigation
Chrome is the serial bottleneck. To minimize time:
1. **Pre-filter aggressively** in quality gate (Step 2f) before Chrome
2. **Batch Chrome tabs** — open 3-4 URLs, then read all sequentially
3. **Use `get_page_text` over screenshots** — faster and more reliable
4. **Parallelize non-Chrome enrichment** — cover letters, company research don't need Chrome

### State Files Updated Each Run
- `watchlist.md` → update `last_checked` dates for all companies checked
- `h1b_verified.md` → add any newly verified companies
- Notion DB → new entries + status updates

---

## v3.3 Enhancements (Mar 28, 2026)

### New Pre-Fetch Layer (Step 0.5)

Added a pre-fetch stage that runs BEFORE the main agent pipeline:

```
STEP 0.5 — PRE-FETCH (Python scripts + Gmail MCP)
│
├── fetch_ats_jobs.py     — Greenhouse + Lever public JSON APIs (14 verified companies)
│   Output: C:\Windows\Temp\ats_jobs.json
│   Speed: ~10 sec for all companies (vs ~8 min Chrome verification)
│   Reliability: 100% (public APIs, no auth, no anti-bot)
│
├── jobspy_search.py      — LinkedIn + Indeed + Glassdoor scraper (python-jobspy)
│   Output: C:\Windows\Temp\jobspy_results.json + .csv
│   Speed: ~30-60 sec for 6 search configs
│   Reliability: Indeed = excellent (no rate limit); LinkedIn = good (~100 results)
│
└── Gmail MCP alerts       — Parse job alert emails from LinkedIn/Indeed/Glassdoor
    Speed: ~10 sec
    Catches: Jobs that Brave-backed WebSearch misses (~13% miss rate vs Google)
```

**Impact on pipeline timing:**
| Phase | v3.2 | v3.3 | Change |
|-------|------|------|--------|
| Pre-fetch | — | 1-2 min | NEW |
| Discovery | 4 min | 4 min | Same |
| Chrome verify | 8 min | 4-5 min | **~40% fewer URLs need Chrome** (ATS API jobs pre-verified) |
| Fit assessment | 2 min | 2 min | Same |
| Enrichment | 3 min | 3 min | Same |
| Delivery | 2 min | 2 min | Same |
| **TOTAL** | **~19 min** | **~16-18 min** | Faster + more exhaustive |

### New US Sources Added to Existing Agents

- **Agent D** now includes HigherEdJobs (cap-exempt university/nonprofit HR roles)
- **Agent E** now includes FlexJobs, We Work Remotely, Remote.co, Himalayas
- **Email alerts** parsed at start of each run via Gmail MCP

### Outcome Tracking Loop (2d-7)

End-of-run check against Google Sheet for status updates on past applications.
Builds feedback data for improving future scoring and resume tailoring.

---

## Future Enhancements (Remaining)

1. **Proactive Company Monitoring:**
   - Track companies that recently raised funding (Crunchbase)
   - Track new CHRO/VP People hires (LinkedIn alerts)
   - These predict future people programs openings

2. **Network Graph:**
   - Build a running graph of Jamie's connections and outreach attempts
   - Track: who was contacted, response received, referral given
   - Avoid re-contacting the same person for different roles

3. **Adzuna MCP Server:**
   - Install `folathecoder/adzuna-job-search-mcp` for direct Claude Code integration
   - Covers 12 countries (NL, UK, DE, FR, etc.) with structured API access
   - Requires free API key from developer.adzuna.com

---

*Created: Mar 24, 2026 — v3.0.0*
*Updated: Mar 28, 2026 — v3.3.0 (pre-fetch layer, NL/EU sources, outcome tracking)*
