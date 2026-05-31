# Research Angle 5: Playwright + Persistent Chrome Profile
**Date:** 2026-05-27 | **Angle:** Replace Chrome MCP extension with Playwright driving existing Chrome profile

---

## TL;DR (3 sentences)

Playwright's `launch_persistent_context()` with `channel="chrome"` and Jamie's existing `User Data` dir is a viable, buildable alternative to Claude-in-Chrome extension — it inherits all cookies, LinkedIn auth, and Simplify sessions without any re-login. The recommended stack is **Patchright** (Python, actively maintained 2026) over vanilla Playwright, as it patches CDP leaks that Workday and LinkedIn both key on; a cloned copy of the profile dir avoids locking Jamie out of normal Chrome usage. This path bypasses the Chrome MCP extension allowlist problem entirely and is the highest-leverage architectural shift available — estimated 4–6 hours to wire up, with the main risk being LinkedIn's behavioral-analysis detection if run at high volume.

---

## Block 1: Chrome user-data-dir on Windows

### Confirmed location (this machine)
```
C:\Users\chent\AppData\Local\Google\Chrome\User Data\
```

Jamie's authenticated accounts are present in:
- **Profile 4** (`name: "usc.edu"`) — contains `jamiecheng0103@gmail.com` and `jamie.cheng@ingeniusprep.com`
- **Profile 6** (also contains Jamie's emails alongside David's)

**Recommended profile to use:** `Profile 4` — Jamie's dedicated profile with LinkedIn, Simplify, and Gmail already authenticated.

### Safe cloning strategy (CRITICAL — do NOT point at live profile)

Chrome locks its SQLite databases with OS-level locks while running. Pointing Playwright at the live profile while Chrome is open = crash + profile corruption. The safe approach is a **one-time clone**:

```python
import shutil, os, pathlib, time

CHROME_USER_DATA = r"C:\Users\chent\AppData\Local\Google\Chrome\User Data"
JAMIE_PROFILE = "Profile 4"
CLONE_DIR = r"C:\Users\chent\Agentic_Workflows_2026\jamie-autopilot\chrome_profiles\jamie_clone"

def clone_profile_safely(src_profile_dir: str, dest: str) -> str:
    """
    Clone Jamie's Chrome profile into an isolated directory.
    Jamie must have Chrome CLOSED before this runs.
    Returns path to the cloned user-data-dir root.
    """
    src = pathlib.Path(src_profile_dir)
    dst = pathlib.Path(dest)
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True)
    
    # Copy only the Default-equivalent subfolder (rename to "Default")
    # Playwright always reads from "Default" inside user-data-dir
    profile_src = src / JAMIE_PROFILE
    profile_dst = dst / "Default"
    shutil.copytree(str(profile_src), str(profile_dst), dirs_exist_ok=True)
    
    # Copy Local State (needed for cookie decryption key)
    local_state_src = src / "Local State"
    if local_state_src.exists():
        shutil.copy2(str(local_state_src), str(dst / "Local State"))
    
    return str(dst)
```

**IMPORTANT caveat on cookie encryption:** Chrome on Windows encrypts cookies with DPAPI (Data Protection API) tied to the Windows user account (`chent`). When Playwright launches Chrome with `channel="chrome"` on the SAME Windows user account, it will decrypt cookies correctly — the DPAPI key is per-user, not per-Chrome-installation. This is unlike macOS (Keychain) where copying profiles to a different machine breaks cookies. On Windows same-user clones, cookies survive intact.

### Headed vs headless

For stealth: **headed mode only**. Headless Chrome has additional fingerprint signals that Cloudflare, Workday (hosted on Akamai), and LinkedIn all detect. Run with `headless=False`.

```python
context = patchright.chromium.launch_persistent_context(
    user_data_dir=CLONE_DIR,
    channel="chrome",          # use real Chrome binary, not bundled Chromium
    headless=False,            # MUST be False for ATS stealth
    no_viewport=True,          # avoids fixed 1280x720 viewport fingerprint
)
```

---

## Block 2: Playwright + Persistent Profile — Code Pattern

### Recommended library: Patchright (Python)

**Why Patchright over vanilla Playwright:**
- Patches `Runtime.enable` CDP leak (the #1 signal all major anti-bot systems key on)
- Adds `--disable-blink-features=AutomationControlled`, removes `--enable-automation`
- Works with `channel="chrome"` to use real Chrome TLS fingerprint (vs bundled Chromium's distinct TLS)
- Actively maintained: PyPI shows regular 2025–2026 commits
- Drop-in API replacement — same `page.locator()`, `page.fill()`, `page.set_input_files()` calls

**Install:**
```bash
pip install patchright
patchright install chrome   # downloads/links real Chrome
```

### Full persistent context launch:

```python
# playwright_proxy.py — PlaywrightProxy implementing the same interface as ChromeMCPProxy
import asyncio
import pathlib
from typing import Any

from patchright.async_api import async_playwright, BrowserContext, Page


class PlaywrightProxy:
    """
    Drop-in replacement for ChromeMCPProxy.
    Implements the same interface: navigate, screenshot, click, find,
    form_input, get_text, read_page, file_upload, js.
    
    Uses Patchright (patched Playwright) with a persistent Chrome profile
    so Jamie's LinkedIn/Simplify/Gmail sessions are already active.
    """

    def __init__(self, user_data_dir: str):
        self._user_data_dir = user_data_dir
        self._context: BrowserContext | None = None
        self._page: Page | None = None

    async def start(self):
        """Launch Chrome with persistent profile. Call once before running handlers."""
        pw = await async_playwright().__aenter__()
        self._context = await pw.chromium.launch_persistent_context(
            user_data_dir=self._user_data_dir,
            channel="chrome",       # real Chrome binary, not bundled Chromium
            headless=False,         # headed: required for ATS stealth
            no_viewport=True,       # don't inject fixed viewport (detection signal)
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars",
                "--start-maximized",
            ],
            ignore_default_args=["--enable-automation"],
        )
        self._page = self._context.pages[0] if self._context.pages else await self._context.new_page()
        return self

    async def stop(self):
        if self._context:
            await self._context.close()

    # ----------------------------------------------------------------
    # Interface methods matching ChromeMCPProxy contract
    # ----------------------------------------------------------------

    async def navigate(self, url: str) -> None:
        await self._page.goto(url, wait_until="domcontentloaded", timeout=30_000)

    async def screenshot(self, path: str) -> None:
        pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
        await self._page.screenshot(path=path, full_page=False)

    async def click(self, selector_or_coords) -> None:
        if isinstance(selector_or_coords, str):
            await self._page.locator(selector_or_coords).first.click(timeout=10_000)
        elif isinstance(selector_or_coords, (list, tuple)) and len(selector_or_coords) == 2:
            x, y = selector_or_coords
            await self._page.mouse.click(x, y)

    async def find(self, selector: str):
        """Returns selector string if element exists, None otherwise."""
        try:
            loc = self._page.locator(selector).first
            await loc.wait_for(state="attached", timeout=5_000)
            return selector  # return selector so callers can use it
        except Exception:
            return None

    async def form_input(self, selector: str, value: str) -> None:
        loc = self._page.locator(selector).first
        await loc.fill(value, timeout=8_000)

    async def get_text(self) -> str:
        return await self._page.inner_text("body")

    async def read_page(self) -> dict:
        title = await self._page.title()
        url = self._page.url
        text = await self.get_text()
        return {"title": title, "url": url, "text": text[:5000]}

    async def file_upload(self, selector_or_element, path: str) -> None:
        """
        Playwright file upload — uses FileChooser pattern for reliability.
        Falls back to set_input_files() for direct input[type=file] elements.
        """
        try:
            async with self._page.expect_file_chooser(timeout=5_000) as fc_info:
                await self._page.locator(selector_or_element).first.click()
            file_chooser = await fc_info.value
            await file_chooser.set_files(path)
        except Exception:
            # Fallback: direct input file set
            await self._page.locator(selector_or_element).first.set_input_files(path)

    async def js(self, script: str) -> Any:
        return await self._page.evaluate(script)
```

### Async wrapper to make handlers work synchronously (since handlers are sync):

```python
# sync_proxy.py — wraps async PlaywrightProxy for sync handler code
import asyncio
from playwright_proxy import PlaywrightProxy


class SyncPlaywrightProxy:
    """
    Synchronous wrapper around PlaywrightProxy.
    Allows existing sync ATSHandler code to call proxy methods normally.
    """

    def __init__(self, user_data_dir: str):
        self._loop = asyncio.new_event_loop()
        self._async_proxy = PlaywrightProxy(user_data_dir)
        self._loop.run_until_complete(self._async_proxy.start())

    def __del__(self):
        try:
            self._loop.run_until_complete(self._async_proxy.stop())
            self._loop.close()
        except Exception:
            pass

    def navigate(self, url: str) -> None:
        self._loop.run_until_complete(self._async_proxy.navigate(url))

    def screenshot(self, path: str) -> None:
        self._loop.run_until_complete(self._async_proxy.screenshot(path))

    def click(self, selector_or_coords) -> None:
        self._loop.run_until_complete(self._async_proxy.click(selector_or_coords))

    def find(self, selector: str):
        return self._loop.run_until_complete(self._async_proxy.find(selector))

    def form_input(self, selector: str, value: str) -> None:
        self._loop.run_until_complete(self._async_proxy.form_input(selector, value))

    def get_text(self) -> str:
        return self._loop.run_until_complete(self._async_proxy.get_text())

    def read_page(self) -> dict:
        return self._loop.run_until_complete(self._async_proxy.read_page())

    def file_upload(self, selector_or_element, path: str) -> None:
        self._loop.run_until_complete(self._async_proxy.file_upload(selector_or_element, path))

    def js(self, script: str):
        return self._loop.run_until_complete(self._async_proxy.js(script))
```

### Wiring into the existing runner (minimal change):

```python
# In runner.py, replace ChromeMCPProxy with SyncPlaywrightProxy:
from sync_proxy import SyncPlaywrightProxy

JAMIE_PROFILE_CLONE = r"C:\Users\chent\Agentic_Workflows_2026\jamie-autopilot\chrome_profiles\jamie_clone"

chrome = SyncPlaywrightProxy(user_data_dir=JAMIE_PROFILE_CLONE)
result = run_application(role, jamie_data, output_dir, chrome_proxy=chrome)
```

---

## Block 3: ATS-Specific Anti-Bot Considerations

### Workday
- **Detection mechanism:** Workday jobs are hosted on Akamai Bot Manager (not Cloudflare). Akamai v4 uses behavioral signals: mouse entropy, keystroke timing, scroll events, event loop timing.
- **Headed Patchright verdict:** Passes fingerprint/TLS checks. Behavioral analysis (human-like timing) is the remaining risk.
- **Mitigation:** Add random delays between form interactions:
  ```python
  import random, time
  # Between each field fill:
  time.sleep(random.uniform(0.3, 1.2))
  ```
- **Shadow DOM:** Workday uses Shadow DOM in newer builds. Patchright explicitly supports closed Shadow Root interaction via normal locators — this is an advantage over vanilla Playwright.

### LinkedIn Easy Apply
- **Detection mechanism:** ML-based Trust Score. Keys on: `navigator.webdriver`, session consistency (real profile helps enormously), action velocity, message pattern uniformity.
- **Persistent profile advantage:** Using Jamie's real LinkedIn session is the single biggest detection avoidance factor. LinkedIn distinguishes "logged-in trusted session doing occasional apply actions" from "fresh session hammering applications."
- **Safe rate:** Max 5–10 Easy Apply submissions per day. Sessions < 4 hours continuous. Add 1–3 second waits between each modal click.
- **Known risk:** LinkedIn banned HeyReach in March 2026 for cloud-based automation. Browser-local automation (same machine, real profile) has 8% restriction rate vs 31% for cloud platforms.

### Greenhouse / Lever / Ashby
- **Detection mechanism:** Minimal. These ATSes run their own JS, rarely use advanced bot detection. Vanilla Playwright would pass; Patchright is overkill but not harmful.

### iCIMS / ADP
- **Detection mechanism:** Basic. CloudFlare CDN on some iCIMS instances; Patchright's CDP patch handles the standard Cloudflare challenge.

### Aurora (PeopleAdmin)
- **Detection mechanism:** reCAPTCHA v3 on some forms. Persistent profile with Google session helps — v3 uses account-level trust signals. A real logged-in Google session dramatically reduces reCAPTCHA challenge rate.

---

## Block 4: Re-architecting `lib/ats_handlers/` for Playwright

### Code change assessment

The existing handlers require **zero selector changes**. All CSS selectors, JavaScript snippets, and flow logic remain identical. The only change is the proxy implementation.

| Handler method | Chrome MCP call | Playwright equivalent | Change needed? |
|---|---|---|---|
| `chrome.navigate(url)` | `mcp__navigate` | `page.goto(url)` | None (proxy handles) |
| `chrome.screenshot(path)` | `mcp__computer screenshot` | `page.screenshot(path=path)` | None |
| `chrome.click(selector)` | `mcp__computer click` | `page.locator(selector).click()` | None |
| `chrome.find(selector)` | `mcp__find` | `page.locator(selector).wait_for()` | None |
| `chrome.form_input(sel, val)` | `mcp__form_input` | `page.locator(sel).fill(val)` | None |
| `chrome.get_text()` | `mcp__get_page_text` | `page.inner_text("body")` | None |
| `chrome.file_upload(sel, path)` | `mcp__file_upload` | `file_chooser.set_files(path)` | None |
| `chrome.js(script)` | `mcp__javascript_tool` | `page.evaluate(script)` | None |

**The proxy pattern in `runner.py` (ChromeMCPProxy) was designed exactly for this swap.** The 8 handlers never import Chrome MCP directly. They only call `self.chrome.*`. Replacing `ChromeMCPProxy` with `SyncPlaywrightProxy` requires touching exactly ONE file: `runner.py`.

### Conversion cost estimate

| Task | Time |
|---|---|
| Write `PlaywrightProxy` + `SyncPlaywrightProxy` | 1.5 hours |
| Clone Chrome profile + test cookie survival | 30 min |
| Install Patchright, verify `channel="chrome"` launch | 30 min |
| Wire into `runner.py`, smoke-test 1 Greenhouse job | 1 hour |
| Test Workday end-to-end (slowest ATS) | 1 hour |
| Test LinkedIn Easy Apply modal flow | 1 hour |
| **Total** | **~5.5 hours** |

### Maintenance cost going forward
- **Lower than Chrome MCP.** Playwright Python has Microsoft-backed maintenance and explicit semantic versioning. Chrome MCP extension is Claude-specific tooling with no public maintenance guarantee.
- Patchright tracks Playwright releases with ~2-week lag. In 2026 it has maintained parity with Playwright 1.44+.

---

## Block 5: Risks

### Risk 1: Account flagging on LinkedIn (HIGH — manageable)
- **What happens:** LinkedIn's ML Trust Score triggers a restriction ("we noticed unusual activity")
- **Actual rate:** 8% for browser-local automation using real profiles (vs 31% for cloud)
- **Mitigation:** Cap at 5 Easy Apply submissions/day; randomize inter-action delays 1–3s; never run overnight; always use Jamie's real session (not a fresh one)
- **Worst case:** Account temporarily restricted (not permanently banned) for 24–48 hours

### Risk 2: Workday behavioral analysis (MEDIUM)
- **What happens:** Akamai Bot Manager v4 detects robotic form-fill timing
- **Mitigation:** `time.sleep(random.uniform(0.5, 2.0))` between each field; use `page.type()` with `delay=random.randint(50,150)` instead of `fill()` for critical fields
- **Detection rate with headed Patchright:** Low. Headed + real Chrome binary + real user profile = near-human fingerprint. Behavioral timing is the last layer.

### Risk 3: Chrome profile corruption (LOW — solvable by cloning)
- **What happens:** If Chrome and Playwright both try to write to the same profile simultaneously, SQLite WAL corruption
- **Mitigation:** Always clone the profile before Playwright runs. Never point Playwright at the live `User Data` dir. Keep clone fresh with a weekly `shutil.copytree` re-clone.

### Risk 4: Chrome version mismatch (LOW)
- **What happens:** If `patchright install chrome` downloads a different Chrome version than what's on disk, TLS fingerprint may differ slightly
- **Mitigation:** Use `channel="chrome"` to point at the locally installed Chrome (not Patchright's downloaded version). `patchright install` in that case just links; the binary is the one from `C:\Program Files\Google\Chrome`.

### Risk 5: Windows DPAPI cookie decryption (LOW — Windows-specific)
- **What happens:** Chrome on Windows encrypts cookies with DPAPI (per Windows user). If the clone is used on the SAME Windows user account, decryption works. If moved to another machine or user, cookies are garbage.
- **This machine:** David and Jamie are on the same Windows user `chent` — cloning within the same user account is safe.

---

## Block 6: 2026 Stealth Library Comparison

| Library | Language | Last updated | Detection rate (Cloudflare) | Persistent profile | Notes |
|---|---|---|---|---|---|
| **Patchright** | Python + Node | Active 2026 | Low (passes standard CF checks) | YES — native | **Recommended for this use case.** Patches CDP at protocol level. `channel="chrome"` uses real Chrome TLS. |
| **CloakBrowser** | Python + Node | Active May 2026 | Very low (30/30 passed) | YES | C++-level fingerprint patches. More powerful but heavier; overkill for ATS. Can use Patchright as backend. |
| **playwright-extra + stealth** | Node only | Last meaningful update 2023 | HIGH — consistently detected by CF 2024+ | Partial | Stale. Do not use for anything touching Cloudflare or modern ATS. |
| **playwright-stealth (Python)** | Python | v2.0.2, April 2026 | Medium — passes basic checks, fails CF Enterprise | Partial | Better than playwright-extra. "Proof-of-concept" per own docs. Use only if Patchright unavailable. |
| **rebrowser-patches** | Node | Active 2026 | Medium — patches CDP leak but behavioral still detectable | NO | Node-only. Patchright is the Python equivalent and more capable. |
| **Camoufox** | Python | v146.0.1-beta.25, Jan 2026 | Low | Partial | Firefox-based. Experimental beta. Slower (42s/CF challenge). Good for heavy-CF sites but overkill and less tested for ATS forms. |
| **nodriver** | Python | Active 2026 | Very low (benchmark winner) | NO | CDP-direct, no Playwright abstraction. Would require full handler rewrite. Skip for this project. |
| **undetected-chromedriver** | Python | Last meaningful update 2023 | HIGH in 2026 | Partial | Selenium-based. Outdated evasion. Do not use. |

### Verdict: Use Patchright

Patchright hits the sweet spot for this project:
- Drop-in Playwright API (zero handler changes)
- Supports `channel="chrome"` + `launch_persistent_context` (the core of this approach)
- Actively maintained in 2026
- Passes Workday/Akamai standard fingerprint check (the main ATS blocker)
- LinkedIn passes with real session + headed mode
- Lower complexity than CloakBrowser (no compiled binary to manage)

---

## Recommended Stack (specific versions, 2026)

```
patchright>=1.44.0      # Python Playwright fork with CDP patches
# Installation:
pip install patchright
patchright install chrome
```

**Supporting:**
```
# No other stealth library needed — Patchright covers it.
# Optional for behavioral stealth (human-like typing):
# Use page.type(selector, text, delay=random_ms) instead of page.fill()
```

**Python version:** 3.11+ (async_playwright works best on 3.11+)

---

## Code Skeleton: Launch + Drive 1 ATS Form (Workday)

```python
#!/usr/bin/env python3
"""
run_playwright_workday.py — Smoke test: drive one Workday application 
using Patchright + Jamie's cloned Chrome profile.
"""
import asyncio
import random
import time
from patchright.async_api import async_playwright

JAMIE_CLONE_DIR = r"C:\Users\chent\Agentic_Workflows_2026\jamie-autopilot\chrome_profiles\jamie_clone"

# Sample Workday application URL
APPLY_URL = "https://adobe.wd5.myworkdayjobs.com/en-US/external/apply/..."

async def main():
    async with async_playwright() as pw:
        context = await pw.chromium.launch_persistent_context(
            user_data_dir=JAMIE_CLONE_DIR,
            channel="chrome",
            headless=False,
            no_viewport=True,
            args=["--disable-blink-features=AutomationControlled", "--start-maximized"],
            ignore_default_args=["--enable-automation"],
        )
        
        page = context.pages[0] if context.pages else await context.new_page()
        
        # Navigate to Workday apply page
        await page.goto(APPLY_URL, wait_until="domcontentloaded")
        await page.wait_for_timeout(2000 + random.randint(0, 1000))  # human-like pause
        
        # Screenshot: confirm page loaded
        await page.screenshot(path="workday_01_loaded.png")
        
        # Wait for Workday data-automation-id elements
        try:
            await page.wait_for_selector("[data-automation-id]", timeout=10_000)
        except Exception:
            print("Workday elements not found — page may require login or CAPTCHA")
            await page.screenshot(path="workday_error.png")
            await context.close()
            return
        
        # Fill first name (Workday automation ID pattern)
        first_name_sel = "[data-automation-id='legalNameSection_firstName'] input"
        try:
            await page.locator(first_name_sel).fill("Yi-Chieh")
            time.sleep(random.uniform(0.4, 0.9))  # human typing pause
        except Exception as e:
            print(f"First name fill failed: {e}")
        
        # Upload resume via FileChooser
        resume_path = r"C:\Users\chent\Agentic_Workflows_2026\oracle-job-search\outputs\2026-05-25-night\applications\aurora_pmpplteam_2026-05-25\resume.pdf"
        try:
            async with page.expect_file_chooser(timeout=5_000) as fc_info:
                await page.locator("input[type=file]").first.click()
            fc = await fc_info.value
            await fc.set_files(resume_path)
            print("Resume uploaded via FileChooser")
        except Exception:
            # Fallback: direct set_input_files
            await page.locator("input[type=file]").first.set_input_files(resume_path)
            print("Resume uploaded via set_input_files")
        
        await page.screenshot(path="workday_02_resume_uploaded.png")
        
        # Dismiss autofill dialog if present
        try:
            no_thanks = page.locator("button:has-text('No thanks'), button:has-text('Manual Entry')")
            await no_thanks.first.click(timeout=3_000)
        except Exception:
            pass  # No autofill dialog
        
        # Execute JS to check for work auth section
        has_work_auth = await page.evaluate("""
            () => document.body.innerText.toLowerCase().includes('authorized')
        """)
        if has_work_auth:
            print("Work auth section detected — clicking Yes for authorization")
            # Click Yes radio for work authorization
            await page.evaluate("""
                () => {
                    const radios = Array.from(document.querySelectorAll('input[type=radio]'));
                    const yesRadio = radios.find(r => {
                        const label = document.querySelector(`label[for="${r.id}"]`);
                        return label && label.textContent.trim() === 'Yes';
                    });
                    if (yesRadio) yesRadio.click();
                }
            """)
        
        await page.screenshot(path="workday_03_final.png")
        print("Smoke test complete. Check workday_03_final.png")
        
        await context.close()


if __name__ == "__main__":
    asyncio.run(main())
```

---

## Estimated Setup Time

| Step | Time |
|---|---|
| `pip install patchright && patchright install chrome` | 10 min |
| Run `clone_profile_safely()` script, verify cookies survive | 20 min |
| Write `PlaywrightProxy` + `SyncPlaywrightProxy` from skeleton above | 1.5 hr |
| Wire into `runner.py` (change 3 lines) | 15 min |
| Smoke test Greenhouse (easiest ATS) | 30 min |
| Smoke test Workday (hardest ATS) | 1 hr |
| Test LinkedIn Easy Apply | 1 hr |
| **Total** | **~4.5–5.5 hours** |

---

## Should This Replace Chrome MCP Entirely OR Coexist?

**Recommendation: Replace entirely for the jamie-autopilot pipeline. Keep Chrome MCP for ad-hoc research tasks.**

### Why replace:
1. **No extension allowlist.** Chrome MCP is blocked by domain-level extension restrictions on many ATS portals. Playwright has no such constraint — it's driving the browser directly, not injecting extension content scripts.
2. **No "Claude is actively using Chrome" requirement.** Chrome MCP requires an active Claude session with the extension open. Playwright runs as a standalone Python process — it can run overnight, on a schedule, without Claude's attention.
3. **Better error handling.** `try/except` on Playwright calls is deterministic. Chrome MCP tool call failures in Claude context require Claude to retry in an ad-hoc way.
4. **Screenshots are native.** Playwright's `page.screenshot()` saves to disk directly; Chrome MCP screenshots require tool-call round-trips.

### Why keep Chrome MCP for non-pipeline tasks:
- Quick one-off lookups, LinkedIn profile research, Notion/Gmail interactions that are already working well
- Tasks where Claude's judgment is needed in the loop (not just form-filling)

---

## Sources

1. [Patchright GitHub — Kaliiiiiiiiii-Vinyzu/patchright-python](https://github.com/Kaliiiiiiiiii-Vinyzu/patchright-python)
2. [Anti-detect browser benchmark 2026 — Ian L. Paterson (7 tools, 31 Cloudflare targets)](https://ianlpaterson.com/blog/anti-detect-browser-benchmark-patchright-nodriver-curl-cffi/)
3. [Playwright Anti-Bot Detection: What Works (2026) — AlterLab](https://alterlab.io/blog/playwright-bot-detection-what-actually-works-in-2026)
4. [CloakBrowser — Stealth Chromium, 30/30 tests passed (GitHub, active May 2026)](https://github.com/CloakHQ/CloakBrowser)
5. [Is LinkedIn Automation Safe in 2026? 23% Ban Risk — Growleads](https://growleads.io/blog/linkedin-automation-ban-risk-2026-safe-use/)
6. [rebrowser-patches — CDP Runtime.enable leak fix, Cloudflare/DataDome (GitHub, active 2026)](https://github.com/rebrowser/rebrowser-patches)
7. [Using Persistent Context in Playwright — BrowserStack](https://www.browserstack.com/guide/playwright-persistent-context)
8. [How to Scrape with Patchright and Avoid Detection — ZenRows](https://www.zenrows.com/blog/patchright)
9. [Best Playwright Stealth 2026: Tested vs Cloudflare & Akamai — Scrapewise.ai](https://scrapewise.ai/blogs/playwright-stealth-2026)
10. [Camoufox — Anti-detect Firefox browser, v146 beta (GitHub, active 2026)](https://github.com/daijro/camoufox)
11. [Playwright FileChooser API — Official Docs](https://playwright.dev/python/docs/api/class-filechooser)
12. [LinkedIn Automation Safety Guide 2026 — GetSales.io](https://getsales.io/blog/linkedin-automation-safety-guide-2026/)

---

## JSON Summary

```json
{
  "angle": 5,
  "title": "Playwright Persistent Profile (Patchright)",
  "tldr": "Patchright + Jamie's cloned Chrome Profile 4 bypasses Chrome MCP extension restrictions entirely. Near-zero fingerprint changes needed. 4.5-5.5hr setup.",
  "feasibility": "HIGH",
  "recommended_stack": {
    "library": "patchright",
    "version": ">=1.44.0",
    "python": ">=3.11",
    "browser": "channel=chrome (real Chrome, not bundled Chromium)",
    "mode": "headless=False (headed required for ATS stealth)"
  },
  "jamie_chrome_profile": {
    "user_data_dir": "C:\\Users\\chent\\AppData\\Local\\Google\\Chrome\\User Data",
    "jamie_profile": "Profile 4",
    "confirmed_accounts": ["jamiecheng0103@gmail.com", "jamie.cheng@ingeniusprep.com"],
    "clone_to": "C:\\Users\\chent\\Agentic_Workflows_2026\\jamie-autopilot\\chrome_profiles\\jamie_clone"
  },
  "code_change_scope": {
    "files_changed": 1,
    "file": "runner.py (swap ChromeMCPProxy -> SyncPlaywrightProxy)",
    "handler_files_changed": 0,
    "selectors_changed": 0
  },
  "setup_hours": 5,
  "risks": [
    {"risk": "LinkedIn account restriction", "level": "MEDIUM", "rate": "8% for browser-local automation", "mitigation": "5 Easy Apply/day max, 1-3s delays"},
    {"risk": "Workday behavioral detection", "level": "LOW-MEDIUM", "mitigation": "random delays 0.5-2s between fields"},
    {"risk": "Chrome profile corruption", "level": "LOW", "mitigation": "always clone before run, never point at live profile"},
    {"risk": "Cookie encryption mismatch", "level": "LOW", "mitigation": "same Windows user account = DPAPI decrypts correctly"}
  ],
  "replace_chrome_mcp": true,
  "coexist_chrome_mcp": "keep for ad-hoc research, not pipeline",
  "sources_count": 12,
  "all_sources_active_2026": true
}
```
