import asyncio
from playwright.async_api import async_playwright
import json

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0]
        
        # Find active fasih page
        page = None
        for pg in context.pages:
            if "fasih-sm.bps.go.id" in pg.url:
                page = pg
                break
        
        if not page:
            print("No active fasih-sm.bps.go.id tab found. Creating new tab...")
            page = await context.new_page()
            await page.goto("https://fasih-sm.bps.go.id/app/dashboard")

        cookies = await context.cookies("https://fasih-sm.bps.go.id")
        token = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), None)
        from urllib.parse import unquote
        token = unquote(token) if token else ""
        
        url = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode"
        
        # Sensus Ekonomi UB
        payload = {
            "start": 0,
            "length": 5,
            "columns": [{"data": "id"}],
            "order": [],
            "search": {"value": "", "regex": False},
            "assignmentExtraParam": {
                "surveyPeriodId": "37526b20-81c8-42f5-a895-6190137d7394",
                "assignmentErrorStatusType": -1
            }
        }
        
        res = await page.evaluate("""
            async ({url, payload, token}) => {
                const r = await fetch(url, { 
                    method: "POST",
                    headers: { 
                        "Content-Type": "application/json",
                        "X-XSRF-TOKEN": token
                    },
                    body: JSON.stringify(payload)
                });
                return await r.json();
            }
        """, {"url": url, "payload": payload, "token": token})
        
        search_data = res.get("searchData", [])
        if search_data:
            print("First row fields:")
            print(json.dumps(search_data[0], indent=2))
        else:
            print("No searchData found. Response:")
            print(json.dumps(res, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
