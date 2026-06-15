import asyncio
import json
import sys
from playwright.async_api import async_playwright
from urllib.parse import unquote

async def run():
    async with async_playwright() as p:
        browser = None
        for port in [9223, 9222]:
            try:
                # Add a timeout so we don't hang if CDP is busy
                browser = await asyncio.wait_for(p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}"), timeout=5.0)
                print(f"Connected on port {port}")
                break
            except Exception as e:
                print(f"Failed to connect on port {port}: {e}")
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
            page = context.pages[0] if context.pages else await context.new_page()
            
        try:
            await page.goto("https://fasih-sm.bps.go.id/app/dashboard", wait_until="domcontentloaded", timeout=15000)
        except Exception:
            pass
            
        cookies = await context.cookies()
        token = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), None)
        if token: token = unquote(token)
        
        survey_period_id = "fd68e454-ba45-4b85-8205-f3bf777ded24" # SE Umum
        pencacah_id = "6d7d919a-45e5-4779-bb87-2905b49fd31a"
        pengawas_id = "93bcf446-c4c1-4462-8ed0-4b0f7ae89e52"
        
        # We will fetch a list of users first to find one with totalRegions > 5
        url = f"https://fasih-sm.bps.go.id/app/api/survey-user/api/v1/allocations-view/by-user?surveyPeriodId={survey_period_id}&surveyRoleId={pengawas_id}&page=0&size=50&regionCode=7206"
        res = await page.evaluate(f"fetch('{url}', {{ headers: {{ 'Accept': 'application/json', 'X-XSRF-TOKEN': '{token}' }} }}).then(r => r.json())")
        content = res.get("data", {}).get("content", [])
        
        target_user = None
        for u in content:
            if u.get("totalRegions", 0) > 5:
                target_user = u
                print(f"Found candidate: {u.get('username')} with totalRegions={u.get('totalRegions')}")
                break
                
        if not target_user:
            # Let's search specifically for abjadalam9@gmail.com
            print("Looking for abjadalam9@gmail.com specifically...")
            url_ab = f"https://fasih-sm.bps.go.id/app/api/survey-user/api/v1/allocations-view/by-user?surveyPeriodId={survey_period_id}&surveyRoleId={pengawas_id}&page=0&size=5&search=abjadalam9"
            res_ab = await page.evaluate(f"fetch('{url_ab}', {{ headers: {{ 'Accept': 'application/json', 'X-XSRF-TOKEN': '{token}' }} }}).then(r => r.json())")
            content_ab = res_ab.get("data", {}).get("content", [])
            if content_ab:
                target_user = content_ab[0]
                print(f"Found abjadalam9: totalRegions={target_user.get('totalRegions')}")
            else:
                print("abjadalam9 not found")
                return
                
        # Now test with and without regionSize
        user_id = target_user.get("userId")
        role_id = target_user.get("roleId")
        
        for rsize in [None, 5, 100, 1000]:
            rsize_param = f"&regionSize={rsize}" if rsize is not None else ""
            test_url = f"https://fasih-sm.bps.go.id/app/api/survey-user/api/v1/allocations-view/by-user?surveyPeriodId={survey_period_id}&surveyRoleId={role_id}&userId={user_id}&page=0&size=5{rsize_param}"
            
            res_test = await page.evaluate(f"fetch('{test_url}', {{ headers: {{ 'Accept': 'application/json', 'X-XSRF-TOKEN': '{token}' }} }}).then(r => r.json())")
            test_content = res_test.get("data", {}).get("content", [])
            if test_content:
                t_user = test_content[0]
                print(f"regionSize={rsize}: regions in array={len(t_user.get('regions', []))}, totalRegions={t_user.get('totalRegions')}")
            else:
                print(f"regionSize={rsize}: Empty response")

asyncio.run(run())
