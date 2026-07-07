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
            print("Local page not found.")
            await browser.close()
            return
            
        print("Evaluating rendered table rows...")
        res = await local_page.evaluate("""
            () => {
                const rows = document.querySelectorAll('#se_umum-table-body tr');
                const rowData = [];
                rows.forEach(r => {
                    const cells = Array.from(r.querySelectorAll('td')).map(c => c.innerText.trim());
                    rowData.push(cells);
                });
                return {
                    headers: Array.from(document.querySelectorAll('#se_umum-table-body').length > 0 ? document.getElementById('se_umum-table-body').parentElement.querySelectorAll('th') : []).map(h => h.innerText.trim().replace(/\\n/g, ' ')),
                    rows: rowData.slice(0, 5) // check first 5 rows
                };
            }
        """)
        print("Rendered Headers:")
        print(res.get("headers"))
        print("\nFirst 5 Rendered Rows:")
        for r in res.get("rows"):
            print(r)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
