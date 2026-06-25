import asyncio
import json
import os
import sys
from urllib.parse import unquote
from playwright.async_api import async_playwright

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
        print("Connecting to browser...")
        browser, context, page = await get_authenticated_context(p)
        
        if "fasih-sm.bps.go.id" not in page.url:
            await page.goto("https://fasih-sm.bps.go.id/app/dashboard", timeout=60000)
            await asyncio.sleep(2)
            
        token = await get_xsrf_token(page)
        is_valid = await check_session_valid(page, token)
        if not is_valid:
            print("[ERROR] Session tidak valid.")
            return
        print("[OK] Sesi valid!")
        
        url = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/report-progress-by-responsibility"
        payload = {
            "surveyPeriodId": "fd68e454-ba45-4b85-8205-f3bf777ded24",
            "surveyRoleId": "6d7d919a-45e5-4779-bb87-2905b49fd31a",
            "size": 3,
            "page": 0,
            "search": "",
            "target": "ALL",
            "region": {
                "region1Id": "5214ecb2-bef1-4a86-9446-451cf430928e",
                "region2Id": None, "region3Id": None, "region4Id": None,
                "region5Id": None, "region6Id": None, "region7Id": None,
                "region8Id": None, "region9Id": None, "region10Id": None
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
                if (!r.ok) return { _error: `HTTP ${r.status}` };
                return await r.json();
            }
        """, {"url": url, "payload": payload, "token": token})
        
        print("Success:", resp.get("success"))
        data = resp.get("data", {})
        if isinstance(data, dict):
            print("Top-level keys:", list(data.keys()))
            print("totalElements:", data.get("totalElements"))
            print("totalPages:", data.get("totalPages"))
            content = data.get("content", [])
            print(f"Content count: {len(content)}")
            if content:
                item0 = content[0]
                print("\n--- FIRST ITEM TOP-LEVEL KEYS ---")
                print(list(item0.keys()))
                print("\n--- FIRST ITEM fields (no regionSummary) ---")
                for k, v in item0.items():
                    if k != "regionSummary":
                        print(f"  {k}: {v}")
                regions = item0.get("regionSummary", [])
                print(f"\n--- regionSummary count: {len(regions)} ---")
                if regions:
                    print("regionSummary[0] keys:", list(regions[0].keys()))
                    print(json.dumps(regions[0], indent=2))
                    if len(regions) > 1:
                        print(json.dumps(regions[1], indent=2))
            else:
                print("Content KOSONG!")
        else:
            print("Data bukan dict:", resp)

if __name__ == "__main__":
    asyncio.run(main())
