import asyncio
import json
import os
import sys
from urllib.parse import unquote
from playwright.async_api import async_playwright

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scrape_granular_core import get_authenticated_context, check_session_valid

async def main():
    async with async_playwright() as p:
        print("Connecting to browser...")
        browser, context, page = await get_authenticated_context(p)
        
        if "fasih-sm.bps.go.id" not in page.url:
            print("Navigating to dashboard...")
            await page.goto("https://fasih-sm.bps.go.id/app/dashboard", timeout=60000)
            await asyncio.sleep(2)
            
        cookies = await context.cookies()
        token_raw = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), "")
        token = unquote(token_raw) if token_raw else ""
        
        is_valid = await check_session_valid(page, token)
        print("Session valid:", is_valid)
        if not is_valid:
            print("Session is not valid. Please make sure you are logged in.")
            return
            
        url = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/report-progress-assignment"
        payload = {
            "surveyPeriodId": "fd68e454-ba45-4b85-8205-f3bf777ded24", # SE Umum
            "assignmentStatusAlias": None,
            "assignmentErrorStatusType": -1,
            "data1": None, "data2": None, "data3": None, "data4": None, "data5": None,
            "data6": None, "data7": None, "data8": None, "data9": None, "data10": None,
            "regionId": "815d35b4-fc43-43b5-b2ff-afc30f187298", # Totikum Kecamatan ID
            "currentUserId": None,
            "userIdResponsibility": None
        }
        
        print("Fetching report-progress-assignment...")
        resp = await page.evaluate("""
            async ({url, payload, token}) => {
                const r = await fetch(url, {
                    method: "POST",
                    headers: { "Content-Type": "application/json", "X-XSRF-TOKEN": token },
                    body: JSON.stringify(payload)
                });
                const text = await r.text();
                try {
                    return JSON.parse(text);
                } catch(e) {
                    return { _error: text };
                }
            }
        """, {"url": url, "payload": payload, "token": token})
        
        if isinstance(resp, dict) and "_error" not in resp:
            print("Success:", resp.get("success"))
            data = resp.get("data", [])
            print("Data type:", type(data))
            if isinstance(data, list):
                print("Content count:", len(data))
                if data:
                    print("First item keys:", list(data[0].keys()))
                    print("First item sample:")
                    print(json.dumps(data[0], indent=2))
            else:
                print("Data is not a list:", data)
        else:
            print("Error response:", resp)

if __name__ == "__main__":
    asyncio.run(main())
