import asyncio
import json
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9223")
        context = browser.contexts[0]
        page = context.pages[0]
        
        if len(page.frames) > 1:
            frame = page.frames[1]
            
            html = await frame.evaluate("""
                () => {
                    const elements = Array.from(document.querySelectorAll('*'));
                    const lainnya = elements.find(el => el.innerText && el.innerText.trim().endsWith('Lainnya'));
                    if (lainnya) {
                        return {
                            tagName: lainnya.tagName,
                            className: lainnya.className,
                            outerHTML: lainnya.outerHTML,
                            parentTagName: lainnya.parentElement ? lainnya.parentElement.tagName : '',
                            parentClassName: lainnya.parentElement ? lainnya.parentElement.className : ''
                        };
                    }
                    return 'Lainnya element not found';
                }
            """)
            with open("scratch/lainnya_info.json", "w") as f:
                json.dump(html, f, indent=2)
            print("Done! Info written to scratch/lainnya_info.json")
        else:
            print("No second frame found")

asyncio.run(run())
