import asyncio
from playwright.async_api import async_playwright
from urllib.parse import unquote

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
            if "/api/" in request.url:
                captured.append((request.method, request.url, request.post_data))
                print(f"Captured: [{request.method}] {request.url}")
            
        page.on("request", handle_request)
        
        # 1. Click on "Petugas" tab button (the middle radio button tab, using simple text match)
        print("Clicking 'Petugas' role tab...")
        try:
            # Click the tab containing "Petugas"
            # In the UI, it's a div/button containing "Petugas"
            await page.click("div.ant-radio-group >> text=Petugas", timeout=5000)
            print("Clicked Petugas tab")
            await asyncio.sleep(3)
        except Exception as e:
            print("Failed to click Petugas tab with primary selector, trying fallback...", e)
            try:
                await page.click("text=Petugas", timeout=5000)
                print("Clicked Petugas text")
                await asyncio.sleep(3)
            except Exception as e2:
                print("Fallback failed:", e2)
            
        # 2. Click "Per Wilayah"
        print("Clicking 'Per Wilayah'...")
        try:
            await page.click("text=Per Wilayah", timeout=5000)
            print("Clicked Per Wilayah")
            await asyncio.sleep(3)
        except Exception as e:
            print("Failed to click Per Wilayah:", e)
            
        print("\n=== CAPTURED APIs ===")
        for method, url, data in captured:
            print(f"- {method} {url}")

asyncio.run(run())
