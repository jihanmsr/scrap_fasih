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
        if not browser:
            print("Failed to connect.")
            return
            
        print(f"Number of contexts: {len(browser.contexts)}")
        for idx, ctx in enumerate(browser.contexts):
            print(f"Context [{idx}] pages:")
            for p_idx, pg in enumerate(ctx.pages):
                print(f"  Page [{p_idx}] URL: {pg.url}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
