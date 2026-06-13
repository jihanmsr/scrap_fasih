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
        
        # We want to check users and see if any parameter expands the regions array
        # Let's test different parameter names
        params_to_test = [
            "",
            "&regionSize=100",
            "&regionSize=1000",
            "&regionLimit=100",
            "&limitRegion=100",
            "&region_size=100",
            "&sizeRegion=100"
        ]
        
        for param in params_to_test:
            url = f"https://fasih-sm.bps.go.id/app/api/survey-user/api/v1/allocations-view/by-user?surveyPeriodId={survey_period_id}&surveyRoleId={pencacah_id}&page=0&size=10&regionCode=7207{param}"
            res = await page.evaluate(f"fetch('{url}', {{ headers: {{ 'Accept': 'application/json', 'X-XSRF-TOKEN': '{token}' }} }}).then(r => r.json())")
            content = res.get("data", {}).get("content", [])
            
            # Find the first user who has totalRegions > 5
            target_user = None
            for u in content:
                if u.get("totalRegions", 0) > 5:
                    target_user = u
                    break
            
            if target_user:
                print(f"Param '{param}': email={target_user.get('email')}, totalRegions={target_user.get('totalRegions')}, arrayLen={len(target_user.get('regions', []))}")
            else:
                print(f"Param '{param}': No user with totalRegions > 5 found in the first 10 users.")

asyncio.run(run())
