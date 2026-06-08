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
        page = context.pages[0] if context.pages else await context.new_page()
        
        await page.bring_to_front()
        
        # Dashboard URL instead of data URL
        target_url = "https://fasih-sm.bps.go.id/app/surveys/ecddb52e-f392-403c-a963-47391f217010/37526b20-81c8-42f5-a895-6190137d7394/dashboard"
        print(f"Navigating to: {target_url}")
        
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
        
        try:
            await page.goto(target_url, wait_until="domcontentloaded", timeout=40000)
            print("Navigation done. Waiting 15 seconds for dashboard to load and API capture...")
            await asyncio.sleep(15)
        except Exception as e:
            print("Navigation failed:", e)

        with open("scratch/captured_dashboard.json", "w", encoding="utf-8") as f:
            json.dump(captured, f, indent=2, ensure_ascii=False)
            
        print(f"Done! Captured {len(captured)} requests. Saved to scratch/captured_dashboard.json")

if __name__ == "__main__":
    asyncio.run(main())
