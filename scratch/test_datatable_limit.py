import asyncio
import json
import os
import sys
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        user_data_dir = os.path.abspath("chrome_user_data")
        chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        context = await p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir, headless=False, executable_path=chrome_path,
            args=["--no-first-run", "--no-default-browser-check"]
        )
        page = context.pages[0] if context.pages else await context.new_page()

        # get token
        await page.goto("https://fasih-sm.bps.go.id/app/dashboard")
        await asyncio.sleep(2)
        token = await page.evaluate("localStorage.getItem('XSRF-TOKEN')")
        if not token:
            print("Token not found!")
            await context.close()
            return
            
        print("Token found. Checking start=1000 limit...")
        
        url = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode"
        
        for start in [900, 1000, 2000]:
            payload = {
                "start": start,
                "length": 100,
                "columns": [{"data": "id"}],
                "order": [{"column": 5, "dir": "desc"}],
                "search": {"value": "", "regex": False},
                "assignmentExtraParam": {
                    "region1Id": "5214ecb2-bef1-4a86-9446-451cf430928e",
                    "surveyPeriodId": "fd68e454-ba45-4b85-8205-f3bf777ded24",
                    "assignmentStatusAlias": "SUBMITTED BY Pencacah",
                    "assignmentErrorStatusType": -1,
                    "filterTargetType": ""
                }
            }
            res = await page.evaluate("""
                async ({url, payload, token}) => {
                    try {
                        const r = await fetch(url, {
                            method: "POST",
                            headers: { "Content-Type": "application/json", "X-XSRF-TOKEN": token },
                            body: JSON.stringify(payload)
                        });
                        if (!r.ok) return { _error: `HTTP ${r.status}` };
                        return await r.json();
                    } catch (e) {
                        return { _error: e.toString() };
                    }
                }
            """, {"url": url, "payload": payload, "token": token})
            
            if "_error" in res:
                print(f"Start {start}: ERROR {res['_error']}")
            else:
                data_len = len(res.get("searchData", []))
                total_hit = res.get("totalHit", 0)
                print(f"Start {start}: Returned {data_len} rows, totalHit={total_hit}")
                
        await context.close()

asyncio.run(run())
