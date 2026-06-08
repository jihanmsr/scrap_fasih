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
        
        # Test 1: Total records for Banggai Kepulauan (bc32354f-1245-426f-b2cf-a5733e1295ad)
        payload1 = {
            "start": 0,
            "length": 1,
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
        
        res1 = await page.evaluate("""
            async ({url, payload, token}) => {
                try {
                    const r = await fetch(url, {
                        method: "POST",
                        headers: { "Content-Type": "application/json", "X-XSRF-TOKEN": token },
                        body: JSON.stringify(payload)
                    });
                    return await r.json();
                } catch (e) {
                    return { error: e.toString() };
                }
            }
        """, {"url": datatable_url, "payload": payload1, "token": token})
        
        print("\nTest 1 (Total records in Banggai Kepulauan) totalHit:", res1.get("totalHit"))
        
        # Test 2: Filter by assignmentStatusAlias = SUBMITTED RESPONDENT
        payload2 = {
            "start": 0,
            "length": 1,
            "columns": [
                {"data": "id", "searchable": True, "orderable": True, "search": {"value": "", "regex": False}},
                {"data": "assignmentStatusAlias", "searchable": True, "orderable": True, "search": {"value": "SUBMITTED RESPONDENT", "regex": False}}
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
        
        res2 = await page.evaluate("""
            async ({url, payload, token}) => {
                try {
                    const r = await fetch(url, {
                        method: "POST",
                        headers: { "Content-Type": "application/json", "X-XSRF-TOKEN": token },
                        body: JSON.stringify(payload)
                    });
                    return await r.json();
                } catch (e) {
                    return { error: e.toString() };
                }
            }
        """, {"url": datatable_url, "payload": payload2, "token": token})
        
        print("Test 2 (SUBMITTED RESPONDENT in Banggai Kepulauan) totalHit:", res2.get("totalHit"))

        # Test 3: Filter by statusId in assignmentExtraParam?
        # Let's check if we can pass "statusId" or "assignmentStatusId" in assignmentExtraParam or in top-level payload.
        # Often BPS has assignmentStatusId filter in assignmentExtraParam.
        payload3 = {
            "start": 0,
            "length": 1,
            "columns": [
                {"data": "id", "searchable": True, "orderable": True, "search": {"value": "", "regex": False}}
            ],
            "order": [],
            "search": {"value": "", "regex": False},
            "assignmentExtraParam": {
                "region1Id": "5214ecb2-bef1-4a86-9446-451cf430928e",
                "region2Id": "bc32354f-1245-426f-b2cf-a5733e1295ad",
                "surveyPeriodId": period_id,
                "assignmentStatusId": 5, # Usually 5 is submitted respondent
                "assignmentErrorStatusType": -1,
                "filterTargetType": ""
            }
        }
        
        res3 = await page.evaluate("""
            async ({url, payload, token}) => {
                try {
                    const r = await fetch(url, {
                        method: "POST",
                        headers: { "Content-Type": "application/json", "X-XSRF-TOKEN": token },
                        body: JSON.stringify(payload)
                    });
                    return await r.json();
                } catch (e) {
                    return { error: e.toString() };
                }
            }
        """, {"url": datatable_url, "payload": payload3, "token": token})
        
        print("Test 3 (assignmentStatusId: 5 in extra param) totalHit:", res3.get("totalHit"))

if __name__ == "__main__":
    asyncio.run(main())
