import asyncio
import json
from playwright.async_api import async_playwright
from urllib.parse import unquote

async def run():
    async with async_playwright() as p:
        browser = None
        for port in [9223, 9222]:
            try:
                browser = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
                print(f"Connected to port {port}")
                break
            except Exception:
                pass
        if not browser:
            print("Could not connect to Chrome")
            return
            
        context = browser.contexts[0]
        page = None
        for p_page in context.pages:
            if "fasih-sm.bps.go.id" in p_page.url:
                page = p_page
                break
        if not page:
            print("Could not find fasih-sm page")
            return
            
        cookies = await context.cookies()
        token = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), None)
        if token: token = unquote(token)
        
        survey_period_id = "fd68e454-ba45-4b85-8205-f3bf777ded24"
        pencacah_id = "6d7d919a-45e5-4779-bb87-2905b49fd31a"
        pengawas_id = "93bcf446-c4c1-4462-8ed0-4b0f7ae89e52"
        
        # Test 1: by-region for Buol (7207)
        url1 = f"https://fasih-sm.bps.go.id/app/api/survey-user/api/v1/allocations-view/by-region?surveyPeriodId={survey_period_id}&surveyRoleId={pengawas_id}&page=0&size=5&regionCode=7207&level=2"
        
        res = await page.evaluate(f"fetch('{url1}', {{ headers: {{ 'Accept': 'application/json', 'X-XSRF-TOKEN': '{token}' }} }}).then(r => r.json())")
        print("Response:", json.dumps(res, indent=2))

async def run_wrapper():
    try:
        await run()
    except Exception as e:
        print("Error:", e)

asyncio.run(run_wrapper())
