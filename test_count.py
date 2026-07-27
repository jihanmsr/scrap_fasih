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
        await asyncio.sleep(2)
        
        cookies = await browser.cookies()
        token = ""
        for c in cookies:
            if c["name"] == "XSRF-TOKEN":
                from urllib.parse import unquote
                token = unquote(c["value"])
                break
        
        # Bangkep ID
        bangkep_id = "bc32354f-1245-426f-b2cf-a5733e1295ad"
        
        def make_payload(t_type):
            return {
                "surveyPeriodId": "fd68e454-ba45-4b85-8205-f3bf777ded24",
                "surveyRoleId": "6d7d919a-45e5-4779-bb87-2905b49fd31a", # Pencacah
                "size": 1,
                "page": 0,
                "search": "",
                "target": t_type,
                "region": {
                    "region1Id": "5214ecb2-bef1-4a86-9446-451cf430928e",
                    "region2Id": bangkep_id,
                    "region3Id": None, "region4Id": None, "region5Id": None, "region6Id": None,
                    "region7Id": None, "region8Id": None, "region9Id": None, "region10Id": None
                },
                "regionSummaryLevel": 6
            }

        async def get_total(t_type):
            res = await page.evaluate("""
                async ({token, payload}) => {
                    const r = await fetch("https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/report-progress-by-responsibility", {
                        method: "POST", headers: { "X-XSRF-TOKEN": token, "Content-Type": "application/json" },
                        body: JSON.stringify(payload)
                    });
                    return await r.json();
                }
            """, {"token": token, "payload": make_payload(t_type)})
            return res.get("data", {}).get("totalElements", "Error: " + str(res))
            
        print("TARGET_ONLY:", await get_total("TARGET_ONLY"))
        print("ALL:", await get_total("ALL") or await get_total(""))
        
        await browser.close()

asyncio.run(main())
