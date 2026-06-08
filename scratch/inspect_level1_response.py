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
        
        cookies = await context.cookies()
        token = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), None)
        if not token:
            print("XSRF-TOKEN not found.")
            return
            
        from urllib.parse import unquote
        token = unquote(token)
        
        group_id = "a45adac1-e711-4c15-b3f9-1f30fc151565" # SENSUS EKONOMI 2026 region group ID
        
        url = f"https://fasih-sm.bps.go.id/app/api/region/api/v1/region/custom-by-smallest-code-and-level?groupId={group_id}&smallestLevelFullCode=72&level=1"
        res = await page.evaluate("""
            async ({url, token}) => {
                const r = await fetch(url, { headers: { "X-XSRF-TOKEN": token } });
                return await r.json();
            }
        """, {"url": url, "token": token})
        
        print(json.dumps(res, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
