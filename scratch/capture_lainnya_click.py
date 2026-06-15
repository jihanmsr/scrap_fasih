import asyncio
from playwright.async_api import async_playwright
from urllib.parse import unquote

async def run():
    async with async_playwright() as p:
        browser = None
        for port in [9223, 9222]:
            try:
                browser = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
                print(f"Connected on port {port}")
                break
            except Exception:
                pass
        if not browser:
            print("Failed to connect to browser")
            return
            
        context = browser.contexts[0]
        page = None
        for p_page in context.pages:
            if "fasih-sm.bps.go.id" in p_page.url:
                page = p_page
                break
        if not page:
            page = context.pages[0]
            
        # Navigate directly to the petugas page
        target_url = "https://fasih-sm.bps.go.id/survey-collection/petugas/a0429e96-51a5-477b-a415-4852bf2cde37"
        print(f"Navigating to {target_url}...")
        try:
            await page.goto(target_url, timeout=30000, wait_until="domcontentloaded")
        except Exception as e:
            print(f"Navigation timed out: {e}")
            
        await asyncio.sleep(3)
        
        # Intercept requests
        captured_requests = []
        def handle_request(request):
            captured_requests.append((request.method, request.url, request.post_data))
            print(f"Captured: [{request.method}] {request.url}")
            
        page.on("request", handle_request)
        
        # Search for abjadalam9@gmail.com
        print("Searching for abjadalam9@gmail.com...")
        # Find the search input. In the screenshot, there is an input with placeholder "Search..." or similar, or we can look for input element.
        # Let's search by typing into the input
        try:
            await page.fill("input[placeholder*='Cari'], input[placeholder*='Search'], input[type='text']", "abjadalam9@gmail.com")
            await page.keyboard.press("Enter")
        except Exception as e:
            print(f"Failed to fill search box: {e}")
            
        await asyncio.sleep(4)
        
        # Click "49 Lainnya" or "Lainnya"
        print("Clicking 'Lainnya' text...")
        try:
            # Look for element containing "Lainnya"
            await page.click("text=/.*Lainnya.*/", timeout=5000)
            print("Clicked!")
        except Exception as e:
            print(f"Failed to click: {e}")
            
        await asyncio.sleep(4)
        
        print("\n=== CAPTURED REQUESTS DURING CLICK ===")
        for method, url, data in captured_requests:
            if "api" in url:
                print(f"- {method} {url}")
                if data:
                    print(f"  Payload: {data}")

asyncio.run(run())
