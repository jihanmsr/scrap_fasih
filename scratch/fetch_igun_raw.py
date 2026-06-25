import asyncio
from playwright.async_api import async_playwright
from urllib.parse import unquote
import json
import sys
import os

# Add parent dir to path to import scrape_granular_core
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scrape_granular_core import get_authenticated_context

async def main():
    async with async_playwright() as p:
        browser, context, page = await get_authenticated_context(p)
        cookies = await context.cookies()
        token_raw = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), "")
        token = unquote(token_raw) if token_raw else ""
        
        url = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode"
        payload = {
            "start": 0,
            "length": 100,
            "columns": [
                {"data": "id"},
                {"data": "codeIdentity"},
                {"data": "data1"},
                {"data": "assignmentStatusAlias"},
                {"data": "currentUserUsername"},
                {"data": "currentUserFullname"},
                {"data": "dateCreated"},
                {"data": "dateModified"},
                {"data": "region"},
                {"data": "assignmentResponsibility"}
            ],
            "order": [],
            "search": {"value": "RUSLI GUNADI", "regex": False},
            "assignmentExtraParam": {
                "region1Id": "5214ecb2-bef1-4a86-9446-451cf430928e", # Sulteng
                "region2Id": "736c4c22-51d1-44be-8b2c-aa197d9459a4", # Tojo Una-Una (7209)
                "surveyPeriodId": "fd68e454-ba45-4b85-8205-f3bf777ded24", # SE Umum
                "assignmentErrorStatusType": -1,
                "filterTargetType": ""
            }
        }
        
        resp = await page.evaluate("""
            async ({url, payload, token}) => {
                const r = await fetch(url, {
                    method: "POST",
                    headers: { "Content-Type": "application/json", "X-XSRF-TOKEN": token },
                    body: JSON.stringify(payload)
                });
                if (!r.ok) return { _error: `HTTP ${r.status}` };
                return await r.json();
            }
        """, {"url": url, "payload": payload, "token": token})
        
        if resp and "searchData" in resp:
            data = resp["searchData"]
            print(f"Found {len(data)} records for RUSLI GUNADI.")
            if len(data) > 0:
                print(json.dumps(data[0], indent=2))
        else:
            print("Error or no data:", resp)
            
        if browser:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
