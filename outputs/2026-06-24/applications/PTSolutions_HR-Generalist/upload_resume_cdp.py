"""
Upload resume PDF to iCIMS via Playwright CDP connect to existing Chrome at port 9333.
The iCIMS tab is at: https://careers-ptsolutions.icims.com/jobs/17163/hr-generalist/candidate
"""
import asyncio
import sys
from pathlib import Path
from playwright.async_api import async_playwright

ROLE_DIR = Path(__file__).parent
RESUME_PDF = ROLE_DIR / "resume.pdf"
SCREENSHOTS_DIR = ROLE_DIR / "screenshots"
SCREENSHOTS_DIR.mkdir(exist_ok=True)

ICIMS_TAB_URL_FRAGMENT = "careers-ptsolutions.icims.com"

async def run():
    async with async_playwright() as p:
        # Connect to existing Chrome at port 9333
        browser = await p.chromium.connect_over_cdp("http://localhost:9333")

        print(f"Connected. Contexts: {len(browser.contexts)}")

        page = None
        for context in browser.contexts:
            for pg in context.pages:
                print(f"  Page: {pg.url[:80]}")
                if ICIMS_TAB_URL_FRAGMENT in pg.url:
                    page = pg
                    print(f"  ** Found iCIMS page!")
                    break
            if page:
                break

        if not page:
            print("ERROR: Could not find iCIMS tab in port 9333")
            sys.exit(1)

        print(f"Working with page: {page.url[:100]}")

        # Take screenshot of current state
        await page.screenshot(path=str(SCREENSHOTS_DIR / "upload_before.png"), full_page=False)
        print("Screenshot taken: upload_before.png")

        # Get the iframe
        frames = page.frames
        print(f"Frames ({len(frames)}):")
        for f in frames:
            print(f"  Frame: {f.name} | {f.url[:80]}")

        # Find the icims_content_iframe frame
        icims_frame = None
        for f in frames:
            if 'icims' in f.url.lower() or f.name == 'icims_content_iframe':
                icims_frame = f
                print(f"  ** Found iCIMS frame: {f.name} | {f.url[:80]}")
                break

        if not icims_frame:
            # Try getting it via element handle
            iframe_el = await page.query_selector('#icims_content_iframe')
            if iframe_el:
                icims_frame = await iframe_el.content_frame()
                print(f"Got frame via element: {icims_frame.url[:80] if icims_frame else 'None'}")

        if not icims_frame:
            print("ERROR: Could not find iCIMS iframe")
            sys.exit(1)

        # Try set_input_files on the resume file input
        print(f"Looking for file input in frame...")
        file_input = await icims_frame.query_selector('#PortalProfileFields\\.Resume_File')

        if not file_input:
            # Try without escaping
            file_input = await icims_frame.query_selector('[id="PortalProfileFields.Resume_File"]')

        if not file_input:
            print("ERROR: Could not find file input element")
            # List all inputs in the frame
            inputs = await icims_frame.query_selector_all('input[type="file"]')
            print(f"  File inputs found: {len(inputs)}")
            for inp in inputs:
                inp_id = await inp.get_attribute('id')
                inp_name = await inp.get_attribute('name')
                print(f"    id={inp_id} name={inp_name}")
            sys.exit(1)

        print(f"File input found! Setting file: {RESUME_PDF}")
        await file_input.set_input_files(str(RESUME_PDF))
        print("File set successfully!")

        # Wait for upload to process
        await page.wait_for_timeout(2000)

        # Screenshot after upload
        await page.screenshot(path=str(SCREENSHOTS_DIR / "upload_after.png"), full_page=False)
        print("Screenshot taken: upload_after.png")

        # Check if filename shows up somewhere in the page
        body_text = await page.evaluate('document.body.innerText')
        if 'resume' in body_text.lower() or '.pdf' in body_text.lower():
            print("SUCCESS: PDF filename visible in page text")

        print("Done!")
        # Don't close the browser - leave it open for the human to see


if __name__ == "__main__":
    asyncio.run(run())
