import asyncio
from playwright.async_api import async_playwright
import json

async def run():
    async with async_playwright() as p:
        print("[INFO] Connecting to Chrome via CDP...")
        try:
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
            context = browser.contexts[0]
            page = context.pages[0]
            
            print(f"[INFO] Current URL: {page.url}")
            
            print("[INFO] Setting up network interceptor...")
            
            async def log_request(route):
                req = route.request
                if "analytic" in req.url or "assignment" in req.url:
                    print(f"\n[NETWORK] {req.method} {req.url}")
                    if req.method == "POST":
                        print(f"Payload: {req.post_data}")
                await route.continue_()
            
            await page.route("**/*", log_request)
            
            print("[INFO] Navigating to Dashboard...")
            await page.goto("https://fasih-sm.bps.go.id/app/analytic/assignment/assignment-status", timeout=60000)
            
            print("[INFO] Waiting 5 seconds to capture requests...")
            await asyncio.sleep(5)
            
            print("[INFO] Attempting to click Rekap Petugas tab...")
            try:
                # Wait for the Rekap Petugas tab and click it
                await page.click("text='Rekap Petugas'", timeout=10000)
                print("[INFO] Clicked 'Rekap Petugas' tab! Waiting for API response...")
                await asyncio.sleep(10)
            except Exception as e:
                print(f"[WARNING] Could not click Rekap Petugas: {e}")
                
            print("[INFO] Done catching network.")
        except Exception as e:
            print(f"[ERROR] Failed to connect or run: {e}")

asyncio.run(run())
