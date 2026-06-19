import asyncio
import json
import socket
import sys
from playwright.async_api import async_playwright

DATATABLE_URL = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode"

def check_port_open(port=9223):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0
    except:
        return False

async def main():
    with open("region_map_sulteng.json", "r") as f:
        REGION_MAP = json.load(f)
        
    async with async_playwright() as p:
        port = 9223 if check_port_open(9223) else 9222
        print(f"Connecting to port {port}...", flush=True)
        try:
            browser = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}", timeout=10000)
        except Exception as e:
            print(f"Failed to connect to CDP: {e}", flush=True)
            return
            
        context = browser.contexts[0]
        
        page = None
        for p_obj in context.pages:
            if "fasih-sm.bps.go.id" in p_obj.url:
                page = p_obj
                break
        if not page:
            page = context.pages[0]
            
        print(f"Active tab: {page.url}", flush=True)
        
        cookies = await context.cookies()
        cookie_dict = {c["name"]: c["value"] for c in cookies}
        token_raw = cookie_dict.get("XSRF-TOKEN", "")
        from urllib.parse import unquote
        token = unquote(token_raw) if token_raw else ""
        
        region1_id = "5214ecb2-bef1-4a86-9446-451cf430928e" # SE Umum
        survey_period_id = "fd68e454-ba45-4b85-8205-f3bf777ded24"
        
        # We will loop over 3 Kabupatens to check a sample of Kecamatans
        kabs_to_check = ["7201", "7202", "7271"]
        
        kab_id_map = {
            "7201": "bc32354f-1245-426f-b2cf-a5733e1295ad",
            "7202": "530e9ca5-86ba-434e-9b04-405102e6d900",
            "7271": "4ab6ca2f-7952-4e8e-a94d-b6dd933e5d44"
        }
        
        for kab_code in kabs_to_check:
            kab_id = kab_id_map[kab_code]
            kab_name = REGION_MAP[kab_code]["kab_name"]
            print(f"\n--- Checking {kab_name} ---", flush=True)
            
            kecamatan_list = REGION_MAP[kab_code]["kecamatan"]
            for kec in kecamatan_list:
                kec_id = kec["id"]
                kec_name = kec["name"]
                if kec_name == "-":
                    continue
                
                payload = {
                    "start": 0,
                    "length": 1,
                    "columns": [{"data": "id"}],
                    "order": [],
                    "search": {"value": "", "regex": False},
                    "assignmentExtraParam": {
                        "region1Id": region1_id,
                        "region2Id": kab_id,
                        "region3Id": kec_id,
                        "surveyPeriodId": survey_period_id,
                        "assignmentErrorStatusType": -1,
                        "filterTargetType": ""
                    }
                }
                
                try:
                    res = await page.evaluate("""
                        async ({url, payload, token}) => {
                            const r = await fetch(url, {
                                method: "POST",
                                headers: {
                                    "Content-Type": "application/json",
                                    "X-XSRF-TOKEN": token
                                },
                                body: JSON.stringify(payload)
                            });
                            if (!r.ok) return { _error: `HTTP ${r.status}` };
                            return await r.json();
                        }
                    """, {"url": DATATABLE_URL, "payload": payload, "token": token})
                    
                    if "_error" not in res:
                        total_hit = res.get("totalHit", 0)
                        print(f"  Kecamatan: {kec_name} -> totalHit: {total_hit}", flush=True)
                    else:
                        print(f"  Kecamatan: {kec_name} -> ERROR: {res['_error']}", flush=True)
                except Exception as ex:
                    print(f"  Kecamatan: {kec_name} -> EXCEPTION: {ex}", flush=True)
                    
                await asyncio.sleep(0.1)
                
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
