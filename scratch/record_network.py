import asyncio
import json
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
        
        # We will listen to requests
        requests_log = []
        
        async def handle_request(request):
            if "/api/v1/chart/data" in request.url:
                try:
                    post_data = request.post_data
                    if post_data:
                        requests_log.append({
                            "url": request.url,
                            "method": request.method,
                            "payload": json.loads(post_data)
                        })
                except Exception as e:
                    pass

        page.on("request", handle_request)
        
        print("Refreshing dashboard page to capture chart data requests...")
        await page.reload(wait_until="networkidle")
        await asyncio.sleep(5)
        
        print(f"Captured {len(requests_log)} requests to /api/v1/chart/data:")
        for idx, req in enumerate(requests_log):
            print(f"\n--- Request {idx+1} ---")
            print(json.dumps(req["payload"], indent=2))

if __name__ == "__main__":
    asyncio.run(main())
