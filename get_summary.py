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
            except Exception:
                pass
        if not browser: return
        context = browser.contexts[0]
        page = None
        for p_page in context.pages:
            if "fasih-sm.bps.go.id" in p_page.url:
                page = p_page
                break
        if not page: return
        
        cookies = await context.cookies()
        token = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), None)
        from urllib.parse import unquote
        if token: token = unquote(token)
        
        survey_period_id = "fd68e454-ba45-4b85-8205-f3bf777ded24"
        pencacah_id = "6d7d919a-45e5-4779-bb87-2905b49fd31a"
        pengawas_id = "93bcf446-c4c1-4462-8ed0-4b0f7ae89e52"
        
        url_p = f"https://fasih-sm.bps.go.id/app/api/survey-user/api/v1/allocations-view/summary?surveyPeriodId={survey_period_id}&surveyRoleId={pencacah_id}"
        res_p = await page.evaluate(f"fetch('{url_p}', {{ headers: {{ 'Accept': 'application/json', 'X-XSRF-TOKEN': '{token}' }} }}).then(r => r.json())")
        
        url_w = f"https://fasih-sm.bps.go.id/app/api/survey-user/api/v1/allocations-view/summary?surveyPeriodId={survey_period_id}&surveyRoleId={pengawas_id}"
        res_w = await page.evaluate(f"fetch('{url_w}', {{ headers: {{ 'Accept': 'application/json', 'X-XSRF-TOKEN': '{token}' }} }}).then(r => r.json())")
        
        print("Pencacah Summary:", res_p)
        print("Pengawas Summary:", res_w)

asyncio.run(run())
