import asyncio
import json
import logging
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
        # Open a new tab and navigate to BPS to bypass CORS
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

        survey_period_id = "37526b20-81c8-42f5-a895-6190137d7394"

        # Resolve Kabupaten UUIDs
        kab_codes = ["7201", "7202", "7203", "7204", "7205", "7206", "7207", "7208", "7209", "7210", "7211", "7212", "7271"]
        uuid_map = {}
        for code in kab_codes:
            url = f"https://fasih-sm.bps.go.id/app/api/region/api/v1/region/custom-by-smallest-code-and-level?groupId=6b0b053f-aa43-4855-ac8f-26857b735c93&smallestLevelFullCode={code}&level=2"
            try:
                res = await page.evaluate(f"fetch('{url}', {{ headers: {{ 'X-XSRF-TOKEN': '{token}' }} }}).then(r => r.json())")
                if res and res.get("success") and res.get("data"):
                    level2 = res["data"].get("level1", {}).get("level2")
                    if level2:
                        uuid_map[code] = { "id": level2["id"], "name": level2["name"] }
            except Exception as e:
                pass

        datatable_url = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode"
        
        print("\n=== DETAILED API RECORD CHECK ===")
        print(f"{'Kab':<6} | {'Kab Name':<25} | {'totalHit':<8} | {'Fetched searchData':<18} | {'Discrepancy':<12}")
        print("-" * 75)

        grand_total_hit = 0
        grand_total_fetched = 0

        for code in kab_codes:
            if code not in uuid_map:
                continue
            kab_id = uuid_map[code]["id"]
            kab_name = uuid_map[code]["name"]

            # Query all records
            all_companies = []
            start_index = 0
            page_length = 100
            total_hit = 0

            while True:
                payload = {
                    "start": start_index,
                    "length": page_length,
                    "columns": [{"data": "id"}],
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
                    res = await page.evaluate(f"fetch('{datatable_url}', {{ method: 'POST', headers: {{ 'Content-Type': 'application/json', 'X-XSRF-TOKEN': '{token}' }}, body: JSON.stringify({json.dumps(payload)}) }}).then(r => r.json())")
                    companies_part = res.get("searchData", [])
                    total_hit = res.get("totalHit", 0)
                    all_companies.extend(companies_part)
                    
                    if not companies_part:
                        break
                    
                    start_index += page_length
                    if start_index >= total_hit:
                        break
                except Exception as e:
                    logging.error(f"Error fetching for {code}: {e}")
                    break

            discrepancy = total_hit - len(all_companies)
            print(f"{code:<6} | {kab_name:<25} | {total_hit:<8} | {len(all_companies):<18} | {discrepancy:<12}")
            grand_total_hit += total_hit
            grand_total_fetched += len(all_companies)

        print("-" * 75)
        print(f"{'TOTAL':<6} | {'':<25} | {grand_total_hit:<8} | {grand_total_fetched:<18} | {grand_total_hit - grand_total_fetched:<12}\n")

if __name__ == "__main__":
    asyncio.run(main())
