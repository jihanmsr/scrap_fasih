import asyncio
import json
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9223")
            context = browser.contexts[0]
            page = None
            for p_page in context.pages:
                if "fasih-sm.bps.go.id" in p_page.url:
                    page = p_page
                    break
            
            if not page:
                print("Could not find FASIH page.")
                return
                
            print(f"Connected to FASIH page: {page.url}")
            
            # Let's extract the table text, headers, and rows from the page
            data = await page.evaluate("""() => {
                const rows = [];
                const headers = [];
                
                // Get table headers
                const thElements = document.querySelectorAll('table th');
                thElements.forEach(th => headers.push(th.innerText.trim()));
                
                // Get table rows
                const trElements = document.querySelectorAll('table tbody tr');
                trElements.forEach(tr => {
                    const rowData = {};
                    const tdElements = tr.querySelectorAll('td');
                    tdElements.forEach((td, index) => {
                        const header = headers[index] || `col_${index}`;
                        rowData[header] = td.innerText.trim();
                    });
                    rows.push(rowData);
                });
                
                return { headers, rows };
            }""")
            
            print("\nHeaders found in page table:")
            print(data["headers"])
            
            print("\nRows found in page table (first 5):")
            for idx, r in enumerate(data["rows"][:5]):
                print(f"Row {idx + 1}:")
                print(json.dumps(r, indent=2))
                
        except Exception as e:
            print("Error:", e)

if __name__ == "__main__":
    asyncio.run(main())
