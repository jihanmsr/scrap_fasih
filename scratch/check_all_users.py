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
        
        # Check Pencacah
        url_p = f"https://fasih-sm.bps.go.id/app/api/survey-user/api/v1/allocations-view/by-user?surveyPeriodId={survey_period_id}&surveyRoleId={pencacah_id}&page=0&size=500&regionCode=7207"
        res_p = await page.evaluate(f"fetch('{url_p}', {{ headers: {{ 'Accept': 'application/json', 'X-XSRF-TOKEN': '{token}' }} }}).then(r => r.json())")
        content_p = res_p.get("data", {}).get("content", [])
        
        truncated_p = []
        for u in content_p:
            tot = u.get("totalRegions", 0)
            arr = len(u.get("regions", []))
            if arr < tot:
                truncated_p.append((u.get("email"), tot, arr))
                
        print(f"Pencacah users count: {len(content_p)}")
        print(f"Pencacah truncated users: {len(truncated_p)}")
        if truncated_p:
            print("Examples of truncated Pencacah:")
            for email, tot, arr in truncated_p[:5]:
                print(f"  {email}: totalRegions={tot}, arrayLen={arr}")
                
        # Check Pengawas
        url_w = f"https://fasih-sm.bps.go.id/app/api/survey-user/api/v1/allocations-view/by-user?surveyPeriodId={survey_period_id}&surveyRoleId={pengawas_id}&page=0&size=500&regionCode=7207"
        res_w = await page.evaluate(f"fetch('{url_w}', {{ headers: {{ 'Accept': 'application/json', 'X-XSRF-TOKEN': '{token}' }} }}).then(r => r.json())")
        content_w = res_w.get("data", {}).get("content", [])
        
        truncated_w = []
        for u in content_w:
            tot = u.get("totalRegions", 0)
            arr = len(u.get("regions", []))
            if arr < tot:
                truncated_w.append((u.get("email"), tot, arr))
                
        print(f"\nPengawas users count: {len(content_w)}")
        print(f"Pengawas truncated users: {len(truncated_w)}")
        if truncated_w:
            print("Examples of truncated Pengawas:")
            for email, tot, arr in truncated_w[:5]:
                print(f"  {email}: totalRegions={tot}, arrayLen={arr}")

asyncio.run(run())
