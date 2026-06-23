import asyncio
import json
import os
from playwright.async_api import async_playwright
from urllib.parse import unquote

USER_DATA_DIR = "playwright_chrome_profile"

def check_port_open(port):
    import socket
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1.0)
            return s.connect_ex(('127.0.0.1', port)) == 0
    except Exception:
        return False

async def main():
    script_dir = "/Users/jihanmaisaroh/scrap_fasih"
    with open(os.path.join(script_dir, "region_map_sulteng_full.json"), "r") as f:
        region_map = json.load(f)
        
    sigi = region_map["kabupaten"]["7210"]
    jono_oge = None
    for kec_code, kec in sigi["kecamatan"].items():
        if "BIROMARU" in kec["kec_name"].upper():
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
        return

    # Find port
    port = None
    for p in [9223, 9222]:
        if check_port_open(p):
            port = p
            break
            
    if not port:
        print("Chrome remote debugging not open!")
        return

    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
        context = browser.contexts[0]
        page = None
        for p_page in context.pages:
            if "fasih-sm.bps.go.id" in p_page.url:
                page = p_page
                break
        if not page:
            page = await context.new_page()
            await page.goto("https://fasih-sm.bps.go.id/app/dashboard")
            await asyncio.sleep(2)
            
        cookies = await context.cookies()
        token_raw = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), None)
        if not token_raw:
            print("XSRF-TOKEN not found!")
            await browser.close()
            return
            
        token = unquote(token_raw)
        
        url = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode"
        
        for idx, sls in enumerate(sls_list):
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
                    "region5Id": sls["sls_id"],
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
            
            total_hit = res.get("totalHit", 0)
            if total_hit > 0:
                print(f"SLS '{sls['sls_name']}' ({sls['sls_code']}): totalHit = {total_hit}")
                print("First record:", res.get("searchData", [])[0])
                break
            else:
                print(f"SLS '{sls['sls_name']}' ({sls['sls_code']}): 0 targets")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
