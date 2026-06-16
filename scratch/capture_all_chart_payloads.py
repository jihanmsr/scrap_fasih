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
        
        payloads = {}
        
        async def handle_request(request):
            if "/api/v1/chart/data" in request.url:
                post_data = request.post_data
                if post_data:
                    payloads[request.url] = json.loads(post_data)

        page.on("request", handle_request)
        
        print("Reloading page to capture all payloads...")
        await page.reload(wait_until="domcontentloaded")
        
        # Wait 8 seconds
        await asyncio.sleep(8)
        
        print(f"Captured {len(payloads)} payloads.")
        with open("scratch/captured_payloads.json", "w") as f:
            json.dump(payloads, f, indent=2)
        print("Saved to scratch/captured_payloads.json")

if __name__ == "__main__":
    asyncio.run(main())
