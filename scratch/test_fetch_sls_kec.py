import asyncio
import json
from playwright.async_api import async_playwright
from urllib.parse import unquote

async def run():
    async with async_playwright() as p:
        browser = None
        for port in [9223, 9222]:
            try:
                browser = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
                print(f"Connected on port {port}")
                break
            except Exception:
                pass
        if not browser: return
        
        context = browser.contexts[0]
        page = None
        for p_page in context.pages:
            if "fasih-sm.bps.go.id" in p_page.url:
                page = p_page
                break
        if not page: page = context.pages[0]
        
        cookies = await context.cookies()
        token = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), None)
        if token: token = unquote(token)
        
        survey_period_id = "fd68e454-ba45-4b85-8205-f3bf777ded24" # SE Umum
        region1_id = "5214ecb2-bef1-4a86-9446-451cf430928e" # Sulawesi Tengah
        kab_id = "d833fdce-ebfb-429b-a1bb-8966239fd8e4" # [06] TOLI-TOLI
        
        # Find a valid kecamatan (index 1)
        try:
            with open("region_map_sulteng.json", "r") as f:
                reg_map = json.load(f)
                toli_kecs = reg_map.get("7206", {}).get("kecamatan", [])
                if len(toli_kecs) > 1:
                    kec_id = toli_kecs[1]["id"]
                    kec_name = toli_kecs[1]["name"]
                    print(f"Using Kecamatan: {kec_name} (ID: {kec_id})")
        except Exception as e:
            print("Failed to read region map:", e)
            return
            
        url = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode"
        payload = {
            "start": 0,
            "length": 50,
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
                return await r.json();
            }
        """, {"url": url, "payload": payload, "token": token})
        
        records = res.get("searchData", [])
        print(f"\nFetched {len(records)} records for Kecamatan.")
        
        sls_dict = {}
        for comp in records:
            region = comp.get("region", {})
            lvl1 = region.get("level1", {}) or {}
            lvl2 = lvl1.get("level2", {}) or {}
            lvl3 = lvl2.get("level3", {}) or {}
            lvl4 = lvl3.get("level4", {}) or {}
            lvl5 = lvl4.get("level5", {}) or {}
            
            sls_code = lvl5.get("fullCode", "LAINNYA")
            if sls_code not in sls_dict:
                sls_dict[sls_code] = {
                    "sls_code": sls_code,
                    "sls_name": lvl5.get("name", "LAINNYA"),
                    "total": 0,
                    "assigned": 0,
                    "officers": set()
                }
            sls_dict[sls_code]["total"] += 1
            officer = comp.get("currentUserUsername")
            if officer:
                sls_dict[sls_code]["assigned"] += 1
                ofc_name = comp.get("currentUserFullname", "-")
                sls_dict[sls_code]["officers"].add(f"{ofc_name} ({officer})" if ofc_name != "-" else officer)
                
        print("\nSLS AGGREGATED SAMPLE:")
        for code, data in list(sls_dict.items())[:5]:
            data["officers"] = list(data["officers"])
            print(json.dumps(data, indent=2))

asyncio.run(run())
