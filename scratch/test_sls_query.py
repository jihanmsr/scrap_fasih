import asyncio
import json
import os
from playwright.async_api import async_playwright
from urllib.parse import unquote

USER_DATA_DIR = "playwright_chrome_profile"

async def main():
    # Load region map to find SLS IDs in Jono Oge
    script_dir = "/Users/jihanmaisaroh/scrap_fasih"
    with open(os.path.join(script_dir, "region_map_sulteng_full.json"), "r") as f:
        region_map = json.load(f)
        
    sigi = region_map["kabupaten"]["7210"]
    biromaru = sigi["kecamatan"]["7210120"] # Sigi Biromaru code is 7210120 or similar, let's look for "7210120"
    
    jono_oge = None
    for kec_code, kec in sigi["kecamatan"].items():
        if "7210120" in kec_code or "BIROMARU" in kec["kec_name"].upper():
            for d_code, d in kec["desa"].items():
                if "JONO OGE" in d["desa_name"].upper():
                    jono_oge = d
                    break
            if jono_oge:
                break
                
    if not jono_oge:
        print("Jono Oge not found in region map!")
        return
        
    sls_list = jono_oge.get("sls", [])
    print(f"Jono Oge has {len(sls_list)} SLS.")
    if not sls_list:
        print("No SLS in Jono Oge!")
        return
        
    sample_sls = sls_list[0]
    print(f"Sample SLS: Name={sample_sls['sls_name']}, Code={sample_sls['sls_code']}, ID={sample_sls['sls_id']}")

    async with async_playwright() as p:
        abs_user_data_dir = os.path.abspath(USER_DATA_DIR)
        chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        
        context = await p.chromium.launch_persistent_context(
            user_data_dir=abs_user_data_dir,
            headless=True,
            executable_path=chrome_path,
            args=["--no-first-run", "--no-default-browser-check"]
        )
        page = context.pages[0] if context.pages else await context.new_page()
        await page.goto("https://fasih-sm.bps.go.id/app/dashboard")
        await asyncio.sleep(2)
        
        cookies = await context.cookies()
        token_raw = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), None)
        token = unquote(token_raw)
        
        url = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode"
        
        # Test query at SLS level using region5Id
        payload = {
            "start": 0,
            "length": 10,
            "columns": [{"data": "id"}, {"data": "codeIdentity"}],
            "order": [],
            "search": {"value": "", "regex": False},
            "assignmentExtraParam": {
                "region1Id": "5214ecb2-bef1-4a86-9446-451cf430928e",
                "region2Id": "0061da62-2a47-4dee-b8d0-239b33e2c59d",
                "region3Id": "a50bf6c3-1d07-42fc-8e4a-5fae6c646b9a",
                "region4Id": "6a3922f5-b3e1-4560-af6f-ad5b11ebcdba",
                "region5Id": sample_sls["sls_id"],
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
                return await r.json();
            }
        """, {"url": url, "payload": payload, "token": token})
        
        print("SLS QUERY RESPONSE:")
        print("totalHit:", res.get("totalHit"))
        search_data = res.get("searchData", [])
        print("Returned length:", len(search_data))
        if search_data:
            print("Sample record:", search_data[0])
            
        await context.close()

if __name__ == "__main__":
    asyncio.run(main())
