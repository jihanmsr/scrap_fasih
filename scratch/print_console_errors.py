import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        print("Connecting to Chrome on port 9222...")
        try:
            browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
            context = browser.contexts[0]
            page = context.pages[0] if context.pages else await context.new_page()
            
            # Listen to console
            page.on("console", lambda msg: print(f"[CONSOLE {msg.type}] {msg.text}"))
            page.on("pageerror", lambda err: print(f"[PAGE ERROR] {err.message}"))
            
            print("Reloading page...")
            await page.reload(timeout=15000)
            await asyncio.sleep(5)
            
            await browser.close()
        except Exception as e:
            print("Error:", e)

if __name__ == "__main__":
    asyncio.run(main())
