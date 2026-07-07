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
                const getElemInfo = (el) => ({
                    tag: el.tagName,
                    id: el.id,
                    className: el.className,
                    text: el.innerText ? el.innerText.substring(0, 100).replace(/\\n/g, ' ') : ''
                });
                
                const root = document.getElementById('root') || document.body;
                return Array.from(root.children).map(getElemInfo);
            }
        """)
        import pprint
        pprint.pprint(res)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
