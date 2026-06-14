import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9223")
        context = browser.contexts[0]
        page = context.pages[0]
        print(f"Main Page URL: {page.url}")
        
        print("\nAll frames:")
        for idx, frame in enumerate(page.frames):
            print(f"[{idx}] Name: '{frame.name}', URL: {frame.url}")

asyncio.run(run())
