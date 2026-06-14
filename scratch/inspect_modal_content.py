import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9223")
        context = browser.contexts[0]
        page = context.pages[0]
        
        if len(page.frames) > 1:
            frame = page.frames[1]
            text = await frame.evaluate("() => document.body ? document.body.innerText : 'No body'")
            print("=== Frame 1 Inner Text ===")
            print(text[:2000])
            
            # Check for modals
            modal_html = await frame.evaluate("""
                () => {
                    const modal = document.querySelector('[role="dialog"], .modal, .ant-modal, [class*="modal"], [class*="dialog"]');
                    return modal ? modal.outerHTML : 'No modal element found';
                }
            """)
            print("\n=== Modal Element HTML ===")
            print(modal_html[:1000])
        else:
            print("No second frame found")

asyncio.run(run())
