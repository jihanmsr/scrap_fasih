import asyncio
import httpx
from urllib.parse import unquote
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = None
        for port in [9223, 9222]:
            try:
                browser = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
                break
            except Exception: pass
        if not browser:
            print("Failed to connect to browser.")
            return
        
        context = browser.contexts[0]
        cookies = await context.cookies()
        token = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), None)
        if token:
            token = unquote(token)
        
        print(f"Found token: {token}")
        
        # Build cookies dictionary for httpx
        cookie_dict = {c["name"]: c["value"] for c in cookies}
        
        headers = {
            "Content-Type": "application/json",
            "X-XSRF-TOKEN": token,
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
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
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload_dt, headers=headers, cookies=cookie_dict, timeout=10.0)
                print(f"Status code: {response.status_code}")
                print("Response:", response.text[:200])
            except Exception as e:
                print("HTTP Request failed:", e)
        
        await browser.close()

asyncio.run(run())
