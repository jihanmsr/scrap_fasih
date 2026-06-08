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
            print("FASIH page not found.")
            return

        await page.bring_to_front()

        captured = []

        async def handle_response(response):
            url = response.url
            if "api" in url:
                req = response.request
                post_data = req.post_data
                try:
                    content_type = response.headers.get("content-type", "")
                    if "application/json" in content_type:
                        text = await response.text()
                        try:
                            res_json = json.loads(text)
                        except:
                            res_json = text
                    else:
                        res_json = f"<non-json content-type: {content_type}>"
                except Exception as e:
                    res_json = f"<error reading response: {str(e)}>"
                
                captured.append({
                    "url": url,
                    "method": req.method,
                    "post_data": post_data,
                    "response": res_json
                })

        page.on("response", handle_response)

        print("Locating refresh button...")
        # Try to locate the refresh button next to Kolom / column options
        refresh_btn = None
        
        # Try finding button by SVG class or icon name
        locators = [
            page.locator("button svg.tabler-icon-refresh"),
            page.locator("button svg.tabler-icon-rotate-clockwise"),
            page.locator("button svg.tabler-icon-rotate"),
            page.locator("button").filter(has=page.locator("svg")),
        ]
        
        for loc in locators:
            if await loc.count() > 0:
                # Find the one closest to the layout/filter area if there are multiple
                for el in await loc.all():
                    # We can click it and see
                    refresh_btn = el
                    break
                if refresh_btn:
                    break
        
        if refresh_btn:
            print("Clicking refresh button...")
            await refresh_btn.click(force=True)
            print("Clicked! Waiting 5 seconds for network traffic...")
            await asyncio.sleep(5)
        else:
            print("Refresh button not found by icon. Trying to click 'Semua' filter button...")
            semua_btn = page.locator("button:has-text('Semua')")
            if await semua_btn.count() > 0:
                await semua_btn.click(force=True)
                print("Clicked 'Semua' button! Waiting 5 seconds...")
                await asyncio.sleep(5)
            else:
                print("Could not find refresh or 'Semua' button.")

        with open("scratch/captured_refresh.json", "w", encoding="utf-8") as f:
            json.dump(captured, f, indent=2, ensure_ascii=False)
        
        print(f"Done! Captured {len(captured)} requests. Results saved to scratch/captured_refresh.json")

if __name__ == "__main__":
    asyncio.run(main())
