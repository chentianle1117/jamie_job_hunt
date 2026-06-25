"""
Submit PT Solutions HR Generalist via iCIMS.
Full form fill + resume upload + submit.
"""
import asyncio
import json
import sys
import time
from pathlib import Path
from playwright.async_api import async_playwright, TimeoutError as PwTimeout

ROLE_DIR = Path(__file__).parent
RESUME_PDF = ROLE_DIR / "resume.pdf"
SCREENSHOTS_DIR = ROLE_DIR / "screenshots"
SCREENSHOTS_DIR.mkdir(exist_ok=True)

pw_file = Path.home() / "Downloads" / "job_password.txt"
PASSWORD = pw_file.read_text().strip()
EMAIL = "jamiecheng0103@gmail.com"

APPLY_URL = "https://careers-ptsolutions.icims.com/jobs/17163/hr-generalist/login?p_lang=en_us&refNum=PSZPSFUS"

async def wait_ready(page, timeout=60000):
    """Wait for page to be ready."""
    try:
        await page.wait_for_load_state("domcontentloaded", timeout=timeout)
    except:
        pass
    await page.wait_for_timeout(2000)

async def screenshot(page, name):
    path = str(SCREENSHOTS_DIR / name)
    await page.screenshot(path=path, full_page=False)
    print(f"  Screenshot: {name}")
    return path

async def get_frame(page):
    """Get the iCIMS content iframe."""
    try:
        iframe_el = await page.wait_for_selector('#icims_content_iframe', timeout=15000)
        frame = await iframe_el.content_frame()
        if frame:
            await frame.wait_for_load_state("domcontentloaded", timeout=10000)
        return frame
    except Exception as e:
        print(f"  get_frame error: {e}")
        return None

async def fill_dropdown(page, frame, selector, search_text, option_contains):
    """Fill a custom search dropdown."""
    try:
        el = await frame.query_selector(selector)
        if not el:
            print(f"  Dropdown not found: {selector}")
            return False
        await el.click()
        await page.wait_for_timeout(800)
        # Check for search box
        search = await frame.query_selector('input.select2-search__field, input[placeholder*="Search"]')
        if search:
            await search.fill(search_text)
            await page.wait_for_timeout(600)
        option = await frame.query_selector(f'li.select2-results__option:has-text("{option_contains}")')
        if not option:
            option = await frame.query_selector(f'.select2-results li:has-text("{option_contains}")')
        if option:
            await option.click()
            await page.wait_for_timeout(400)
            return True
        # Try pressing enter
        if search:
            await search.press("Enter")
        return False
    except Exception as e:
        print(f"  fill_dropdown error for {selector}: {e}")
        return False

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu',
                  '--disable-blink-features=AutomationControlled'],
            ignore_default_args=['--enable-automation']
        )
        context = await browser.new_context(
            viewport={'width': 1440, 'height': 900},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
        )
        page = await context.new_page()

        print("=== STEP 1: Login page ===")
        await page.goto(APPLY_URL, wait_until="domcontentloaded", timeout=60000)
        await wait_ready(page)
        title = await page.title()
        print(f"Title: {title}")
        await screenshot(page, "h01_login.png")

        body = await page.evaluate("document.body.innerText")
        print(f"Page text: {body[:200]}")

        # Fill email
        email_sel = await page.query_selector('input[type="email"], input[name*="login" i], input[placeholder*="email" i]')
        if not email_sel:
            # Try to find the iframe first
            frame = await get_frame(page)
            if frame:
                email_sel = await frame.query_selector('input[type="email"], input[name*="login" i]')
                if email_sel:
                    print("Found email input in iframe")
                    await email_sel.fill(EMAIL)
                    # Privacy checkbox in iframe
                    cb = await frame.query_selector('input[type="checkbox"]')
                    if cb:
                        await cb.check()
                    # Next in iframe
                    nb = await frame.query_selector('input[value="Next"], button:has-text("Next")')
                    if nb:
                        await nb.click()
                    await wait_ready(page)
        else:
            await email_sel.fill(EMAIL)
            # Privacy checkbox
            cb = await page.query_selector('input[type="checkbox"]')
            if cb:
                await cb.check()
            # Next button
            nb = await page.query_selector('input[value="Next"], button:has-text("Next")')
            if nb:
                await nb.click()
            elif await page.query_selector('input[type="submit"]'):
                await page.click('input[type="submit"]')
            await wait_ready(page)

        await screenshot(page, "h02_after_email.png")
        print(f"URL: {page.url[:80]}")

        # === Step 2: Candidate Profile form ===
        print("\n=== STEP 2: Candidate Profile ===")
        frame = await get_frame(page)
        if not frame:
            print("Could not get iframe. Checking main page...")
            body = await page.evaluate("document.body.innerText")
            print(f"Main page: {body[:300]}")
            await browser.close()
            sys.exit(1)

        frame_text = await frame.evaluate("document.body.innerText")
        print(f"Frame text: {frame_text[:300]}")

        # Check if existing account (Sign In) or new account
        is_signin = "Sign In" in frame_text and "Password_Confirm" not in frame_text
        print(f"Sign In mode: {is_signin}")

        if is_signin:
            # Sign into existing account
            print("Signing into existing account...")
            pw = await frame.query_selector('input[type="password"]')
            if pw:
                await pw.fill(PASSWORD)
            btn = await frame.query_selector('input[value="Sign In"], input[type="submit"], button[type="submit"]')
            if btn:
                await btn.click()
            await wait_ready(page)
            await screenshot(page, "h03_signed_in.png")
            print(f"URL after sign in: {page.url[:80]}")

            # Now navigate to the actual application
            # May need to click Apply
            apply_link = await page.query_selector('a:has-text("Apply"), input[value*="Apply"]')
            if apply_link:
                print("Clicking Apply link...")
                await apply_link.click()
                await wait_ready(page)
                await screenshot(page, "h04_apply_clicked.png")
        else:
            # New account - fill full form
            print("Filling new account form...")

            # RESUME UPLOAD FIRST
            print("  Uploading resume...")
            file_input = await frame.query_selector('[id="PortalProfileFields.Resume_File"]')
            if not file_input:
                file_inputs = await frame.query_selector_all('input[type="file"]')
                print(f"  Found {len(file_inputs)} file inputs")
                if file_inputs:
                    file_input = file_inputs[0]
            if file_input:
                await file_input.set_input_files(str(RESUME_PDF))
                await page.wait_for_timeout(2000)
                print(f"  Resume set: {RESUME_PDF.name}")
            else:
                print("  WARNING: No file input found")

            # Login / password
            for sel, val in [
                ('#PersonProfileFields\\.Login', EMAIL),
                ('#PersonProfileFields\\.Password', PASSWORD),
                ('#PersonProfileFields\\.Password_Confirm', PASSWORD),
                ('#PersonProfileFields\\.FirstName', 'Yi-Chieh'),
                ('#rcf2024', 'Jamie'),
                ('#PersonProfileFields\\.LastName', 'Cheng'),
                ('#-1_PersonProfileFields\\.PhoneNumber', '+12137003831'),
                ('#-1_PersonProfileFields\\.AddressStreet1', '1784 NW Northrup St'),
                ('#-1_PersonProfileFields\\.AddressCity', 'Portland'),
                ('#-1_PersonProfileFields\\.AddressZip', '97209'),
            ]:
                el = await frame.query_selector(sel)
                if el:
                    await el.fill(val)
                    print(f"  Filled {sel}")

            # Standard select dropdowns
            for sel, label in [
                ('#-1_PersonProfileFields\\.PhoneType', 'Mobile'),
                ('#-1_PersonProfileFields\\.AddressType', 'Home'),
            ]:
                el = await frame.query_selector(sel)
                if el:
                    try:
                        await el.select_option(label=label)
                        print(f"  Selected {sel} = {label}")
                    except Exception as e:
                        print(f"  select_option failed for {sel}: {e}")

            # Custom search dropdowns (Select2/iCIMS custom)
            print("  Setting Country...")
            await fill_dropdown(page, frame, '#-1_PersonProfileFields\\.AddressCountry', 'United States', 'United States')
            await page.wait_for_timeout(500)

            print("  Setting State...")
            await fill_dropdown(page, frame, '#-1_PersonProfileFields\\.AddressState', 'Oregon', 'Oregon')

            await screenshot(page, "h05_form_filled.png")
            print("  Form filled. Clicking Next...")
            btn = await frame.query_selector('input[value="Next"], input[type="submit"][value*="Next"]')
            if not btn:
                btn = await frame.query_selector('input[type="submit"]')
            if btn:
                await btn.click()
                await wait_ready(page)
                await screenshot(page, "h06_step2.png")
                print(f"  URL after Next: {page.url[:80]}")
            else:
                print("  WARNING: No Next button found")
                await screenshot(page, "h06_no_next.png")

        # === Step 3: Application Questions ===
        print("\n=== STEP 3: Application Questions ===")
        frame2 = await get_frame(page)
        if frame2:
            frame2_text = await frame2.evaluate("document.body.innerText")
            print(f"Step 3 text: {frame2_text[:500]}")
            await screenshot(page, "h07_app_questions.png")

            # Find all questions and inputs
            radios = await frame2.query_selector_all('input[type="radio"]')
            selects = await frame2.query_selector_all('select')
            textareas = await frame2.query_selector_all('textarea')
            print(f"  Radios: {len(radios)}, Selects: {len(selects)}, Textareas: {len(textareas)}")

            for radio in radios:
                r_id = await radio.get_attribute('id')
                r_val = await radio.get_attribute('value')
                r_name = await radio.get_attribute('name')
                lbl = await frame2.query_selector(f'label[for="{r_id}"]')
                lbl_text = (await lbl.inner_text()).strip() if lbl else ""
                print(f"    radio: name={r_name} val={r_val} label={lbl_text}")

            for sel in selects:
                s_id = await sel.get_attribute('id')
                s_name = await sel.get_attribute('name')
                options = await sel.query_selector_all('option')
                opt_texts = [await o.inner_text() for o in options]
                print(f"    select: id={s_id} name={s_name} opts={opt_texts[:5]}")

        print("\nScript complete.")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
