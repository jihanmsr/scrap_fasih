import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9223")
        context = browser.contexts[0]
        page = context.pages[0]
        
        # Find elements containing "Viewer" and print their parent's HTML
        html = await page.evaluate("""
            () => {
                const els = Array.from(document.querySelectorAll('*'));
                const viewer = els.find(el => el.innerText && el.innerText.trim() === 'Viewer');
                if (viewer) {
                    return {
                        viewerTag: viewer.tagName,
                        viewerClass: viewer.className,
                        parentTag: viewer.parentElement.tagName,
                        parentClass: viewer.parentElement.className,
                        parentHTML: viewer.parentElement.outerHTML
                    };
                }
                return null;
            }
        """)
        import json
        print(json.dumps(html, indent=2))

asyncio.run(run())
