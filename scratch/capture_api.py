import asyncio
from playwright.async_api import async_playwright
from urllib.parse import unquote

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9223")
        context = browser.contexts[0]
        
        # Find the active page
        page = None
        for p_page in context.pages:
            if "fasih-sm.bps.go.id" in p_page.url:
                page = p_page
                break
                
        if not page:
            print("Could not find fasih-sm page")
            return
            
        print(f"Connected to page: {page.url}")
        
        # Let's set up request interception
        captured = []
        def handle_request(request):
            if "/api/" in request.url:
                captured.append((request.method, request.url, request.post_data))
                print(f"Captured: [{request.method}] {request.url}")
                
        page.on("request", handle_request)
        
        # 1. Click on Petugas in the left sidebar
        # In BPS FASIH, the sidebar menu has a "Petugas" link. Let's find it and click it.
        print("Clicking 'Petugas' menu in sidebar...")
        # Try different selectors to click the Petugas menu in left sidebar
        sidebar_clicked = False
        selectors = [
            "text=Petugas",
            "a:has-text('Petugas')",
            "div:has-text('Petugas')",
            "span:has-text('Petugas')"
        ]
        for sel in selectors:
            try:
                # We want to click the one in the sidebar. Let's check if it exists and is visible.
                loc = page.locator(sel)
                count = await loc.count()
                for i in range(count):
                    el = loc.nth(i)
                    if await el.is_visible():
                        # Check if it has a class like menu or sidebar
                        # Let's just click it
                        await el.click()
                        print(f"Clicked selector: {sel}")
                        sidebar_clicked = True
                        break
                if sidebar_clicked:
                    break
            except Exception as e:
                print(f"Failed to click selector {sel}: {e}")
                
        await asyncio.sleep(4)
        print(f"URL after clicking Petugas: {page.url}")
        
        # 2. Click on 'Per Wilayah' button
        print("Clicking 'Per Wilayah' toggle button...")
        try:
            await page.click("text=Per Wilayah", timeout=5000)
            print("Clicked 'Per Wilayah'")
        except Exception as e:
            print(f"Failed to click 'Per Wilayah': {e}")
            
        await asyncio.sleep(4)
        
        print("\n=== CAPTURED ALLOCATIONS / SURVEY APIs ===")
        for method, url, data in captured:
            if "allocation" in url.lower() or "survey" in url.lower():
                print(f"- {method} {url}")
                if data:
                    print(f"  Payload: {data}")

asyncio.run(run())
