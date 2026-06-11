import asyncio
import json
import os
from playwright.async_api import async_playwright

USER_DATA_DIR = "playwright_chrome_profile"

async def test_api():
    async with async_playwright() as p:
        # Connect to port 9222 or 9223
        browser = None
        for port in [9223, 9222]:
            try:
                browser = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
                print(f"Connected to Chrome on port {port}")
                break
            except Exception as e:
                pass
        
        if not browser:
            print("Could not connect to Chrome on remote debugging ports 9222 or 9223")
            return
            
        context = browser.contexts[0]
        page = None
        for p_page in context.pages:
            if "fasih-sm.bps.go.id" in p_page.url:
                page = p_page
                break
        if not page:
            page = context.pages[0] if context.pages else await context.new_page()
            
        cookies = await context.cookies()
        token = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), None)
        if not token:
            print("XSRF-TOKEN not found in cookies")
            return
            
        from urllib.parse import unquote
        token = unquote(token)
        print("XSRF-TOKEN found:", token[:20] + "...")
        
        # Test REPORT_URL for one kab in UB
        # Survey period for UB: 37526b20-81c8-42f5-a895-6190137d7394
        # Region1 (Sulawesi Tengah): a00c8aef-afc4-4d4f-b80d-789a15450ef9
        # Donggala UB id: c075c4b4-7eb0-4d72-9c16-5103088fb5eb
        
        payload = {
            "surveyPeriodId": "37526b20-81c8-42f5-a895-6190137d7394",
            "region1Id": "a00c8aef-afc4-4d4f-b80d-789a15450ef9",
            "region2Id": "34165dd5-372e-42fa-99c6-0cc19a9b4d0b", # Banggai UB ID
        }
        
        url = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/report-user-assignment"
        res = await page.evaluate("""
            async ({url, payload, token}) => {
                const r = await fetch(url, {
                    method: "POST",
                    headers: { "Content-Type": "application/json", "X-XSRF-TOKEN": token },
                    body: JSON.stringify(payload)
                });
                return await r.json();
            }
        """, {"url": url, "payload": payload, "token": token})
        
        print("Banggai UB Report (first 5):")
        print(json.dumps(res[:5] if isinstance(res, list) else res, indent=2))
        
        # Let's also test DATATABLE_URL for UB
        url_dt = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode"
        payload_dt = {
            "start": 0, "length": 10, "columns": [{"data": "id"}], "order": [],
            "search": {"value": "", "regex": False},
            "assignmentExtraParam": {
                "region1Id": "a00c8aef-afc4-4d4f-b80d-789a15450ef9", 
                "surveyPeriodId": "37526b20-81c8-42f5-a895-6190137d7394", 
                "assignmentErrorStatusType": -1, 
                "filterTargetType": ""
            }
        }
        
        res_dt = await page.evaluate("""
            async ({url, payload, token}) => {
                const r = await fetch(url, {
                    method: "POST",
                    headers: { "Content-Type": "application/json", "X-XSRF-TOKEN": token },
                    body: JSON.stringify(payload)
                });
                return await r.json();
            }
        """, {"url": url_dt, "payload": payload_dt, "token": token})
        
        print("DATATABLE UB Sample Records:")
        if res_dt and "searchData" in res_dt:
            print(json.dumps(res_dt["searchData"][:2], indent=2))
        else:
            print(json.dumps(res_dt, indent=2))

asyncio.run(test_api())
