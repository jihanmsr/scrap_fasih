import asyncio
import json
from playwright.async_api import async_playwright
from urllib.parse import unquote

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9223")
        context = browser.contexts[0]
        page = None
        for p_page in context.pages:
            if "fasih-sm.bps.go.id" in p_page.url:
                page = p_page
                break
        if not page:
            print("Could not find fasih-sm page")
            return
            
        cookies = await context.cookies()
        token = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), None)
        if token: token = unquote(token)
        
        survey_period_id = "fd68e454-ba45-4b85-8205-f3bf777ded24"
        pencacah_id = "6d7d919a-45e5-4779-bb87-2905b49fd31a"
        user_id = "cb75b347-d56a-430e-8bdd-e64e37eb0be8" # 02lovelymore@gmail.com
        
        test_urls = [
            f"https://fasih-sm.bps.go.id/app/api/survey-user/api/v1/allocations-view/by-user/{user_id}",
            f"https://fasih-sm.bps.go.id/app/api/survey-user/api/v1/allocations-view/by-user/{user_id}/regions",
            f"https://fasih-sm.bps.go.id/app/api/survey-user/api/v1/allocations-view/regions?userId={user_id}&surveyPeriodId={survey_period_id}",
            f"https://fasih-sm.bps.go.id/app/api/survey-user/api/v1/allocations-view/by-user-id?userId={user_id}&surveyPeriodId={survey_period_id}",
            f"https://fasih-sm.bps.go.id/app/api/survey-user/api/v1/allocations-view/user-regions?userId={user_id}",
            f"https://fasih-sm.bps.go.id/app/api/survey-user/api/v1/allocations-view/by-user/detail?userId={user_id}",
            f"https://fasih-sm.bps.go.id/app/api/survey-user/api/v1/allocations-view/by-user?surveyPeriodId={survey_period_id}&surveyRoleId={pencacah_id}&userId={user_id}"
        ]
        
        for url in test_urls:
            try:
                res = await page.evaluate(f"fetch('{url}', {{ headers: {{ 'Accept': 'application/json', 'X-XSRF-TOKEN': '{token}' }} }}).then(r => r.json())")
                print(f"URL: {url}")
                print(f"  success: {res.get('success')}")
                if res.get("success"):
                    print(f"  data keys: {list(res.get('data', {}).keys()) if isinstance(res.get('data'), dict) else type(res.get('data'))}")
                    print(f"  data sample: {str(res.get('data'))[:200]}")
            except Exception as e:
                print(f"URL: {url} failed with {e}")

asyncio.run(run())
