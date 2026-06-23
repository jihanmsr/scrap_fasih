import asyncio
import os
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        print("Connecting to Chrome on port 9222...")
        try:
            browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
            context = browser.contexts[0]
            print(f"Total pages: {len(context.pages)}")
            page = None
            for p_page in context.pages:
                print(f"  Page URL: {p_page.url}")
                if "fasih-sm.bps.go.id" in p_page.url:
                    page = p_page
            
            if not page:
                print("No active BPS page found. Using context.pages[0]")
                page = context.pages[0] if context.pages else await context.new_page()
            
            print(f"Current page URL: {page.url}")
            screenshot_path = "/Users/jihanmaisaroh/.gemini/antigravity-ide/brain/1a24ac2a-c5ea-4fc1-a239-82c17f1356f0/chrome_state.png"
            await page.screenshot(path=screenshot_path)
            print(f"Screenshot saved to {screenshot_path}")
            await browser.close()
        except Exception as e:
            print("Error:", e)

if __name__ == "__main__":
    asyncio.run(main())
