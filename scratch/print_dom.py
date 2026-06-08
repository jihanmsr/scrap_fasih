import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
            print("Connected to Chrome.")
        except Exception as e:
            print("Failed to connect to Chrome:", e)
            return

        for i, c in enumerate(browser.contexts):
            print(f"Context {i} has {len(c.pages)} pages:")
            for j, pg in enumerate(c.pages):
                print(f"  Page {j}: {pg.url}")

if __name__ == "__main__":
    asyncio.run(main())
