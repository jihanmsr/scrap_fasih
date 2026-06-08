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
        
        # Survey ID for SENSUS EKONOMI 2026
        se_survey_id = "a0429e96-51a5-477b-a415-485f9c153004"
        periods_url = f"https://fasih-sm.bps.go.id/app/api/survey/api/v1/survey-periods/my?surveyId={se_survey_id}"
        
        print("Querying survey periods for SENSUS EKONOMI 2026...")
        res_eval = await page.evaluate("""
            async ({url, token}) => {
                try {
                    const r = await fetch(url, {
                        headers: { "X-XSRF-TOKEN": token }
                    });
                    return await r.json();
                } catch (e) {
                    return { error: e.toString() };
                }
            }
        """, {"url": periods_url, "token": token})
        
        print("Survey Periods response:")
        print(json.dumps(res_eval, indent=2))
        
        if not res_eval.get("success") or not res_eval.get("data"):
            print("No periods found.")
            return
            
        # Try to call datatable for the first period found
        for period in res_eval["data"]:
            period_id = period["id"]
            period_name = period["name"]
            print(f"\nTesting period: {period_name} ({period_id})")
            
            datatable_url = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode"
            payload = {
                "start": 0,
                "length": 1,
                "columns": [{"data": "id"}],
                "order": [],
                "search": {"value": "", "regex": False},
                "assignmentExtraParam": {
                    "region1Id": "a00c8aef-afc4-4d4f-b80d-789a15450ef9",
                    "region2Id": "9c9b2d79-9fb1-4ce7-b0f1-6b7bb5511beb", # Banggai Kepulauan
                    "surveyPeriodId": period_id,
                    "assignmentErrorStatusType": -1,
                    "filterTargetType": ""
                }
            }
            
            res_dt = await page.evaluate("""
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
            """, {"url": datatable_url, "payload": payload, "token": token})
            
            print(f"Datatable response totalHit: {res_dt.get('totalHit')}")

if __name__ == "__main__":
    asyncio.run(main())
