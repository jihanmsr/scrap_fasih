import asyncio
import json
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = None
        for port in [9223, 9222]:
            try:
                browser = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
                break
            except Exception: pass
        if not browser: return
        context = browser.contexts[0]
        page = None
        for p_page in context.pages:
            if "fasih-sm.bps.go.id" in p_page.url: page = p_page; break
        if not page: return
        
        cookies = await context.cookies()
        token = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), None)
        from urllib.parse import unquote
        if token: token = unquote(token)
        
        survey_period_id = "fd68e454-ba45-4b85-8205-f3bf777ded24"
        region1_id = "5214ecb2-bef1-4a86-9446-451cf430928e"
        
        payload_dt = {
            "start": 0, "length": 2, "columns": [{"data": "id"}], "order": [],
            "search": {"value": "", "regex": False},
            "assignmentExtraParam": {
                "region1Id": region1_id, 
                "surveyPeriodId": survey_period_id, 
                "assignmentErrorStatusType": -1, 
                "filterTargetType": ""
            }
        }
        
        url = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode"
        res = await page.evaluate(f"""
            fetch('{url}', {{ 
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json', 'X-XSRF-TOKEN': '{token}' }},
                body: JSON.stringify({json.dumps(payload_dt)})
            }}).then(r => r.json())
        """)
        
        print(json.dumps(res, indent=2))

asyncio.run(run())
