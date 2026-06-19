# What's Working — analysis of Jamie's reply-getting applications (2026-06-19)

> Audited every application that drew human engagement, checked which have source resume/cover files on disk,
> and extracted the concrete format/content pattern. Goal: codify "what works" so every future package matches it.

## The reply-getters (from dashboard outcomes.json, Gmail-verified 2026-06-18)

| Role | Outcome | Source files on disk? | Usable to learn from? |
|---|---|---|---|
| **More Than Models** — Talent Coordinator (Portland) | 🟢 **Interview requested** | ❌ none | No — Jamie applied herself (email-thread win, not pipeline) |
| **Bank of China** — HR/Quality Control Assoc | 🟢 **Interview booked** (panel) | ❌ none | No — applied herself, outside pipeline |
| **Brex** — Sales Enablement Specialist | 🟢 **Recruiter call** (Diane), then warm-reject | ✅ resume.json + cover.md/pdf | **YES — best pipeline-generated signal** |
| **Nike** — Lead, Learning & Development | 🟡 Warm (recruiter offered a call) | ✅ resume.json + cover.md/pdf | **YES** |
| **C1 / ConductorOne** | 🟡 Warm (then stalled) | ❌ none found | No |

**Honest caveat:** the two *interviews* (More Than Models, Bank of China) were Jamie's own applications — no files to study. The two pipeline packages that earned engagement are **Brex (recruiter call)** and **Nike (warm)**. Formatting exemplars **BCG** (screening call earlier) + **Roblox** (canonical gold standard) round out the set.

## The pattern — consistent across ALL engagement-getters

**Bold density (the thing that kept getting dropped):**
- Brex = **10** bold spans · Nike = **12** · BCG = **11**. Tonight's failures (Curai/Oscar/Amazon) = 0–1.
- This is now mechanically enforced by `verify_cover_format.py` (≥6 body bolds + ≥1 metric + ≥1 company).

**WHAT gets bolded (not random — high-scan-value targets):**
1. **The thesis phrase** in para 1 ("**Strong enablement**", "**people and process**")
2. **Every company name** at first mention (**InGenius Prep**, **Vestas Wind Systems**, **NextGen Healthcare**, **ODN Oregon**)
3. **The quantified accomplishment phrases with the numbers inside the bold** — e.g.
   "**built the onboarding processes and documentation for 70+ staff that cut ramp time by 75%**",
   "**facilitate training webinars for 600+ participants**", "**analyzed 2,000+ employee experiences**",
   "**300+ leave cases to surface $362K in costs**"
4. **The credential** — "**MS in Applied Organizational Psychology (USC)**" / "**MS, USC, 3.95**"
5. **A closing identity phrase** — "**analytical organizer with a growth mindset**"

**STRUCTURE (4 paragraphs, every engagement cover follows this):**
- **P1 — belief + role hook:** one belief sentence about the craft ("enablement isn't just scheduling a training—it's ramping people faster by building the logistics, materials, and feedback loops") + one sentence naming why THIS role drew her. Bold the thesis phrase.
- **P2 — strongest experience, story-led:** lead with the most relevant job; bold company + the metric phrases; include ONE specific mini-story ("when I launched a new sales process and adoption lagged, I interviewed the reps, found the blocker was friction not resistance, and built a one-page asset that lifted usage").
- **P3 — second experience + HONEST GAP DISCLOSURE:** Brex's worked *with* a candid gap line — "I'll be candid: I haven't carried an SDR quota myself. But the heart of this role—[the real overlap]—is exactly the work I've been doing." This RULE-0 honesty did NOT hurt — it got a recruiter call. Disclose-then-bridge is a feature, not a risk.
- **P4 — org-psych scientific-method close:** "grounded in my MS in Applied Organizational Psychology, which trained me to treat [domain] as a system: I diagnose with data where [X] stalls, collaborate cross-functionally on the fix, and track [metric] to make sure it holds." This close appears in BCG, Brex, Nike — it's the signature.

**TONE:** warm, first-person, specific; no clichés; em-dashes for rhythm; one genuine mini-story; ends "Sincerely/Warmly, Jamie".

**RESUME side (paired with every engagement cover):** canonical format — broad 3-pillar summary (97% extrovert kept), InGenius title "Program Enablement Manager" (or enablement variant), ODN=3 bullets / others=4, bolded `{kw|}` keyword highlights in bullets, canonical skills line. The resume that got the Brex call used the L&D/enablement recipe (LMS + CRM-HubSpot surfaced because the JD was sales-enablement).

## The takeaway (already enforced or to enforce)
1. ✅ **Cover keyword bolding** — now a hard gate (`verify_cover_format.py`), calibrated against these exact covers.
2. **Disclose-then-bridge on gaps is GOOD** — Brex proves an honest "I haven't done X, but the core of this role is Y which I have done" earns trust, not rejection. Keep doing it (it's also RULE 0).
3. **The 4-para structure + scientific-method close** is the proven spine — already in JAMIE_FEEDBACK_RULES §cover, reinforced by this evidence.
4. **Numbers belong inside the bold**, not adjacent to it — bold "**70+ staff... cut ramp time by 75%**", not just "staff".
