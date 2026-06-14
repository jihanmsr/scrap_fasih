import asyncio
import os
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Capture console logs
        page.on("console", lambda msg: print(f"CONSOLE {msg.type}: {msg.text}"))
        page.on("pageerror", lambda err: print(f"PAGE ERROR: {err}"))
        
        file_path = os.path.abspath("index.html")
        print(f"Opening file://{file_path}...")
        await page.goto(f"file://{file_path}")
        await page.wait_for_timeout(3000)
        
        print("Switching to assign tab...")
        await page.evaluate("window.switchTab('assign')")
        await page.wait_for_timeout(3000)
        
        # Check text in sync table body
        text = await page.inner_text("#sync-table-body")
        print(f"Sync table body content:\n{text}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
