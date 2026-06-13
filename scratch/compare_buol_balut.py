import asyncio
import json
import time
from playwright.async_api import async_playwright
from urllib.parse import unquote

async def run():
    async with async_playwright() as p:
        browser = None
        for port in [9223, 9222]:
            try:
                browser = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
                print(f"Connected to Chrome on port {port}")
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
        if token: 
            token = unquote(token)
        
        survey_period_id = "fd68e454-ba45-4b85-8205-f3bf777ded24"
        pencacah_id = "6d7d919a-45e5-4779-bb87-2905b49fd31a"
        pengawas_id = "93bcf446-c4c1-4462-8ed0-4b0f7ae89e52"

        async def get_regions_for_kab(role_id, role_name, kab_code):
            regions = {}
            page_idx = 0
            while True:
                url = f"https://fasih-sm.bps.go.id/app/api/survey-user/api/v1/allocations-view/by-user?surveyPeriodId={survey_period_id}&surveyRoleId={role_id}&page={page_idx}&size=500&regionCode={kab_code}"
                res = await page.evaluate(f"""
                    fetch('{url}', {{ headers: {{ "Accept": "application/json", "X-XSRF-TOKEN": "{token}" }} }}).then(r => r.json())
                """)
                data = res.get("data", {})
                content = data.get("content", [])
                if not content: 
                    break
                
                for user in content:
                    for reg in user.get("regions", []):
                        rcode = reg.get("regionCode")
                        if rcode:
                            regions[rcode] = reg.get("regionName", "")
                
                print(f"Fetched page {page_idx} for {role_name} in Kabupaten {kab_code} (Got {len(regions)} regions so far)")
                if data.get("isLast", True): 
                    break
                page_idx += 1
                await asyncio.sleep(0.3)
            return regions
            
        print("Fetching Buol (7207) Pencacah regions...")
        buol_pencacah = await get_regions_for_kab(pencacah_id, "Pencacah", "7207")
        print("Fetching Buol (7207) Pengawas regions...")
        buol_pengawas = await get_regions_for_kab(pengawas_id, "Pengawas", "7207")
        
        print("Fetching Banggai Laut (7211) Pencacah regions...")
        balut_pencacah = await get_regions_for_kab(pencacah_id, "Pencacah", "7211")
        print("Fetching Banggai Laut (7211) Pengawas regions...")
        balut_pengawas = await get_regions_for_kab(pengawas_id, "Pengawas", "7211")
        
        # Differences
        # 1. Buol Pencacah vs Pengawas
        buol_p_not_w = set(buol_pencacah.keys()) - set(buol_pengawas.keys())
        buol_w_not_p = set(buol_pengawas.keys()) - set(buol_pencacah.keys())
        
        # 2. Banggai Laut Pencacah vs Pengawas
        balut_p_not_w = set(balut_pencacah.keys()) - set(balut_pengawas.keys())
        balut_w_not_p = set(balut_pengawas.keys()) - set(balut_pencacah.keys())
        
        report = {
            "buol": {
                "total_pencacah_regions": len(buol_pencacah),
                "total_pengawas_regions": len(buol_pengawas),
                "pencacah_not_pengawas": [{"code": k, "name": buol_pencacah[k]} for k in sorted(buol_p_not_w)],
                "pengawas_not_pencacah": [{"code": k, "name": buol_pengawas[k]} for k in sorted(buol_w_not_p)]
            },
            "banggai_laut": {
                "total_pencacah_regions": len(balut_pencacah),
                "total_pengawas_regions": len(balut_pengawas),
                "pencacah_not_pengawas": [{"code": k, "name": balut_pencacah[k]} for k in sorted(balut_p_not_w)],
                "pengawas_not_pencacah": [{"code": k, "name": balut_pengawas[k]} for k in sorted(balut_w_not_p)]
            }
        }
        
        with open("scratch/selisih_buol_balut.json", "w") as f:
            json.dump(report, f, indent=2)
            
        print("\n=== COMPARISON REPORT FOR BUOL ===")
        print(f"Total regions in Pencacah: {len(buol_pencacah)}")
        print(f"Total regions in Pengawas: {len(buol_pengawas)}")
        print(f"Pencacah but not Pengawas: {len(buol_p_not_w)}")
        print(f"Pengawas but not Pencacah: {len(buol_w_not_p)}")
        
        print("\n=== COMPARISON REPORT FOR BANGGAI LAUT ===")
        print(f"Total regions in Pencacah: {len(balut_pencacah)}")
        print(f"Total regions in Pengawas: {len(balut_pengawas)}")
        print(f"Pencacah but not Pengawas: {len(balut_p_not_w)}")
        print(f"Pengawas but not Pencacah: {len(balut_w_not_p)}")

asyncio.run(run())
