import asyncio
from playwright.async_api import async_playwright
import json
import time

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

        print("Reloading page...")
        try:
            # wait_until="commit" is fast and does not hang on websockets/long polls
            await page.reload(wait_until="commit", timeout=20000)
            print("Page reload initiated.")
        except Exception as e:
            print("Reload failed:", e)

        print("Waiting 10 seconds for API calls to settle...")
        await asyncio.sleep(10)

        with open("scratch/captured_apis.json", "w", encoding="utf-8") as f:
            json.dump(captured, f, indent=2, ensure_ascii=False)
        
        print(f"Done! Captured {len(captured)} requests. Results saved to scratch/captured_apis.json")

if __name__ == "__main__":
    asyncio.run(main())
