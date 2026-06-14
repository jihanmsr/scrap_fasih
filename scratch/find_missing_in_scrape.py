import asyncio
import json
import logging
import requests
from playwright.async_api import async_playwright
from urllib.parse import unquote

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def main():
    async with async_playwright() as p:
        browser = None
        for port in [9223]:
            try:
                browser = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
                logging.info(f"Connected to Chrome on port {port}")
                break
            except Exception:
                pass
        
        if not browser:
            logging.error("Could not connect to Chrome on port 9223.")
            return

        context = browser.contexts[0]
        page = await context.new_page()
        try:
            await page.goto("https://fasih-sm.bps.go.id/app/dashboard", wait_until="domcontentloaded", timeout=15000)
        except Exception as e:
            logging.warning(f"Failed to navigate: {e}")

        cookies = await context.cookies()
        token_raw = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), None)
        if not token_raw:
            logging.error("XSRF-TOKEN not found.")
            return
        token = unquote(token_raw)

        # Build cookie header and session using the exact logic from scrape_via_api.py
        http_session = requests.Session()
        for c in cookies:
            http_session.cookies.set(
                c['name'],
                c['value'],
                domain=c.get('domain', 'fasih-sm.bps.go.id'),
                path=c.get('path', '/')
            )
        headers = {
            "Content-Type": "application/json",
            "X-XSRF-TOKEN": token,
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*"
        }
        http_session.headers.update(headers)

        survey_period_id = "37526b20-81c8-42f5-a895-6190137d7394"

        # Resolve Kabupaten UUIDs programmatically
        kab_codes = ["7201", "7202", "7203", "7204", "7205", "7206", "7207", "7208", "7209", "7210", "7211", "7212", "7271"]
        uuid_map = {}
        for code in kab_codes:
            url = f"https://fasih-sm.bps.go.id/app/api/region/api/v1/region/custom-by-smallest-code-and-level?groupId=6b0b053f-aa43-4855-ac8f-26857b735c93&smallestLevelFullCode={code}&level=2"
            try:
                res = http_session.get(url, timeout=30).json()
                if res and res.get("success") and res.get("data"):
                    level2 = res["data"].get("level1", {}).get("level2")
                    if level2:
                        uuid_map[code] = { "id": level2["id"], "name": level2["name"] }
            except Exception as e:
                pass

        datatable_url = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode"
        
        print("\n=== RUNNING EXACT SCRAPE LOOP ===")
        print(f"{'Kab':<6} | {'Kab Name':<25} | {'totalHit':<8} | {'Fetched':<8}")
        print("-" * 55)

        grand_total_fetched = 0

        for code in kab_codes:
            if code not in uuid_map:
                continue
            kab_id = uuid_map[code]["id"]
            kab_name = uuid_map[code]["name"]

            start_index = 0
            page_length = 100
            companies_data = []

            while True:
                payload = {
                    "start": start_index,
                    "length": page_length,
                    "columns": [
                        {"data": "id", "orderable": True},
                        {"data": "codeIdentity", "orderable": True},
                        {"data": "data1", "orderable": True},
                        {"data": "data2", "orderable": True},
                        {"data": "data3", "orderable": True},
                        {"data": "data4", "orderable": True},
                        {"data": "data5", "orderable": True},
                        {"data": "data6", "orderable": True},
                        {"data": "data7", "orderable": True},
                        {"data": "data8", "orderable": True},
                        {"data": "data9", "orderable": True},
                        {"data": "data10", "orderable": True}
                    ],
                    "order": [],
                    "search": {"value": "", "regex": False},
                    "assignmentExtraParam": {
                        "region1Id": "a00c8aef-afc4-4d4f-b80d-789a15450ef9",
                        "region2Id": kab_id,
                        "surveyPeriodId": survey_period_id,
                        "assignmentErrorStatusType": -1,
                        "filterTargetType": ""
                    }
                }

                try:
                    res = http_session.post(datatable_url, json=payload, timeout=60)
                    res_json = res.json()
                    companies_part = res_json.get("searchData", [])
                    total_hits_part = res_json.get("totalHit", 0)

                    companies_data.extend(companies_part)
                    start_index += page_length
                    
                    if start_index >= total_hits_part:
                        break
                except Exception as e:
                    logging.error(f"Error fetching: {e}")
                    break

            print(f"{code:<6} | {kab_name:<25} | {total_hits_part:<8} | {len(companies_data):<8}")
            grand_total_fetched += len(companies_data)

        print("-" * 55)
        print(f"GRAND TOTAL FETCHED: {grand_total_fetched}\n")

if __name__ == "__main__":
    asyncio.run(main())
