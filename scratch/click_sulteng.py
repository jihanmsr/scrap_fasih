import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9223")
        context = browser.contexts[0]
        
        page = None
        for p_page in context.pages:
            if "fasih-sm.bps.go.id" in p_page.url:
                page = p_page
                break
        if not page: return
        
        captured = []
        def handle_request(request):
            captured.append((request.method, request.url, request.post_data))
            print(f"Captured: [{request.method}] {request.url}")
            
        page.on("request", handle_request)
        
        print("Clicking SULAWESI TENGAH...")
        await page.click("text=SULAWESI TENGAH")
        
        await asyncio.sleep(4)
        
        print("\n=== CAPTURED APIs WHEN CLICKING SULAWESI TENGAH ===")
        for method, url, data in captured:
            if "/api/" in url:
                print(f"- {method} {url}")
                if data:
                    print(f"  Payload: {data}")

asyncio.run(run())
