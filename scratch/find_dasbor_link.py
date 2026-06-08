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
        page = context.pages[0] if context.pages else await context.new_page()
        
        await page.goto("https://fasih-sm.bps.go.id/app/surveys/ecddb52e-f392-403c-a963-47391f217010/37526b20-81c8-42f5-a895-6190137d7394/data", wait_until="domcontentloaded")
        await asyncio.sleep(2)
        
        elements = await page.evaluate("""
            () => {
                const all = Array.from(document.querySelectorAll('*'));
                const matched = [];
                for (const el of all) {
                    if (el.innerText && el.innerText.trim() === 'Dasbor') {
                        matched.append({
                            tag: el.tagName,
                            className: el.className,
                            parentTag: el.parentElement ? el.parentElement.tagName : '',
                            parentClass: el.parentElement ? el.parentElement.className : '',
                            outerHTML: el.outerHTML.substring(0, 300)
                        });
                    }
                }
                return matched;
            }
        """)
        
        print(f"\nMatched {len(elements)} elements with text 'Dasbor':")
        for idx, el in enumerate(elements):
            print(f"[{idx}] Tag: {el['tag']} | Class: {el['className']} | Parent: {el['parentTag']} ({el['parentClass']})")
            print(f"    HTML: {el['outerHTML']}")

if __name__ == "__main__":
    asyncio.run(main())
