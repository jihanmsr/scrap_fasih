import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp("http://localhost:9223")
            print("Connected successfully!")
            for i, context in enumerate(browser.contexts):
                print(f"Context {i}: {len(context.pages)} pages")
                for j, page in enumerate(context.pages):
                    print(f"  Page {j}: URL={page.url} Title={await page.title()}")
            await browser.close()
        except Exception as e:
            print("Error connecting:", e)

asyncio.run(main())
