import asyncio
import json
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = None
        for port in [9223, 9222]:
            try: browser = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}"); break
            except: pass
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
        
        url1 = f"https://fasih-sm.bps.go.id/app/api/survey-user/api/v1/allocations-view/by-user?surveyPeriodId=fd68e454-ba45-4b85-8205-f3bf777ded24&surveyRoleId=6d7d919a-45e5-4779-bb87-2905b49fd31a&page=0&size=10&regionSize=100"
        res1 = await page.evaluate(f"fetch('{url1}', {{ headers: {{ 'Accept': 'application/json', 'X-XSRF-TOKEN': '{token}' }} }}).then(r => r.json())")
        
        print("With regionSize=100:")
        for user in res1.get("data", {}).get("content", []):
            if user.get("totalRegions") > 5:
                print(f"total: {user.get('totalRegions')}, len: {len(user.get('regions', []))}")

asyncio.run(run())
