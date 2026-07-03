import asyncio
import os
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        user_data_dir = os.path.abspath("playwright_chrome_profile_w2")
        chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        
        context = await p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=True,
            executable_path=chrome_path,
            ignore_default_args=["--enable-automation"],
            args=["--no-first-run", "--no-default-browser-check", "--disable-blink-features=AutomationControlled"]
        )
        
        page = context.pages[0] if context.pages else await context.new_page()
        print("Navigating to surveys page...")
        await page.goto("https://fasih-sm.bps.go.id/app/surveys", wait_until="networkidle", timeout=30000)
        await asyncio.sleep(3)
        
        print("URL after navigation:", page.url)
        body_text = await page.inner_text("body")
        print("Page Title:", await page.title())
        print("Snippet:")
        print(body_text[:1000])
        
        # Take a screenshot
        screenshot_path = "/Users/jihanmaisaroh/.gemini/antigravity-ide/brain/579d006d-43f3-4a82-8007-72c554af05e3/surveys_page.png"
        await page.screenshot(path=screenshot_path)
        print("Screenshot saved.")
        
        await context.close()

if __name__ == "__main__":
    asyncio.run(main())
