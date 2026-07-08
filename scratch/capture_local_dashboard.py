import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
            context = browser.contexts[0]
            # Find index.html page
            page = next((pg for pg in context.pages if "index.html" in pg.url), None)
            if page:
                print("Found local dashboard page.")
                print("URL:", page.url)
                # Take screenshot
                await page.screenshot(path="/Users/jihanmaisaroh/scrap_fasih/local_dashboard_screenshot.png")
                print("Screenshot saved to local_dashboard_screenshot.png")
                # Get text content of some key elements
                text = await page.inner_text("body")
                print("Body text snippet (first 1500 chars):")
                print(text[:1500])
            else:
                print("Local dashboard page not found.")
            await browser.close()
        except Exception as e:
            print("Error:", e)

if __name__ == "__main__":
    asyncio.run(main())
