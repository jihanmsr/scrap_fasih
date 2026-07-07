import asyncio
import os
import sys
from urllib.parse import unquote
from playwright.async_api import async_playwright

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scrape_granular_core import get_authenticated_context

async def main():
    async with async_playwright() as p:
        print("Connecting to browser...")
        browser, context, page = await get_authenticated_context(p)
        if not browser:
            print("Failed to connect.")
            return
            
        print("Active Page URL:", page.url)
        cookies = await context.cookies()
        print(f"Total cookies: {len(cookies)}")
        for c in cookies:
            if "xsrf" in c["name"].lower() or "session" in c["name"].lower() or "token" in c["name"].lower():
                print(f"  Cookie: {c['name']} = {c['value'][:20]}... (domain: {c['domain']})")
                
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
