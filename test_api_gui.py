import asyncio
import json
from playwright.async_api import async_playwright

async def main():
    print("[INFO] Membuka browser (GUI)...")
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
        
        # Check login
        if "auth/login" in page.url:
            print("[WARNING] Harap login di browser Chrome yang baru terbuka! Script akan menunggu...")
            while "auth/login" in page.url:
                await asyncio.sleep(2)
            print("[INFO] Login berhasil dideteksi!")
            await page.wait_for_load_state("networkidle")
        
        # Get cookies
        cookies = await browser.cookies()
        token = ""
        for c in cookies:
            if c["name"] == "XSRF-TOKEN":
                from urllib.parse import unquote
                token = unquote(c["value"])
                break
                
        print("Token:", token)
        
        headers = {
            "content-type": "application/json",
            "x-xsrf-token": token,
            "accept": "*/*",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36"
        }
        
        import httpx
        client = httpx.AsyncClient(timeout=30.0, verify=False)
        client_cookies = {c["name"]: c["value"] for c in cookies}
        
        # Test endpoint 1: datatable-all-user-survey-periode-aggregation
        url1 = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode-aggregation?page=0&size=10"
        payload1 = {"assignmentExtraParam":{"surveyPeriodId":"fd68e454-ba45-4b85-8205-f3bf777ded24","assignmentErrorStatusType":-1,"filterTargetType":"TARGET_ONLY"}}
        
        try:
            r1 = await client.post(url1, json=payload1, headers=headers, cookies=client_cookies)
            print("Resp1 Status:", r1.status_code)
            with open("test_resp1.json", "w") as f:
                f.write(r1.text)
            print("Resp1 disimpan di test_resp1.json")
        except Exception as e:
            print("Resp1 Error:", e)

        # Test endpoint 2: report-user-assignment
        url2 = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/report-user-assignment"
        payload2 = {"surveyPeriodId":"fd68e454-ba45-4b85-8205-f3bf777ded24","assignmentStatusAlias":None,"assignmentErrorStatusType":-1,"data1":None,"data2":None,"data3":None,"data4":None,"data5":None,"data6":None,"data7":None,"data8":None,"data9":None,"data10":None,"regionId":None,"region1Id":"5214ecb2-bef1-4a86-9446-451cf430928e","region2Id":"bc32354f-1245-426f-b2cf-a5733e1295ad","currentUserId":None,"userIdResponsibility":None}
        
        try:
            r2 = await client.post(url2, json=payload2, headers=headers, cookies=client_cookies)
            print("Resp2 Status:", r2.status_code)
            with open("test_resp2.json", "w") as f:
                f.write(r2.text)
            print("Resp2 disimpan di test_resp2.json")
        except Exception as e:
            print("Resp2 Error:", e)

        await browser.close()
        await client.aclose()
        print("Selesai testing.")

asyncio.run(main())
