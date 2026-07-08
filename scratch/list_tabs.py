import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
            for i, context in enumerate(browser.contexts):
                print(f"Context {i}:")
                for page in context.pages:
                    print(f"  URL: {page.url}")
                    print(f"  Title: {await page.title()}")
            await browser.close()
        except Exception as e:
            print("Error connecting:", e)

if __name__ == "__main__":
    asyncio.run(main())
