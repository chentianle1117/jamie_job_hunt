# Feed-First Run — Submissions Log (2026-06-12)

## ✅ SUBMITTED
| # | Company | Role | ATS | Result | Notes |
|---|---------|------|-----|--------|-------|
| 1 | MaintainX | Educational Program Manager | Greenhouse (no acct) | ✅ Confirmation page | Genuine STRONG fit via mined InGenius BD/partnership experience ($316K B2B partnerships, 15+ ed programs, sales enablement). Fact-check PASS, PDFs visually verified. Location field = fixed hub list → "Other" (remote). Sponsorship=Yes, WorkAuth=Yes (truthful). |

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
| **PeaceHealth** | HR Consultant (req 128515) | ✅ **Infor registration FILLED to captcha in a RESPONSIVE detached Chrome window (port 9344)** — name Yi-Chieh Cheng, email jamiecheng0103@gmail.com, shared password ×2, **resume.pdf uploaded** — visually verified (`ph_81_filled.png`). David types the captcha + Submit there → account created → application continues. **Confirmed H-1B sponsor (40 LCAs).** Flow cracked: JD `/apply?tm_src=0` → `css-peacehealth-prd.inforcloudsuite.com/hcm/Jobs/...JobPostingDisplay` → `#...ApplyButtonLabel` → Infor SSO `/sso/SSOServlet` → **Register** → `Candidate.SelfRegistrationForm`. Reliable handoff = launch dedicated Chrome w/ `--remote-debugging-port`, drive via CDP, `browser.close()` detaches connection (window stays live). NEVER hold persistent-context with sleep() — that froze the tab. | https://careers.peacehealth.org/jobs/17583716-hr-consultant |
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

## 📊 Run tally so far
- **10 roles pre-scanned · 1 clean auto-apply SUBMITTED (MaintainX) · 7 ineligible (5+YOE / ITAR / no-sponsor / gov — killed pre-build) · 3 caution/account-gated**
- Pre-scan doctrine prevented ~6 wasted account-builds. The single eligible role got a genuine strong-fit package built on mined real BD/partnership experience.
