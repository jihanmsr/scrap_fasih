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
        if not page: return
        
        cookies = await context.cookies()
        token = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), None)
        if token: token = unquote(token)
        
        survey_period_id = "fd68e454-ba45-4b85-8205-f3bf777ded24"
        pengawas_id = "93bcf446-c4c1-4462-8ed0-4b0f7ae89e52"
        
        # Test different query parameter names to get child regions of 72
        params = [
            "parentCode=72",
            "parentId=72",
            "regionCode=72",
            "code=72",
            "id=72",
            "parent=72",
            "regionCodeParent=72"
        ]
        
        for param in params:
            url = f"https://fasih-sm.bps.go.id/app/api/survey-user/api/v1/allocations-view/by-region/children?surveyPeriodId={survey_period_id}&surveyRoleId={pengawas_id}&{param}"
            res = await page.evaluate(f"fetch('{url}', {{ headers: {{ 'Accept': 'application/json', 'X-XSRF-TOKEN': '{token}' }} }}).then(r => r.json())")
            data = res.get("data", [])
            print(f"Param '{param}': success={res.get('success')}, data length={len(data)}")
            if data:
                print(f"  First child: {data[0]}")

asyncio.run(run())
