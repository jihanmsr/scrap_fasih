import asyncio
from playwright.async_api import async_playwright

async def main():
    print("[START] Connecting to Chrome...")
    async with async_playwright() as p:
        browser = None
        for port in [9222, 9223]:
            try:
                browser = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
                print(f"[SUCCESS] Connected on port {port}")
                break
            except Exception as e:
                pass
        
        if not browser:
            print("[ERROR] Could not connect to Chrome.")
            return

        try:
            context = browser.contexts[0]
            page = await context.new_page()
            
            # Print page errors with complete detail
            def on_pageerror(err):
                print("\n=== PAGE ERROR ===")
                print(f"Message: {err.message}")
                print(f"Name: {err.name}")
                print(f"Stack:\n{err.stack}")
                print("==================\n")
                
            page.on("pageerror", on_pageerror)
            page.on("console", lambda msg: print(f"[CONSOLE {msg.type}] {msg.text}"))
            
            url = "file:///Users/jihanmaisaroh/scrap_fasih/index.html"
            await page.goto(url, wait_until="load")
            await asyncio.sleep(2)
            await page.close()
        except Exception as e:
            print(f"[ERROR] {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
