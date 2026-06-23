import asyncio
import json
import os
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            user_data_dir="playwright_chrome_profile",
            executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--no-first-run", "--no-default-browser-check", "--disable-blink-features=AutomationControlled"]
        )
        page = browser.pages[0]
        try:
            await page.goto("https://fasih-sm.bps.go.id/app/surveys", wait_until="domcontentloaded", timeout=60000)
        except Exception as e:
            pass

        xsrf_match = await page.evaluate("document.cookie.match(/XSRF-TOKEN=([^;]+)/)")
        if not xsrf_match:
            print("Tidak menemukan XSRF-TOKEN.")
            await browser.close()
            return
            
        xsrf_token = xsrf_match[1].replace("%3D", "=")
        prov_id = "5214ecb2-bef1-4a86-9446-451cf430928e"
        period_id = "fd68e454-ba45-4b85-8205-f3bf777ded24"
        
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json",
            "X-Xsrf-Token": xsrf_token,
        }
        
        # Test query for Kab Banggai (id: 530e9ca5-86ba-434e-9b04-405102e6d900)
        payload = {
            "start": 0, "length": 1, 
            "columns": [{"data": "id"}], "order": [], "search": {"value": "", "regex": False},
            "assignmentExtraParam": {
                "region1Id": prov_id,
                "region2Id": "530e9ca5-86ba-434e-9b04-405102e6d900",
                "surveyPeriodId": period_id,
                "assignmentErrorStatusType": -1,
                "filterTargetType": "target"
            }
        }
        res = await page.evaluate(f'''async () => {{
            const response = await fetch("https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode", {{
                method: "POST",
                headers: {json.dumps(headers)},
                body: JSON.stringify({json.dumps(payload)})
            }});
            return await response.json();
        }}''')
        
        print("Total Target in Banggai with ErrorStatusType -1:", res.get("totalHit"))
        print("Aggregation:", res.get("searchAggregation"))
        
        payload["assignmentExtraParam"]["assignmentErrorStatusType"] = 1
        res1 = await page.evaluate(f'''async () => {{
            const response = await fetch("https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode", {{
                method: "POST",
                headers: {json.dumps(headers)},
                body: JSON.stringify({json.dumps(payload)})
            }});
            return await response.json();
        }}''')
        print("Total Target in Banggai with ErrorStatusType 1:", res1.get("totalHit"))
        
        payload["assignmentExtraParam"]["assignmentErrorStatusType"] = 2
        res2 = await page.evaluate(f'''async () => {{
            const response = await fetch("https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode", {{
                method: "POST",
                headers: {json.dumps(headers)},
                body: JSON.stringify({json.dumps(payload)})
            }});
            return await response.json();
        }}''')
        print("Total Target in Banggai with ErrorStatusType 2:", res2.get("totalHit"))
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
