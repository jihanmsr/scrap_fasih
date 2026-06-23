import asyncio
import json
import os
import csv
from playwright.async_api import async_playwright

async def fetch_api_safely(page, url, payload, xsrf_token, max_retries=3):
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "X-Xsrf-Token": xsrf_token,
    }
    for attempt in range(max_retries):
        try:
            res = await page.evaluate(f'''async () => {{
                try {{
                    const response = await fetch("{url}", {{
                        method: "POST",
                        headers: {json.dumps(headers)},
                        body: JSON.stringify({json.dumps(payload)})
                    }});
                    if (!response.ok) return {{error: response.statusText}};
                    return await response.json();
                }} catch (e) {{ return {{error: e.message}}; }}
            }}''')
            if res and "error" not in res:
                return res
            await asyncio.sleep(1)
        except Exception as e:
            pass
    return None

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            user_data_dir="playwright_chrome_profile",
            executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )
        page = browser.pages[0]
        await page.goto("https://fasih-sm.bps.go.id/app/surveys", wait_until="networkidle")

        xsrf_match = await page.evaluate("document.cookie.match(/XSRF-TOKEN=([^;]+)/)")
        if not xsrf_match:
            print("Tidak menemukan XSRF-TOKEN di profil Chrome ini.")
            await browser.close()
            return
            
        xsrf_token = xsrf_match[1].replace("%3D", "=")
        
        prov_id = "07fbcbf0-3eeb-4bc2-af82-595304bc2b6f"
        period_id = "fd68e454-ba45-4b85-8205-f3bf777ded24"
        datatable_url = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode"

        with open("region_map_sulteng.json", "r") as f:
            survey_cfg = json.load(f)

        error_records = []
        
        print("Mengambil data error/dropped target dari API...")
        for kab in survey_cfg["kabs"]:
            for status_type in [1, 2]:
                start = 0
                while True:
                    payload = {
                        "start": start, "length": 1000, 
                        "columns": [{"data": "id"}, {"data": "codeIdentity"}, {"data": "data1"}, {"data": "assignmentErrorStatusAlias"}], 
                        "order": [], "search": {"value": "", "regex": False},
                        "assignmentExtraParam": {
                            "region1Id": prov_id,
                            "region2Id": kab["id"],
                            "surveyPeriodId": period_id,
                            "assignmentErrorStatusType": status_type,
                            "filterTargetType": "target"
                        }
                    }
                    res = await fetch_api_safely(page, datatable_url, payload, xsrf_token)
                    if not res or "searchData" not in res:
                        break
                        
                    records = res["searchData"]
                    if not records:
                        break
                        
                    for r in records:
                        error_records.append({
                            "id": r.get("id"),
                            "codeIdentity": r.get("codeIdentity"),
                            "name": r.get("data1"),
                            "kabupaten": kab["name"],
                            "errorType": r.get("assignmentErrorStatusAlias", "Error/Dropped") if "assignmentErrorStatusAlias" in r else ("Error" if status_type == 1 else "Dropped")
                        })
                    
                    start += 1000
                    if start >= res.get("totalHit", 0):
                        break
        
        print(f"Selesai! Ditemukan {len(error_records)} assignment Error/Dropped.")
        
        # Save to CSV
        csv_filename = "csv_reports/error_dropped_assignments.csv"
        os.makedirs("csv_reports", exist_ok=True)
        with open(csv_filename, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=["id", "codeIdentity", "name", "kabupaten", "errorType"])
            writer.writeheader()
            for row in error_records:
                writer.writerow(row)
        print(f"Data disimpan ke {csv_filename}")
        await browser.close()

asyncio.run(main())
