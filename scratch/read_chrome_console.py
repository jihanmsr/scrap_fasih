import asyncio
import os
import sys
from playwright.async_api import async_playwright

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scrape_granular_core import get_authenticated_context

async def main():
    async with async_playwright() as p:
        print("Connecting to browser...")
        browser, context, page = await get_authenticated_context(p)
        if not page:
            print("Failed to connect.")
            return
            
        print("Active Page URL:", page.url)
        
        console_messages = []
        page.on("console", lambda msg: console_messages.append(f"[{msg.type.upper()}] {msg.text}"))
        page.on("pageerror", lambda err: console_messages.append(f"[EXCEPTION] {err.message}"))
        
        print("Reloading page and listening for console logs...")
        await page.reload()
        await asyncio.sleep(8)
        
        print("\n--- CONSOLE LOGS ---")
        for msg in console_messages:
            print(msg)
        print("--------------------")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
