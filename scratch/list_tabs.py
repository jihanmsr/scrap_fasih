import asyncio
import os
import sys
from playwright.async_api import async_playwright

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scrape_granular_core import get_authenticated_context

async def main():
    async with async_playwright() as p:
        print("Connecting to browser...")
        browser, context, page = await get_authenticated_context(p)
        if not page:
            print("Failed to connect.")
            return
            
        print("All Open Pages:")
        for idx, pg in enumerate(context.pages):
            content_len = len(await pg.content())
            print(f"Tab {idx}: URL={pg.url} Title={await pg.title()} ContentLength={content_len}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
