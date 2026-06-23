import asyncio
from playwright.async_api import async_playwright
import os

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        errors = []
        page.on("pageerror", lambda err: errors.append(f"Page Error: {err}"))
        page.on("console", lambda msg: errors.append(f"Console {msg.type}: {msg.text}"))
        
        await page.goto("file:///Users/jihanmaisaroh/scrap_fasih/index.html")
        await asyncio.sleep(2) # Let the javascript execute
        
        print("\n=== CONSOLE & PAGE ERRORS ===")
        for error in errors:
            print(error)
        print("=============================\n")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
