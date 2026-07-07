import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        print("Connecting to browser...")
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        context = browser.contexts[0]
        
        local_page = next((pg for pg in context.pages if "index.html" in pg.url), None)
        if not local_page:
            local_page = await context.new_page()
            
        print("Disabling Chrome cache via CDP session...")
        cdp_session = await context.new_cdp_session(local_page)
        await cdp_session.send("Network.setCacheDisabled", {"cacheDisabled": True})
        
        print("Loading local index.html...")
        await local_page.goto("file:///Users/jihanmaisaroh/scrap_fasih/index.html")
        
        print("Waiting 15 seconds for Supabase fetch & render...")
        await asyncio.sleep(15)
        
        print("Explicitly switching to 'se_umum' tab...")
        await local_page.evaluate("window.switchTab('se_umum')")
        await asyncio.sleep(1)
        
        print("\n--- POPULATED PREMIUM CARD TEXTS ---")
        try:
            pct = await local_page.inner_text("#se_umum-stat-premium-pct")
            count = await local_page.inner_text("#se_umum-stat-premium-count")
            print(f"Premium Pct: {pct}")
            print(f"Premium Count: {count}")
        except Exception as e:
            print("Premium card error:", e)
            
        print("\n--- POPULATED COMPACT CARD TEXTS ---")
        try:
            prelist = await local_page.inner_text("#se_umum-stat-total-prelist")
            print(f"Total Target Prelist: {prelist}")
        except Exception as e:
            print("Prelist error:", e)
            
        print("\nTaking screenshot of local dashboard...")
        screenshot_path = "/Users/jihanmaisaroh/scrap_fasih/local_dashboard_verify.png"
        await local_page.screenshot(path=screenshot_path)
        print(f"Screenshot successfully saved to {screenshot_path}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
