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
        
        # Go to a page to ensure cookies are loaded
        await page.goto("https://fasih-sm.bps.go.id/app/dashboard")
        
        # Get token
        cookies = await browser.cookies()
        token = ""
        for c in cookies:
            if c["name"] == "XSRF-TOKEN":
                from urllib.parse import unquote
                token = unquote(c["value"])
                break
        
        payload_target = {
            "pageNumber": 1, "pageSize": 10, "keyword": "",
            "assignmentExtraParam": {
                "region1Id": "046d3eb7-a7eb-42cc-a128-40b9db8d706a", # SULTENG
                "surveyPeriodId": "ce6d2cde-bba3-4c9c-b5f7-66a98246a064",
                "assignmentErrorStatusType": -1,
                "filterTargetType": "TARGET_ONLY",
                "region2Id": "bb856f6f-23be-4c4c-aeb3-2410a7b45ad3" # 7201 Bangkep
            }
        }
        
        payload_nontarget = payload_target.copy()
        payload_nontarget["assignmentExtraParam"]["filterTargetType"] = "NON_TARGET_ONLY"
        
        payload_all = payload_target.copy()
        payload_all["assignmentExtraParam"]["filterTargetType"] = ""

        # Fetch Target Only
        res_target = await page.evaluate("""
            async ({token, payload}) => {
                const r = await fetch("https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode-aggregation", {
                    method: "POST", headers: { "X-XSRF-TOKEN": token, "Content-Type": "application/json" },
                    body: JSON.stringify(payload)
                });
                return await r.json();
            }
        """, {"token": token, "payload": payload_target})
        
        res_nontarget = await page.evaluate("""
            async ({token, payload}) => {
                const r = await fetch("https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode-aggregation", {
                    method: "POST", headers: { "X-XSRF-TOKEN": token, "Content-Type": "application/json" },
                    body: JSON.stringify(payload)
                });
                return await r.json();
            }
        """, {"token": token, "payload": payload_nontarget})
        
        res_all = await page.evaluate("""
            async ({token, payload}) => {
                const r = await fetch("https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode-aggregation", {
                    method: "POST", headers: { "X-XSRF-TOKEN": token, "Content-Type": "application/json" },
                    body: JSON.stringify(payload)
                });
                return await r.json();
            }
        """, {"token": token, "payload": payload_all})

        print("Total Target Only (Prelist Awal?):", res_target.get("totalHit"))
        print("Total Non Target Only (Tambahan?):", res_nontarget.get("totalHit"))
        print("Total Semua (Tanpa Filter):", res_all.get("totalHit"))
        
        await browser.close()

asyncio.run(main())
