# Jamie's Job Application Tracker

> **🔴 SINGLE SOURCE OF TRUTH: The Google Sheet, always.**
> No static snapshot is maintained in this file. Static snapshots become stale
> within days and have repeatedly caused incorrect dedup decisions
> (e.g. recommending companies Jamie has already applied to, or assuming an
> "Applied" status that's actually been updated to "Rejected" / "Interview" /
> "Not God's Plan" in the live sheet).

## Live Data Source

- **Sheet ID:** `1tRN3KMGHOSyRMf14TRUj3wPldbM9fwDxVu9XsEH6s2E`
- **Sheet URL (browser):** https://docs.google.com/spreadsheets/d/1tRN3KMGHOSyRMf14TRUj3wPldbM9fwDxVu9XsEH6s2E
- **2025 tab CSV export (gid=0):** https://docs.google.com/spreadsheets/d/1tRN3KMGHOSyRMf14TRUj3wPldbM9fwDxVu9XsEH6s2E/export?format=csv&gid=0
- **2026 tab CSV export (gid=1018026840):** https://docs.google.com/spreadsheets/d/1tRN3KMGHOSyRMf14TRUj3wPldbM9fwDxVu9XsEH6s2E/export?format=csv&gid=1018026840

## How to read live data

### Preferred: workspace-mcp Drive tools (authenticated)
- If the file is accessible through the workspace-mcp Drive resources, use
  those tools — they handle Google authentication cleanly.

### Fallback: WebFetch on the CSV export URL
1. `WebFetch` the 2026 CSV export URL above.
2. Google returns a 307 redirect to a googleusercontent.com URL — follow it
   with a second `WebFetch` to retrieve the raw CSV.
3. Parse CSV columns: `App. date, Job Title, Company, Job Category,
   Location, Interest, Notes, Fun Fact, Hiring Managers/Team, Alumni,
   Referral, Sponsorship?`

### When the live Sheet is unreachable
- **DO NOT fabricate a snapshot.** Tell Jamie the Sheet is unreachable and
  pause the pipeline until it can be re-fetched. Skipping the dedup check is
  worse than waiting — duplicate applications waste runway and create a poor
  signal to recruiters.

## When to consult the Sheet

| Skill / pipeline step | Why fetch the Sheet |
|---|---|
| `/evaluate` (Stage 1 hard-constraint check) | Confirm Jamie hasn't already applied to this company + title pair |
| `/apply-pipeline` (any stage) | Same as above |
| `/jamie-job-search` Oracle daily run | Dedup against in-flight applications before adding new leads to Notion |
| Funnel analysis / pipeline reporting | The Sheet IS the funnel — Status + Date + Outreach columns drive metrics |

## Sheet schema (as of 2026-05-14)

Each row represents one application. Columns:

| Column | Meaning |
|---|---|
| `App. date` | Date of application submission (M/D/YYYY) |
| `Job Title` | Exact JD title at the time of application |
| `Company` | Employer |
| `Job Category` | One of: L&D · OD/OCM/EX · HR/HRBP · HR/Consulting · Program Management · Others |
| `Location` | Stated location on JD |
| `Interest` | Jamie's interest rating (1-5 stars) |
| `Notes` | Hiring manager contacts, role notes, internal status updates |
| `Fun Fact` | Optional flavor |
| `Hiring Managers/Team` | Names and contact info gathered from outreach |
| `Alumni` | USC / Wesleyan alumni at the company |
| `Referral` | Referral status / contact |
| `Sponsorship?` | H-1B sponsorship verified / unknown / "YES" flag |

Status is tracked implicitly through the **Job Category** and **Notes** columns
plus the legend Jamie maintains in the Sheet (Applied / Interview / Not
God's Plan / Connected NGP / Unavailable / Not Yet). The Sheet is the
single source of truth — do not infer status from this markdown file.

## Status key (used by Jamie in the Sheet)

- **Applied** — application submitted, awaiting response
- **Interview** — phone screen or onsite interview scheduled or completed
- **Not God's Plan** (NGP) — rejected by employer OR Jamie decided not to pursue
- **Connected, NGP** — warm conversation reached but role didn't progress
- **Unavailable** — role closed before Jamie could apply
- **Not Yet** — identified but not yet applied
