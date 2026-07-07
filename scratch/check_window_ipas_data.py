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
            if "index.html" in pg.url:
                local_page = pg
                break
                
        if not local_page:
            local_page = context.pages[0]
            
        print("Using Page URL:", local_page.url)
        
        # Check window.IPAS_DATA
        res = await local_page.evaluate("""
            () => {
                return {
                    has_ipas: typeof window.IPAS_DATA !== 'undefined',
                    keys: window.IPAS_DATA ? Object.keys(window.IPAS_DATA) : [],
                    se_umum_len: window.IPAS_DATA && window.IPAS_DATA.se_umum ? window.IPAS_DATA.se_umum.length : 0,
                    se_umum_prov_total: window.IPAS_DATA ? window.IPAS_DATA.se_umum_prov_total : null
                };
            }
        """)
        print("window.IPAS_DATA status:", res)
        
        # Also print console errors
        print("Checking for console errors...")
        # (We can listen to console event, but since this is immediate, we just reload and listen)
        
        local_page.on("console", lambda msg: print(f"Browser Console {msg.type}: {msg.text}"))
        print("Reloading page...")
        await local_page.reload()
        print("Waiting 5 seconds...")
        await asyncio.sleep(5)
        
        res = await local_page.evaluate("""
            () => {
                return {
                    has_ipas: typeof window.IPAS_DATA !== 'undefined',
                    keys: window.IPAS_DATA ? Object.keys(window.IPAS_DATA) : [],
                    se_umum_len: window.IPAS_DATA && window.IPAS_DATA.se_umum ? window.IPAS_DATA.se_umum.length : 0,
                    se_umum_prov_total: window.IPAS_DATA ? window.IPAS_DATA.se_umum_prov_total : null
                };
            }
        """)
        print("window.IPAS_DATA AFTER reload:", res)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
