import asyncio
import httpx
import json
import os
from urllib.parse import unquote
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        user_data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "chrome_user_data")
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir, headless=False, 
            executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            no_viewport=True
        )
        page = browser.pages[0] if browser.pages else await browser.new_page()
        await page.goto("https://fasih-sm.bps.go.id/assignment/list/all-user")
        await asyncio.sleep(2)
        
        cookies = await browser.cookies()
        token = ""
        cookie_header = []
        for c in cookies:
            cookie_header.append(f"{c['name']}={c['value']}")
            if c["name"] == "XSRF-TOKEN":
                token = unquote(c["value"])
                
        url = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode"
        
        # Check Error (1) and Dropped (2)
        results = {}
        for err_type, err_name in [(1, "Error"), (2, "Dropped")]:
            payload = {
                "start": 0, "length": 10, "columns": [{"data": "id"}, {"data": "codeIdentity"}, {"data": "data1"}], "order": [], "search": {"value": "", "regex": False},
                "assignmentExtraParam": {
                    "region1Id": "5214ecb2-bef1-4a86-9446-451cf430928e", # Sulteng
                    "surveyPeriodId": "fd68e454-ba45-4b85-8205-f3bf777ded24", # SE UMUM
                    "assignmentErrorStatusType": err_type, 
                    "filterTargetType": "target"
                }
            }
            
            async with httpx.AsyncClient() as client:
                client.headers.update({
                    "X-XSRF-TOKEN": token,
                    "Content-Type": "application/json",
                    "Cookie": "; ".join(cookie_header)
                })
                r = await client.post(url, json=payload)
                if r.status_code == 200:
                    res = r.json()
                    total = res.get("totalHit", 0)
                    results[err_name] = total
                    print(f"--- DAFTAR TARGET {err_name.upper()} (Total: {total}) ---")
                    
                    if "searchData" in res and total > 0:
                        for idx, item in enumerate(res["searchData"][:10], 1): # ambil 10 sampel pertama
                            c_id = item.get("codeIdentity")
                            name = item.get("data1")
                            print(f"{idx}. {name} [Code: {c_id}]")
                        if total > 10:
                            print(f"... (dan {total - 10} data lainnya)")
                    print("")
                else:
                    results[err_name] = f"Failed API {r.status_code}"
                    
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
