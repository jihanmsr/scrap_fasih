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
        await asyncio.sleep(4)
        
        screenshot_path = "/Users/jihanmaisaroh/scrap_fasih/scratch/full_page_load_verify.png"
        await local_page.screenshot(path=screenshot_path, full_page=True)
        print(f"Full page screenshot saved to {screenshot_path}")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
