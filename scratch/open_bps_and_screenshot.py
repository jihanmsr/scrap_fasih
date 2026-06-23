import asyncio
import os
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        print("Connecting to Chrome on port 9222...")
        try:
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
            context = browser.contexts[0]
            
            # Find or create BPS page
            page = None
            for p_page in context.pages:
                if "fasih-sm.bps.go.id" in p_page.url:
                    page = p_page
                    break
            
            if not page:
                print("Opening new page for FASIH...")
                page = await context.new_page()
                
            survey_detail_url = "https://fasih-sm.bps.go.id/app/surveys/a0429e96-51a5-477b-a415-485f9c153004/fd68e454-ba45-4b85-8205-f3bf777ded24"
            print(f"Navigating to {survey_detail_url}...")
            await page.goto(survey_detail_url, timeout=60000, wait_until="domcontentloaded")
            
            print("Waiting 8 seconds for dashboard to render...")
            await page.wait_for_timeout(8000)
            
            print(f"Current page URL: {page.url}")
            screenshot_path = "/Users/jihanmaisaroh/.gemini/antigravity-ide/brain/1a24ac2a-c5ea-4fc1-a239-82c17f1356f0/bps_dashboard_screenshot.png"
            await page.screenshot(path=screenshot_path)
            print(f"Screenshot saved to {screenshot_path}")
            
        except Exception as e:
            print("Error:", e)

if __name__ == "__main__":
    asyncio.run(main())
