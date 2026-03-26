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

## Future Enhancements

1. **Outcome Tracking:** Google Sheet integration to track apply → screen → offer pipeline
   - Add `Outcome` column to Notion DB or Google Sheet
   - After each application, track: Applied → Phone Screen → Interview → Offer/Reject
   - Use this data to tune scoring weights over time

2. **Proactive Company Monitoring:**
   - Track companies that recently raised funding (Crunchbase)
   - Track new CHRO/VP People hires (LinkedIn alerts)
   - These predict future people programs openings

3. **Scheduled Runs:**
   - Use `create_scheduled_task` for automatic daily execution
   - Weekday mornings (9am PT) when fresh listings appear

4. **Network Graph:**
   - Build a running graph of Jamie's connections and outreach attempts
   - Track: who was contacted, response received, referral given
   - Avoid re-contacting the same person for different roles

---

*Created: Mar 24, 2026 — v3.0.0*
