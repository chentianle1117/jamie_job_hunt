---
name: pipeline-filtering-should-be-lenient
description: "Oracle pipeline should show all viable candidates to Jamie, not over-filter. Skip by company+title pair not company name."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 1cc5945f-7f76-42d1-8cb4-acad5c9bc387
---

Pipeline should be lenient on selections — show Jamie MORE candidates and let her filter, not less.

**Why:** David observed that the skip list was rejecting entire companies (e.g., all of Roblox, all of Stripe) just because Jamie applied to one specific role there. This threw away potentially good matches at the same company but different role. Also, the pipeline was gatekeeping "stretch" roles (60% fit) that Jamie might actually want to try, especially if cap-exempt.

**How to apply:**
- Skip list must use (company, title) pairs, never whole company names
- Only auto-reject on hard constraints: 5+ yrs, "no sponsorship", non-US, Senior/Director/VP title
- Everything else goes in the email digest with honest assessment — let Jamie decide
- Include posted date on every role so Jamie can filter by freshness herself
- When in doubt, include the role with a clear note about the stretch/gap

## UPDATE 2026-05-29 — Scope is broader than People-only; review-gate before bulk submit
- **Product/Program PM is IN-SCOPE, not a stretch.** Jamie's current title is Program Manager and she
  manages educational *products*. She is explicitly open to product-related program management — "as long
  as my skill sets can fit, I would not shy away." So product-ops / product PM / program PM roles (e.g.
  Accuris "Program Manager, NPI") count as legitimate fits, not off-field. Discovery should target BOTH
  People/HR/OD/L&D AND product/program-management roles.
- **Review-gate protocol:** When Jamie hand-picks specific jobs OR after encoding new feedback, do NOT
  auto-submit. Tailor + render the resume/cover and surface them in the dashboard as a PENDING-CONFIRMATION
  lane so Jamie can verify her feedback was incorporated BEFORE any live submission. She confirms, then submit.
- **2026-05-29 run was package-only:** 3 hand-picked (Axon EE Program Manager / Accuris PM-NPI / Chartis
  Associate-Learning) + a discovery fleet of ~20-30 roles, ALL tailored + rendered to dashboard, ZERO submitted,
  pending Jamie's confirmation that the new feedback rules landed correctly.

## UPDATE 2026-05-29 (later) — more global rules + blocked-ATS research + dashboard outreach lane
- **NEW global resume rules** (JAMIE_FEEDBACK_RULES.md + content_library.md): default metric = "78% PROGRAM
  ENROLLMENT rate" (client-conversion only for product/sales roles); self-title must be a BROAD UMBRELLA (People &
  Org Development professional / Strategic Program Manager / People Program Manager), never niche like "Employee
  Experience professional"; ODN = TWO SEPARATE PROJECTS (absenteeism-diagnosis vs NGO-leadership-accountability),
  never blended; aggressive JD keyword swapping (operations/logistics/communication/new hires/delivery); reorder
  bullets by relevance. InGenius real scope: communication strategy, Mktg/Tech/Sales teams, logistics, delivery,
  operations, program positioning/value proposition, documentation.
- **Dashboard standard going forward: embed outreach DRAFTS inline** (subject + full body + LinkedIn link +
  verification) so Jamie reviews content in one place. In runs/2026-05-29_jamie3/build_dashboard.py.
- **Blocked-ATS auto-apply research** (jamie-autopilot/docs/blocked_ats_automation_research_2026-05-29.md):
  path = CDP-attach to real Chrome + vision-LLM agent (browser-use, maintained) cdp_url=localhost:9222. Jamie
  pre-creates the per-employer account ONCE (safety rules forbid us creating accounts), agent reuses session.
  Easiest+highest-ROI = PeopleAdmin + PageUp (state universities). Workday ~65-75%. Taleo dead, AIHawk archived.
- **LIVE-SUBMIT BLOCKER (recurring):** needs Chrome on CDP port 9222, but 9222 often held by msedgewebview2
  (Lenovo Vantage). Relaunch Chrome: --remote-debugging-port=9222 --profile-directory="Profile 6".
- 5 verified outreach contacts (Axon: Cheney Ferrell HRBP Mgr + Katie Becker Exec Recruiting; Stripe: Julia Simpson
  PM People Strategy; Ironclad: Jenna Flint Dir People Ops; 80k Hours: Lucia De Santis). In runs/2026-05-29_jamie3/outreach_drafts.json.

## UPDATE 2026-05-29 — STANDING AUTHORIZATION for autopilot submission (David, explicit)
- **Once David authorizes a submission run, JUST COMPLETE IT end-to-end.** Do NOT pause to re-confirm
  each app, each batch, or "should I proceed?" mid-run. The authorization is standing for that run:
  relaunch Chrome, submit every auto-submittable role, retry fixable failures, run all ATS batches,
  capture confirmations, update dashboard/tracker, commit — all without stopping to ask.
- This applies to the autopilot auto-submission specifically. David trusts the pipeline; asking for
  permission at each step is friction he doesn't want.
- **The ONE exception that still routes to manual review (not a permission ask — a correctness/legal limit):**
  legal-attestation form questions — firearms eligibility (18 USC 922), criminal-history, court-order,
  EAR/ITAR export-control. Never auto-answer these; flag NEEDS_REVIEW so Jamie certifies them herself.
  Everything else (work-auth=Yes, sponsorship=Yes honest, demographics Woman/Asian, age 18+, standard
  custom questions) is auto-filled and submitted.

## UPDATE 2026-05-30 — David authorizes answering legal-attestation questions (Jamie has ZERO exposure)
- David explicitly authorized auto-answering the previously-gated legal questions, because neither Jamie
  nor David has any exposure to them. Truthful answers to use:
  - ATF / firearms eligibility (18 USC 922): Jamie is ELIGIBLE / NOT prohibited. Answer the disqualifier
    questions (felony conviction, domestic-violence misdemeanor, court/protection order, indictment,
    dishonorable discharge, fugitive, etc.) as NO / not-applicable. If asked "are you eligible to possess
    a firearm" answer YES.
  - Criminal history: NONE. No convictions, no indictment, no pending charges -> answer No.
  - Veteran status: No / "I am not a protected veteran".
  - EAR/ITAR deemed-export: answer the standard truthful way for a foreign national, BUT surface the exact
    question text to David in the conclusion so he can confirm.
- **NEW RULE — never silently skip:** if there's any custom question the handler genuinely cannot answer,
  DISPLAY THE EXACT QUESTION TEXT to David (in the chat conclusion AND the dashboard NEEDS_REVIEW section),
  never just drop it. David authorizes answering; he just wants visibility into what was answered/asked.
- Override scope: "submit everything" — answer all standard + legal-attestation questions truthfully and
  submit; only escalate genuinely-ambiguous custom questions (with their exact text) for David to see.

## UPDATE 2026-05-30 — LLM submitter built; react-select commit + Chrome 136 CDP wall
- Built `jamie-autopilot/lib/submit_llm_generic.py`: Patchright loads the Greenhouse form,
  extracts every question (label/type/options), batches to **Gemini CLI (gemini-2.5-flash) via stdin**
  with `lib/jamie_answer_profile.py` (truthful answer source), gets JSON answers, fills + submits.
  The BRAIN WORKS GREAT — answers employer/title/work-auth/sponsorship/demographics/legal correctly.
- **TWO blockers stop actual submission on the current machine:**
  1. **react-select commit:** values fill visually + pass a `.select__single-value` chip-check, but
     Greenhouse SERVER-SIDE validation still reports the field empty on final submit. The hidden
     controlled-input isn't registering the option click as a React change event that survives validation.
     Adopted the proven Aurora-v6 pattern (click input → type full value → click div[role=option] by
     has_text → 900/1300/700ms waits) — DRY shows could_not_answer=[] but live submit still rejects.
  2. **CDP-attach is blocked:** the prior breakthrough (connect_over_cdp to real Chrome on a debug port)
     no longer works — **Chrome 136+ refuses --remote-debugging-port on the DEFAULT user-data-dir** (2025
     security change), and port 9222/9333 launches silently ignore the flag if Chrome already runs on that
     profile dir. Also msedgewebview2 (Lenovo Vantage) squats on 9222.
- **NEXT-SESSION FIX OPTIONS (in priority order):**
  a) Run Patchright via `connect_over_cdp` against a DEDICATED clone profile dir launched with the debug
     port (NOT the default dir) — Chrome allows debugging on non-default dirs. Re-clone profile if DPAPI stale.
  b) Set the react-select value by dispatching native input+change events via page.evaluate on the hidden
     input, then verify the hidden requiredInput, instead of relying on the option click.
  c) Install `browser-use` + a vision model and let it drive (the research's original recommendation).
- **What IS done + shippable now:** 19 fully-tailored packages (resume+cover PDFs, 1-page, audited),
  5 verified outreach drafts, dashboard with all of it. Forms fill correctly (screenshots prove it);
  only the final commit-through-validation is unresolved on this Chrome build. 0 live submissions landed
  this session via autopilot.

## UPDATE 2026-05-30 — AUTOPILOT SUBMISSION WORKS AGAIN: 5 LIVE SUBMITS + the fix
**5 confirmed live submissions this run** (Greenhouse /confirmation pages captured):
Flexport People Ops Coordinator, Stripe PM People Ops Strategy, Faire HRBP, Asana
Implementation Manager, Asana Customer Enablement Manager. Tracker: oracle-job-search/jamie/master_tracker.json (10 total).

### THE WORKING SUBMITTER (jamie-autopilot/lib/submit_llm_generic.py) — how it works now:
- **Engine:** Patchright `connect_over_cdp` to a DEDICATED debug Chrome profile (Chrome 148 BLOCKS
  --remote-debugging-port on the DEFAULT user-data-dir; a separate dir works). Launch:
  `chrome.exe --remote-debugging-port=9222 --user-data-dir="%LOCALAPPDATA%\Google\Chrome\autopilot_debug_profile"`
  then run with env `CDP_PORT=9222`. (Also runs without CDP via clone-profile launch_persistent_context.)
- **Brain:** Gemini CLI (`gemini -m gemini-2.5-flash`, prompt via stdin) + `lib/jamie_answer_profile.py`
  (truthful answer source). Extracts every form question, asks Gemini to pick answers.
- **THE TWO ROOT-CAUSE FIXES (why it failed all day, then worked):**
  1. **Scrape REAL options per dropdown** (live_options) and let Gemini pick a valid one. The brain was
     answering guessed text ("LinkedIn") that wasn't a real option ("Career Platform (LinkedIn, Glassdoor,
     BuiltIn, etc.)") so Greenhouse silently kept the field empty.
  2. **Scope option clicks to `#react-select-{qid}-listbox`** — NOT the global `[role=option]` pool. Greenhouse
     forms with a phone field have an intl-tel-input widget injecting 244 country options into the global DOM;
     clicking "Yes" globally was actually clicking "Zimbabwe". Scoping to the question's own listbox fixes it.
  - Plus: truthful legal answers (firearms eligible / criminal none / veteran No — David authorized),
    demographics Woman/Asian, checkbox-tick for acknowledgments, EAR flagged-for-review.
- **Why the prior 5 (Roivant/BuiltIn/Aurora) worked before:** their dropdowns had no phone-widget pollution
  and filtered on type, so plain type+Enter hit the right option.

### STILL MANUAL / NOT LANDED:
- **Axon (Jamie pick #1):** 50-field Greenhouse form w/ ATF Prohibited-Possessor questionnaire + acknowledgment
  checkbox + EEO; the form RESETS all fields on submit-validation — single-pass autopilot can't land it.
  NEEDS_REVIEW.json written. Best path: Greenhouse candidate account (auto-fills) or one manual pass. Strong fit + sponsor.
- **Accuris (pick #2):** Dayforce — blocked ATS, manual only.
- **Chartis (pick #3) + Ashby roles (Whatnot/Replit/Ironclad/80kHours):** Ashby is a deferred React SPA;
  submit_ashby_generic.py exists but lacks the Gemini brain + needs more mount-wait. NOT yet submitted. TODO next session.
- **Human Interest:** role closed (404).
- **5 outreach drafts** (Axon x2, Stripe, Ironclad, 80k) in runs/2026-05-29_jamie3/outreach_drafts.json — review/send via Jamie Gmail (auth was down).

---

## Night run 2026-05-31 — results + new mechanics (essay-gate, embed-URL wrappers, Ashby)

**Run dir:** `oracle-job-search/runs/2026-05-30_night/`. Dashboard: `dashboard_review.html`.

### Outcome (40 roles discovered → processed)
- **7 AUTO-SUBMITTED** (confirmed): Affirm (People Knowledge Exp), Datadog (PBP + People Solutions Coord), Decagon (Talent Associate + Implementation Mgr), Instacart (Assoc HRBP), Scale AI (Engagement Mgr). master_tracker now 17 total.
- **16 ESSAY-REVIEW**: custom "Why this company?" essays. Opus drafted answers in Jamie's voice (`essay_answers_draft.json` per role) for dashboard approval. NOT auto-submitted (David policy 2026-05-31).
- **4 NEEDS-MANUAL**: branded-form widgets a couple fields didn't auto-fill.
- **6 BLOCKED-ATS**: Workday/iCIMS/Stanford-portal (incl. cap-exempt gems: Stanford ×3, UO, OHSU + Nike). Packages ready, manual apply.
- **7 DEFERRED**: per-company sound-judgment cap (keep best 1-2 per company) + Affirm Workplace (no-sponsor).

### KEY NEW MECHANICS (all committed)
1. **ESSAY REVIEW-GATE** (`submit_llm_generic.py`): `_is_essay()` detects open-ended prose Qs (textarea, or "why/tell us/what excites" labels). Essay roles → write `essays_for_review.json` + `NEEDS_REVIEW.json`, fill all NON-essay fields, then DO NOT submit. No-essay roles auto-submit. Pre-approved answers loaded from `essay_answers.json` (so an approved essay role becomes auto-submittable). Opus drafts essays — NOT Gemini.
2. **jamie_voice_profile.md** (jamie-autopilot/lib): mined from real cover letters — reframe-then-belief openings, diagnose→collaborate→measure throughline, "analytical organizer with a growth mindset," honest gap-naming. Prepend for any Jamie-voice prose.
3. **EMBED-URL FIX for branded careers wrappers**: Datadog (careers.datadoghq.com), Instacart (instacart.careers), Lyft (careerpuck), SoFi (sofi.com/careers) all redirect the canonical Greenhouse URL to a branded JD page with NO form → bot fills nothing. FIX: use `job-boards.greenhouse.io/embed/job_app?for={slug}&token={gh_jid}` (returns the bare form, no redirect). This recovered Datadog PBP + Instacart submits. Detect wrappers by `url_after` not being a greenhouse.io domain.
4. **Verifier false-negative fix**: `_committed()` now also detects newer Greenhouse react-select skins (Faire) via `.select__multi-value`, value-container text ≠ placeholder, and clear-indicator presence. Earlier these valid selections were wrongly flagged `[??]`.
5. **WORKING Ashby submitter** (`submit_ashby_generic.py`): deferred React SPA cracked — navigate `{url}/application` directly (form mounts there, no Apply-click needed), poll for input count >0, iterate LEAF `.ashby-application-form-field-entry` only, Yes/No = hidden checkbox + visible buttons (click button, verify `_active_` class), EEO radios fuzzy-match (Woman→Female). Delegates `ask_gemini` to the shared brain. Resume upload = `input[type=file][id="_systemfield_resume"]`.

### VOLUME SAFETY (answered David's Q)
20 apps across ~18 distinct companies/ATS tenants = safe (no cross-company counter; not LinkedIn which is the only rate-limited surface). Risk is only many-roles-at-one-company → applied per-company cap (best 1-2). Patchright stealth + dedicated debug profile + human pauses mitigate bot-detection.

### STILL-OPEN failure modes (for next iteration)
- Ashby `unanswered=1` on several (Writer/Ramp/Harvey/Notion CS/ElevenLabs/Replit/Baseten) — usually a missed required field (location-ack statement, or an essay). Mostly captured as essay now.
- Datadog/complex Greenhouse: multi-select "select all languages" + long certify-checkbox-as-statement sometimes miss. Tighten multi-select + statement-checkbox handling.
- Axon: still NEEDS_REVIEW (50-field ATF firearms form) per David.

---

## STRICT YOE RULE (David, 2026-05-31) — applies to ALL future runs
**Only apply to roles requiring ≤4 years of experience. 5+ years required = DO NOT APPLY.**
- "3-5 yrs" (floor 3) = apply. "4-6" (floor 4) = apply. "5+" / "5-7" / "6-10" / "7+" = DROP.
- 4 years or under = apply; 5 or more = drop. Be strict; default Jamie to ~3 yrs.
- Confirmed DROPs this run: Harvey PBP (6-10 yrs), Lyft Program Mgr Process (5+ yrs), Notion CS Enablement PM (5+ yrs). Re-audit all roles' JD YOE before submitting.
- This supersedes the looser "consulting exception / ≤5 YOE" heuristic for non-consulting roles.

## ESSAY ACCURACY corrections (David/Jamie, 2026-05-31) — bake into voice profile + drafts
- ODN Oregon work = ALWAYS collective ("I worked with a team of consultants who partnered with an HR client… we…"). Never "I upskilled the team" (solo).
- Tooling truth: Jamie uses spreadsheets, Excel, SharePoint + data-analysis tools. She has used **Greenhouse (ATS)**. She does NOT build BI dashboards. At InGenius she does NOT build reporting/metrics — it's enrollment data + an existing CRM dashboard she USES.
- For "reporting & metrics" prompts → lead with **NextGen** (2,000+ analysis → scorecards → C-suite reports) — genuine reporting. 
- Strongest "used data to improve a process / change a decision" example = **InGenius onboarding**: interview stakeholders → turn feedback into concrete data → enhance onboarding programs (tighten communications + better-track/organize digital libraries) → streamlined, onboarding time -75%. Use this over weaker examples.
- Company-fit answers must be CONCRETE, not lofty/vague ("build the layer that makes everything trustworthy" = bad). No fabricated personal history (e.g. "spent time around small independent businesses" — Jamie did NOT; removed). If a "why company" reason is weak/fake, drop it and use a single strong genuine reason.
- Lean into Jamie's genuine belief: using DATA + AI tools to improve processes/strategy — strong hook for data/tech-leaning roles.
