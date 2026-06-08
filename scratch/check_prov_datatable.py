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
        
        # Test 1: region1Id = Sulawesi Tengah, region2Id = ""
        payload1 = {
            "start": 0,
            "length": 1,
            "columns": [{"data": "id"}],
            "order": [],
            "search": {"value": "", "regex": False},
            "assignmentExtraParam": {
                "region1Id": "a00c8aef-afc4-4d4f-b80d-789a15450ef9",
                "region2Id": "",
                "surveyPeriodId": "37526b20-81c8-42f5-a895-6190137d7394",
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
        
        print("\nTest 1 (region2Id = empty string) totalHit:", res1.get("totalHit"))
        
        # Test 2: region1Id = Sulawesi Tengah, region2Id omitted
        payload2 = {
            "start": 0,
            "length": 1,
            "columns": [{"data": "id"}],
            "order": [],
            "search": {"value": "", "regex": False},
            "assignmentExtraParam": {
                "region1Id": "a00c8aef-afc4-4d4f-b80d-789a15450ef9",
                "surveyPeriodId": "37526b20-81c8-42f5-a895-6190137d7394",
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
        
        print("Test 2 (region2Id omitted) totalHit:", res2.get("totalHit"))

        # Test 3: No region filters at all
        payload3 = {
            "start": 0,
            "length": 1,
            "columns": [{"data": "id"}],
            "order": [],
            "search": {"value": "", "regex": False},
            "assignmentExtraParam": {
                "surveyPeriodId": "37526b20-81c8-42f5-a895-6190137d7394",
                "assignmentErrorStatusType": -1,
                "filterTargetType": ""
            }
        }
        
        res3 = await page.evaluate("""
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
        """, {"url": datatable_url, "payload": payload3, "token": token})
        
        print("Test 3 (No region filters) totalHit:", res3.get("totalHit"))

if __name__ == "__main__":
    asyncio.run(main())
