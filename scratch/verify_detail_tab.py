import asyncio
import os
import sys
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        print("Connecting to browser...")
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0]
        
        # Find local index.html page
        target_page = None
        for pg in context.pages:
            if 'index.html' in pg.url:
                target_page = pg
                break
        
        if not target_page:
            target_page = await context.new_page()
            print("Opened new page")
        
        print(f"Active page: {target_page.url}")
        await target_page.bring_to_front()
        
        # Force hard reload to pick up edited app.js
        print("Hard reloading page to pick up latest app.js...")
        await target_page.reload(wait_until="networkidle")
        await asyncio.sleep(15)
        
        # Confirm function exists now
        fn_exists = await target_page.evaluate("typeof window.switchGranularSummaryView")
        print(f"switchGranularSummaryView type: {fn_exists}")
        
        # Click the Detail tab
        print("Switching to Detail tab...")
        await target_page.evaluate("window.switchTab('target')")
        await asyncio.sleep(2)
        
        # Take screenshot of Detail tab
        await target_page.screenshot(path="scratch/detail_tab_verify.png", full_page=False)
        print("Saved scratch/detail_tab_verify.png")
        
        # Switch to Desa view
        if fn_exists == 'function':
            print("Switching to Desa summary view...")
            await target_page.evaluate("window.switchGranularSummaryView('desa')")
            await asyncio.sleep(1)
            
            desa_rows = await target_page.evaluate("document.querySelectorAll('#desa-summary-table-body tr').length")
            first_cell = await target_page.evaluate("document.querySelector('#desa-summary-table-body tr td:nth-child(2)')?.textContent || 'N/A'")
            print(f"Desa table rows: {desa_rows}")
            print(f"First kec column: {first_cell}")
            
            await target_page.screenshot(path="scratch/desa_view_verify.png", full_page=False)
            print("Saved scratch/desa_view_verify.png")
        else:
            print("ERROR: switchGranularSummaryView still not a function after reload!")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
