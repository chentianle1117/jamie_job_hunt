"""
Submit PT Solutions HR Generalist application via iCIMS.
Uses Playwright to handle the file upload in the iframe.
"""
import asyncio
import json
import os
import time
from pathlib import Path
from playwright.async_api import async_playwright

ROLE_DIR = Path(__file__).parent
RESUME_PDF = ROLE_DIR / "resume.pdf"
COVER_PDF = ROLE_DIR / "cover_letter.pdf"
SCREENSHOTS_DIR = ROLE_DIR / "screenshots"
SCREENSHOTS_DIR.mkdir(exist_ok=True)

# Read password
pw_file = Path.home() / "Downloads" / "job_password.txt"
PASSWORD = pw_file.read_text().strip()

EMAIL = "jamiecheng0103@gmail.com"

# The iCIMS URL - we already navigated to this and have the candidate page open
ICIMS_URL = "https://careers-ptsolutions.icims.com/jobs/17163/hr-generalist/candidate"

async def run():
    async with async_playwright() as p:
        # Launch fresh browser (not CDP attach)
        browser = await p.chromium.launch(headless=False, args=['--start-maximized'])
        page = await browser.new_page()

        # Go to the iCIMS login page
        login_url = ("https://careers-ptsolutions.icims.com/jobs/17163/hr-generalist/login"
                     "?p_lang=en_us&refNum=PSZPSFUS"
                     "&mobile=false&width=1268&height=500&bga=true&needsRedirect=false")
        await page.goto(login_url)
        await page.wait_for_load_state("networkidle")

        # Fill email
        email_input = await page.wait_for_selector('input[type="email"]', timeout=10000)
        await email_input.fill(EMAIL)

        # Check privacy checkbox
        checkbox = await page.query_selector('input[type="checkbox"]')
        if checkbox:
            await checkbox.check()

        # Click Next
        next_btn = await page.query_selector('button:has-text("Next"), input[value="Next"]')
        if next_btn:
            await next_btn.click()
        else:
            # Try finding Next button by text
            await page.click('text=Next')

        await page.wait_for_load_state("networkidle")
        await page.screenshot(path=str(SCREENSHOTS_DIR / "01_login_email.png"))

        # Now on candidate profile page
        # Find the iframe
        iframe_el = await page.wait_for_selector('#icims_content_iframe', timeout=10000)
        frame = await iframe_el.content_frame()

        if not frame:
            print("Could not access iframe")
            await browser.close()
            return

        # Upload resume
        file_input = await frame.wait_for_selector('#PortalProfileFields\\.Resume_File', timeout=5000)
        await file_input.set_input_files(str(RESUME_PDF))
        print(f"Resume uploaded: {RESUME_PDF.name}")
        await page.wait_for_timeout(2000)
        await page.screenshot(path=str(SCREENSHOTS_DIR / "02_resume_uploaded.png"))

        # Fill login credentials
        login_input = await frame.query_selector('#PersonProfileFields\\.Login')
        if login_input:
            await login_input.fill(EMAIL)

        pw_input = await frame.query_selector('#PersonProfileFields\\.Password')
        if pw_input:
            await pw_input.fill(PASSWORD)

        pw_confirm = await frame.query_selector('#PersonProfileFields\\.Password_Confirm')
        if pw_confirm:
            await pw_confirm.fill(PASSWORD)

        # Fill name fields
        first_name = await frame.query_selector('#PersonProfileFields\\.FirstName')
        if first_name:
            await first_name.fill("Yi-Chieh")

        # Preferred first name
        pref_name = await frame.query_selector('#rcf2024')
        if pref_name:
            await pref_name.fill("Jamie")

        last_name = await frame.query_selector('#PersonProfileFields\\.LastName')
        if last_name:
            await last_name.fill("Cheng")

        # Phone
        phone = await frame.query_selector('#-1_PersonProfileFields\\.PhoneNumber')
        if phone:
            await phone.fill("2137003831")

        phone_type = await frame.query_selector('#-1_PersonProfileFields\\.PhoneType')
        if phone_type:
            await phone_type.select_option(label="Mobile")

        # Address
        addr = await frame.query_selector('#-1_PersonProfileFields\\.AddressStreet1')
        if addr:
            await addr.fill("1784 NW Northrup St")

        addr_type = await frame.query_selector('#-1_PersonProfileFields\\.AddressType')
        if addr_type:
            await addr_type.select_option(label="Home")

        city = await frame.query_selector('#-1_PersonProfileFields\\.AddressCity')
        if city:
            await city.fill("Portland")

        zip_code = await frame.query_selector('#-1_PersonProfileFields\\.AddressZip')
        if zip_code:
            await zip_code.fill("97209")

        # Country - click and select US
        country = await frame.query_selector('#-1_PersonProfileFields\\.AddressCountry')
        if country:
            await country.click()
            await page.wait_for_timeout(500)
            # Look for United States option
            us_option = await frame.query_selector('li:has-text("United States")')
            if us_option:
                await us_option.click()
                await page.wait_for_timeout(1000)

        # State
        state = await frame.query_selector('#-1_PersonProfileFields\\.AddressState')
        if state:
            await state.click()
            await page.wait_for_timeout(500)
            search_box = await frame.query_selector('input[placeholder="— Type to Search —"]')
            if search_box:
                await search_box.fill("Oregon")
                await page.wait_for_timeout(500)
            oregon_opt = await frame.query_selector('li:has-text("Oregon")')
            if oregon_opt:
                await oregon_opt.click()
                await page.wait_for_timeout(500)

        await page.screenshot(path=str(SCREENSHOTS_DIR / "03_profile_filled.png"))
        print("Profile filled")

        # Find and click Next/Submit button
        next_btn = await frame.query_selector('input[type="submit"], button[type="submit"], input[value="Next"]')
        if next_btn:
            print(f"Clicking Next button")
            await next_btn.click()
            await page.wait_for_load_state("networkidle")
            await page.screenshot(path=str(SCREENSHOTS_DIR / "04_after_next.png"))

        print("Done! Check screenshots for status.")
        await page.wait_for_timeout(5000)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
