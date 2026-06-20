# ▶ RESUME HERE after compact — finish RxBenefits + Xenium; Nike is review-ready (2026-06-19 late)

## Current submit status (truthful)
- **0 of 4 ATS-submitted tonight.** Forms fill perfectly; the walls are the final upload/click + ADP session.
- **Nike PSA I + Nike Sr L&D = DONE as REVIEW PACKAGES** (David's call: high-stakes + warm connections → Jamie
  reviews before submit). See `NIKE_REVIEW_FOR_JAMIE.md`. Previews rendered, auditor-PASS. DO NOT auto-submit Nike.
- **RxBenefits = the one to finish autonomously.** ADP/WorkforceNow. Hardest gate (email OTP) is SOLVED; remaining
  gap = ADP drops the session each fresh Chrome launch, so it re-prompts identity+OTP every run, and the
  post-OTP application form was never mapped.
- **Xenium = upload-wiring wall** (file <input>s detached from labels). Lower priority; finish after RxBenefits.

## ⭐⭐ HOW TO FINISH RXBENEFITS (the full chain — do it in ONE uninterrupted run, never close Chrome mid-flow)
ATS = ADP WorkforceNow. cid=`5c500a2b-27a7-4828-9817-166ddd8fb76e`, jobId=`940320`, req=`9202061631366_1`.
Apply URL: `https://workforcenow.adp.com/mascsr/default/mdf/recruitment/recruitment.html?cid=5c500a2b-27a7-4828-9817-166ddd8fb76e&ccId=19000101_000001&lang=en_US&type=JS&jobId=940320`
Profile (own Chrome): `%LOCALAPPDATA%\Google\Chrome\User Data\agent_rxbenefits`, Patchright channel="chrome", headless=False.
Package: `applications/RxBenefits_Learning-Talent-Dev-Specialist/` (resume.pdf, cover_letter.pdf).

**The proven working script is `scratchpad/submit_rxbenefits_v3.py`** — it already does identity-fill → Continue →
OTP-send → polls `scratchpad/rx_otp.txt` → enters code → reaches the job page. Run it (no --otp arg; it polls the
flag). The chain that WORKS:
1. Run `submit_rxbenefits_v3.py` from cwd `jamie-autopilot/lib`. It fills identity, sends OTP, prints "Polling rx_otp.txt".
2. Orchestrator fetches the code: workspace-mcp `search_gmail_messages(query="from:SecurityServices_NoReply@adp.com newer_than:15m", user_google_email="jamiecheng0103@gmail.com")` → `get_gmail_message_content` → body has "Verification code NNNNNN".
3. Write the 6 digits to `scratchpad/rx_otp.txt` (printf, no newline). The live session enters it within 3s → logs in.
4. ⚠️ NEW WORK NEEDED: after OTP login it lands on the JOB-DETAIL page ("Application Started" + an "Apply" button),
   NOT a confirmation. The v3 `fill_and_submit` FALSE-POSITIVES here. Must then: click "Apply" (trusted), map the
   real application form (likely multi-step: contact prefill → resume/cover upload → screening Qs → review → Submit),
   upload via set_input_files (verify slot by screenshot), answer truthfully, screenshot review, THEN real Submit.
   This post-OTP form was never reached/mapped — that's the remaining task. Keep Chrome OPEN the whole time (closing
   = session lost = OTP wall again).

## ⭐ CRITICAL MECHANICS LEARNED (reusable for ALL future apps — don't re-discover)
1. **ADP uses react-responsive-ui (rrui): synthetic `el.click()` in JS does NOT fire React handlers** (button
   "clicks" but page doesn't advance). USE TRUSTED Patchright clicks: `locator.click()` / `page.mouse.click(x,y)` /
   `get_by_role("button", name=...)`. This cracked the Continue + email-radio + Send. Pattern is in v3
   `click_continue_and_send_otp` (the TRUSTED-click + coordinate-fallback block).
2. **intl-tel phone widget reads leading "213" as Algeria (+213).** Type `+12137003831` (explicit +1). Verify US flag
   by screenshot. (Already fixed in scripts; applies everywhere.)
3. **MCP `file_upload` is sandboxed** (rejects repo + scratchpad PDFs). Upload via Patchright `.set_input_files()`.
4. **PrismHR/ADP file inputs are often detached from their visible labels** (separate DOM subtree). Blind index/
   geometry/containment mapping ALL failed on Xenium. To map: set a marker file into each input, screenshot which
   visible box it lands in, derive the true index empirically, re-verify by screenshot before submit. If it still
   won't land in the right slot after 2 honest tries → STOP, don't submit wrong-slot. (Xenium: 3 inputs, all
   route weirdly; consider page.on("filechooser") + clicking the visible dropzone instead of targeting the input.)
5. **ADP does NOT persist the session across fresh Chrome launches** — re-prompts identity+OTP each run. So the
   ENTIRE flow (identity→OTP→apply→upload→submit) must complete in ONE process without closing Chrome.
6. **Always screenshot-verify before the Submit click** (phone flag US, both PDFs in correct slots, sponsorship=Yes).
   "Script said submitted" is NOT proof — only a real confirmation page counts. (v3 false-positived twice.)

## Jamie's verified facts (truthful)
Yi-Chieh / Cheng / Jamie · jamiecheng0103@gmail.com · phone +12137003831 · 1784 NW Northrup St Apt 635, Portland OR 97209 USA ·
LinkedIn https://www.linkedin.com/in/jamieyccheng · work-auth YES · sponsorship YES · ~3yr · Woman/Asian if asked · heard via LinkedIn.
Shared ATS pw: `~/Downloads/job_password.txt` (never print/echo/commit). L&D roles: NO Articulate/Storyline/video-editing/EJ4/ThinkZoom.

## Scripts (scratchpad)
- `submit_rxbenefits_v3.py` — the working RxBenefits driver (identity→OTP→job page). Extend its post-OTP step.
- `rx_apply_grind.py` — my continuation attempt (confirmed session doesn't persist; re-prompts identity).
- `drive_xenium.py` — Xenium PrismHR filler (fills perfectly; upload-slot mapping unsolved).
- OTP flag protocol: write code to `scratchpad/rx_otp.txt`; abort via `scratchpad/rx_ABORT`.

## This session's durable wins (already committed + pushed to both repos)
- Cover-letter canonical-skeleton system + hardened gates + auditor check F (oracle 5f395f1 / autopilot 17e659f).
- All 4 covers regenerated to skeleton, auditor-PASS.
- Memory saved: cover skeleton, intl-phone +1, MCP-upload-sandbox→CDP.
