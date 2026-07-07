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
            
        print("Active Page URL:", page.url)
        content = await page.content()
        print("Content sample (first 1000 chars):")
        print(content[:1000])
        
        # Check if login button or something exists
        print("Is login present:", "login" in content.lower())
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
