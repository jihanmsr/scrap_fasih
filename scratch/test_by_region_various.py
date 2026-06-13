import asyncio
import json
from playwright.async_api import async_playwright
from urllib.parse import unquote

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9223")
        context = browser.contexts[0]
        page = context.pages[1]
        
        cookies = await context.cookies()
        token = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), None)
        if token: token = unquote(token)
        
        survey_period_id = "fd68e454-ba45-4b85-8205-f3bf777ded24"
        pencacah_id = "6d7d919a-45e5-4779-bb87-2905b49fd31a"
        pengawas_id = "93bcf446-c4c1-4462-8ed0-4b0f7ae89e52"
        
        # We will try various combinations of query parameters for by-region
        tests = [
            # 1. basic
            f"https://fasih-sm.bps.go.id/app/api/survey-user/api/v1/allocations-view/by-region?surveyPeriodId={survey_period_id}&surveyRoleId={pengawas_id}&page=0&size=5",
            # 2. with regionCode and level=2
            f"https://fasih-sm.bps.go.id/app/api/survey-user/api/v1/allocations-view/by-region?surveyPeriodId={survey_period_id}&surveyRoleId={pengawas_id}&page=0&size=5&regionCode=7207&level=2",
            # 3. without surveyRoleId?
            f"https://fasih-sm.bps.go.id/app/api/survey-user/api/v1/allocations-view/by-region?surveyPeriodId={survey_period_id}&page=0&size=5&regionCode=7207&level=2",
            # 4. with different level?
            f"https://fasih-sm.bps.go.id/app/api/survey-user/api/v1/allocations-view/by-region?surveyPeriodId={survey_period_id}&surveyRoleId={pengawas_id}&page=0&size=5&regionCode=7207&level=6",
        ]
        
        for idx, url in enumerate(tests):
            try:
                res = await page.evaluate(f"fetch('{url}', {{ headers: {{ 'Accept': 'application/json', 'X-XSRF-TOKEN': '{token}' }} }}).then(r => r.json())")
                print(f"Test {idx+1}: success={res.get('success')}, keys={list(res.get('data', {}).keys()) if res.get('success') else 'error'}")
                if res.get("success"):
                    print(f"  First item: {res.get('data', {}).get('content', [])[:1]}")
            except Exception as e:
                print(f"Test {idx+1} raised exception: {e}")

asyncio.run(run())
