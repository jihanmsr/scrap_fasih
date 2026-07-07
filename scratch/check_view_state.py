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
        
        res = await local_page.evaluate("""
            () => {
                const activeTab = localStorage.getItem('active_tab');
                const seUmumTab = document.getElementById('se_umum');
                const seUmumDisplay = seUmumTab ? seUmumTab.style.display : 'not found';
                const seUmumClass = seUmumTab ? seUmumTab.className : '';
                
                // Get innerText of target count
                const targetText = document.getElementById('se_umum-stat-total-prelist') ? document.getElementById('se_umum-stat-total-prelist').innerText : 'not found';
                const targetWrapperText = document.getElementById('se_umum-stat-total-prelist-wrapper') ? document.getElementById('se_umum-stat-total-prelist-wrapper').innerText : 'not found';
                
                return {
                    activeTab,
                    seUmumDisplay,
                    seUmumClass,
                    targetText,
                    targetWrapperText
                };
            }
        """)
        print("View state:", res)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
