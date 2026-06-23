import asyncio
import json
import httpx
from playwright.async_api import async_playwright
from urllib.parse import unquote
from scrape_granular_core import get_authenticated_context

async def main():
    async with async_playwright() as p:
        browser, context, page = await get_authenticated_context(p)
        cookies = await context.cookies()
        token_raw = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), "")
        token = unquote(token_raw) if token_raw else ""
        
        period_id = "fd68e454-ba45-4b85-8205-f3bf777ded24" # SE Umum
        url = f"https://fasih-sm.bps.go.id/app/api/survey-user/api/v1/allocations-view/by-user?surveyPeriodId={period_id}&page=0&size=2"
        
        res = await page.evaluate("""
            async ({url, token}) => {
                const r = await fetch(url, {
                    headers: { "X-XSRF-TOKEN": token }
                });
                return await r.json();
            }
        """, {"url": url, "token": token})
        
        print("Keys of top-level response:", list(res.keys()))
        if "data" in res and "content" in res["data"] and res["data"]["content"]:
            sample_user = res["data"]["content"][0]
            print("\nKeys of user object:")
            for k, v in sample_user.items():
                if isinstance(v, (dict, list)):
                    print(f"  {k}: type {type(v)}, preview: {str(v)[:150]}")
                else:
                    print(f"  {k}: {v}")
        else:
            print("No users found or error:", res)
            
        if browser:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
