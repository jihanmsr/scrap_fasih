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
                break
            except Exception:
                pass
        if not browser:
            print("Could not connect to Chrome")
            return
            
        context = browser.contexts[0]
        page = await context.new_page()
        try:
            await page.goto("https://fasih-sm.bps.go.id/app/dashboard", wait_until="domcontentloaded", timeout=15000)
        except Exception:
            pass
            
        cookies = await context.cookies()
        token = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), None)
        if token: token = unquote(token)
        
        survey_period_id = "fd68e454-ba45-4b85-8205-f3bf777ded24"
        pencacah_id = "6d7d919a-45e5-4779-bb87-2905b49fd31a"
        pengawas_id = "93bcf446-c4c1-4462-8ed0-4b0f7ae89e52"
        
        # Call by-user for Buol Pengawas
        url = f"https://fasih-sm.bps.go.id/app/api/survey-user/api/v1/allocations-view/by-user?surveyPeriodId={survey_period_id}&surveyRoleId={pengawas_id}&page=0&size=100&regionCode=7207"
        res = await page.evaluate(f"fetch('{url}', {{ headers: {{ 'Accept': 'application/json', 'X-XSRF-TOKEN': '{token}' }} }}).then(r => r.json())")
        
        print("Keys in response root:", res.keys())
        if "data" in res:
            print("Keys in 'data':", res["data"].keys())
            print("totalElements:", res["data"].get("totalElements"))
            print("totalPages:", res["data"].get("totalPages"))
            
            # Print first user structure
            content = res["data"].get("content", [])
            if content:
                print("\nKeys in first user object:")
                for k, v in content[0].items():
                    print(f"  {k} : {type(v)}")
        
        await page.close()

asyncio.run(run())
