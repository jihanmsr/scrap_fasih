import asyncio
import json
from playwright.async_api import async_playwright
from urllib.parse import unquote
from scrape_granular_core import get_authenticated_context

async def main():
    async with async_playwright() as p:
        browser, context, page = await get_authenticated_context(p)
        if "fasih-sm.bps.go.id" not in page.url:
            await page.goto("https://fasih-sm.bps.go.id/app/dashboard")
            await asyncio.sleep(2)
            
        cookies = await context.cookies()
        token_raw = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), "")
        token = unquote(token_raw) if token_raw else ""
        
        url = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/report-progress-by-responsibility"
        payload = {
            "surveyPeriodId": "fd68e454-ba45-4b85-8205-f3bf777ded24", # SE Umum
            "surveyRoleId": "6d7d919a-45e5-4779-bb87-2905b49fd31a", # Pencacah
            "size": 10,
            "page": 0,
            "search": "",
            "target": "ALL",
            "region": {
                "region1Id": "5214ecb2-bef1-4a86-9446-451cf430928e",
                "region2Id": None,
                "region3Id": None,
                "region4Id": None,
                "region5Id": None,
                "region6Id": None,
                "region7Id": None,
                "region8Id": None,
                "region9Id": None,
                "region10Id": None
            },
            "regionSummaryLevel": 6
        }
        
        resp = await page.evaluate("""
            async ({url, payload, token}) => {
                const r = await fetch(url, {
                    method: "POST",
                    headers: { "Content-Type": "application/json", "X-XSRF-TOKEN": token },
                    body: JSON.stringify(payload)
                });
                return await r.json();
            }
        """, {"url": url, "payload": payload, "token": token})
        
        print("Success:", resp.get("success"))
        print("Message:", resp.get("message"))
        data = resp.get("data", {})
        print("Data top-level keys:", list(data.keys()))
        for k, v in data.items():
            if k != "content":
                print(f"  {k}: {v}")
            else:
                print(f"  content length: {len(v)}")
                
        if browser:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
