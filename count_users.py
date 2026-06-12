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
        pencacah_id = "6d7d919a-45e5-4779-bb87-2905b49fd31a"
        
        page_idx = 0
        total_users = 0
        total_regions_in_users = 0
        unique_regions = set()
        
        while True:
            url = f"https://fasih-sm.bps.go.id/app/api/survey-user/api/v1/allocations-view/by-user?surveyPeriodId={survey_period_id}&surveyRoleId={pencacah_id}&page={page_idx}&size=500"
            res = await page.evaluate(f"fetch('{url}', {{ headers: {{ 'Accept': 'application/json', 'X-XSRF-TOKEN': '{token}' }} }}).then(r => r.json())")
            data = res.get("data", {})
            content = data.get("content", [])
            if not content: break
            
            total_users += len(content)
            for user in content:
                # user has 'totalRegions' and 'regions'
                total_regions_in_users += user.get("totalRegions", 0)
                for reg in user.get("regions", []):
                    unique_regions.add(reg.get("regionCode"))
            
            if data.get("isLast", True): break
            page_idx += 1
            
        print(f"Total Users fetched: {total_users}")
        print(f"Sum of totalRegions in users: {total_regions_in_users}")
        print(f"Unique regions extracted: {len(unique_regions)}")

asyncio.run(run())
