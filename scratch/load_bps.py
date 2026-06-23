import asyncio
import os
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        print("Connecting to Chrome on port 9222...")
        try:
            browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
            context = browser.contexts[0]
            page = context.pages[0] if context.pages else await context.new_page()
            
            print("Navigating to BPS dashboard with 15s timeout...")
            try:
                await page.goto("https://fasih-sm.bps.go.id/app/dashboard", timeout=15000)
            except Exception as e:
                print("Navigation error/timeout:", e)
            
            print(f"Current page URL: {page.url}")
            screenshot_path = "/Users/jihanmaisaroh/.gemini/antigravity-ide/brain/1a24ac2a-c5ea-4fc1-a239-82c17f1356f0/chrome_state_after_load.png"
            await page.screenshot(path=screenshot_path)
            print(f"Screenshot saved to {screenshot_path}")
            await browser.close()
        except Exception as e:
            print("Error:", e)

if __name__ == "__main__":
    asyncio.run(main())
