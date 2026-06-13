import asyncio
import json
from playwright.async_api import async_playwright
from urllib.parse import unquote

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        context = browser.contexts[0]
        
        page = None
        for p_page in context.pages:
            if "/app/surveys/" in p_page.url:
                page = p_page
                break
        if not page:
            print("No surveys page found")
            return
            
        print(f"Connected to page: {page.url}")
        
        cookies = await context.cookies()
        token = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), None)
        if token: token = unquote(token)
        
        survey_period_id = "fd68e454-ba45-4b85-8205-f3bf777ded24"
        pencacah_id = "6d7d919a-45e5-4779-bb87-2905b49fd31a"
        pengawas_id = "93bcf446-c4c1-4462-8ed0-4b0f7ae89e52"
        
        # Query children for Pengawas
        url_w = f"https://fasih-sm.bps.go.id/app/api/survey-user/api/v1/allocations-view/by-region/children?surveyPeriodId={survey_period_id}&surveyRoleId={pengawas_id}&level=1&regionCode=72"
        res_w = await page.evaluate(f"fetch('{url_w}', {{ headers: {{ 'Accept': 'application/json', 'X-XSRF-TOKEN': '{token}' }} }}).then(r => r.json())")
        data_w = res_w.get("data", [])
        print(f"\n[Pengawas] Kabupatens count: {len(data_w)}")
        for item in data_w:
            print(f"  {item.get('regionCode')} - {item.get('regionName')} (userCount={item.get('userCount')})")
            
        # Query children for Pencacah
        url_p = f"https://fasih-sm.bps.go.id/app/api/survey-user/api/v1/allocations-view/by-region/children?surveyPeriodId={survey_period_id}&surveyRoleId={pencacah_id}&level=1&regionCode=72"
        res_p = await page.evaluate(f"fetch('{url_p}', {{ headers: {{ 'Accept': 'application/json', 'X-XSRF-TOKEN': '{token}' }} }}).then(r => r.json())")
        data_p = res_p.get("data", [])
        print(f"\n[Pencacah] Kabupatens count: {len(data_p)}")
        for item in data_p:
            print(f"  {item.get('regionCode')} - {item.get('regionName')} (userCount={item.get('userCount')})")

asyncio.run(run())
