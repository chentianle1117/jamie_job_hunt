# Feed-First Run — Submissions Log (2026-06-12)

## ✅ SUBMITTED
| # | Company | Role | ATS | Result | Notes |
|---|---------|------|-----|--------|-------|
| 1 | MaintainX | Educational Program Manager | Greenhouse (no acct) | ✅ Confirmation page | Genuine STRONG fit via mined InGenius BD/partnership experience ($316K B2B partnerships, 15+ ed programs, sales enablement). Fact-check PASS, PDFs visually verified. Location field = fixed hub list → "Other" (remote). Sponsorship=Yes, WorkAuth=Yes (truthful). |
| 2 | **PeaceHealth** | **HR Consultant** (req 128515, cand 275601) | **Infor CloudSuite (account)** | ✅ **"Application Submitted — Thank you for applying" (screenshot-verified)** | **Confirmed H-1B sponsor (40 LCAs).** Drove the FULL 11-section Infor wizard end-to-end: account created → Contact → Employment (parsed 5 real jobs; deleted stray parse-row; corrected ODN 'CEO/HR'→true title per RULE 0) → Education → Credentials → Attachments (resume + cover) → Profile Questions (sponsorship=Yes truthful, current/former-employee=No) → Job Specific Questions (3yr=Yes, shared-svc HR=Yes, **administer leave/benefits=No** honest, ER support=Yes, salary $85-100K) → Self-ID (Asian/Female/no-disability/non-veteran, truthful) → Finalize (I-Agree + signature; SoHo ack needed scrolling the content panel) → **Submit**. Every section visually verified. Resume + cover letter both attached. |
| 3 | **Lightfox Games** | **People & Operations Coordinator** | **Custom form (lightfoxgames.com via Google Cloud Function)** | ✅ **"Application received!" on-page banner + confirmation email (screenshot-verified)** | LinkedIn "Apply" → redirects to custom careers form (NOT Easy Apply). Fields: name, email, LinkedIn URL, resume.pdf upload, hybrid-ack checkbox. **Cloudflare Turnstile auto-solved in the authenticated real Chrome session (port 9222 CDP-attach)** — no human needed. Submit POST → HTTP 200. No sponsorship/YOE/salary question (disclosed via package). 3yr ✓, $80-95K, Seattle hybrid. RULE-0 fact-checked, PDFs visually verified. |

## ❌ INELIGIBLE (form/JD pre-scan killed before build)
| Company | Role | Killer |
|---------|------|--------|
| Pacific Office Automation | L&D Specialist | Posting 404 (dead) + 0 H-1B filings ever |
| Applied Intuition | PM People Operations | 5+ YOE required (Jamie ~3) |
| Anduril | Talent Enablement PM | "U.S. Person" ITAR block + 5+ YOE |
| DraftKings | PM Talent Management | 5+ YOE required |
| Valley Medical Center | Talent & OD Partner | No sponsorship (form-gate) + 5 YOE — prior run |

## ❌ INELIGIBLE (continued — batch 2 pre-scan)
| Company | Role | Killer |
|---------|------|--------|
| Sonos | People Programs Coordinator | Explicit "unable to sponsor" |
| Seattle Public Utilities | Workforce Development Advisor | Gov role — citizenship/residency |

## 🧩 CAPTCHA-GATED → HUMAN-SUBMIT lane (FILLED up to captcha; human just solves captcha + clicks Submit)
| Company | Role | Status | Apply URL |
|---------|------|--------|-----------|
| **PeaceHealth** | HR Consultant (req 128515) — **ACCOUNT CREATED (cand 275601); 6/11 wizard sections DONE** | ✅ Signed in. ApplicationTasks wizard driven + visually verified: **Welcome ✓ · Contact Information ✓** (phone+email) **· Employment ✓** (Infor parsed all 5 real jobs; deleted stray 'Consultant?' parse-row; corrected ODN 'CEO/HR'→true 'Consultant, Organization & Talent Development' per RULE 0) **· Education ✓** (USC MS + Wesleyan BA, accurate) **· Credentials ✓** (empty/optional) **· Attachments ✓** (resume.pdf + Cover Letter both attached). REMAINING (live window port 9344, David can finish): Profile Questions, **Job Specific Questions (answer sponsorship=Yes truthfully — PeaceHealth IS a sponsor)**, Self-Identification (Woman/Asian truthful), Finalize, Submit. <br>— Earlier captcha staging detail: | — name Yi-Chieh Cheng, email jamiecheng0103@gmail.com, shared password ×2, **resume.pdf uploaded** — visually verified (`ph_81_filled.png`). David types the captcha + Submit there → account created → application continues. **Confirmed H-1B sponsor (40 LCAs).** Flow cracked: JD `/apply?tm_src=0` → `css-peacehealth-prd.inforcloudsuite.com/hcm/Jobs/...JobPostingDisplay` → `#...ApplyButtonLabel` → Infor SSO `/sso/SSOServlet` → **Register** → `Candidate.SelfRegistrationForm`. Reliable handoff = launch dedicated Chrome w/ `--remote-debugging-port`, drive via CDP, `browser.close()` detaches connection (window stays live). NEVER hold persistent-context with sleep() — that froze the tab. | https://careers.peacehealth.org/jobs/17583716-hr-consultant |
| OHSU | HR Business Partner (req 39450) | Package READY (resume+cover fact-checked + visually verified, 1-page). LIVE posting confirmed; **no explicit no-sponsor → GO**; 3+yr ✓; cap-exempt. iCIMS account entry is **reCAPTCHA-protected** at the email step → fill up to captcha + leave open (re-drive with the fill-to-captcha pattern). PDFs staged. | https://externalcareers-ohsu.icims.com/jobs/39450/hr-business-partner/job |

## ⏭️ GO — package ready / partway, still to drive (no explicit no-sponsor)
| Company | Role | Mechanism | Status |
|---------|------|-----------|--------|
| PeaceHealth | HR Consultant (req 128515) | Infor Cloud Suite, careers.peacehealth.org | **Package READY (fact-checked + visually verified).** ✅ Confirmed H-1B SPONSOR (40 LCAs FY2025), 3yr ✓, $79-119K, Vancouver WA (4-day on-site hybrid). No explicit no-sponsor, **no captcha / no account gate seen** on JD apply page — Infor portal entry is one click deeper (JS/new-tab) that the probe didn't follow. Best remaining GO; resume PDF staged. |
| ICHS | Workforce Development Administrator | ADP Workforce Now | DROP — posting no longer live (filled/expired). |
| Applied Intuition / DraftKings | (5yr stretch) | Greenhouse / Workday | YOE stretch per loosened bar; lower priority than 3yr fits. |

## 🔑 KEY MECHANISM LEARNING (this run)
- **Clean auto-apply ATS** = Greenhouse (no-account quick-apply) → MaintainX SUBMITTED in one drive.
- **Captcha-gated account ATS** = iCIMS (OHSU) → reCAPTCHA at the email/account step → HUMAN-SUBMIT lane (never bypass).
- **Account/healthcare ATS** (Infor/Workday/iGreentree) = multi-step, often captcha or account-gated; package-ready + screenshot-staged, finish manually.
- The reliable autopilot win is the **no-account Greenhouse/Lever/Ashby pool** — prioritize discovering MORE of those (like MaintainX) over grinding captcha-gated account ATSes.

| 4 | **Ripple** | **Program Manager, DEI** (GH job 7951682) | **Greenhouse (no-acct embed via ripple.com)** | ✅ **"Thank you for applying. Your application has been received." (page-verified)** | Greenhouse form embedded in ripple.com via lazy-loaded iframe (Application tab → `job-boards.greenhouse.io/embed/job_app?for=ripple`). Patchright `launch_persistent_context` (not CDP attach) solved cross-origin frame access. All fields: Yi-Chieh Cheng / jamiecheng0103@gmail.com / +12137003831 / NY. Preferred=Jamie. LinkedIn=https://www.linkedin.com/in/jamieyccheng/. Auth=Yes, **Sponsorship=Yes (truthful)**, PrevRipple=No. Resume.pdf attached. Demographics: Woman/Asian/No/non-veteran/no-disability. Confirmed H-1B sponsor. New York NY, $116-130K, 4+YOE ✓ strong fit. |

## 🧩 HUMAN-FINISH lane (account + everything filled; human does the final step)
| Company | Role | Status | What the human does |
|---------|------|--------|---------------------|
| **OHSU** | HR Business Partner (req 39450, iCIMS) | **STAGED at hCaptcha (live tab port 9403).** Account/email step, full Candidate Profile filled + resume.pdf + cover_letter.pdf uploaded; leaked Drive links in Vestas/NextGen description fields CLEANED + verified. | Open the live Chrome tab → scroll to bottom → solve hCaptcha → click **Submit Profile**. (Also: clean the Drive links from Jamie's *saved* iCIMS profile so they stop auto-filling — spawned task.) |
| **BCG** | Talent Senior Specialist - People (Phenom ATS) | **BLOCKED on automation, account CREATED + all fields filled** (incl. Sponsorship=Yes, EEO). The "Available Start Date" React date-picker is automation-resistant (19 attempts; commits a past 2025 date, fails validation). NOT a fit/eligibility problem. | Log into `experiencedtalent.bcg.com` (jamiecheng0103@gmail.com) → open the in-progress application → set Available Start Date to a 2026 date → **Submit**. Everything else is done. |

## 📊 Run tally (this overnight run)
- **SUBMITTED live: 4** — MaintainX, PeaceHealth, Lightfox, Ripple (all confirmation-page/banner verified).
- **Human-finish staged: 2** — OHSU (solve hCaptcha + Submit), BCG (set start-date + Submit).
- **Ineligible (hard-stop, correctly skipped): 9+** — incl. Customer.io (no-sponsor), Axon (hard 4-day onsite), Sonos/Anduril/Applied Intuition/DraftKings/Seattle PU/Valley Medical/Pacific Office/ICHS/Xenium(clerical)/Trend(no mechanism).
- Pre-scan doctrine prevented ~7 wasted account-builds. Greenhouse/custom no-account embed pool = reliable autopilot wins.

## 🔑 NEW MECHANISM LEARNINGS (this batch)
- **Lightfox** = LinkedIn "Apply" → custom careers form w/ Cloudflare Turnstile that **auto-solves in an authenticated real Chrome session** (CDP-attach 9222); submit POST → 200. No human needed.
- **Ripple** = ripple.com embeds Greenhouse via a lazy-loaded iframe revealed by the Application tab; **`launch_persistent_context` beats CDP-attach** for cross-origin frame access. (Reusable for other site-embedded Greenhouse forms.)
- **BCG = Phenom ATS** (not Workday). Account-create works; the React date-picker is automation-resistant → human-finish lane.
- **iCIMS stored-profile autofill leaks `workSampleUrl` Drive links** into description fields → must clean per-field at staging (and clean the saved profile to stop recurrence).
