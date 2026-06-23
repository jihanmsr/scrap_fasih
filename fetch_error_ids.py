import asyncio
import json
import os
import csv
from urllib.parse import unquote
from playwright.async_api import async_playwright

async def fetch_api_safely(page, url, payload, token, timeout_seconds=120, max_retries=3):
    for attempt in range(1, max_retries + 1):
        try:
            res = await page.evaluate("""
                async ({url, payload, token, timeoutMs}) => {
                    const controller = new AbortController();
                    const id = setTimeout(() => controller.abort(), timeoutMs);
                    try {
                        const fetchOpts = {
                            method: "POST",
                            headers: { "Content-Type": "application/json", "X-XSRF-TOKEN": token },
                            signal: controller.signal,
                            body: JSON.stringify(payload)
                        };
                        const r = await fetch(url, fetchOpts);
                        clearTimeout(id);
                        if (!r.ok) return {error: "HTTP " + r.status};
                        return await r.json();
                    } catch (e) {
                        clearTimeout(id);
                        return {error: e.message};
                    }
                }
            """, {"url": url, "payload": payload, "token": token, "timeoutMs": timeout_seconds * 1000})
            if res and "error" not in res:
                return res
            print(f"Fetch gagal pada percobaan {attempt}: {res}")
            await asyncio.sleep(2)
        except Exception as e:
            print(f"Exception saat fetch_api_safely: {e}")
            await asyncio.sleep(2)
    return None

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            user_data_dir="playwright_chrome_profile",
            executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--no-first-run", "--no-default-browser-check", "--disable-blink-features=AutomationControlled"]
        )
        page = browser.pages[0]
        try:
            await page.goto("https://fasih-sm.bps.go.id/app/dashboard", wait_until="domcontentloaded", timeout=60000)
        except Exception as e:
            print(f"Warning saat memuat halaman: {e}")

        cookies = await page.context.cookies()
        xsrf_token_raw = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), "")
        
        if not xsrf_token_raw:
            print("Tidak menemukan XSRF-TOKEN. Pastikan Anda sudah login di Chrome.")
            await browser.close()
            return
            
        xsrf_token = unquote(xsrf_token_raw)
        
        prov_id = "5214ecb2-bef1-4a86-9446-451cf430928e"
        period_id = "fd68e454-ba45-4b85-8205-f3bf777ded24"
        datatable_url = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode"

        kabs = [
            {"code": "01", "name": "[01] BANGGAI KEPULAUAN", "id": "bc32354f-1245-426f-b2cf-a5733e1295ad"},
            {"code": "02", "name": "[02] BANGGAI", "id": "530e9ca5-86ba-434e-9b04-405102e6d900"},
            {"code": "03", "name": "[03] MOROWALI", "id": "9783f0c1-f047-477f-8840-11eae7cf70e2"},
            {"code": "04", "name": "[04] POSO", "id": "fb9cd9f0-c4c0-4a37-9041-57190693f625"},
            {"code": "05", "name": "[05] DONGGALA", "id": "289f1ff3-a6ad-4c9b-a49f-7b454d03a33f"},
            {"code": "06", "name": "[06] TOLI-TOLI", "id": "d833fdce-ebfb-429b-a1bb-8966239fd8e4"},
            {"code": "07", "name": "[07] BUOL", "id": "c523694a-2e72-4570-9489-da2d7b119fe7"},
            {"code": "08", "name": "[08] PARIGI MOUTONG", "id": "25c59fd9-afd5-4c1a-9dfb-42bb697a7434"},
            {"code": "09", "name": "[09] TOJO UNA-UNA", "id": "736c4c22-51d1-44be-8b2c-aa197d9459a4"},
            {"code": "10", "name": "[10] SIGI", "id": "0061da62-2a47-4dee-b8d0-239b33e2c59d"},
            {"code": "11", "name": "[11] BANGGAI LAUT", "id": "eed1a3e7-b81d-4fc7-b0d6-61257c1449b2"},
            {"code": "12", "name": "[12] MOROWALI UTARA", "id": "d05ef8fd-b5e4-414f-9a83-8cdea03e0767"},
            {"code": "71", "name": "[71] PALU", "id": "4ab6ca2f-7952-4e8e-a94d-b6dd933e5d44"}
        ]

        error_records = []
        
        print("Mengambil data error/dropped target dari API...")
        for kab in kabs:
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
                        print(f"  > Menghentikan paginasi untuk status_type {status_type} di kab {kab['name']} (res invalid)")
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
                            "errorType": r.get("assignmentErrorStatusAlias", "Error/Dropped") if r.get("assignmentErrorStatusAlias") else ("Error" if status_type == 1 else "Dropped")
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

if __name__ == "__main__":
    asyncio.run(main())
