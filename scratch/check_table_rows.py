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
            
        print("Evaluating table rows...")
        res = await local_page.evaluate("""
            () => {
                const rows = document.querySelectorAll('#se_umum-table-body tr');
                return {
                    count: rows.length,
                    first_row_text: rows.length > 0 ? rows[0].innerText : 'no rows found'
                };
            }
        """)
        print("Table Rows:", res)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
