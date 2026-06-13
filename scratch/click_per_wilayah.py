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
            print("Could not find fasih-sm page")
            return
            
        print("Connected. Current URL:", page.url)
        
        captured_requests = []
        def handle_request(request):
            if "allocations-view" in request.url:
                captured_requests.append((request.method, request.url, request.post_data))
                print(f"Captured: [{request.method}] {request.url}")

        page.on("request", handle_request)
        
        # Click on 'Per Wilayah' button
        # In the UI, the button text is 'Per Wilayah'
        print("Clicking 'Per Wilayah'...")
        await page.click("text=Per Wilayah")
        
        await asyncio.sleep(4)
        
        print("\nCaptured allocations-view requests:")
        for method, url, data in captured_requests:
            print(f"- {method} {url}")
            if data:
                print(f"  Payload: {data}")

asyncio.run(run())
