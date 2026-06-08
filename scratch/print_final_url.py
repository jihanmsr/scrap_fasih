import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
            print("Connected to Chrome.")
        except Exception as e:
            print("Failed to connect to Chrome:", e)
            return

        context = browser.contexts[0]
        page = context.pages[0]
        
        print(f"Active Page URL: {page.url}")
        title = await page.title()
        print(f"Active Page Title: {title}")
        
        text = await page.evaluate("() => document.body.innerText")
        print(f"Total length of page text: {len(text)}")
        
        # Search for occurrences of '240' or '240.141' or '240,141' or '240141'
        queries = ["240", "240.141", "240,141", "240141"]
        print("\nSearching text for queries:")
        for q in queries:
            count = text.count(q)
            print(f"  '{q}': found {count} times")
            if count > 0:
                # print snippet
                idx = text.find(q)
                print(f"    Snippet: ... {text[max(0, idx-50):min(len(text), idx+50)]} ...")

        # Let's list some rows from the table if visible
        rows = await page.evaluate("""
            () => {
                const trs = Array.from(document.querySelectorAll('table tr'));
                return trs.slice(0, 5).map(tr => tr.innerText);
            }
        """)
        print(f"\nFound {len(rows)} table rows:")
        for idx, row in enumerate(rows):
            print(f"  [{idx}] {row.strip().replace(chr(10), ' | ')}")

if __name__ == "__main__":
    asyncio.run(main())
