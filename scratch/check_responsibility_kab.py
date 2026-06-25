import asyncio
import json
import os
import sys
from urllib.parse import unquote
from playwright.async_api import async_playwright

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scrape_granular_core import get_authenticated_context, check_session_valid

async def get_xsrf_token(page):
    try:
        cookies = await page.context.cookies()
        for c in cookies:
            if c["name"] == "XSRF-TOKEN":
                return unquote(c["value"])
    except Exception:
        pass
    return ""

async def main():
    async with async_playwright() as p:
        browser, context, page = await get_authenticated_context(p)
        
        if "fasih-sm.bps.go.id" not in page.url:
            await page.goto("https://fasih-sm.bps.go.id/app/dashboard", timeout=60000)
            await asyncio.sleep(2)
            
        token = await get_xsrf_token(page)
        is_valid = await check_session_valid(page, token)
        while not is_valid:
            print("\n==============================================================")
            print("[WARNING] Harap LOGIN atau REFRESH halaman FASIH di browser Chrome Anda.")
            print("Mencoba mendeteksi secara otomatis setiap 5 detik...")
            print("==============================================================\n", flush=True)
            await asyncio.sleep(5)
            token = await get_xsrf_token(page)
            is_valid = await check_session_valid(page, token)
            
        print("[SUCCESS] Sesi valid!")
        
        url = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/report-progress-by-responsibility"
        payload = {
            "surveyPeriodId": "fd68e454-ba45-4b85-8205-f3bf777ded24", # SE Umum
            "surveyRoleId": "6d7d919a-45e5-4779-bb87-2905b49fd31a", # Pencacah
            "size": 50,
            "page": 0,
            "search": "",
            "target": "ALL",
            "region": {
                "region1Id": "5214ecb2-bef1-4a86-9446-451cf430928e",
                "region2Id": "bc32354f-1245-426f-b2cf-a5733e1295ad", # Banggai Kepulauan ID
                "region3Id": None,
                "region4Id": None,
                "region5Id": None,
                "region6Id": None,
                "region7Id": None,
                "region8Id": None,
                "region9Id": None,
                "region10Id": None
            },
            "regionSummaryLevel": 6
        }
        
        resp = await page.evaluate("""
            async ({url, payload, token}) => {
                const r = await fetch(url, {
                    method: "POST",
                    headers: { "Content-Type": "application/json", "X-XSRF-TOKEN": token },
                    body: JSON.stringify(payload)
                });
                return await r.json();
            }
        """, {"url": url, "payload": payload, "token": token})
        
        content = resp.get("data", {}).get("content", [])
        print("Fetched content count:", len(content))
        
        found = 0
        for item in content:
            regions = item.get("regionSummary", [])
            if regions:
                print(f"\nUser: {item.get('username')}, Fullname: {item.get('fullName') or item.get('fullname') or '-'}")
                print(f"Total regions assigned: {len(regions)}")
                print("First region summary details:")
                print(json.dumps(regions[0], indent=2))
                found += 1
                if found >= 3:
                    break
                    
        if found == 0:
            print("No officer with regionSummary found.")

if __name__ == "__main__":
    asyncio.run(main())
