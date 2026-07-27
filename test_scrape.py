import asyncio
import json
import os
from playwright.async_api import async_playwright

DATATABLE_URL = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/report-user-assignment"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            user_data_dir="playwright_chrome_profile",
            executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            headless=False,
            ignore_default_args=["--enable-automation"],
            args=["--no-first-run", "--no-default-browser-check", "--disable-blink-features=AutomationControlled"]
        )
        page = await browser.new_page()
        
        await page.goto("https://fasih-sm.bps.go.id/app/surveys/a0429e96-51a5-477b-a415-485f9c153004/fd68e454-ba45-4b85-8205-f3bf777ded24", timeout=60000)
        await page.wait_for_load_state("networkidle")
        
        if "auth/login" in page.url:
            print("Please login manually...")
            while "auth/login" in page.url:
                await asyncio.sleep(2)
            await page.wait_for_load_state("networkidle")
        
        cookies = await browser.cookies()
        token = ""
        for c in cookies:
            if c["name"] == "XSRF-TOKEN":
                from urllib.parse import unquote
                token = unquote(c["value"])
                break
                
        headers = {
            "content-type": "application/json",
            "x-xsrf-token": token,
            "accept": "*/*",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36"
        }
        
        import httpx
        client = httpx.AsyncClient(timeout=30.0, verify=False)
        client_cookies = {c["name"]: c["value"] for c in cookies}
        
        # Test request
        payload = {
            "surveyPeriodId": "fd68e454-ba45-4b85-8205-f3bf777ded24",
            "assignmentStatusAlias": None,
            "assignmentErrorStatusType": -1,
            "regionId": None,
            "region1Id": "5214ecb2-bef1-4a86-9446-451cf430928e",
            "region2Id": "fb9cd9f0-c4c0-4a37-9041-57190693f625", # Banggai Kepulauan
            "currentUserId": None,
            "userIdResponsibility": None
        }
        
        try:
            r = await client.post(DATATABLE_URL, json=payload, headers=headers, cookies=client_cookies)
            print("Status:", r.status_code)
            print(r.text[:500])
        except Exception as e:
            print("Error:", e)

        await browser.close()
        await client.aclose()

asyncio.run(main())
