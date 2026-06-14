import asyncio
import json
from playwright.async_api import async_playwright
from urllib.parse import unquote

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9223")
        context = browser.contexts[0]
        page = context.pages[0]
        
        cookies = await context.cookies()
        token = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), None)
        if token: token = unquote(token)
        
        survey_period_id = "fd68e454-ba45-4b85-8205-f3bf777ded24"
        pengawas_id = "93bcf446-c4c1-4462-8ed0-4b0f7ae89e52"
        
        url = f"https://fasih-sm.bps.go.id/survey-user/api/v1/allocations-view/by-user?surveyRoleId={pengawas_id}&surveyPeriodId={survey_period_id}&page=0&size=10"
        res = await page.evaluate(f"fetch('{url}', {{ headers: {{ 'Accept': 'application/json', 'X-XSRF-TOKEN': '{token}' }} }}).then(r => r.json())")
        
        if res.get("success"):
            content = res.get("data", {}).get("content", [])
            user = next((u for u in content if u.get("email") == "082293jya@gmail.com"), None)
            if user:
                print(f"User 082293jya@gmail.com: totalRegions={user.get('totalRegions')}, arrayLen={len(user.get('regions', []))}")
                print("Regions list in API:")
                print(json.dumps(user.get("regions", []), indent=2))
            else:
                print("User 082293jya@gmail.com not found in first page")
        else:
            print("Error:", res)

asyncio.run(run())
