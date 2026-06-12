import asyncio
import json
import time
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = None
        for port in [9223, 9222]:
            try:
                browser = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
                break
            except Exception:
                pass
        if not browser:
            print("Could not connect to Chrome")
            return
        
        context = browser.contexts[0]
        page = None
        for p_page in context.pages:
            if "fasih-sm.bps.go.id" in p_page.url:
                page = p_page
                break
                
        if not page:
            print("Could not find fasih-sm page")
            return
            
        cookies = await context.cookies()
        token = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), None)
        from urllib.parse import unquote
        if token: token = unquote(token)
        
        survey_period_id = "fd68e454-ba45-4b85-8205-f3bf777ded24"
        pencacah_id = "6d7d919a-45e5-4779-bb87-2905b49fd31a"
        pengawas_id = "93bcf446-c4c1-4462-8ed0-4b0f7ae89e52"
        
        async def get_all_regions(role_id, role_name):
            regions = set()
            region_names = {}
            page_idx = 0
            while True:
                url = f"https://fasih-sm.bps.go.id/app/api/survey-user/api/v1/allocations-view/by-user?surveyPeriodId={survey_period_id}&surveyRoleId={role_id}&page={page_idx}&size=500"
                res = await page.evaluate(f"""
                    fetch('{url}', {{ headers: {{ "Accept": "application/json", "X-XSRF-TOKEN": "{token}" }} }}).then(r => r.json())
                """)
                data = res.get("data", {})
                content = data.get("content", [])
                if not content: break
                
                for user in content:
                    for reg in user.get("regions", []):
                        rcode = reg.get("regionCode")
                        if rcode:
                            regions.add(rcode)
                            region_names[rcode] = reg.get("regionName", "")
                
                print(f"Fetched page {page_idx} for {role_name}")
                if data.get("isLast", True): break
                page_idx += 1
                await asyncio.sleep(0.5)
            return regions, region_names
            
        pencacah_regions, pencacah_names = await get_all_regions(pencacah_id, "Pencacah")
        pengawas_regions, pengawas_names = await get_all_regions(pengawas_id, "Pengawas")
        
        print(f"\\nTotal Pencacah Regions: {len(pencacah_regions)}")
        print(f"Total Pengawas Regions: {len(pengawas_regions)}")
        
        diff1 = pencacah_regions - pengawas_regions
        diff2 = pengawas_regions - pencacah_regions
        
        with open("selisih_wilayah.txt", "w") as f:
            f.write(f"=== {len(diff1)} WILAYAH DI PENCACAH TAPI TIDAK ADA DI PENGAWAS ===\\n")
            for x in sorted(list(diff1)): 
                name = pencacah_names.get(x, "")
                f.write(f"{x} - {name}\\n")
                
            f.write(f"\\n=== {len(diff2)} WILAYAH DI PENGAWAS TAPI TIDAK ADA DI PENCACAH ===\\n")
            for x in sorted(list(diff2)): 
                name = pengawas_names.get(x, "")
                f.write(f"{x} - {name}\\n")
                
        print("\\nDone! Hasil selisih ditulis ke selisih_wilayah.txt")

asyncio.run(run())
