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

        context = browser.contexts[0]
        page = context.pages[0] if context.pages else await context.new_page()
        
        # Go to the SENSUS EKONOMI 2026 dashboard
        target_url = "https://fasih-sm.bps.go.id/app/surveys/a0429e96-51a5-477b-a415-485f9c153004/fd68e454-ba45-4b85-8205-f3bf777ded24/dashboard"
        print(f"Navigating to: {target_url}")
        
        await page.goto(target_url, wait_until="networkidle", timeout=60000)
        print("Page loaded. Waiting 10 seconds for any dynamic charts...")
        await asyncio.sleep(10)
        
        # Take a screenshot
        screenshot_path = "scratch/dashboard.png"
        await page.screenshot(path=screenshot_path)
        print(f"Screenshot saved to {screenshot_path}")
        
        # Print some info about the DOM
        title = await page.title()
        print("Page title:", title)
        
        # Check if there is an iframe or charts
        charts = await page.locator("canvas, svg, .chart, .card").count()
        print(f"Found {charts} potential chart/card elements.")
        
        # Print text of the page
        text = await page.evaluate("() => document.body.innerText")
        print("\nPage text preview (first 1000 chars):")
        print(text[:1000])

if __name__ == "__main__":
    asyncio.run(main())
