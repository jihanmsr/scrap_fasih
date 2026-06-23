import asyncio
import os
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        print("Connecting to Chrome on port 9222...")
        try:
            browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
            context = browser.contexts[0]
            print(f"Total open pages: {len(context.pages)}")
            
            for idx, page in enumerate(context.pages):
                url = page.url
                title = await page.title()
                print(f"Tab {idx}: Title='{title}' | URL='{url}'")
                
                # Take screenshot of any BPS or local dashboard tabs
                if "fasih-sm.bps.go.id" in url or "index.html" in url:
                    screenshot_name = f"tab_{idx}_{url.replace('://', '_').replace('/', '_')[:50]}.png"
                    screenshot_path = f"/Users/jihanmaisaroh/.gemini/antigravity-ide/brain/1a24ac2a-c5ea-4fc1-a239-82c17f1356f0/{screenshot_name}"
                    await page.screenshot(path=screenshot_path)
                    print(f"  Saved screenshot: {screenshot_path}")
            
            await browser.close()
        except Exception as e:
            print("Error:", e)

if __name__ == "__main__":
    asyncio.run(main())
