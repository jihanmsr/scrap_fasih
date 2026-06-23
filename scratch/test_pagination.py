import asyncio
import json
import os
from playwright.async_api import async_playwright
from urllib.parse import unquote

USER_DATA_DIR = "playwright_chrome_profile"

async def main():
    async with async_playwright() as p:
        abs_user_data_dir = os.path.abspath(USER_DATA_DIR)
        chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        
        print("Launching persistent Chrome context...")
        context = await p.chromium.launch_persistent_context(
            user_data_dir=abs_user_data_dir,
            headless=True,
            executable_path=chrome_path,
            args=["--no-first-run", "--no-default-browser-check"]
        )
        
        page = context.pages[0] if context.pages else await context.new_page()
        
        print("Navigating to BPS dashboard to verify session...")
        await page.goto("https://fasih-sm.bps.go.id/app/dashboard")
        await asyncio.sleep(2)
        
        cookies = await context.cookies()
        token_raw = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), None)
        if not token_raw:
            print("XSRF-TOKEN not found in cookies! Please make sure you are logged in.")
            await context.close()
            return
            
        token = unquote(token_raw)
        print("Session verified! Token found.")
        
        url = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode"
        
        # Desa Jono Oge ID (kab: 0061da62-2a47-4dee-b8d0-239b33e2c59d, kec: a50bf6c3-1d07-42fc-8e4a-5fae6c646b9a, desa: 6a3922f5-b3e1-4560-af6f-ad5b11ebcdba)
        # Jono Oge Code: 7210120009
        kab_id = "0061da62-2a47-4dee-b8d0-239b33e2c59d"
        kec_id = "a50bf6c3-1d07-42fc-8e4a-5fae6c646b9a"
        desa_id = "6a3922f5-b3e1-4560-af6f-ad5b11ebcdba"
        
        for start in [0, 900, 1000, 1100]:
            payload = {
                "start": start,
                "length": 100,
                "columns": [{"data": "id"}],
                "order": [],
                "search": {"value": "", "regex": False},
                "assignmentExtraParam": {
                    "region1Id": "5214ecb2-bef1-4a86-9446-451cf430928e",
                    "region2Id": kab_id,
                    "region3Id": kec_id,
                    "region4Id": desa_id,
                    "surveyPeriodId": "fd68e454-ba45-4b85-8205-f3bf777ded24",
                    "assignmentErrorStatusType": -1,
                    "filterTargetType": ""
                }
            }
            
            res = await page.evaluate("""
                async ({url, payload, token}) => {
                    const r = await fetch(url, {
                        method: "POST",
                        headers: { "Content-Type": "application/json", "X-XSRF-TOKEN": token },
                        body: JSON.stringify(payload)
                    });
                    if (!r.ok) return { _error: `HTTP ${r.status}` };
                    return await r.json();
                }
            """, {"url": url, "payload": payload, "token": token})
            
            if "_error" in res:
                print(f"Start {start}: ERROR {res['_error']}")
            else:
                data_len = len(res.get("searchData", []))
                total_hit = res.get("totalHit", 0)
                print(f"Start {start}: Returned {data_len} rows, totalHit={total_hit}")
                if data_len > 0:
                    print(f"  Sample ID: {res['searchData'][0].get('id')} | codeIdentity: {res['searchData'][0].get('codeIdentity')}")
                
        await context.close()

if __name__ == "__main__":
    asyncio.run(main())
