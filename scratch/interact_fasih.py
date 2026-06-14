import asyncio
from playwright.async_api import async_playwright
from urllib.parse import unquote

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9223")
        context = browser.contexts[0]
        page = context.pages[0]
        print(f"Connected to page: {page.url}")
        
        # Navigate to allocation page
        # The URL structure for survey allocations is usually:
        # https://fasih-sm.bps.go.id/survey-collection/survey
        # or similar. Let's go to:
        # https://fasih-sm.bps.go.id/survey-collection/survey
        await page.goto("https://fasih-sm.bps.go.id/survey-collection/survey")
        await page.wait_for_timeout(5000)
        
        # Take a screenshot to see where we are
        await page.screenshot(path="scratch/active_page_petugas_selected.png")
        print("Screenshot saved to scratch/active_page_petugas_selected.png")

asyncio.run(run())
