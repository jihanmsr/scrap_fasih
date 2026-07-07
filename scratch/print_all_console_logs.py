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
            
        local_page = None
        for pg in context.pages:
            if "index.html" in pg.url:
                local_page = pg
                break
        if not local_page:
            local_page = context.pages[0]
            
        print("Using Page URL:", local_page.url)
        
        # Listen to console
        local_page.on("console", lambda msg: print(f"[CONSOLE {msg.type.upper()}] {msg.text}"))
        
        print("Reloading page...")
        await local_page.reload()
        print("Waiting 5 seconds for page load...")
        await asyncio.sleep(5)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
