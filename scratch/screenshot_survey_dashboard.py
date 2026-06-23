import asyncio
import os
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        print("Connecting to Chrome on port 9222...")
        try:
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
            context = browser.contexts[0]
            page = None
            for p_page in context.pages:
                if "fasih-sm.bps.go.id" in p_page.url:
                    page = p_page
                    break
            
            if not page:
                print("No active BPS page found.")
                return
            
            print(f"Current page URL: {page.url}")
            # Wait for some elements to load or wait a few seconds
            await page.wait_for_timeout(3000)
            
            screenshot_path = "/Users/jihanmaisaroh/.gemini/antigravity-ide/brain/1a24ac2a-c5ea-4fc1-a239-82c17f1356f0/bps_dashboard_screenshot.png"
            await page.screenshot(path=screenshot_path)
            print(f"Screenshot saved to {screenshot_path}")
            # Note: Do NOT close browser/page to keep the session alive!
        except Exception as e:
            print("Error:", e)

if __name__ == "__main__":
    asyncio.run(main())
