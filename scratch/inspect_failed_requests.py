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
        
        failed_requests = []
        page.on("requestfailed", lambda req: failed_requests.append(f"[FAILED] {req.method} {req.url} -> {req.failure.error_text if req.failure else 'unknown error'}"))
        
        async def handle_resp(res):
            if "analytic" in res.url or "assignment" in res.url:
                try:
                    text = await res.text()
                    print(f"[RESP] Status={res.status} URL={res.url} BodySample={text[:200]}")
                except Exception as e:
                    print(f"[RESP] Status={res.status} URL={res.url} (Failed to read body: {e})")
                    
        page.on("response", lambda res: asyncio.create_task(handle_resp(res)))
        
        print("Reloading page with wait_until='commit'...")
        try:
            await page.reload(wait_until="commit")
            print("Page reload triggered. Waiting 10 seconds for initial network settles...")
            await asyncio.sleep(10)
        except Exception as e:
            print("Reload failed:", e)
            
        print("\n--- FAILED REQUESTS ---")
        for req in failed_requests:
            print(req)
        print("-----------------------")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
