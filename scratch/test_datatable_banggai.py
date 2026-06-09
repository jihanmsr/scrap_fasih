import asyncio
from playwright.async_api import async_playwright
import json

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else await context.new_page()

        cookies = await context.cookies()
        token = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), None)
        from urllib.parse import unquote
        token = unquote(token)
        
        url = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode"
        uuid_umum = "bc32354f-1245-426f-b2cf-a5733e1295ad" # Banggai Kepulauan Group 1
        
        payload_umum = {
            "start": 0, "length": 1, "columns": [{"data": "id"}], "order": [], "search": {"value": "", "regex": False},
            "assignmentExtraParam": {
                "surveyPeriodId": "fd68e454-ba45-4b85-8205-f3bf777ded24",
                "assignmentErrorStatusType": -1,
                "region2Id": uuid_umum
            }
        }
        res = await page.evaluate(f"""
            async () => {{
                try {{
                    const r = await fetch('{url}', {{ 
                        method: "POST", headers: {{ "Content-Type": "application/json", "X-XSRF-TOKEN": '{token}' }},
                        body: JSON.stringify({json.dumps(payload_umum)})
                    }});
                    return await r.json();
                }} catch (e) {{ return {{ error: e.toString() }}; }}
            }}
        """)
        
        print("Banggai Kep UMUM:", res.get("totalHit"), res.get("searchAggregation"))

if __name__ == "__main__":
    asyncio.run(main())
