# LinkedIn Authed Harvest — Round 3 (2026-06-14)

**Auth:** ✅ Confirmed authenticated (port 9222 CDP, Jamie logged in — USC-alumni annotations + Premium upsells present on every surface). Read-only. No submit / no account / no apply / no save. Other agent tabs left untouched.

**Verdict:** LinkedIn is **lightly tapped, not saturated.** Saved/Applied/Archived tabs are essentially fully consumed. Recommended recycles known hard-stops. Targeted authed searches DID surface a genuine fresh batch — but it's **incremental** (9 new, ~4 clean fits), and most P1 hits are **sponsor-silent remote roles needing an h1bdata check before build.**

## Genuinely-new roles: 9 recordable + 5 sidebar leads

### Tier A — clean / strong fits (build-first)
| Company | Title | Loc | YOE | Mechanism | Why |
|---|---|---|---|---|---|
| **Navitus Health Solutions** | Learning & Development Generalist | Remote | ~3 (clean!) | external ATS | Best YOE alignment of the batch; L&D-ops generalist = Jamie's core. P1b. |
| **Autodesk** | Senior Org Effectiveness Consultant | **Portland, OR (Hybrid)** | ~8 (stretch) | Workday | ONLY Portland-local sweet-spot find; OD = ODN-Oregon + Applied Org Psych core. Jamie already "Viewed" it. P3 + local advantage. |
| **RxBenefits** | Learning & Talent Development Specialist | Remote | ~5 | external ATS | From Jamie's own Saved list (saved 1d ago = high intent). Direct P1b title. |
| **LEAP Legal Software** | Client Success Learning Program Manager | Remote | ~4 | Easy Apply | CS-enablement/learning PM, $115-140K. P1b. |

### Tier B — stretch / low-priority (record, verify before effort)
| Company | Title | Loc | Caveat |
|---|---|---|---|
| **Gainsight** | Sr Program Manager, People Programs & AI | Remote | Bullseye title BUT **6-10+ yr PM** req = real 2yr gap → fit caps ~60. Fresh (1d) + 76 apps. $120-150K. |
| **Chainalysis** | People Programs Lead | Remote | P1 title, ~6 yr stretch, 6d old. Re-check ITAR/clearance at build (blockchain/LE customers; JD body silent). |
| **Core & Main** | Operations & Learning Specialist | Remote (TX) | Thin JD; industrial distributor → H1B-for-L&D unlikely. Low confidence. |
| **Exact Sciences** | Clinical Lab Learning Program Manager | **On-site Madison WI** | Niche clinical + relocation; misses Tier-3 85% bar. |
| **Tenstorrent** | HR Project Manager, People Programs (**Contractor**) | Remote | Contract → rarely sponsors + Tier-3 excludes contract; semiconductor ITAR risk on FTE. Likely ineligible. |

### Sidebar leads (authed "More jobs" rail — need jid resolution next window)
- **Wrapbook** — Senior People Programs Manager — Remote — $130K-211.5K — **P1, strongest-looking lead**, ~2wk old
- **Ashby** — Customer Education Program Manager — Remote — $135K-153K — P1b (distinct from the OpenAI Cust-Ed PM already in pipeline), ~2d
- **Spring Health** — Sr PM, Dedicated Workplace Teams — Remote — ~6d (verify internal-People vs client-delivery)
- **Superior Plus Propane** — PM, Talent Performance & Experience — Remote — ~1wk (verify sponsor; propane distributor)
- **Activate** — PM, Fellowship & Programs Recruitment — Remote — ~2wk (verify duties; "Recruitment" may = TA)

## Excluded this run
- **Hard blockers:** Deloitte (no-H1B), Sonos (no-sponsor), Seattle Public Utilities (gov), Propeller (7yr), **L3Harris (defense → ITAR, not opened)**, Legacy Health (ER-casework primary)
- **Too senior (PASS):** Oregon Nurses Assn — Equity & HR **Director**; Stanley House — Exec Culture Coach (10-12yr)
- **Weak/borderline (noted, not recommended):** IA Interior Architects Workplace Strategist (= physical-space consulting, not HR EX); ESC Central Ohio Early-Dev Learning PM (K-12/gov + onsite OH)
- **Saved tab:** 9/10 already in pipeline (C1, EY, Premera, Jacobs, Banfield, Syneos, OHSU-HRBP, Aptive, 4G Clinical)
- **Applied tab:** 9 Jamie applied herself — all excluded
- **Archived tab:** 10 all closed — excluded
- Deduped against full 115-record `master_submissions.json` + round-1 (27) + round-2 (5) discovery files + tonight's explicit submitted/staged/hard-stop sets

## Caveats / honesty
1. **Search depth was capped at ~7 cards/query** by LinkedIn's virtualized list (scroll did not reliably page the result pane). Pagination via `&start=25` helped on the Portland query (14) but most queries returned the first page only. There may be a few more fresh roles on pages 2-3 of the broader searches I couldn't surface.
2. **Every P1 hit here is sponsor-SILENT** at a firm whose **non-tech** H1B pattern is unverified. Per the H1B cache discipline, each needs an h1bdata SOC-13-1151/11-3121 check before being treated as anything better than sponsor-unknown STRETCH.
3. All 9 recorded roles **rendered a live JD** when opened (live_verified = true). None showed "No longer accepting applications."

**Files:** `LINKEDIN_HARVEST_ROUND3.json` (structured) · `LINKEDIN_HARVEST_ROUND3.md` (this).
