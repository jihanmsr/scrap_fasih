import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9223")
        context = browser.contexts[0]
        page = context.pages[0]
        for p_page in context.pages:
            if "fasih-sm.bps.go.id" in p_page.url:
                page = p_page
                break
        print("Connected to:", page.url)
        await page.screenshot(path="scratch/active_page_after_clicks.png")
        print("Screenshot saved to scratch/active_page_after_clicks.png")

asyncio.run(run())
