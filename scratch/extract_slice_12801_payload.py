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
            print("Dashboard page not found")
            return
            
        print(f"Connected to page: {page.url}")
        
        captured_payload = None
        
        async def handle_request(request):
            nonlocal captured_payload
            if "/api/v1/chart/data" in request.url and "12801" in request.url:
                post_data = request.post_data
                if post_data:
                    captured_payload = json.loads(post_data)

        page.on("request", handle_request)
        
        print("Reloading page to capture slice 12801 payload...")
        await page.reload(wait_until="domcontentloaded")
        
        # Wait up to 10 seconds for the request to fire
        for _ in range(20):
            if captured_payload:
                break
            await asyncio.sleep(0.5)
            
        if captured_payload:
            print("\nCaptured Payload for Slice 12801:")
            print(json.dumps(captured_payload, indent=2))
        else:
            print("Failed to capture slice 12801 payload")

if __name__ == "__main__":
    asyncio.run(main())
