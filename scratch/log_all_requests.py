import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = None
        for port in [9223, 9222]:
            try:
                browser = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
                break
            except Exception:
                pass
        if not browser:
            print("CDP connection failed")
            return
        
        context = browser.contexts[0]
        page = None
        for p_page in context.pages:
            if "fasih-dashboard.bps.go.id" in p_page.url:
                page = p_page
                break
        if not page:
            print("Dashboard page not found open")
            return
            
        print(f"Connected to page: {page.url}")
        
        async def handle_request(request):
            if "fasih-dashboard" in request.url:
                print(f"Request: {request.method} {request.url}")
                if request.method == "POST":
                    try:
                        print("Payload:", request.post_data[:500] if request.post_data else None)
                    except:
                        pass

        page.on("request", handle_request)
        
        print("Reloading page...")
        await page.reload(wait_until="domcontentloaded")
        await asyncio.sleep(8)

if __name__ == "__main__":
    asyncio.run(main())
