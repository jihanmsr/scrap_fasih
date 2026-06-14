import asyncio
from playwright.async_api import async_playwright
import json

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9223")
        context = browser.contexts[0]
        page = context.pages[0]
        
        captured = []
        async def handle_response(response):
            try:
                url = response.url
                if "api" in url:
                    try:
                        text = await response.text()
                        captured.append({
                            "url": url,
                            "status": response.status,
                            "response": text[:1000] # truncate response text
                        })
                    except Exception:
                        captured.append({
                            "url": url,
                            "status": response.status,
                            "response": "Could not read response text"
                        })
            except Exception as e:
                pass
                
        page.on("response", handle_response)
        
        print("Reloading page...")
        await page.reload(wait_until="domcontentloaded")
        await asyncio.sleep(8) # wait for all APIs to load
        
        print("\n=== CAPTURED API RESPONSES ===")
        for item in captured:
            print(f"URL: {item['url']} (Status: {item['status']})")
            print(f"Response: {item['response']}\n")
            
        with open("scratch/page_apis_log.json", "w") as f:
            json.dump(captured, f, indent=2)

asyncio.run(run())
