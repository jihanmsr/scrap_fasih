import asyncio
import json
import os
import sys
from urllib.parse import unquote
from playwright.async_api import async_playwright

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def main():
    async with async_playwright() as p:
        print("Connecting to Chrome on port 9222...")
        try:
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
            context = browser.contexts[0]
            page = None
            for p_page in context.pages:
                if "fasih-sm.bps.go.id" in p_page.url:
                    page = p_page
                    break
            if not page:
                page = await context.new_page()
                await page.goto("https://fasih-sm.bps.go.id/app/dashboard")
        except Exception as e:
            print("Failed to connect:", e)
            return

        cookies = await page.context.cookies()
        xsrf_token_raw = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), "")
        xsrf_token = unquote(xsrf_token_raw)

        url = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/report-progress-by-responsibility"
        
        async def fetch_responsibility_data(target_type):
            # Query at province level (regionSummaryLevel=2)
            payload = {
                "surveyPeriodId": "fd68e454-ba45-4b85-8205-f3bf777ded24", # SE Umum
                "surveyRoleId": "6d7d919a-45e5-4779-bb87-2905b49fd31a", # Pencacah role
                "size": 100,
                "page": 0,
                "search": "",
                "target": target_type,
                "region": {
                    "region1Id": "5214ecb2-bef1-4a86-9446-451cf430928e", # Sulteng
                    "region2Id": None,
                    "region3Id": None,
                    "region4Id": None,
                    "region5Id": None,
                    "region6Id": None,
                    "region7Id": None,
                    "region8Id": None,
                    "region9Id": None,
                    "region10Id": None
                },
                "regionSummaryLevel": 2 # 2 is Kabupaten level aggregation
            }
            res = await page.evaluate("""
                async ({url, payload, token}) => {
                    const r = await fetch(url, {
                        method: "POST",
                        headers: { "Content-Type": "application/json", "X-XSRF-TOKEN": token },
                        body: JSON.stringify(payload)
                    });
                    if (!r.ok) return { error: `HTTP ${r.status}` };
                    return await r.json();
                }
            """, {"url": url, "payload": payload, "token": xsrf_token})
            return res

        print("Querying TARGET_ONLY...")
        target_only_res = await fetch_responsibility_data("TARGET_ONLY")
        
        print("Querying ALL...")
        all_res = await fetch_responsibility_data("ALL")
        
        def print_summary(label, res):
            if "error" in res:
                print(f"Error for {label}: {res['error']}")
                return
            
            content = res.get("content", [])
            print(f"\nSummary for {label} (count = {len(content)} kabupatens):")
            print(f"{'Kabupaten':<30} | {'Target (Prelist)':<15} | {'Submitted':<10} | {'Approved':<10}")
            print("-" * 75)
            sum_target = 0
            sum_submitted = 0
            sum_approved = 0
            for item in content:
                kab_name = item.get("regionName", "")
                target = item.get("target", 0)
                submitted = item.get("submitted", 0)
                approved = item.get("approved", 0)
                print(f"{kab_name:<30} | {target:<15} | {submitted:<10} | {approved:<10}")
                sum_target += target
                sum_submitted += submitted
                sum_approved += approved
            print("-" * 75)
            print(f"{'TOTAL':<30} | {sum_target:<15} | {sum_submitted:<10} | {sum_approved:<10}")

        print_summary("TARGET_ONLY", target_only_res)
        print_summary("ALL", all_res)

if __name__ == "__main__":
    asyncio.run(main())
