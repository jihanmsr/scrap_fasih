import asyncio
import json
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = None
        for port in [9223, 9222]:
            try:
                browser = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
                break
            except Exception:
                pass
        if not browser:
            print("CDP connection failed")
            return
        
        context = browser.contexts[0]
        page = None
        for p_page in context.pages:
            if "fasih-dashboard.bps.go.id" in p_page.url:
                page = p_page
                break
        if not page:
            print("Dashboard page not found open")
            return
            
        print(f"Connected to page: {page.url}")
        
        # Let's extract the tables
        data = await page.evaluate("""() => {
            const tables = [];
            document.querySelectorAll('table').forEach((table, tIdx) => {
                const rows = [];
                const headers = [];
                
                const thElements = table.querySelectorAll('th');
                thElements.forEach(th => headers.push(th.innerText.trim().replace(/\\n/g, ' ')));
                
                const trElements = table.querySelectorAll('tbody tr');
                trElements.forEach(tr => {
                    const rowData = [];
                    tr.querySelectorAll('td').forEach(td => rowData.push(td.innerText.trim()));
                    rows.push(rowData);
                });
                
                tables.push({ index: tIdx, headers, rowsCount: rows.length, rows });
            });
            return tables;
        }""")
        
        for t in data:
            print(f"\nTable {t['index']} (Rows: {t['rowsCount']}):")
            print("Headers:", t["headers"])
            print("Rows (first 15):")
            for idx, r in enumerate(t["rows"][:15]):
                print(f" - Row {idx+1}: {r}")

if __name__ == "__main__":
    asyncio.run(main())
