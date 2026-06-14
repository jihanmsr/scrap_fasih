import asyncio
from playwright.async_api import async_playwright
import json

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9223")
        context = browser.contexts[0]
        page = context.pages[0]
        print(f"Connected to page: {page.url}")
        
        captured = []
        def handle_request(request):
            if "/api/" in request.url:
                captured.append((request.method, request.url, request.post_data))
                print(f"Captured: [{request.method}] {request.url}")
                
        page.on("request", handle_request)
        
        # Click on Petugas tab
        await page.click("text=Petugas")
        await page.wait_for_timeout(5000)
        
        print(f"New URL: {page.url}")
        await page.screenshot(path="scratch/active_page_petugas_tab.png")
        
        print("\n=== CAPTURED APIs WHEN CLICKING PETUGAS ===")
        for method, url, data in captured:
            print(f"- {method} {url}")
            if data:
                print(f"  Payload: {data}")

asyncio.run(run())
