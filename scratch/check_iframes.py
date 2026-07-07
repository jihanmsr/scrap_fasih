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
            
        res = await page.evaluate("""
            () => {
                const iframes = Array.from(document.querySelectorAll('iframe')).map(f => ({
                    id: f.id,
                    src: f.src,
                    name: f.name
                }));
                return {
                    iframeCount: iframes.length,
                    iframes: iframes
                };
            }
        """)
        print("Iframes found on page:", res)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
