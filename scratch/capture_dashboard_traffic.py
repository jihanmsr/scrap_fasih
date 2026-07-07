import asyncio
import os
import sys
from playwright.async_api import async_playwright

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scrape_granular_core import get_authenticated_context

async def main():
    async with async_playwright() as p:
        print("Connecting to browser...")
        browser, context, page = await get_authenticated_context(p)
        if not page:
            print("Failed to connect.")
            return
            
        print("Active Page URL:", page.url)
        
        # Listen to API requests on the page
        async def handle_request(req):
            if "report-progress-assignment" in req.url:
                print(f"[REQUEST] {req.url}")
                print(f"  Method: {req.method}")
                print(f"  Headers: {req.headers}")
                print(f"  PostData: {req.post_data}")
                
        async def handle_response(res):
            if "report-progress-assignment" in res.url:
                print(f"[RESPONSE] {res.url}")
                print(f"  Status: {res.status}")
                try:
                    text = await res.text()
                    print(f"  Text length: {len(text)}")
                    print(f"  Text sample: {text[:200]}")
                except Exception as e:
                    print(f"  Failed to get response text: {e}")
                    
        page.on("request", handle_request)
        page.on("response", handle_response)
        
        print("Triggering page reload to capture dashboard network traffic...")
        await page.reload()
        print("Waiting 15 seconds for dashboard to load...")
        await asyncio.sleep(15)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
