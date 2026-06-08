import asyncio
from playwright.async_api import async_playwright
import json

async def main():
    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
            print("Connected to Chrome.")
        except Exception as e:
            print("Failed to connect to Chrome:", e)
            return

        context = browser.contexts[0]
        page = context.pages[0] if context.pages else await context.new_page()
        
        cookies = await context.cookies()
        token = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), None)
        if not token:
            print("XSRF-TOKEN not found.")
            return
            
        from urllib.parse import unquote
        token = unquote(token)
        
        group_id = "a45adac1-e711-4c15-b3f9-1f30fc151565" # SENSUS EKONOMI 2026 region group ID
        period_id = "fd68e454-ba45-4b85-8205-f3bf777ded24" # SE2026 PENDATAAN
        
        # We will fetch kecamatans for Banggai (7202)
        url_kecs = f"https://fasih-sm.bps.go.id/app/api/region/api/v1/region/custom-by-smallest-code-and-level?groupId={group_id}&smallestLevelFullCode=7202&level=2"
        res_kecs = await page.evaluate("""
            async ({url, token}) => {
                const r = await fetch(url, { headers: { "X-XSRF-TOKEN": token } });
                return await r.json();
            }
        """, {"url": url_kecs, "token": token})
        
        if not res_kecs.get("success") or "data" not in res_kecs:
            print("Failed to fetch kecamatans:", res_kecs)
            return
            
        # Let's print level 3 children of 7202
        # Under level 2, we have the kabupaten itself, let's see if children contains level 3
        level2_data = res_kecs["data"]
        children = level2_data.get("children", [])
        print(f"Found {len(children)} children at level 3 (Kecamatan):")
        
        datatable_url = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode"
        
        total_banggai = 0
        for kec in children:
            kec_id = kec.get("id")
            kec_name = kec.get("name")
            kec_code = kec.get("code")
            
            payload = {
                "start": 0, "length": 1, "columns": [{"data": "id"}], "order": [], "search": {"value": "", "regex": False},
                "assignmentExtraParam": {
                    "region1Id": "5214ecb2-bef1-4a86-9446-451cf430928e", # Sulawesi Tengah
                    "region2Id": "530e9ca5-86ba-434e-9b04-405102e6d900", # Banggai
                    "region3Id": kec_id,
                    "surveyPeriodId": period_id,
                    "assignmentErrorStatusType": -1,
                    "filterTargetType": ""
                }
            }
            
            res_dt = await page.evaluate("""
                async ({url, payload, token}) => {
                    const r = await fetch(url, {
                        method: "POST",
                        headers: { "Content-Type": "application/json", "X-XSRF-TOKEN": token },
                        body: JSON.stringify(payload)
                    });
                    return await r.json();
                }
            """, {"url": datatable_url, "payload": payload, "token": token})
            
            count = res_dt.get("totalHit", 0)
            print(f"  Kec: [{kec_code}] {kec_name:<25} | ID: {kec_id} | count: {count}")
            total_banggai += count
            
        print(f"\nSum of all kecamatans in Banggai: {total_banggai}")

if __name__ == "__main__":
    asyncio.run(main())
