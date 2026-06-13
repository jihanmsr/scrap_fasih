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
        
        # Test summary endpoint for Buol Pengawas
        url_summary_pengawas = f"https://fasih-sm.bps.go.id/app/api/survey-user/api/v1/allocations-view/summary?surveyPeriodId={survey_period_id}&surveyRoleId={pengawas_id}&regionCode=7207&level=2"
        res_summary_pengawas = await page.evaluate(f"fetch('{url_summary_pengawas}', {{ headers: {{ 'X-XSRF-TOKEN': '{token}' }} }}).then(r => r.json())")
        print("Summary Pengawas Buol:", json.dumps(res_summary_pengawas, indent=2))
        
        # Test summary endpoint for Buol Pencacah
        url_summary_pencacah = f"https://fasih-sm.bps.go.id/app/api/survey-user/api/v1/allocations-view/summary?surveyPeriodId={survey_period_id}&surveyRoleId={pencacah_id}&regionCode=7207&level=2"
        res_summary_pencacah = await page.evaluate(f"fetch('{url_summary_pencacah}', {{ headers: {{ 'X-XSRF-TOKEN': '{token}' }} }}).then(r => r.json())")
        print("Summary Pencacah Buol:", json.dumps(res_summary_pencacah, indent=2))

asyncio.run(run())
