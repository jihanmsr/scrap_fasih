import asyncio
import os
from playwright.async_api import async_playwright

USER_DATA_DIR = "playwright_chrome_profile"

async def main():
    async with async_playwright() as p:
        abs_user_data_dir = os.path.abspath(USER_DATA_DIR)
        chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        
        print("Launching browser with user profile...")
        context = await p.chromium.launch_persistent_context(
            user_data_dir=abs_user_data_dir,
            headless=True,
            executable_path=chrome_path,
            args=["--no-first-run", "--no-default-browser-check", "--disable-blink-features=AutomationControlled"]
        )
        
        page = context.pages[0] if context.pages else await context.new_page()
        
        print("Navigating to https://fasih-sm.bps.go.id/app/dashboard ...")
        await page.goto("https://fasih-sm.bps.go.id/app/dashboard", timeout=30000)
        await page.wait_for_load_state("networkidle")
        
        print(f"Current URL: {page.url}")
        
        # Search for buttons, links, or texts related to "download", "csv", "export", etc.
        html = await page.content()
        print("\nSearching for download buttons...")
        
        buttons = await page.query_selector_all("button")
        for idx, btn in enumerate(buttons):
            text = await btn.inner_text()
            outer = await btn.evaluate("el => el.outerHTML")
            if any(x in text.lower() or x in outer.lower() for x in ["download", "csv", "export", "unduh"]):
                print(f"Button {idx}: Text='{text}', HTML='{outer}'")
                
        links = await page.query_selector_all("a")
        for idx, a in enumerate(links):
            text = await a.inner_text()
            outer = await a.evaluate("el => el.outerHTML")
            if any(x in text.lower() or x in outer.lower() for x in ["download", "csv", "export", "unduh"]):
                print(f"Link {idx}: Text='{text}', HTML='{outer}'")
                
        await context.close()

if __name__ == "__main__":
    asyncio.run(main())
