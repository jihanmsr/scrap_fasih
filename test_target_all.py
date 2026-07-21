import asyncio
from playwright.async_api import async_playwright
import json

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            user_data_dir="/Users/jihanmaisaroh/scrap_fasih/playwright_chrome_profile",
            headless=True
        )
        page = browser.pages[0]
        
        await page.goto("https://fasih-sm.bps.go.id/app/dashboard")
        cookies = await browser.cookies()
        token = ""
        for c in cookies:
            if c["name"] == "XSRF-TOKEN":
                from urllib.parse import unquote
                token = unquote(c["value"])
                break
        
        payload_target = {
            "surveyPeriodId": "fd68e454-ba45-4b85-8205-f3bf777ded24",
            "surveyRoleId": "6d7d919a-45e5-4779-bb87-2905b49fd31a", # Pencacah
            "size": 10, "page": 0, "search": "",
            "target": "TARGET_ONLY",
            "region": {
                "region1Id": None, "region2Id": "bb856f6f-23be-4c4c-aeb3-2410a7b45ad3", # Bangkep 
                "region3Id": None, "region4Id": None, "region5Id": None, "region6Id": None, 
                "region7Id": None, "region8Id": None, "region9Id": None, "region10Id": None
            },
            "regionSummaryLevel": 6
        }
        
        payload_all = payload_target.copy()
        payload_all["target"] = "ALL"

        res_target = await page.evaluate("""
            async ({token, payload}) => {
                const r = await fetch("https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/report-progress-by-responsibility", {
                    method: "POST", headers: { "X-XSRF-TOKEN": token, "Content-Type": "application/json" },
                    body: JSON.stringify(payload)
                });
                return await r.json();
            }
        """, {"token": token, "payload": payload_target})
        
        res_all = await page.evaluate("""
            async ({token, payload}) => {
                const r = await fetch("https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/report-progress-by-responsibility", {
                    method: "POST", headers: { "X-XSRF-TOKEN": token, "Content-Type": "application/json" },
                    body: JSON.stringify(payload)
                });
                return await r.json();
            }
        """, {"token": token, "payload": payload_all})

        print("Total Target Only:", res_target.get("data", {}).get("totalElements"))
        print("Total ALL:", res_all.get("data", {}).get("totalElements"))
        
        await browser.close()

asyncio.run(main())
