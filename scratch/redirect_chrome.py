import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        try:
            print("Connecting to Chrome on port 9222...")
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
            context = browser.contexts[0]
            page = context.pages[0]
            print(f"Redirecting page from {page.url} to https://fasih-sm.bps.go.id/app/dashboard ...")
            await page.goto("https://fasih-sm.bps.go.id/app/dashboard")
            print("Navigation triggered successfully!")
            await browser.close()
        except Exception as e:
            print("Error:", e)

if __name__ == "__main__":
    asyncio.run(main())
