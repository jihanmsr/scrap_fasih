import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        print("Connecting directly to port 9222...")
        try:
            browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
            print("Successfully connected!")
            context = browser.contexts[0]
            print("Pages:")
            for idx, pg in enumerate(context.pages):
                print(f"  Tab {idx}: {pg.url}")
            await browser.close()
        except Exception as e:
            print("Failed directly:", e)

if __name__ == "__main__":
    asyncio.run(main())
