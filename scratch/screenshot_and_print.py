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
            
        print("Reloading page...")
        await local_page.reload()
        
        print("Waiting dynamically for rendering to finish (value != '0')...")
        for i in range(40):
            await asyncio.sleep(1)
            target_val = await local_page.evaluate("document.getElementById('se_umum-stat-total-prelist').innerText")
            if target_val != "0" and target_val != "":
                print(f"Render completed after {i+1} seconds!")
                break
        else:
            print("Timed out waiting for render. Current DOM value:", target_val)
        
        # Get final innerText
        target_val = await local_page.evaluate("document.getElementById('se_umum-stat-total-prelist').innerText")
        print("DOM target value at screenshot time:", target_val)
        
        screenshot_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "local_dashboard_verify.png")
        await local_page.screenshot(path=screenshot_path)
        print("Screenshot updated.")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
