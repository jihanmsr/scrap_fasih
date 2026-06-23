import asyncio
from playwright.async_api import async_playwright
import os

async def main():
    async with async_playwright() as p:
        try:
            print("Connecting to Chrome on port 9222...")
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
            context = browser.contexts[0]
            print(f"Total pages: {len(context.pages)}")
            page = context.pages[0]
            print(f"Active URL: {page.url}")
            screenshot_path = "/Users/jihanmaisaroh/.gemini/antigravity-ide/brain/1a24ac2a-c5ea-4fc1-a239-82c17f1356f0/chrome_login_check.png"
            await page.screenshot(path=screenshot_path)
            print(f"Screenshot saved to {screenshot_path}")
            await browser.close()
        except Exception as e:
            print("Error:", e)

if __name__ == "__main__":
    asyncio.run(main())
