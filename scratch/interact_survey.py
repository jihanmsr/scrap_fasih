import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9223")
        context = browser.contexts[0]
        page = context.pages[0]
        print(f"Connected to page: {page.url}")
        
        # Click the link "SENSUS EKONOMI 2026"
        # We need to target the text specifically, ensuring it doesn't click SENSUS EKONOMI 2026 - UB
        # Let's locate the row containing "SENSUS EKONOMI 2026" and click its link.
        await page.click("text=SENSUS EKONOMI 2026")
        await page.wait_for_timeout(5000)
        
        print(f"New URL: {page.url}")
        await page.screenshot(path="scratch/active_page_after_survey_click.png")

asyncio.run(run())
