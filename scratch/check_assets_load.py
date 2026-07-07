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
            
        failed_resources = []
        local_page.on("requestfailed", lambda req: failed_resources.append(f"Failed to load: {req.url} - Error: {req.failure.error_text if req.failure else 'unknown'}"))
        
        print("Loading local index.html...")
        await local_page.goto("file:///Users/jihanmaisaroh/scrap_fasih/index.html")
        await asyncio.sleep(3)
        
        print("\n--- FAILED RESOURCES ---")
        for res in failed_resources:
            print(res)
        print("------------------------")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
