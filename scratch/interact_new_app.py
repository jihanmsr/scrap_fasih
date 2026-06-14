import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9223")
        context = browser.contexts[0]
        page = context.pages[0]
        print(f"Page URL: {page.url}")
        
        # Print all text content of elements that look like tab buttons
        elements = await page.evaluate("""
            () => {
                const items = Array.from(document.querySelectorAll('div, button, span, label'));
                return items.filter(el => {
                    const txt = el.innerText ? el.innerText.trim() : '';
                    return (txt === 'Admin' || txt === 'Viewer' || txt === 'Petugas' || txt === 'Daftar Petugas' || txt === 'Per Wilayah') && el.childNodes.length <= 3;
                }).map(el => ({
                    tagName: el.tagName,
                    className: el.className,
                    text: el.innerText.trim(),
                    parentClass: el.parentElement ? el.parentElement.className : ''
                }));
            }
        """)
        import json
        print(json.dumps(elements, indent=2))

asyncio.run(run())
