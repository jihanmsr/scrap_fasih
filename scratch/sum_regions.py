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
            page = context.pages[0] if context.pages else await context.new_page()
            
        # Open a new tab and navigate to BPS to bypass CORS
        page = await context.new_page()
        try:
            await page.goto("https://fasih-sm.bps.go.id/app/dashboard", wait_until="domcontentloaded", timeout=15000)
        except Exception as e:
            print(f"Navigation timed out/failed (using current origin): {e}")
            
        cookies = await context.cookies()
        token = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), None)
        if token: token = unquote(token)
        
        survey_period_id = "fd68e454-ba45-4b85-8205-f3bf777ded24"
        pencacah_id = "6d7d919a-45e5-4779-bb87-2905b49fd31a"
        pengawas_id = "93bcf446-c4c1-4462-8ed0-4b0f7ae89e52"
        
        async def analyze(role_id, role_name, kab_code):
            # Fetch using by-user with regionSize=2000
            # Since size=500 is larger than total users in either Buol or Balut, we can get all users in a single page.
            url = f"https://fasih-sm.bps.go.id/app/api/survey-user/api/v1/allocations-view/by-user?surveyPeriodId={survey_period_id}&surveyRoleId={role_id}&page=0&size=500&regionCode={kab_code}&regionSize=2000"
            res = await page.evaluate(f"fetch('{url}', {{ headers: {{ 'Accept': 'application/json', 'X-XSRF-TOKEN': '{token}' }} }}).then(r => r.json())")
            
            content = res.get("data", {}).get("content", [])
            
            unique_regions = {}
            total_allocations = 0
            
            for user in content:
                user_regions = user.get("regions", [])
                total_allocations += len(user_regions)
                for reg in user_regions:
                    rcode = reg.get("regionCode")
                    if rcode:
                        unique_regions[rcode] = reg.get("regionName", "")
            
            return {
                "users_count": len(content),
                "total_allocations": total_allocations,
                "unique_regions_count": len(unique_regions),
                "regions_dict": unique_regions
            }
            
        print("Analyzing Buol Pencacah...")
        buol_p = await analyze(pencacah_id, "Pencacah", "7207")
        print("Analyzing Buol Pengawas...")
        buol_w = await analyze(pengawas_id, "Pengawas", "7207")
        
        print("Analyzing Balut Pencacah...")
        balut_p = await analyze(pencacah_id, "Pencacah", "7211")
        print("Analyzing Balut Pengawas...")
        balut_w = await analyze(pengawas_id, "Pengawas", "7211")
        
        print("\n=== RESULTS ===")
        print(f"Buol Pencacah: Users={buol_p['users_count']} Allocations={buol_p['total_allocations']} UniqueRegions={buol_p['unique_regions_count']}")
        print(f"Buol Pengawas: Users={buol_w['users_count']} Allocations={buol_w['total_allocations']} UniqueRegions={buol_w['unique_regions_count']}")
        print(f"Balut Pencacah: Users={balut_p['users_count']} Allocations={balut_p['total_allocations']} UniqueRegions={balut_p['unique_regions_count']}")
        print(f"Balut Pengawas: Users={balut_w['users_count']} Allocations={balut_w['total_allocations']} UniqueRegions={balut_w['unique_regions_count']}")
        
        # Let's save the exact difference to compare
        buol_p_regions = set(buol_p["regions_dict"].keys())
        buol_w_regions = set(buol_w["regions_dict"].keys())
        balut_p_regions = set(balut_p["regions_dict"].keys())
        balut_w_regions = set(balut_w["regions_dict"].keys())
        
        buol_p_not_w = buol_p_regions - buol_w_regions
        buol_w_not_p = buol_w_regions - buol_p_regions
        
        balut_p_not_w = balut_p_regions - balut_w_regions
        balut_w_not_p = balut_w_regions - balut_p_regions
        
        print(f"\n--- BUOL DIFFERENCES ---")
        print(f"Pencacah but not Pengawas ({len(buol_p_not_w)} regions):")
        for k in sorted(buol_p_not_w):
            print(f"  {k} : {buol_p['regions_dict'][k]}")
        print(f"Pengawas but not Pencacah ({len(buol_w_not_p)} regions):")
        for k in sorted(buol_w_not_p):
            print(f"  {k} : {buol_w['regions_dict'][k]}")
            
        print(f"\n--- BALUT DIFFERENCES ---")
        print(f"Pencacah but not Pengawas ({len(balut_p_not_w)} regions):")
        for k in sorted(balut_p_not_w):
            print(f"  {k} : {balut_p['regions_dict'][k]}")
        print(f"Pengawas but not Pencacah ({len(balut_w_not_p)} regions):")
        for k in sorted(balut_w_not_p):
            print(f"  {k} : {balut_w['regions_dict'][k]}")
            
        report = {
            "buol": {
                "pencacah_regions_count": len(buol_p_regions),
                "pengawas_regions_count": len(buol_w_regions),
                "pencacah_not_pengawas": [{"code": k, "name": buol_p["regions_dict"][k]} for k in sorted(buol_p_not_w)],
                "pengawas_not_pencacah": [{"code": k, "name": buol_w["regions_dict"][k]} for k in sorted(buol_w_not_p)]
            },
            "banggai_laut": {
                "pencacah_regions_count": len(balut_p_regions),
                "pengawas_regions_count": len(balut_w_regions),
                "pencacah_not_pengawas": [{"code": k, "name": balut_p["regions_dict"][k]} for k in sorted(balut_p_not_w)],
                "pengawas_not_pencacah": [{"code": k, "name": balut_w["regions_dict"][k]} for k in sorted(balut_w_not_p)]
            }
        }
        
        with open("scratch/selisih_buol_balut.json", "w") as f:
            json.dump(report, f, indent=2)
            
        await page.close()

asyncio.run(run())
