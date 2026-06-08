import asyncio
from playwright.async_api import async_playwright
import json

async def main():
    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
            print("Connected to Chrome.")
        except Exception as e:
            print("Failed to connect to Chrome:", e)
            return

        context = browser.contexts[0]
        page = None
        for pg in context.pages:
            if "fasih-sm.bps.go.id" in pg.url:
                page = pg
                break

        if not page:
            print("Active FASIH tab not found. Creating a new one...")
            page = await context.new_page()
            await page.goto("https://fasih-sm.bps.go.id/app/surveys/ecddb52e-f392-403c-a963-47391f217010/37526b20-81c8-42f5-a895-6190137d7394/data", wait_until="networkidle")

        print(f"Monitoring network on tab: {page.url}")

        async def handle_response(response):
            url = response.url
            if "api" in url:
                print(f"\n[API Response] {response.status} {response.request.method} {url}")
                try:
                    # Only print text/json responses
                    content_type = response.headers.get("content-type", "")
                    if "application/json" in content_type:
                        text = await response.text()
                        print(f"Response (truncated): {text[:500]}")
                        # Also print request payload if POST
                        if response.request.method == "POST":
                            print(f"Request Payload: {response.request.post_data}")
                except Exception as e:
                    print(f"Error reading response content: {e}")

        page.on("response", handle_response)

        print("Reloading page to capture initial API calls...")
        try:
            await page.reload(wait_until="domcontentloaded", timeout=30000)
        except Exception as e:
            print("Reload timeout/warning:", e)

        print("Press Ctrl+C to stop monitoring after capturing requests.")
        # Keep running to capture clicks/interactions
        try:
            await asyncio.sleep(60)
        except KeyboardInterrupt:
            pass

if __name__ == "__main__":
    asyncio.run(main())
