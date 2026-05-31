# Chrome MCP Permission Model — Deep Research
Date: 2026-05-27

---

## The Honest Answer (TL;DR — what David needs to do tonight)

**The reason `navigate` works while `screenshot`/`click`/`type` are blocked is a fundamental architectural split: `navigate` uses Chrome's `chrome.tabs` API (a lightweight, always-available browser API), while `screenshot`, `click`, `type`, and `javascript_tool` ALL require `chrome.debugger.attach()` — a privileged CDP session that hits a separate domain-level permission gate and is currently broken by a regression bug in extension v1.0.66+.**

**The most useful immediate action**: Check what version of Claude in Chrome is installed (`chrome://extensions` → find Claude). If it's v1.0.66 or later, you're hitting a known Anthropic regression bug — the approval popup that would let you whitelist domains never renders. The fix is NOT in your settings; it requires Anthropic to ship a patched extension version.

**David's hypothesis** ("opening a URL manually first warms up the domain") is PARTIALLY correct in theory (the intended flow requires it), but is BLOCKED by the current regression. Even if you manually visit a domain, the popup that was supposed to fire on first MCP contact never renders, so the domain never gets added to the internal allowlist.

---

## Mechanism Explained

### Two completely different code paths

Claude in Chrome uses two distinct browser API stacks depending on what action you're asking for:

| Action type | Browser API used | Permission gate |
|---|---|---|
| `navigate` | `chrome.tabs.update()` / `chrome.tabs.create()` | Low-friction — same as any extension that can open tabs; Chrome's "site access" setting at the `chrome://extensions` level |
| `read_page`, `find`, `form_input`, `get_page_text` | Chrome Accessibility Tree (content scripts) | Same low-friction path |
| `screenshot`, `left_click`, `right_click`, `type`, `scroll`, `key`, `javascript_tool` | `chrome.debugger.attach()` → Chrome DevTools Protocol (CDP) | High-friction — requires BOTH Chrome's extension "site access" AND Claude's internal domain allowlist |

**Source confirming the split**: GitHub issue #29790 ("screenshot, left_click, and javascript_tool fail with 'Cannot access a chrome-extension:// URL' on Anthropic websites") explicitly states:

> "Failing tools (CDP/debugger-dependent): screenshot, left_click, right_click, double_click, key, scroll, javascript_tool  
> Working tools (accessibility-tree-based): read_page, find, form_input, navigate, get_page_text"

### Why `chrome.debugger` hits a separate wall

When the extension calls `chrome.debugger.attach(tabId)`, Chrome:
1. Checks the extension's declared host permissions (the `chrome://extensions` "Site access" setting)
2. Shows a yellow "Extension is debugging this browser" banner
3. Checks Claude's INTERNAL domain allowlist (stored in extension local storage, populated only via the approval popup UI)

**Both gates must pass for CDP-based actions to work.** `navigate` only needs gate #1.

### The regression bug (v1.0.66 through v1.0.70+)

Starting with extension v1.0.66, a bug was introduced in the `PermissionManager` that causes:

1. MCP-initiated `navigate` or any action on a new domain triggers a `permission_required` response
2. The approval popup ("Always allow actions on this site") is supposed to render in the extension side panel
3. Due to the bug, `chrome.debugger.attach()` fires in a retry loop without tracking in-flight attempts
4. Chrome rejects subsequent attach attempts with "Another debugger is already attached"
5. These rejections are caught and re-surfaced to MCP callers as `permission_required`
6. The popup NEVER renders → user can never add a domain to the internal allowlist
7. All subsequent CDP-dependent tool calls fail

**Critical**: This regression affects ALL versions from v1.0.66 onward. Setting Chrome to "On all sites" at the extension level (gate #1) does NOT fix it because gate #2 (the internal allowlist) is never getting populated.

Sources: GitHub issues #53630, #56965, #50606, #61611, #55706

---

## The 3 Specific Questions Answered

### Q1: Does opening a URL manually unblock MCP actions on that domain?

**In theory: YES. In practice right now: NO (blocked by regression).**

The intended flow documented by Anthropic works like this:
1. User (or MCP) visits a new domain
2. First MCP action on that domain triggers approval popup in extension side panel
3. User clicks "Always allow actions on this site"
4. Domain is written to extension's internal allowlist
5. All subsequent MCP actions (including CDP-based ones: screenshot, click, type) succeed

David's hypothesis is directionally correct: the intended design DOES require a domain to be visited + approved before CDP actions work. But the regression means the approval popup never fires, so step 3 never happens.

**IF Anthropic fixes the regression**: manually navigating to a domain first would NOT be enough — you would still need to either (a) trigger the first MCP action against that domain while watching for the popup, OR (b) have the popup appear automatically and click "Always allow."

**The "warm up" hypothesis is hypothesis only until the bug is fixed.** After a fix ships, the correct procedure would be: navigate to domain manually → run one MCP action → approval popup renders → click "Always allow" → done.

### Q2: Is there a "grant this domain" UI button in the extension popup/settings?

**No. There is no manual add-domain button. This is itself a documented bug.**

The Permissions settings page (`options.html#permissions`) shows "Your approved sites" as a list but has NO input field, no "Add site" button, and no way to manually add a domain. GitHub issue #21723 documents this as an explicit missing feature request.

The ONLY path to add a domain to the allowlist is:
1. Extension side panel popup → appears when MCP first hits an unapproved domain → click "Always allow on this site"

Since the popup never renders (regression), there is literally no working path to populate the allowlist today.

**What David might see in the settings:**
- Extension icon → three dots → Settings → Permissions → "Your approved sites" 
- Listed domains: empty or showing only previously-approved ones
- No "Add" button

**"Grant all sites" mode:**
- `chrome://extensions` → Claude → "Site access" → "On all sites" sets gate #1 to open
- This is NOT sufficient because gate #2 (internal allowlist) is still empty
- Users in the bug reports confirmed "On all sites" was enabled and tools STILL failed

### Q3: Can Chrome extension settings at chrome://extensions override the MCP block?

**Partially. It removes ONE of the two gates, but not the one causing the current block.**

Setting "Site access: On all sites" at `chrome://extensions`:
- Removes the host-permission check (gate #1)
- Does NOT affect Claude's internal domain allowlist (gate #2)
- Tools that only need gate #1 (navigate, read_page, find) work fine with this set
- Tools that need BOTH gates (screenshot, click, type, javascript_tool) still fail because gate #2 is empty

**Bottom line**: Setting "On all sites" in Chrome extension settings is necessary but NOT sufficient. It is already the correct setting. The blocking issue is the internal allowlist that can't be populated due to the regression.

---

## Live Test David Can Run in 5 Minutes

This test will tell you exactly where the block is and confirm whether a fix has shipped.

**Step 1: Check extension version**
1. Go to `chrome://extensions`
2. Find "Claude" extension
3. Look at version number
4. If v1.0.66 or later: you're in regression territory (skip to Step 5 for the nuclear option)

**Step 2: Confirm gate #1 is open**
1. `chrome://extensions` → Claude → "Site access" → must show "On all sites"
2. If it shows "On click" or "On specific sites" → change to "On all sites"

**Step 3: Check current approved sites list**
1. Click Claude extension icon in toolbar
2. Three dots (top right of side panel) → Settings → Permissions
3. Under "Your approved sites" — note what's listed (probably empty or missing the target domain)

**Step 4: Test if popup fires (the regression test)**
1. Open a new blank tab
2. Navigate manually to a target ATS domain (e.g., `workday.com`)
3. Leave that tab focused with Claude side panel open
4. In Claude Code terminal, run:
   ```
   mcp__Claude_in_Chrome__navigate --url "https://workday.com"
   ```
5. Watch the Claude side panel for 10 seconds
   - If a popup asking "Always allow actions on this site?" appears → regression is FIXED, click it
   - If nothing appears and you get `permission_required` → regression still active

**Step 5: If Step 4 shows popup never fires — nuclear option (may work)**
1. Fully quit Chrome (File → Exit, or kill all Chrome processes)
2. Find and delete Claude extension local storage:
   - Windows: `%LOCALAPPDATA%\Google\Chrome\User Data\Default\Local Extension Settings\` 
   - Find the folder for Claude extension ID: `fcoeoabgfenejglbffodgkkbkcdhcgfn`
   - Delete the contents (this resets the internal state including any cached permission denials)
3. Restart Chrome
4. Re-pair the extension via `/chrome` in Claude Code
5. Retry Step 4

**Step 6: Confirm a CDP action works after allowlist is populated**
After successfully seeing and clicking the "Always allow" popup:
```
mcp__Claude_in_Chrome__computer --action screenshot
```
If this returns an image, the domain is fully unblocked for all actions.

**Expected success indicator**: screenshot returns a base64 image of the current tab.
**Failure mode**: still returns "Permission denied for this action on this domain" → regression not yet fixed.

---

## What if None of This Works

If the regression is not fixed by Anthropic, here are fallback approaches for job application automation:

### Option A: Playwright/Puppeteer via Claude Code CLI
Claude Code can run `playwright` or `puppeteer` scripts directly — no Chrome extension needed, no MCP permission model. This is the most reliable path for ATS automation today.
```bash
npx playwright chromium --headed
```
Provide Claude with a Playwright script template and let it fill in the ATS-specific selectors.

### Option B: Switch to `browser-use` Python library
Open-source browser automation library (`browser-use/browser-use` on GitHub) that uses Playwright + its own permission model, bypasses Claude's Chrome extension entirely. Works with the Claude API.

### Option C: Use Claude Code with `--dangerously-skip-permissions` in a sandboxed session
Only in a VM or isolated browser profile — this bypasses all Claude permission prompts but also removes safety guards.

### Option D: Read-only data extraction now, manual submit later
Since `read_page`, `find`, `get_page_text`, and `navigate` work fine (they use accessibility tree, not CDP), Claude can:
- Navigate to ATS
- Read all form fields and their selectors
- Generate a structured JSON of "what to fill where"
- David or Jamie manually submits with that JSON as a guide

This is the fastest practical workaround tonight.

### Option E: Wait for extension patch
Watch for v1.0.71+ in the Chrome Web Store. The root cause is identified (PermissionManager / debugger.attach race condition). Once patched, the full flow should work with no user-side changes needed.

---

## Sources

1. [Claude in Chrome Permissions Guide — Anthropic Help Center](https://support.claude.com/en/articles/12902446-claude-in-chrome-permissions-guide)
2. [Use Claude Code with Chrome (beta) — Official Docs](https://code.claude.com/docs/en/chrome) — confirms "Site-level permissions are inherited from the Chrome extension. Manage permissions in the Chrome extension settings to control which sites Claude can browse, click, and type on."
3. [GitHub Issue #29790: screenshot, left_click, and javascript_tool fail with "Cannot access a chrome-extension:// URL"](https://github.com/anthropics/claude-code/issues/29790) — **PRIMARY SOURCE** confirming navigate/accessibility tools vs CDP/debugger tool split
4. [GitHub Issue #53630: permission_required for all MCP navigations, approval popup never renders (v1.0.69)](https://github.com/anthropics/claude-code/issues/53630) — root cause: PermissionManager retry loop + chrome.debugger.attach race condition
5. [GitHub Issue #56965: permission_required regression continues in v1.0.70](https://github.com/anthropics/claude-code/issues/56965) — confirms navigate blocked + all downstream CDP tools unusable; list of 10 failed workarounds
6. [GitHub Issue #50606: "Navigation to this domain is not allowed" for ALL domains (v1.0.66+ regression)](https://github.com/anthropics/claude-code/issues/50606) — confirms block is upstream of extension's site-access layer, in MCP wrapper
7. [GitHub Issue #55706: permission errors on every domain, persists through reinstall](https://github.com/anthropics/claude-code/issues/55706) — hypothesis about server-side cached permission state
8. [GitHub Issue #58464: MCP navigate blocks domains in "Your approved sites"](https://github.com/anthropics/claude-code/issues/58464) — confirms approved-sites list and MCP guard use different sources of truth
9. [GitHub Issue #21723: options.html#permissions page lacks UI to grant site permissions](https://github.com/anthropics/claude-code/issues/21723) — confirms no manual "Add site" button exists
10. [GitHub Issue #37971: Chrome MCP read-only tools execute without permission prompt](https://github.com/anthropics/claude-code/issues/37971) — confirms two-tier model: write ops (navigate) DO trigger prompts; read-only tools do NOT
11. [GitHub Issue #43172: MCP tool permissions require session focus in Desktop app](https://github.com/anthropics/claude-code/issues/43172) — focus/visibility as secondary factor
12. [GitHub Issue #61611: All Claude in Chrome MCP page-content tools blocked — permission_required / Navigation not allowed, approval UI never renders](https://github.com/anthropics/claude-code/issues/61611) — most recent report (May 2026), confirms regression continues
13. [How Claude in Chrome Works — Medium](https://medium.com/@buttercanbentley/how-claude-in-chrome-works-45b86b06f689) — confirms all operations depend on debugger permission; accessibility tree used first before screenshots
14. [Using Claude in Chrome safely — Anthropic Help Center](https://support.claude.com/en/articles/12902428-using-claude-in-chrome-safely) — per-domain permission requirement: "each domain requires separate permission"
