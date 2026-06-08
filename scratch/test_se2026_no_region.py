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
        
        # Test 1: No regions
        payload1 = {
            "start": 0,
            "length": 1,
            "columns": [{"data": "id"}],
            "order": [],
            "search": {"value": "", "regex": False},
            "assignmentExtraParam": {
                "surveyPeriodId": period_id,
                "assignmentErrorStatusType": -1,
                "filterTargetType": ""
            }
        }
        
        res1 = await page.evaluate("""
            async ({url, payload, token}) => {
                try {
                    const r = await fetch(url, {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                            "X-XSRF-TOKEN": token
                        },
                        body: JSON.stringify(payload)
                    });
                    return await r.json();
                } catch (e) {
                    return { error: e.toString() };
                }
            }
        """, {"url": datatable_url, "payload": payload1, "token": token})
        print("Test 1 (No regions) totalHit:", res1.get("totalHit"), "error:", res1.get("error"))

        # Test 2: Only region1Id
        payload2 = {
            "start": 0,
            "length": 1,
            "columns": [{"data": "id"}],
            "order": [],
            "search": {"value": "", "regex": False},
            "assignmentExtraParam": {
                "region1Id": "a00c8aef-afc4-4d4f-b80d-789a15450ef9",
                "surveyPeriodId": period_id,
                "assignmentErrorStatusType": -1,
                "filterTargetType": ""
            }
        }
        
        res2 = await page.evaluate("""
            async ({url, payload, token}) => {
                try {
                    const r = await fetch(url, {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                            "X-XSRF-TOKEN": token
                        },
                        body: JSON.stringify(payload)
                    });
                    return await r.json();
                } catch (e) {
                    return { error: e.toString() };
                }
            }
        """, {"url": datatable_url, "payload": payload2, "token": token})
        print("Test 2 (Only region1Id) totalHit:", res2.get("totalHit"), "error:", res2.get("error"))

if __name__ == "__main__":
    asyncio.run(main())
