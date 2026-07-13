import asyncio
from playwright.async_api import async_playwright
import os

async def run():
    async with async_playwright() as p:
        abs_user_data_dir = os.path.abspath(os.environ.get("CHROME_PROFILE_DIR", "playwright_chrome_profile"))
        chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        
        context = await p.chromium.launch_persistent_context(
            user_data_dir=abs_user_data_dir,
            executable_path=chrome_path,
            headless=True
        )
        page = context.pages[0] if context.pages else await context.new_page()
        
        await page.goto("https://fasih-sm.bps.go.id/app/analytic/assignment/assignment-status", timeout=60000)
        await page.wait_for_load_state("networkidle")
        
        cookies = await context.cookies()
        token = ""
        for c in cookies:
            if c["name"] == "XSRF-TOKEN":
                from urllib.parse import unquote
                token = unquote(c["value"])
                break

        if not token:
            print("No token")
            return
            
        payload = {
            "surveyPeriodId": "fd68e454-ba45-4b85-8205-f3bf777ded24",
            "size": 1,
            "page": 0,
            "search": "",
            "target": "TARGET_ONLY",
            "region": {
                "region1Id": "5214ecb2-bef1-4a86-9446-451cf430928e",
                "region2Id": "4ab6ca2f-7952-4e8e-a94d-b6dd933e5d44",
                "region3Id": None,
                "region4Id": None,
                "region5Id": None,
                "region6Id": None,
                "region7Id": None,
                "region8Id": None,
                "region9Id": None,
                "region10Id": None
            },
            "regionSummaryLevel": 6,
            "surveyRoleId": "6d7d919a-45e5-4779-bb87-2905b49fd31a"
        }

        res = await page.evaluate("""
            async ({url, payload, token}) => {
                const r = await fetch(url, {
                    method: "POST",
                    headers: { 
                        "Content-Type": "application/json", 
                        "X-XSRF-TOKEN": token,
                        "Accept": "application/json, text/plain, */*"
                    },
                    body: JSON.stringify(payload)
                });
                return await r.text();
            }
        """, {"url": "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/report-progress-by-responsibility", "payload": payload, "token": token})
        
        import json
        try:
            print(json.dumps(json.loads(res)["data"]["content"][0], indent=2))
        except:
            print(res)

        await context.close()

asyncio.run(run())
