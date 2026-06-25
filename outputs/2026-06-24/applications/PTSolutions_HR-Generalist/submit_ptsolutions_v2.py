"""
Submit PT Solutions HR Generalist via iCIMS.
Uses Playwright fresh browser: log into existing iCIMS account, upload resume, fill form, submit.
"""
import asyncio
import json
import sys
from pathlib import Path
from playwright.async_api import async_playwright

ROLE_DIR = Path(__file__).parent
RESUME_PDF = ROLE_DIR / "resume.pdf"
COVER_PDF = ROLE_DIR / "cover_letter.pdf"
SCREENSHOTS_DIR = ROLE_DIR / "screenshots"
SCREENSHOTS_DIR.mkdir(exist_ok=True)

pw_file = Path.home() / "Downloads" / "job_password.txt"
PASSWORD = pw_file.read_text().strip()
EMAIL = "jamiecheng0103@gmail.com"

# This is the direct apply URL (with job ID 17163)
APPLY_URL = "https://careers-ptsolutions.icims.com/jobs/17163/hr-generalist/login?p_lang=en_us&refNum=PSZPSFUS"

async def fill_custom_dropdown(page, frame, selector, search_text, option_text):
    """Fill a custom iCIMS search dropdown (not standard <select>)."""
    el = await frame.query_selector(selector)
    if not el:
        print(f"  Dropdown not found: {selector}")
        return False
    await el.click()
    await page.wait_for_timeout(500)
    # Type in search box
    search_box = await frame.query_selector('input[placeholder="— Type to Search —"], input.select2-search__field')
    if search_box:
        await search_box.fill(search_text)
        await page.wait_for_timeout(600)
    # Click the matching option
    option = await frame.query_selector(f'li:has-text("{option_text}"), .select2-results__option:has-text("{option_text}")')
    if option:
        await option.click()
        await page.wait_for_timeout(400)
        return True
    print(f"  Option '{option_text}' not found after search")
    return False

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=['--start-maximized', '--no-sandbox']
        )
        context = await browser.new_context(viewport={'width': 1280, 'height': 900})
        page = await context.new_page()

        print("Navigating to iCIMS login page...")
        await page.goto(APPLY_URL)
        await page.wait_for_load_state("networkidle")
        await page.screenshot(path=str(SCREENSHOTS_DIR / "s01_login_page.png"))
        print("Screenshot: s01_login_page.png")

        # Look for sign-in with existing account
        # iCIMS email-first flow: enter email, check if account exists
        email_input = await page.query_selector('input[type="email"], input[name*="login"], input[name*="email"], input[placeholder*="email" i]')
        if email_input:
            await email_input.fill(EMAIL)
            print(f"Filled email: {EMAIL}")
        else:
            print("No email input found. Page source snippet:")
            body = await page.evaluate("document.body.innerText")
            print(body[:500])
            await browser.close()
            sys.exit(1)

        # Check/accept privacy policy checkbox
        checkbox = await page.query_selector('input[type="checkbox"]')
        if checkbox:
            is_checked = await checkbox.is_checked()
            if not is_checked:
                await checkbox.check()
            print("Privacy checkbox checked")

        # Click Next button
        next_btn = await page.query_selector('input[value="Next"], button:has-text("Next"), input[type="submit"][value*="Next"]')
        if next_btn:
            await next_btn.click()
        else:
            await page.keyboard.press("Enter")

        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(1000)
        await page.screenshot(path=str(SCREENSHOTS_DIR / "s02_after_email.png"))
        print("Screenshot: s02_after_email.png")

        # Check if we're on candidate profile page or password page
        current_url = page.url
        print(f"URL after email: {current_url[:100]}")

        # Look for iframe
        iframe_el = await page.wait_for_selector('#icims_content_iframe', timeout=10000)
        if not iframe_el:
            print("No iframe found")
            await browser.close()
            sys.exit(1)

        frame = await iframe_el.content_frame()
        if not frame:
            print("Could not access iframe content")
            await browser.close()
            sys.exit(1)

        print(f"Iframe URL: {frame.url[:100]}")

        # Check for sign-in (existing account) vs new account fields
        pw_input = await frame.query_selector('#PersonProfileFields\\.Password')
        sign_in_pw = await frame.query_selector('input[type="password"]')

        page_text = await frame.evaluate("document.body.innerText")

        if "Sign In" in page_text or "password" in page_text.lower():
            print("Account exists - signing in...")
            # Find password field and fill it
            pw_field = await frame.query_selector('input[type="password"]')
            if pw_field:
                await pw_field.fill(PASSWORD)
                print("Password filled")
            # Click Sign In
            sign_in_btn = await frame.query_selector('input[value="Sign In"], button:has-text("Sign In")')
            if sign_in_btn:
                await sign_in_btn.click()
            else:
                await frame.query_selector('input[type="submit"]')
                submit = await frame.query_selector('input[type="submit"]')
                if submit:
                    await submit.click()
            await page.wait_for_load_state("networkidle")
            await page.wait_for_timeout(1500)
            await page.screenshot(path=str(SCREENSHOTS_DIR / "s03_signed_in.png"))
            print("Screenshot: s03_signed_in.png")

            # After sign in, look for the candidate profile/application form
            # Navigate to the application
            apply_btn = await page.query_selector('a:has-text("Apply"), input[value*="Apply"]')
            if apply_btn:
                await apply_btn.click()
                await page.wait_for_load_state("networkidle")
                await page.wait_for_timeout(1000)

            # Re-get the iframe
            iframe_el = await page.query_selector('#icims_content_iframe')
            if iframe_el:
                frame = await iframe_el.content_frame()
        else:
            print("New account - filling registration form...")
            # --- File Upload FIRST ---
            print("Uploading resume...")
            file_input = await frame.query_selector('[id="PortalProfileFields.Resume_File"]')
            if not file_input:
                inputs = await frame.query_selector_all('input[type="file"]')
                print(f"File inputs: {len(inputs)}")
                for inp in inputs:
                    inp_id = await inp.get_attribute('id')
                    print(f"  file input id={inp_id}")
                    file_input = inp  # use first one

            if file_input:
                await file_input.set_input_files(str(RESUME_PDF))
                await page.wait_for_timeout(2000)
                print("Resume uploaded!")
                await page.screenshot(path=str(SCREENSHOTS_DIR / "s03_resume_uploaded.png"))
            else:
                print("WARNING: Could not find file input")

            # Fill login credentials
            login_f = await frame.query_selector('#PersonProfileFields\\.Login')
            if login_f:
                await login_f.fill(EMAIL)

            pw_f = await frame.query_selector('#PersonProfileFields\\.Password')
            if pw_f:
                await pw_f.fill(PASSWORD)

            pw_c = await frame.query_selector('#PersonProfileFields\\.Password_Confirm')
            if pw_c:
                await pw_c.fill(PASSWORD)

            # Name fields
            fn = await frame.query_selector('#PersonProfileFields\\.FirstName')
            if fn:
                await fn.fill("Yi-Chieh")

            pref = await frame.query_selector('#rcf2024')
            if pref:
                await pref.fill("Jamie")

            ln = await frame.query_selector('#PersonProfileFields\\.LastName')
            if ln:
                await ln.fill("Cheng")

            # Phone
            phone = await frame.query_selector('#-1_PersonProfileFields\\.PhoneNumber')
            if phone:
                await phone.fill("+12137003831")

            phone_type = await frame.query_selector('#-1_PersonProfileFields\\.PhoneType')
            if phone_type:
                try:
                    await phone_type.select_option(label="Mobile")
                except:
                    pass

            # Address
            addr = await frame.query_selector('#-1_PersonProfileFields\\.AddressStreet1')
            if addr:
                await addr.fill("1784 NW Northrup St")

            addr_type = await frame.query_selector('#-1_PersonProfileFields\\.AddressType')
            if addr_type:
                try:
                    await addr_type.select_option(label="Home")
                except:
                    pass

            city = await frame.query_selector('#-1_PersonProfileFields\\.AddressCity')
            if city:
                await city.fill("Portland")

            zip_c = await frame.query_selector('#-1_PersonProfileFields\\.AddressZip')
            if zip_c:
                await zip_c.fill("97209")

            # Country - custom dropdown
            country_ok = await fill_custom_dropdown(page, frame, '#-1_PersonProfileFields\\.AddressCountry', "United States", "United States")
            print(f"Country set: {country_ok}")
            await page.wait_for_timeout(500)

            # State - custom dropdown
            state_ok = await fill_custom_dropdown(page, frame, '#-1_PersonProfileFields\\.AddressState', "Oregon", "Oregon")
            print(f"State set: {state_ok}")

            await page.screenshot(path=str(SCREENSHOTS_DIR / "s04_form_filled.png"))
            print("Screenshot: s04_form_filled.png")

            # Click Next
            next_btn = await frame.query_selector('input[value="Next"], button:has-text("Next"), input[type="submit"]')
            if next_btn:
                print("Clicking Next...")
                await next_btn.click()
                await page.wait_for_load_state("networkidle")
                await page.wait_for_timeout(2000)
                await page.screenshot(path=str(SCREENSHOTS_DIR / "s05_step2.png"))
                print("Screenshot: s05_step2.png")
            else:
                print("WARNING: No Next button found")

        # --- Now on Step 2 (Application Questions) ---
        print("\n--- STEP 2: Application Questions ---")
        current_url = page.url
        print(f"URL: {current_url[:100]}")

        # Re-get iframe
        iframe_el2 = await page.query_selector('#icims_content_iframe')
        if iframe_el2:
            frame2 = await iframe_el2.content_frame()
        else:
            frame2 = frame

        if frame2:
            body2 = await frame2.evaluate("document.body.innerText")
            print(f"Step 2 page text (first 500 chars): {body2[:500]}")
            await page.screenshot(path=str(SCREENSHOTS_DIR / "s06_step2_full.png"))

            # Look for sponsorship question
            # iCIMS typically uses radio buttons or dropdowns for yes/no questions
            # Find "sponsor" related elements
            sponsor_elements = await frame2.query_selector_all('[id*="sponsor" i], [name*="sponsor" i], label')
            print(f"Found {len(sponsor_elements)} potential sponsor elements")

            # Answer all Yes/No questions
            # Try to find all radio groups and answer them
            radios = await frame2.query_selector_all('input[type="radio"]')
            print(f"Found {len(radios)} radio inputs")
            for radio in radios:
                radio_id = await radio.get_attribute('id')
                radio_val = await radio.get_attribute('value')
                radio_name = await radio.get_attribute('name')
                label_el = await frame2.query_selector(f'label[for="{radio_id}"]')
                label_text = await label_el.inner_text() if label_el else ""
                print(f"  Radio: name={radio_name} id={radio_id} val={radio_val} label={label_text}")

        print("\nDone. Check screenshots.")
        await page.wait_for_timeout(10000)  # Keep browser open for inspection
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
