import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
            print("Connected on port 9222")
            context = browser.contexts[0]
            for idx, page in enumerate(context.pages):
                print(f"Page {idx}: URL={page.url} Title={await page.title()}")
        except Exception as e:
            print("Failed to connect on port 9222:", e)

asyncio.run(run())
