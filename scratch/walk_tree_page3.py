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
        if not page: return
        
        cookies = await context.cookies()
        token = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), None)
        if token: token = unquote(token)
        
        survey_period_id = "fd68e454-ba45-4b85-8205-f3bf777ded24"
        pengawas_id = "93bcf446-c4c1-4462-8ed0-4b0f7ae89e52"
        pencacah_id = "6d7d919a-45e5-4779-bb87-2905b49fd31a"
        
        # Query Buol
        url_buol = f"https://fasih-sm.bps.go.id/app/api/survey-user/api/v1/allocations-view/by-region/children?surveyPeriodId={survey_period_id}&surveyRoleId={pengawas_id}&level=2&regionCode=7207"
        res_buol = await page.evaluate(f"fetch('{url_buol}', {{ headers: {{ 'Accept': 'application/json', 'X-XSRF-TOKEN': '{token}' }} }}).then(r => r.json())")
        print("Buol children level 3 (Kecamatan):", len(res_buol.get("data", [])))

        # Query Banggai Laut
        url_balut = f"https://fasih-sm.bps.go.id/app/api/survey-user/api/v1/allocations-view/by-region/children?surveyPeriodId={survey_period_id}&surveyRoleId={pengawas_id}&level=2&regionCode=7211"
        res_balut = await page.evaluate(f"fetch('{url_balut}', {{ headers: {{ 'Accept': 'application/json', 'X-XSRF-TOKEN': '{token}' }} }}).then(r => r.json())")
        print("Balut children level 3 (Kecamatan):", len(res_balut.get("data", [])))

asyncio.run(run())
