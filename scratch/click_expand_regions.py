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
        
        # Click Petugas menu first
        print("Clicking Petugas sidebar item...")
        try:
            await page.click("text=Petugas")
            await asyncio.sleep(4)
        except Exception as e:
            print(f"Failed to click Petugas sidebar: {e}")
            
        print(f"Current URL: {page.url}")
        
        # Find any text like "Lainnya" or containing "Lainnya" and click it
        print("Looking for 'Lainnya' button/link...")
        clicked = False
        locators = [
            "text=Lainnya",
            "span:has-text('Lainnya')",
            "button:has-text('Lainnya')",
            "div:has-text('Lainnya')"
        ]
        
        for loc_str in locators:
            try:
                loc = page.locator(loc_str)
                count = await loc.count()
                for i in range(count):
                    el = loc.nth(i)
                    if await el.is_visible():
                        await el.click()
                        print(f"Clicked: {loc_str}")
                        clicked = True
                        break
                if clicked:
                    break
            except Exception as e:
                print(f"Error clicking {loc_str}: {e}")
                
        await asyncio.sleep(4)
        
        print("\n=== CAPTURED APIs WHEN EXPANDING REGIONS ===")
        for method, url, data in captured:
            print(f"- {method} {url}")
            if data:
                print(f"  Payload: {data}")

asyncio.run(run())
