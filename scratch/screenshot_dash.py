import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
            context = browser.contexts[0]
            page = await context.new_page()
            
            await page.goto("file:///Users/jihanmaisaroh/scrap_fasih/index.html")
            await asyncio.sleep(2)
            
            # Select Banggai Kepulauan
            await page.select_option('#se_umum-kab-filter', '[01] BANGGAI KEPULAUAN')
            await asyncio.sleep(1)
            
            await page.screenshot(path="local_dash_delta.png", full_page=True)
            print("Screenshot saved to local_dash_delta.png")
            
            await page.close()
            await browser.close()
        except Exception as e:
            print(f"Error: {e}")

asyncio.run(main())
