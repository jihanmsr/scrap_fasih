import asyncio
import json
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
            context = browser.contexts[0]
            page = context.pages[0]
        except Exception as e:
            print("Failed to connect to browser on 9222:", e)
            return

        cookies = await context.cookies("https://fasih-sm.bps.go.id")
        token = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), None)
        if not token:
            print("No token in cookies")
            await browser.close()
            return
            
        print("Token found!")
        
        url = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode"
        
        for start in [900, 1000, 1100, 1900, 2000, 2100, 3000, 5000, 10000]:
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
                
        await browser.close()

asyncio.run(run())
