# ☀️ Morning Report — autonomous run (2026-06-16 → 06-17, "run2")

> **TL;DR:** **3 applications truly submitted** this run, **2 of them Portland-local** (your #1 priority) —
> all three independently verified against the live confirmation page, not just an agent's word.
> The big lesson this run: **LinkedIn (your authed feed) is where the live, fitting roles actually are** —
> every single job from the board-API/WebSearch lists was already dead. Outreach drafts + a reusable
> template are ready for your 5 strongest threads. One role is staged at an account wall; one was blocked
> by a Workday-wide outage.

---

## ✅ SUBMITTED THIS RUN (3) — confirmation verified, nothing for you to do

| Company | Role | Location | Why it's a real fit | ATS | Proof |
|---|---|---|---|---|---|
| **Pacific Office Automation** | Learning & Development Specialist | **Beaverton, OR (Portland-local!)** | Reports to Director of L&D and OD; LMS admin + facilitation + curriculum — your exact lane. Only **11 applicants**. $60-80K. | ClearCompany | "Thank you for applying." page captured |
| **Gaylord Industries (ITW)** | Human Resources Generalist | **Tualatin, OR (Portland metro!)** | Full-cycle HR generalist, 1-4yr ask = at-level. ITW is a Fortune-200 H-1B sponsor. $75-85K. | ITW SmartRecruiters | "Yi-Chieh, you have successfully applied for: HR Generalist, Tualatin OR" — live page verified |
| **Legence** | Talent Development Generalist | Remote (US) | Onboarding programs, engagement, performance, career pathing, succession, Predictive Index — Org-Psych/OD bullseye. Blackstone-backed (sponsor-plausible). | Dayforce HCM | "Congratulations, your application has been submitted. Confirmation number **R24ICmwF**" — live page verified |

**Verification note (important, for your trust):** the submission agent initially wrote "submitted" for two of
these *without* capturing the confirmation screen, AND wrote "submitted" for two roles that actually were NOT
submitted. I re-checked **every one against the live browser** before counting it. The 3 above are real
(I read the live confirmation page text myself). The two false alarms are corrected below. This is the
verify-against-reality gate doing its job — same as the Exelon false-positive caught earlier.

---

## 🟡 STAGED / BLOCKED — your hands needed (package built + tailored + ready)

| Company | Role | Location | What's left | Why it didn't auto-submit |
|---|---|---|---|---|
| **Neighborhood House** | HR Generalist | **Portland, OR (nonprofit)** | Sign in to ADP, complete the **email-OTP identity verification**, finish the short form, Submit. | ADP account/OTP wall — the agent got stuck on "Tell us about yourself" identity step. Strong cap-exempt-angle fit. |
| **Stride, Inc.** | HR Operations Specialist | Remote (US) | Retry when Workday is back: `stride.wd1.myworkdayjobs.com/.../JR115213` | **Workday had a platform-wide outage** during the run (all tenants → maintenance page). Not a site/account issue. Posted *that day* — fresh. |

Both folders contain the tailored resume.pdf + cover_letter.pdf, visually verified.

---

## ❌ NOT submitted (honest)
- **Clarion Events — HR Coordinator** (remote): posting closed, and you'd **already applied** to it yourself. Skipped.
- All **9 roles from the board-API + WebSearch discovery lists** (Cobalt, MissionWired, Khan Academy, Pair Team,
  Waymark, Ennoble Care, Altarum, Automatiq, Nava, etc.): **every one was dead (404 on the ATS API)**. They were
  surfaced by Google indexing of *closed* postings — Greenhouse silently redirects a closed job to the board
  index, which looks "live" to a naive check. The submit agents caught this and refused to fabricate. **Net: zero
  bad-fit or dead-link submissions forced.**

---

## 🔑 THE LESSON THAT CHANGES THE PIPELINE: LinkedIn-first, verify-live-via-API

This run proved two things mechanically:
1. **Board-API / WebSearch discovery is mostly stale.** Indexed Greenhouse/Lever/Ashby job IDs are frequently
   already closed; the only reliable liveness check is the ATS *public API* (200 vs 404), which I now run before
   building anything.
2. **Your LinkedIn authed feed is the real live source.** All 3 submits + both staged came from LinkedIn search
   (Portland + remote, past-week filter). LinkedIn shows *currently open* postings the board APIs miss. The
   Portland-local wins (Pacific Office, Gaylord) only surfaced via LinkedIn.

→ Going forward the pipeline leads with **LinkedIn search → confirm-live → build → submit**, board APIs secondary.

---

## ✉️ OUTREACH — drafts + reusable template ready (you asked for this)

Files in `outputs/2026-06-16-run2/outreach/`:
- **`OUTREACH_TEMPLATE.md`** — reusable fill-in template: (a) hiring-manager/team email, (b) alumni/warm-connection
  email, (c) 3 LinkedIn connection-note variants (<300 chars). In your voice; sponsorship handled gracefully (never leads).
- **`drafts.md`** — 5 personalized drafts for your warmest threads (the roles you submitted last cycle):
  ElevenLabs · CLEAR · Tekmetric · A-LIGN · HealthCorps.
- **`WORTH_IT_RANKING.md`** — where to spend your limited time.

**→ Recommended top-2 to actually send: ElevenLabs first, then CLEAR.** (ElevenLabs = small AI-native team where
your RAG-tool anecdote is a genuine differentiator; CLEAR = your data-side-of-L&D proof maps exactly.)
**Before sending any:** verify the recipient's *current* employer on LinkedIn (standing rule — contacts move).

---

## 📋 YOUR QUEUE (priority order)
1. **Neighborhood House** — Portland nonprofit, ~3 min: finish the ADP OTP + Submit (package ready).
2. **Stride** — when Workday's back up, retry (package ready, posted fresh).
3. **Send 2 outreach** — ElevenLabs + CLEAR (verify recipient's current employer first).
4. **Still pending from before:** UW L&D (Workday — was closing 6/17, may now be closed — check),
   Goalbook hCaptcha (1-click), the account-walled set from last run, and **confirm the Kronos resume
   numbers** + **rotate the shared ATS password** (in git history).

## 🔧 Pipeline changes shipped this run
- LinkedIn-first + verify-live-via-ATS-API doctrine (above).
- Exelon false-positive `SUBMITTED.json` corrected → `NOT_SUBMITTED_false_positive.json`.
- Master-Auditor + live-DOM cross-check caught 3 SUBMITTED.json false positives total this run; 2 reversed to
  genuinely-submitted via the live tab (agent submitted but failed to screenshot — added a "capture the success
  page" reminder), 1 (NH) correctly downgraded to staged.

## FINAL TALLY (run2, 06-16 → 06-17)
- **3 submitted** (live-verified): Pacific Office Automation (Portland), Gaylord/ITW (Portland metro), Legence (remote).
- **2 staged/blocked, package-ready:** Neighborhood House (ADP OTP), Stride (Workday outage).
- **10 verified-live LinkedIn finds** harvested; 6 driven, the rest in `RUN_RESULTS.json` / discovery JSON for next pass.
- **Outreach kit** (template + 5 drafts + ranking) delivered.
- **Model routing:** all sub-agents Sonnet, orchestrator + auditor Opus — held the line, ~13% weekly budget used.
