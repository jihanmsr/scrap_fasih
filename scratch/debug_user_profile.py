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
        await page.goto("https://fasih-sm.bps.go.id/app/dashboard", wait_until="networkidle", timeout=30000)
        await asyncio.sleep(3)
        
        # Get username/fullname if visible in the navbar/page
        body_text = await page.inner_text("body")
        print("Page text content snippet (first 1000 chars):")
        print(body_text[:1000])
        
        await context.close()

if __name__ == "__main__":
    asyncio.run(main())
