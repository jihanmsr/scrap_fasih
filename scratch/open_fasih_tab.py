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
            
        print("Opening FASIH Dashboard in a new tab...")
        new_page = await context.new_page()
        await new_page.goto("https://fasih-sm.bps.go.id/app/surveys/a0429e96-51a5-477b-a415-485f9c153004/fd68e454-ba45-4b85-8205-f3bf777ded24")
        print("FASIH tab opened. Please log in to FASIH in this window if prompted.")
        
        # Keep connection for 5 seconds to let the tab register
        await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
