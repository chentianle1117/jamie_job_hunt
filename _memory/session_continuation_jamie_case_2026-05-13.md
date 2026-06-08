---
name: Session continuation — Jamie FMLA case Drive reorganization
description: Resume the Jamie case work after restarting Claude Code to pick up new drive:full MCP permissions
type: session-handoff
created: 2026-05-13
originSessionId: 7275d610-ad8c-48e9-ad55-d5d52c6a0d9d
---

# Session handoff — Jamie FMLA case (2026-05-13)

## What changed in this session
1. Comprehensively researched Jamie's FMLA retaliation case across both Gmail accounts and her Drive folder
2. Wrote two vault files:
   - `W:\SecondBrain\Career\Planning\Jamie FMLA H-1B Case — Status & Strategy.md` (updated)
   - `W:\SecondBrain\Career\Planning\Jamie FMLA H-1B Case — Evidence Brief for Stember Cohn.md` (new, comprehensive evidence brief with verbatim quotes)
3. Drafted email replies to both lawyers (Jon Cohn + Colleen Ramage) — see Status & Strategy file for content
4. Read Colleen Ramage's engagement letter at `C:\Users\chent\Downloads\Review and Sign.pdf` — confirmed $600/hr, $1,200 retainer, arbitration clause, 30-day invoice challenge window
5. **Changed `~/.claude.json` workspace-mcp `drive:readonly` → `drive:full`** to enable Drive write tools

## Why a restart is needed
The workspace-mcp permissions config (`drive:full`) takes effect on MCP server start. Jamie's OAuth token in `C:/Users/chent/.google_workspace_mcp/credentials/jamiecheng0103@gmail.com.json` was issued with `drive.readonly` scope and must be re-issued.

## Re-auth steps after restart

In the new Claude Code session, run:

1. **Kill the persistent workspace-mcp process on port 8765:**
   ```powershell
   netstat -ano | findstr ":8765"
   # Note the PID, then:
   Stop-Process -Id <PID> -Force
   ```

2. **Immediately call `mcp__workspace-mcp__start_google_auth`:**
   - `service_name="drive"`
   - `user_google_email="jamiecheng0103@gmail.com"`

3. **Click the auth link in Claude's response, sign in as Jamie, approve permissions** (the consent screen will now show Drive write scopes — accept them all).

4. **Verify by listing the folder again:**
   - `mcp__workspace-mcp__list_drive_items` with `folder_id="1-oV24KZ752lVSDHdXMoQFx02G7_RBbkl"` and `user_google_email="jamiecheng0103@gmail.com"`

5. **Test write access by creating a temporary folder.** If the `create_file` tool with `contentMimeType="application/vnd.google-apps.folder"` is available in workspace-mcp now, it should succeed.

## Continuation prompt for next Claude Code session

Paste this into the new session after restart:

```
Resume the Jamie FMLA case work. Context: I just restarted Claude Code after updating the workspace-mcp config from drive:readonly to drive:full. Jamie's OAuth token needs to be re-issued with Drive write scopes.

Steps to do, in order:
1. Re-auth jamiecheng0103@gmail.com for workspace-mcp with the new drive:full scopes (kill PID 8765, call start_google_auth(service_name="drive", user_google_email="jamiecheng0103@gmail.com"), I'll click the link)
2. Verify Drive write tools are now available in workspace-mcp
3. Read W:\SecondBrain\Career\Planning\Jamie FMLA H-1B Case — Evidence Brief for Stember Cohn.md for full case context
4. Read C:\Users\chent\.claude\projects\C--Users-chent-Agentic-Workflows-2026\memory\session_continuation_jamie_case_2026-05-13.md for handoff details
5. Reorganize Jamie's Drive folder per the plan below
6. Update the glossary Google Doc
7. Help me finalize and send two parallel emails: one to Jon Cohn (jcohn@stembercohn.com, priority) and one to Colleen Ramage (cramage@ramagelykos.law, parallel preview-and-evaluate request)

Drive folder IDs:
- Parent folder: 1-oV24KZ752lVSDHdXMoQFx02G7_RBbkl
- Child folder with 14 PDFs: 1oCQfvQ23aDn61W1uWo_Jgqvtk8RVfY4h
- Glossary Google Doc: 17fGwenPlPrut_KEpH_l2tJ3JvOowOAjVLVkuPgXTGlI
```

## Drive reorganization plan (already approved in this session)

Inside the child folder `1oCQfvQ23aDn61W1uWo_Jgqvtk8RVfY4h`, create 5 subfolders:
- `01 — Employment Contracts`
- `02 — Promotion & Role Transition (Dec 2025 – Jan 2026)`
- `03 — FMLA Approval & Reduced Schedule (Jan – Feb 2026)`
- `04 — Role Elimination & Retaliation (Mar – May 2026)`
- `05 — Resume`

Then **copy** each existing PDF into the right subfolder with a properly-formatted name, then update the glossary doc, then **prompt David to manually delete the 14 originals at the top level** (the MCP has no delete tool).

### File mapping (existing name → new name → target subfolder)

**01 — Employment Contracts:**
- `Sept 2023—Yi-Chieh Cheng (Jamie) BD Specialist Contract_Signed by JC (1) (1).pdf` (ID `1HDIfLoQDRqKM9lTphj078-J-mXl5Wj7A`) → `2023-09-05 — BD Specialist Contract (original employment) — signed by Jamie & Lia Heflin.pdf`
- `June 2024—Offer Letter - Jamie (Yi-Chieh)Cheng.pdf` (ID `1xVcnNKLTE0uN1jnvJB8-L29LA5Y3kPli`) → `2024-06-12 — School Adjustment Counselor offer letter — Brian Flynn.pdf`
- `Oct 12, 2024—Jamie Cheng Contract Addendum_signed.pdf` (ID `1EImQD3UXmIC2D-3k-LU1wwtPvHBzThFy`) → `2024-09-30 — Contract Addendum (H-1B payment restructuring) — signed.pdf`
- `Jan 2026—New Contract Addendum_Program Manager 2026 pdf.pdf` (ID `1XAKfIESegYo1sx-5T8ILXw_secyHeC6-`) → `2026-01-20 — Contract Addendum (Program Enablement Manager promotion, effective Jan 26) — signed.pdf`

**02 — Promotion & Role Transition (Dec 2025 – Jan 2026):**
- `Dec 11, 2025—InGenius Prep Mail - Inside Sales Position.pdf` (ID `1SDjwx2P2xEFvW3WwhYd04K-Y0J_Pb09w`) → `2025-12-11 — Email — Inside Sales Position offer (Rosenbaum → Jamie, names Joel Butterly as interviewer).pdf`
- `Jan 26th, 2026—InGenius Prep Mail - Contract Addendum (Effective Jan 26th, 2026)_ Test Prep, Tutoring and Competition Prep.pdf` (ID `1yCBDsWOVOJ795F805box_JzTs6C0KUWD`) → `2026-01-06 to 01-21 — Email thread — Contract addendum negotiation (Brian Flynn ↔ Jamie, title updated in Rippling Jan 21).pdf`
- `Jan 21, 2026—InGenius Prep Mail - Role Transition Training.pdf` (ID `1qbELaGG61A3MGkxoizcRt8ISV4JAG0xI`) → `2026-01-21 — Calendar invite — Jamie-Tingting-Erin transition training (organized by Erin Gu).pdf`

**03 — FMLA Approval & Reduced Schedule (Jan – Feb 2026):**
- `2026-01-29 Yi-Chieh Cheng FMLA WH-380 form.pdf` (ID `1BkNgXndpbWogU61yDj5aAOTTWGxdVlun`) → `2026-01-29 — WH-380-E (Physician certification of serious health condition).pdf`
- `Jan 2026—InGenius Prep Mail - Medical Leave _ PTO.pdf` (ID `1aDaUJBuKVSfnHUpfr7i1veMzsF59fAuU`) → `2026-01-23 to 02-10 — Email thread — Medical leave-PTO-FMLA approval (Brian Flynn promises full-time reinstatement on June 6).pdf`
- `WH-381 FMLA Eligibility Form_Jamie Cheng.pdf` (ID `1hY_49k639MmRjNAFAg3OtzcyOlcszhbw`) → `2026-02-10 — WH-381 (Employer eligibility notice).pdf`

**04 — Role Elimination & Retaliation (Mar – May 2026):**
- `Mar 2026—InGenius Prep Mail - Update from Erin.pdf` (ID `1x5rxY4vARxLPs-xG1laHJFdOtPrralpJ`) → `2026-03-16 — Email — Update from Erin (first 'never transitioned into' framing, sent while Jamie on FMLA).pdf`
- `May 1, 2026—InGenius Prep Mail - Change to Tutoring _ Test Prep Management.pdf` (ID `11zXN9-n249EcBcirPJIPZzPY93pR0HAw`) → `2026-05-01 — Email — Company-wide announcement (Camille Li takes Jamie's role scope while Jamie on FMLA).pdf`
- `May 5 2026—InGenius Prep Mail - Following-up + Career counseling ideas attached.pdf` (ID `1K7nno3sxCbFjAQLIwMK1y7zCiugDyiK5`) → `2026-05-05 — Email — Erin elimination email (cites Jamie's health accommodation, tells her to look elsewhere) + Jamie's Apr 30 contemporaneous summary.pdf`

**05 — Resume:**
- `Jamie (Yi-Chieh) Cheng's Resume_2026.pdf` (ID `1-lqGu-rX1tNTeOy2RZV4hUls4YC-xmC-`) → `Jamie Yi-Chieh Cheng — Resume — 2026.pdf`

## Two email replies pending send (already drafted, in Status & Strategy file)

**To Jon Cohn (`jcohn@stembercohn.com`, cc `tschaeffer@stembercohn.com`)**:
Reply to thread `19e1e4d5bf52f8f4`. Subject: `Re: your case`. Priority send. Includes Drive link to the (newly reorganized) folder. Already drafted — see vault file.

**To Colleen Ramage (`cramage@ramagelykos.law`)**:
New email (don't reply to Adobe Sign notification). Subject: `Re: Hourly engagement letter - Cheng — request to preview materials before signing`. Parallel send. Includes Drive link and 4 specific questions (case merit, outcome range, hours estimate, paid limited-scope option). Discloses parallel diligence with another firm. Already drafted — see vault file.

## Other context

- `__test_folder_DELETE_ME` (ID `1kEBXCSkt3wJyBZAmLHMw7-oLqzanYsef`) was created in David's Drive root as part of debugging the 91b04cfe MCP authentication. David can delete it manually.
- The token refresh task `WorkspaceMCPTokenRefresh` runs every 50 min and will keep all accounts' tokens fresh once they're authorized.
- All 6 accounts in `C:\Users\chent\.google_workspace_mcp\credentials\` currently have `drive.readonly` scope. Only Jamie's account needs re-auth for the immediate case work; the other accounts can be re-authorized later as needed.
