import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9223")
            context = browser.contexts[0]
            print(f"Total open tabs on port 9223: {len(context.pages)}")
            for idx, page in enumerate(context.pages):
                print(f"Tab {idx}: {page.url}")
        except Exception as e:
            print("Failed to connect to port 9223:", e)

if __name__ == "__main__":
    asyncio.run(main())
