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
        
        # Test 1: with regionCode and level
        url1 = f"https://fasih-sm.bps.go.id/app/api/survey-user/api/v1/allocations-view/by-region?surveyPeriodId={survey_period_id}&surveyRoleId={pencacah_id}&page=0&size=5&regionCode=7207&level=2"
        res1 = await page.evaluate(f"fetch('{url1}', {{ headers: {{ 'Accept': 'application/json', 'X-XSRF-TOKEN': '{token}' }} }}).then(r => r.json())")
        print("Test 1 (with regionCode & level):", json.dumps(res1, indent=2)[:500])

        # Test 2: what about by-user with regionSize parameter?
        # In check_cap.py line 22, regionSize=100 was used. Let's try regionSize=2000!
        url2 = f"https://fasih-sm.bps.go.id/app/api/survey-user/api/v1/allocations-view/by-user?surveyPeriodId={survey_period_id}&surveyRoleId={pencacah_id}&page=0&size=500&regionCode=7207&regionSize=2000"
        res2 = await page.evaluate(f"fetch('{url2}', {{ headers: {{ 'Accept': 'application/json', 'X-XSRF-TOKEN': '{token}' }} }}).then(r => r.json())")
        if res2.get("success"):
            content = res2.get("data", {}).get("content", [])
            print(f"Test 2 (by-user with regionSize=2000): success! Users fetched: {len(content)}")
            if content:
                print(f"User 0: email={content[0].get('email')} regions count in array={len(content[0].get('regions', []))} totalRegions property={content[0].get('totalRegions')}")
        else:
            print("Test 2 failed:", json.dumps(res2, indent=2))

asyncio.run(run())
