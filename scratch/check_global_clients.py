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
                const keys = Object.keys(window);
                const clients = [];
                for (const k of keys) {
                    if (k.toLowerCase().includes('axios') || k.toLowerCase().includes('http') || k.toLowerCase().includes('api') || k.toLowerCase().includes('fetch')) {
                        clients.push(k);
                    }
                }
                return {
                    matchingKeys: clients,
                    hasAxios: typeof window.axios !== 'undefined',
                    localStorageKeys: Object.keys(localStorage),
                    sessionStorageKeys: Object.keys(sessionStorage)
                };
            }
        """)
        print("Global client check:", res)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
