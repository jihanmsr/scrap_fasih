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
        
        # 1. Call by-region for Buol Pengawas
        url_w = f"https://fasih-sm.bps.go.id/app/api/survey-user/api/v1/allocations-view/by-region?surveyPeriodId={survey_period_id}&surveyRoleId={pengawas_id}&page=0&size=10&regionCode=7207&level=2"
        res_w = await page.evaluate(f"fetch('{url_w}', {{ headers: {{ 'Accept': 'application/json', 'X-XSRF-TOKEN': '{token}' }} }}).then(r => r.json())")
        
        print("Pengawas by-region:")
        print("  totalElements:", res_w.get("data", {}).get("totalElements"))
        print("  totalPages:", res_w.get("data", {}).get("totalPages"))
        
        # 2. Call by-region for Buol Pencacah
        url_p = f"https://fasih-sm.bps.go.id/app/api/survey-user/api/v1/allocations-view/by-region?surveyPeriodId={survey_period_id}&surveyRoleId={pencacah_id}&page=0&size=10&regionCode=7207&level=2"
        res_p = await page.evaluate(f"fetch('{url_p}', {{ headers: {{ 'Accept': 'application/json', 'X-XSRF-TOKEN': '{token}' }} }}).then(r => r.json())")
        
        print("\nPencacah by-region:")
        print("  totalElements:", res_p.get("data", {}).get("totalElements"))
        print("  totalPages:", res_p.get("data", {}).get("totalPages"))
        
        await page.close()

asyncio.run(run())
