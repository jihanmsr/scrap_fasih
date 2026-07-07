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
        
        # Check window variables
        res = await page.evaluate("""
            () => {
                return {
                    bobcmn: typeof window.bobcmn,
                    TSPD_101: typeof window.TSPD_101,
                    cookies: document.cookie.substring(0, 200)
                };
            }
        """)
        print("Browser environment:", res)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
