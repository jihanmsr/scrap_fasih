import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto("file:///Users/jihanmaisaroh/scrap_fasih/index.html")
        await asyncio.sleep(3)
        await page.screenshot(path="/Users/jihanmaisaroh/.gemini/antigravity-ide/brain/9cdd2a58-e61c-4dfc-9b4d-aebb1ef993e4/artifacts/sidebar_ui.png", full_page=True)
        await browser.close()
        print("Screenshot saved to artifacts/sidebar_ui.png")

if __name__ == "__main__":
    asyncio.run(main())
