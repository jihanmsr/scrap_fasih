import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = None
        for port in [9223, 9222]:
            try: browser = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}"); break
            except: pass
        if not browser: return
        context = browser.contexts[0]
        page = None
        for p_page in context.pages:
            if "fasih-sm.bps.go.id" in p_page.url: page = p_page; break
        if not page: return
        
        print("Waiting for network requests...")
        
        async def handle_request(request):
            if "allocations-view" in request.url and "by-user" not in request.url and "summary" not in request.url:
                print("FOUND API:", request.url)
        
        page.on("request", handle_request)
        
        await page.evaluate("""
            const buttons = document.querySelectorAll('button, div, span, a');
            for (const b of buttons) {
                if (b.innerText && b.innerText.includes('Lainnya')) {
                    b.click();
                    break;
                }
            }
        """)
        
        await asyncio.sleep(3)

asyncio.run(run())
