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
            if "fasih-sm.bps.go.id" in p_page.url:
                page = p_page
                break
        if not page: 
            print("No page found")
            return
        
        print(f"Connected to page on port 9222: {page.url}")
        
        cookies = await context.cookies()
        token = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), None)
        if token: token = unquote(token)
        
        survey_period_id = "fd68e454-ba45-4b85-8205-f3bf777ded24"
        pengawas_id = "93bcf446-c4c1-4462-8ed0-4b0f7ae89e52"
        pencacah_id = "6d7d919a-45e5-4779-bb87-2905b49fd31a"
        
        # Let's get the children of level 1 (72) for Pengawas on port 9222
        url_l1 = f"https://fasih-sm.bps.go.id/app/api/survey-user/api/v1/allocations-view/by-region/children?surveyPeriodId={survey_period_id}&surveyRoleId={pengawas_id}&level=1&regionCode=72"
        res_l1 = await page.evaluate(f"fetch('{url_l1}', {{ headers: {{ 'Accept': 'application/json', 'X-XSRF-TOKEN': '{token}' }} }}).then(r => r.json())")
        data_l1 = res_l1.get("data", [])
        print(f"Level 2 children (Kabupatens) under SULAWESI TENGAH (72) for Pengawas on port 9222: count={len(data_l1)}")
        for item in data_l1:
            print(f"  {item.get('regionCode')} - {item.get('regionName')} (level={item.get('level')}, userCount={item.get('userCount')})")

asyncio.run(run())
