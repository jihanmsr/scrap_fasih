import asyncio
import os
import json
from playwright.async_api import async_playwright

USER_DATA_DIR = "playwright_chrome_profile"

async def check_port_open(port):
    import socket
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0
    except:
        return False

async def main():
    async with async_playwright() as p:
        browser = None
        for port in [9223, 9222]:
            if await check_port_open(port):
                try:
                    browser = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
                    print(f"Connected to port {port}")
                    break
                except:
                    pass
        
        if not browser:
            print("Could not connect to browser")
            return
            
        context = browser.contexts[0]
        
        cookies = await context.cookies()
        token = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), "")
        from urllib.parse import unquote
        token = unquote(token)
        
        target_page = None
        for page in context.pages:
            if "fasih-sm.bps.go.id" in page.url:
                target_page = page
                break
        
        if not target_page:
            target_page = context.pages[0]

        survey_period_id = "fd68e454-ba45-4b85-8205-f3bf777ded24" # SE Umum
        url = f"https://fasih-sm.bps.go.id/app/api/survey-user/api/v1/allocations-view/by-user?surveyPeriodId={survey_period_id}&page=0&size=1"
        
        res = await target_page.evaluate("""
            async ({url, token}) => {
                const r = await fetch(url, {
                    headers: { "Accept": "application/json", "X-XSRF-TOKEN": token }
                });
                return await r.json();
            }
        """, {"url": url, "token": token})
        
        print(json.dumps(res, indent=2))

asyncio.run(main())
