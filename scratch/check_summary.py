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
        except Exception as e:
            print(f"Navigation timed out/failed: {e}")
            
        cookies = await context.cookies()
        token = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), None)
        if token: token = unquote(token)
        
        survey_period_id = "fd68e454-ba45-4b85-8205-f3bf777ded24"
        pencacah_id = "6d7d919a-45e5-4779-bb87-2905b49fd31a"
        pengawas_id = "93bcf446-c4c1-4462-8ed0-4b0f7ae89e52"
        
        async def get_summary(role_id, kab_code):
            url = f"https://fasih-sm.bps.go.id/app/api/survey-user/api/v1/allocations-view/summary?surveyPeriodId={survey_period_id}&surveyRoleId={role_id}&regionCode={kab_code}&level=2"
            res = await page.evaluate(f"fetch('{url}', {{ headers: {{ 'Accept': 'application/json', 'X-XSRF-TOKEN': '{token}' }} }}).then(r => r.json())")
            return res
            
        print("BUOL (7207) SUMMARIES:")
        buol_p = await get_summary(pencacah_id, "7207")
        buol_w = await get_summary(pengawas_id, "7207")
        print("Pencacah:", json.dumps(buol_p, indent=2))
        print("Pengawas:", json.dumps(buol_w, indent=2))
        
        print("\nBANGGAI LAUT (7211) SUMMARIES:")
        balut_p = await get_summary(pencacah_id, "7211")
        balut_w = await get_summary(pengawas_id, "7211")
        print("Pencacah:", json.dumps(balut_p, indent=2))
        print("Pengawas:", json.dumps(balut_w, indent=2))
        
        await page.close()

asyncio.run(run())
