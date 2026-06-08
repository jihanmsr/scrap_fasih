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
        
        # Fetch 20 records
        payload = {
            "start": 0,
            "length": 20,
            "columns": [
                {"data": "id", "searchable": True, "orderable": True, "search": {"value": "", "regex": False}},
                {"data": "assignmentStatusAlias", "searchable": True, "orderable": True, "search": {"value": "", "regex": False}}
            ],
            "order": [],
            "search": {"value": "", "regex": False},
            "assignmentExtraParam": {
                "region1Id": "5214ecb2-bef1-4a86-9446-451cf430928e",
                "region2Id": "bc32354f-1245-426f-b2cf-a5733e1295ad",
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
        
        print("Status aliases of the first 20 records:")
        if "searchData" in res:
            for idx, item in enumerate(res["searchData"]):
                print(f"[{idx}] id: {item.get('id')} | alias: {item.get('assignmentStatusAlias')} | id: {item.get('assignmentStatusId')}")
        else:
            print("Response:", res)

if __name__ == "__main__":
    asyncio.run(main())
