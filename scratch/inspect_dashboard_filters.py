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
        
        # Look for select dropdowns or filter components
        dropdowns = await page.evaluate("""
            () => {
                const results = [];
                // Check select elements
                document.querySelectorAll('select').forEach((el, idx) => {
                    results.push({
                        tag: 'select',
                        id: el.id,
                        className: el.className,
                        options: Array.from(el.options).map(o => ({ value: o.value, text: o.text }))
                    });
                });
                
                // Check button dropdowns or divs that might be custom dropdowns
                document.querySelectorAll('button').forEach((el, idx) => {
                    if (el.innerText.toLowerCase().includes('kabupaten') || el.innerText.toLowerCase().includes('wilayah')) {
                        results.push({
                            tag: 'button',
                            id: el.id,
                            className: el.className,
                            text: el.innerText
                        });
                    }
                });
                return results;
            }
        """)
        print("Detected Filter Elements:")
        import pprint
        pprint.pprint(dropdowns)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
