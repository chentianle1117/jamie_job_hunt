# 🔬 SOC-Code Sponsor Pre-Filter (v4.0 — May 15, 2026)

> **Purpose:** Pre-qualify every employer at the **SOC-code level** before adding to Oracle
> discovery pool. A company that sponsored 50 software engineers is NOT evidence they'll
> sponsor a non-tech People role. This file documents the procedure + the running result list.

---

## Why This Exists

May 15, 2026 forensic audit found a systemic failure: the `h1b_verified.md` ✅ list was
populated based on **any** H1B sponsorship by a company, not SOC-specific sponsorship for the
job categories Jamie targets. This produced multiple false positives that became real costs:

- Stripe, HubSpot, Plaid, Cloudflare, Datadog, Shopify, Twilio — all "✅ confirmed" but their
  LCA records are 100% tech (SWE/data/eng). Zero HR/People LCAs.
- Hasbro — listed as ✅, but actual LCA history is 9 petitions ever, all ecom/eng/QA/procurement —
  **zero HR/L&D/people roles**. Jamie would have been rejected at offer stage.
- Amazon — listed as ✅, but late-2024 policy halted non-tech H1B sponsorship including
  HR/Program Manager. Cache lagged this for months.

The fix: filter by SOC code, not by company name.

---

## Target SOC Codes for Jamie

| SOC Code | Title | Why It Matters |
|---|---|---|
| **13-1151** | Training and Development Specialists | Jamie's P1/P1b sweet spot — L&D, talent dev, learning program |
| **13-1071** | Human Resources Specialists | Jamie's P4/P5 — generalist HR, HRBP associate, people ops |
| **13-1121** | Meeting, Convention, and Event Planners | P1b cross-listing — program coordination, event ops in L&D contexts |
| **13-1141** | Compensation, Benefits, and Job Analysis Specialists | P2/P3 cross-listing — only relevant for consulting-side Mercer/Aon-type Total Rewards Analyst |
| **11-3121** | Human Resources Managers | Company-level signal only — most are too senior for Jamie. Used to confirm HR-mgmt sponsorship infrastructure exists. |
| **19-3032** | Industrial-Organizational Psychologists | Jamie's degree-coded SOC. Rare but exact match. |

**Excluded** (not Jamie's targets, but appear in HR-adjacent searches):
- 13-1075 (Labor Relations Specialists) — ER casework primary, ★☆☆ for Jamie
- 11-3111 (Compensation and Benefits Managers) — senior comp, not Jamie's tier

---

## Procedure

### Per NEW or UNKNOWN-status company

1. **Query `h1bdata.info`:**
   ```
   https://h1bdata.info/index.php?em={company-name}&job=&year=All
   ```
   Scan results table — filter for any title containing:
   `training`, `talent`, `people`, `human resources`, `HR`, `OD`, `organization development`,
   `learning`, `employee experience`, `engagement`, `change management`

2. **Cross-check `myvisajobs.com`:**
   ```
   https://www.myvisajobs.com/employer/{company-slug}/
   ```
   Look for LCA breakdown by job title.

3. **Optional — `h1bgrader.com`** for approval rates + FY2025 freshness:
   ```
   https://h1bgrader.com/h1b-sponsors/{company-slug}
   ```

4. **Classify the company:**

   | Result | Action |
   |---|---|
   | ≥1 certified LCA in past 24 months for one of the target SOC codes (or matching-title) | **✅ SOC-confirmed.** Add to `h1b_verified.md` ✅ section with `[SOC 13-1151, N LCAs FY25]` evidence note. Apply full H1B +5 modifier. |
   | Has LCAs but all in 15-1XXX (SWE/data) or 17-XXXX (engineer) categories | **⚠️ Tech-only.** Add to `h1b_verified.md` ⚠️ section with note "tech-only — non-tech sponsorship not demonstrated." No H1B +5 modifier. PASS the role unless JD explicitly says "will sponsor." |
   | Zero certified LCAs in past 24 months for any role | **❌ No history.** PASS the role unless company is cap-exempt OR JD explicitly says "will sponsor." Add to `h1b_verified.md` ❌ section with note "no LCA history past 24 months." |

5. **Re-check ✅-listed companies quarterly.** Sponsorship policy changes silently (Amazon halted non-tech sponsorship late 2024; the cache lagged this for months). Set a calendar reminder: 1st of every quarter, re-verify the top 20 ✅ entries.

---

## ⚠️ Tech-Only Sponsors (May 15 baseline — Apply NO H1B modifier)

These companies sponsor H1B but their LCA records show ZERO non-tech/non-engineering HR/People role sponsorship in the past 24 months. Treat as ❌ for Jamie's role types until SOC-specific evidence appears.

| Company | SOC Pattern | Source Date | Evidence |
|---|---|---|---|
| Stripe | 15-1252 (SWE) only | 2026-05-15 | 272 FY25 LCAs, all eng/data/PM |
| HubSpot | 15-1252 only | 2026-05-15 | No HR LCAs found |
| Plaid | 15-1252 only | 2026-05-15 | 40 FY25 LCAs, all eng |
| Cloudflare | 15-1252, 17-2XXX | 2026-05-15 | Systems/Data/Network Eng only |
| Datadog | 15-1252 | 2026-05-15 | Eng-only LCA pattern |
| Shopify | 15-1252 | 2026-05-15 | No HR LCAs |
| Twilio | 15-1252 + Staff PM/TAM | 2026-05-15 | Zero People LCAs |
| T-Mobile | Tech architects, eng | 2026-05-15 | 482 FY24 records, zero HR/coordinator/engagement |
| Zillow | 15-1252 + data | 2026-05-15 | 142 sponsorships, zero HR/people ops |
| Amazon (post-2024) | 15-1252 only (HR halted) | 2026-05-15 | Policy halt late 2024 — see h1b_verified.md note |
| Hasbro | Historical: ecom/eng/QA/procurement | 2026-05-15 | 9 LCAs total ever — ZERO HR/L&D |

---

## ✅ SOC-Confirmed (Non-Tech Sponsors for Jamie's Target SOCs)

| Company | SOC Match | Source Date | Evidence |
|---|---|---|---|
| Microsoft | 13-1151, 13-1071 ("Integrated Learning", "HR Business Partnership") | 2026-05-15 | Confirmed via May 15 Pass 3 LCA review — Microsoft does sponsor L&D function specifically. |
| BCG | Associate/Consultant titles incl People & Org Practice | 2026-05-15 | 69 FY26 LCAs, 131 historical Associate H1Bs. Selective at Analyst tier — possible not guaranteed. |
| Mercer (Marsh McLennan) | "Career Consulting Senior Analyst" historically | 2026-05-15 | Confirmed sponsor for Career business. |
| Guidehouse | 13-1XXX Consultant tier | 2026-05-15 | 25 FY25 LCAs, 100% approval. Sponsored titles include Consultant (2), Senior Consultant (28), Managing Consultant (16). |
| West Monroe | Consultant, Experienced Consultant | 2026-05-15 | 3 FY25 LCAs across People-adjacent titles. Small footprint but valid. |
| Google | Multiple non-eng SOCs including 13-1151 | 2026-05-15 | 8,945 FY25 LCAs, includes People Programs Specialist sponsorship for Talent Engagement role. |

---

## 🔄 Quarterly Re-Check Schedule

| Quarter | Action Date | Companies to Re-Verify |
|---|---|---|
| 2026 Q3 | Aug 1, 2026 | All ✅ entries in h1b_verified.md (top 20 by frequency in Oracle picks) + all ⚠️ tech-only entries (check if SOC pattern broadened) |
| 2026 Q4 | Nov 1, 2026 | Same |

---

## 📋 Update Log

| Date | Action |
|---|---|
| 2026-05-15 | v4.0 created. SOC-code procedure documented. Tech-only and SOC-confirmed lists seeded from May 15 7-pass forensic audit. |
