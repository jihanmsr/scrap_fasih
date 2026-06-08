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
        
        datatable_url = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode"
        period_id = "fd68e454-ba45-4b85-8205-f3bf777ded24" # SE2026 PENDATAAN
        
        kab_id = "530e9ca5-86ba-434e-9b04-405102e6d900" # Banggai (7202)
        
        payload = {
            "start": 0, "length": 1, "columns": [{"data": "id"}], "order": [], "search": {"value": "", "regex": False},
            "assignmentExtraParam": {
                "region1Id": "5214ecb2-bef1-4a86-9446-451cf430928e",
                "region2Id": kab_id,
                "surveyPeriodId": period_id,
                "assignmentErrorStatusType": -1,
                "filterTargetType": ""
            }
        }
        
        res = await page.evaluate("""
            async ({url, payload, token}) => {
                const r = await fetch(url, {
                    method: "POST",
                    headers: { "Content-Type": "application/json", "X-XSRF-TOKEN": token },
                    body: JSON.stringify(payload)
                });
                return await r.json();
            }
        """, {"url": datatable_url, "payload": payload, "token": token})
        
        print("Banggai response:")
        print("totalHit:", res.get("totalHit"))
        print("searchAggregation:", res.get("searchAggregation"))

if __name__ == "__main__":
    asyncio.run(main())
