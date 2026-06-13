import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = None
        for port in [9223, 9222]:
            try:
                browser = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
                print(f"Connected to Chrome on port {port}")
                break
            except Exception:
                pass
        if not browser:
            print("Could not connect to Chrome")
            return
        
        context = browser.contexts[0]
        page = None
        for p_page in context.pages:
            if "fasih-sm.bps.go.id" in p_page.url:
                page = p_page
                break
                
        if not page:
            print("Could not find fasih-sm page")
            return
            
        print("Monitoring network requests. Click around in Chrome (e.g. click 'Per Wilayah' or click 'Lainnya' button). Press Ctrl+C to stop.")
        
        def handle_request(request):
            if "/api/" in request.url:
                print(f"[{request.method}] {request.url}")
                if request.post_data:
                    print("  Payload:", request.post_data)

        page.on("request", handle_request)
        
        # Keep running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("Stopped.")

asyncio.run(run())
