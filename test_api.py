import asyncio
import json
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            user_data_dir="playwright_chrome_profile",
            executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            headless=True
        )
        page = await browser.new_page()
        
        # We need the XSRF token
        await page.goto("https://fasih-sm.bps.go.id/app/surveys/a0429e96-51a5-477b-a415-485f9c153004/fd68e454-ba45-4b85-8205-f3bf777ded24", timeout=30000)
        await page.wait_for_load_state("networkidle")
        
        cookies = await browser.cookies()
        token = ""
        for c in cookies:
            if c["name"] == "XSRF-TOKEN":
                from urllib.parse import unquote
                token = unquote(c["value"])
                break
                
        print("Token:", token)
        
        # Test endpoint 1
        url1 = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode-aggregation?page=0&size=10"
        payload1 = {"assignmentExtraParam":{"surveyPeriodId":"fd68e454-ba45-4b85-8205-f3bf777ded24","assignmentErrorStatusType":-1,"filterTargetType":"TARGET_ONLY"}}
        
        # Test endpoint 2
        url2 = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/report-progress-assignment"
        payload2 = {"surveyPeriodId":"fd68e454-ba45-4b85-8205-f3bf777ded24","assignmentStatusAlias":None,"assignmentErrorStatusType":-1,"data1":None,"data2":None,"data3":None,"data4":None,"data5":None,"data6":None,"data7":None,"data8":None,"data9":None,"data10":None,"regionId":None,"currentUserId":None,"userIdResponsibility":None}
        
        headers = {
            "content-type": "application/json",
            "x-xsrf-token": token,
            "accept": "*/*"
        }
        
        resp1 = await page.request.post(url1, data=payload1, headers=headers)
        print("Resp1 Status:", resp1.status)
        try:
            print("Resp1 JSON:", str(await resp1.json())[:500])
        except:
            print("Resp1 Text:", await resp1.text())
            
        resp2 = await page.request.post(url2, data=payload2, headers=headers)
        print("Resp2 Status:", resp2.status)
        try:
            print("Resp2 JSON:", str(await resp2.json())[:500])
        except:
            print("Resp2 Text:", await resp2.text())

        await browser.close()

asyncio.run(main())
