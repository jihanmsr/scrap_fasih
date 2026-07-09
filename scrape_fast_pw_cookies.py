import asyncio
import json
from playwright.async_api import async_playwright
import csv

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
    print("[INFO] Memulai tarikan CEPAT dengan Cookies Injeksi...")
    async with async_playwright() as p:
        # Gunakan headless murni
        browser = await p.chromium.launch(headless=True, executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
        context = await browser.new_context()
        
        # Inject cookies from user's cURL
        cookies = [
            {"name": "XSRF-TOKEN", "value": "c406ff8c-a60b-4c5f-90fa-998f55393663", "domain": "fasih-sm.bps.go.id", "path": "/"},
            {"name": "SESSION", "value": "bcc86f50-4d70-4ee2-9549-56b09659236e", "domain": "fasih-sm.bps.go.id", "path": "/"}
        ]
        await context.add_cookies(cookies)
        
        page = await context.new_page()
        
        # Bypass Cloudflare/F5 checking (optional: goto homepage first)
        await page.goto("https://fasih-sm.bps.go.id/")
        await asyncio.sleep(2)
        
        all_results = []
        current_page = 0
        
        while True:
            print(f"Fetching page {current_page}...")
            payload = PAYLOAD_TEMPLATE.copy()
            payload["page"] = current_page
            
            req_data = {
                "url": API_URL,
                "options": {
                    "method": "POST",
                    "headers": {
                        "Content-Type": "application/json",
                        "Accept": "application/json, text/plain, */*",
                        "X-XSRF-TOKEN": "c406ff8c-a60b-4c5f-90fa-998f55393663"
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
            
        csv_file = "/Users/jihanmaisaroh/scrap_fasih/fast_petugas_palu.csv"
        with open(csv_file, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Email", "Role", "Region Code", "Total Target", "OPEN", "DRAFT", "SUBMITTED BY Pencacah", "APPROVED BY Pengawas", "REJECTED BY Pengawas"])
            
            for row in all_results:
                email = row.get("email", "")
                role = "Pencacah" if row.get("isPencacah") else "Pengawas"
                region_summaries = row.get("regionSummary", [])
                for r_sum in region_summaries:
                    reg_code = r_sum.get("regionCode", "")
                    status_breakdown = r_sum.get("statusBreakdown", [])
                    counts = {"OPEN": 0, "DRAFT": 0, "SUBMITTED BY Pencacah": 0, "APPROVED BY Pengawas": 0, "REJECTED BY Pengawas": 0}
                    total = r_sum.get("total", 0)
                    for st in status_breakdown:
                        counts[st.get("status", "")] = st.get("count", 0)
                    writer.writerow([email, role, reg_code, total, counts.get("OPEN",0), counts.get("DRAFT",0), counts.get("SUBMITTED BY Pencacah",0), counts.get("APPROVED BY Pengawas",0), counts.get("REJECTED BY Pengawas",0)])
                    
        print(f"[SUCCESS] Tersimpan di {csv_file}")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
