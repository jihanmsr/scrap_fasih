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
        if not page:
            print("No page found")
            return
            
        print(f"Connected to page: {page.url}")
        
        captured = []
        def handle_request(request):
            if "by-region/children" in request.url:
                captured.append((request.method, request.url, request.post_data))
                print(f"Captured: [{request.method}] {request.url}")
            
        page.on("request", handle_request)
        
        # Click on the SULAWESI TENGAH row or the arrow
        print("Clicking SULAWESI TENGAH row...")
        try:
            # Click the text directly
            await page.click("text=SULAWESI TENGAH", timeout=5000)
            print("Clicked row")
        except Exception as e:
            print("Failed to click row:", e)
            
        await asyncio.sleep(4)
        
        print("\n=== CAPTURED by-region/children APIs ===")
        for method, url, data in captured:
            print(f"- {method} {url}")

asyncio.run(run())
