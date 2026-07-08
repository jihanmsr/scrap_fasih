import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        # open file
        await page.goto('file:///Users/jihanmaisaroh/scrap_fasih/index.html')
        await asyncio.sleep(1.5)
        
        # Select Banggai Kepulauan
        await page.select_option('#se_umum-kab-filter', '[01] BANGGAI KEPULAUAN')
        await asyncio.sleep(1)
        
        await page.screenshot(path='local_dash_filtered.png', full_page=True)
        await browser.close()
        print("Screenshot saved to local_dash_filtered.png")

asyncio.run(main())
