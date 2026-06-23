import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
            context = browser.contexts[0]
            print(f"Total pages: {len(context.pages)}")
            for idx, page in enumerate(context.pages):
                print(f"Page {idx}: {page.url}")
        except Exception as e:
            print("Error:", e)

if __name__ == "__main__":
    asyncio.run(main())
