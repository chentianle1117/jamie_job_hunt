"""
Submit PT Solutions HR Generalist via iCIMS.
Uses Playwright - try different launch options.
"""
import asyncio
import sys
from pathlib import Path
from playwright.async_api import async_playwright

ROLE_DIR = Path(__file__).parent
RESUME_PDF = ROLE_DIR / "resume.pdf"
SCREENSHOTS_DIR = ROLE_DIR / "screenshots"
SCREENSHOTS_DIR.mkdir(exist_ok=True)

pw_file = Path.home() / "Downloads" / "job_password.txt"
PASSWORD = pw_file.read_text().strip()
EMAIL = "jamiecheng0103@gmail.com"

APPLY_URL = "https://careers-ptsolutions.icims.com/jobs/17163/hr-generalist/login?p_lang=en_us&refNum=PSZPSFUS"

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu']
        )
        context = await browser.new_context(viewport={'width': 1280, 'height': 900})
        page = await context.new_page()

        print("Navigating to iCIMS login...")
        await page.goto(APPLY_URL)
        await page.wait_for_load_state("networkidle")

        title = await page.title()
        print(f"Page title: {title}")
        await page.screenshot(path=str(SCREENSHOTS_DIR / "h01_login.png"))
        print("Screenshot: h01_login.png")

        # Find email input
        email_input = await page.query_selector('input[type="email"], input[name*="login"], input[placeholder*="email" i]')
        if email_input:
            await email_input.fill(EMAIL)
            print(f"Filled email")
        else:
            body = await page.evaluate("document.body.innerText")
            print(f"No email input found. Page: {body[:300]}")

        # Privacy checkbox
        checkbox = await page.query_selector('input[type="checkbox"]')
        if checkbox:
            await checkbox.check()

        # Click Next
        next_btn = await page.query_selector('input[value="Next"], button:has-text("Next")')
        if next_btn:
            await next_btn.click()
        else:
            await page.keyboard.press("Enter")

        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(1000)
        await page.screenshot(path=str(SCREENSHOTS_DIR / "h02_after_email.png"))
        print(f"After email URL: {page.url[:80]}")

        # Get iframe
        try:
            iframe_el = await page.wait_for_selector('#icims_content_iframe', timeout=10000)
            frame = await iframe_el.content_frame()
            print(f"Iframe URL: {frame.url[:80]}")

            page_text = await frame.evaluate("document.body.innerText")
            print(f"Iframe text (first 400): {page_text[:400]}")
        except Exception as e:
            print(f"Error getting iframe: {e}")
            body = await page.evaluate("document.body.innerText")
            print(f"Main page text: {body[:400]}")

        print("Done.")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
