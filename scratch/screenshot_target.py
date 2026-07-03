import asyncio
import os
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        user_data_dir = os.path.abspath("playwright_chrome_profile_w2")
        chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        
        print(f"Launching Chrome with profile: {user_data_dir}")
        context = await p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=True,
            executable_path=chrome_path,
            ignore_default_args=["--enable-automation"],
            args=["--no-first-run", "--no-default-browser-check", "--disable-blink-features=AutomationControlled"]
        )
        
        page = context.pages[0] if context.pages else await context.new_page()
        
        target_url = "https://fasih-sm.bps.go.id/app/assignment/fd68e454-ba45-4b85-8205-f3bf777ded24/1031ce1b-21e8-46c9-89c3-297a99896c4b"
        print(f"Navigating to {target_url}...")
        await page.goto(target_url, wait_until="networkidle", timeout=30000)
        await asyncio.sleep(5)
        
        print(f"Current Page URL: {page.url}")
        
        # Take a screenshot
        screenshot_path = "/Users/jihanmaisaroh/.gemini/antigravity-ide/brain/579d006d-43f3-4a82-8007-72c554af05e3/scratch_target_screenshot.png"
        await page.screenshot(path=screenshot_path)
        print(f"Screenshot saved to: {screenshot_path}")
        
        # Print page text content or title
        title = await page.title()
        print(f"Page Title: {title}")
        
        await context.close()

if __name__ == "__main__":
    asyncio.run(main())
