import asyncio
import json
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        print("Connecting to browser...")
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        context = browser.contexts[0]
        
        local_page = next((pg for pg in context.pages if "index.html" in pg.url), None)
        if not local_page:
            print("Local page not found.")
            await browser.close()
            return
            
        print("Evaluating window.IPAS_DATA...")
        res = await local_page.evaluate("""
            () => {
                return {
                    has_data: !!window.IPAS_DATA,
                    updated_at: window.IPAS_DATA?.updated_at || 'none',
                    se_umum_len: window.IPAS_DATA?.se_umum?.length || 0,
                    se_ub_len: window.IPAS_DATA?.se_ub?.length || 0,
                    prov_total: window.IPAS_DATA?.se_umum_prov_total || 0,
                    sample_kab: window.IPAS_DATA?.se_umum?.[0] ? {
                        kabupaten: window.IPAS_DATA.se_umum[0].kabupaten,
                        total_prelist: window.IPAS_DATA.se_umum[0].total_prelist,
                        breakdown: window.IPAS_DATA.se_umum[0].breakdown || null
                    } : null
                };
            }
        """)
        print("window.IPAS_DATA state:")
        print(json.dumps(res, indent=2))
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
