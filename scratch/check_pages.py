import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = None
        for port in [9223, 9222]:
            try:
                browser = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
                print(f"Connected on port {port}")
                break
            except Exception as e:
                print(f"Failed to connect on port {port}: {e}")
        if not browser:
            return
        
        context = browser.contexts[0]
        for idx, page in enumerate(context.pages):
            print(f"Page {idx}: URL={page.url} Title={await page.title()}")

asyncio.run(run())
