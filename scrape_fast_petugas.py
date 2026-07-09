import asyncio
import json
import os
from playwright.async_api import async_playwright

API_URL = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/report-progress-by-responsibility"

PAYLOAD_TEMPLATE = {
    "surveyPeriodId": "fd68e454-ba45-4b85-8205-f3bf777ded24",
    "surveyRoleId": "93bcf446-c4c1-4462-8ed0-4b0f7ae89e52",
    "size": 100,
    "page": 0,
    "search": "",
    "target": "TARGET_ONLY",
    "region": {
        "region1Id": "5214ecb2-bef1-4a86-9446-451cf430928e",
        "region2Id": "4ab6ca2f-7952-4e8e-a94d-b6dd933e5d44",
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

async def run():
    print("[INFO] Memulai tarikan CEPAT progres petugas (Palu)...")
    async with async_playwright() as p:
        try:
            abs_user_data_dir = os.path.abspath("chrome_profile")
            chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
            
            # Launch persistent context instead of connecting to CDP
            context = await p.chromium.launch_persistent_context(
                user_data_dir=abs_user_data_dir, 
                headless=False, 
                executable_path=chrome_path,
                ignore_default_args=["--enable-automation"],
                args=["--no-first-run", "--no-default-browser-check", "--disable-blink-features=AutomationControlled"]
            )
            
            page = context.pages[0] if context.pages else await context.new_page()
            await page.goto("https://fasih-sm.bps.go.id/")
            
            print(f"[INFO] Terhubung ke halaman: {page.url}")
            await asyncio.sleep(3) # Wait for page to load cookies
            
            all_results = []
            current_page = 0
            
            while True:
                print(f"[INFO] Fetching page {current_page}...")
                payload = PAYLOAD_TEMPLATE.copy()
                payload["page"] = current_page
                
                req_data = {
                    "url": API_URL,
                    "options": {
                        "method": "POST",
                        "headers": {
                            "Content-Type": "application/json",
                            "Accept": "application/json, text/plain, */*"
                        },
                        "body": json.dumps(payload)
                    }
                }
                
                resp = await page.evaluate('''async (req) => {
                    const res = await fetch(req.url, req.options);
                    if (!res.ok) throw new Error("HTTP error " + res.status);
                    return await res.json();
                }''', req_data)
                
                content = resp.get("data", {}).get("content", [])
                if not content:
                    break
                    
                all_results.extend(content)
                current_page += 1
                
            with open("fast_petugas_progress.json", "w") as f:
                json.dump(all_results, f, indent=2)
                
            print(f"[SUCCESS] Berhasil menarik {len(all_results)} petugas Palu.")
            
        except Exception as e:
            print(f"[ERROR] {e}")

if __name__ == "__main__":
    asyncio.run(run())
