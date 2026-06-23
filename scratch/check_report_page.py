import asyncio
from playwright.async_api import async_playwright
import os

async def main():
    async with async_playwright() as p:
        try:
            print("Connecting to Chrome on port 9222...")
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
            print("Connected!")
            
            context = browser.contexts[0]
            print(f"Total contexts: {len(browser.contexts)}, Total pages: {len(context.pages)}")
            
            for idx, page in enumerate(context.pages):
                print(f"Page {idx}: URL='{page.url}' | Title='{page.title()}'")
                
                # Take screenshot to help debug if it's stuck on login screen
                screenshot_path = f"/Users/jihanmaisaroh/.gemini/antigravity-ide/brain/1a24ac2a-c5ea-4fc1-a239-82c17f1356f0/chrome_page_{idx}.png"
                await page.screenshot(path=screenshot_path)
                print(f"  Screenshot saved to {screenshot_path}")
                
            await browser.close()
        except Exception as e:
            print("Error connecting or executing:", e)

if __name__ == "__main__":
    asyncio.run(main())
