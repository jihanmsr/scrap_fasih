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
            
        local_page = None
        for pg in context.pages:
            if "index.html" in pg.url or pg.url.startswith("file:///"):
                local_page = pg
                break
                
        if not local_page:
            print("[INFO] Local index.html page not found in active tabs. Creating a new tab...")
            local_page = await context.new_page()
            await local_page.goto("file:///Users/jihanmaisaroh/scrap_fasih/index.html")
        else:
            print("Using Page URL:", local_page.url)
            print("Reloading local dashboard...")
            await local_page.reload()
            
        print("Waiting 10 seconds for render...")
        await asyncio.sleep(10)
        
        screenshot_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "local_dashboard_verify.png")
        await local_page.screenshot(path=screenshot_path)
        print(f"Screenshot saved to {screenshot_path}")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
