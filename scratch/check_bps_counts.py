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
            logging.error("Could not connect to any running Chrome instance on port 9222, 9223, or 9224.")
            return

        context = browser.contexts[0]
        page = None
        for p_page in context.pages:
            if "fasih-sm.bps.go.id" in p_page.url:
                page = p_page
                break
        
        page = await context.new_page()
        try:
            await page.goto("https://fasih-sm.bps.go.id/app/dashboard", wait_until="domcontentloaded", timeout=15000)
        except Exception as e:
            logging.warning(f"Failed to navigate to dashboard: {e}")

        # Get session details
        cookies = await context.cookies()
        token_raw = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), None)
        if not token_raw:
            logging.error("XSRF-TOKEN cookie not found in browser. Make sure you are logged in.")
            return
        token = unquote(token_raw)

        # Detect surveyPeriodId from active URL
        current_url = page.url
        logging.info(f"Current page URL: {current_url}")
        
        import re
        survey_period_id = "37526b20-81c8-42f5-a895-6190137d7394" # fallback
        match = re.search(r"/surveys/([a-f0-9\-]+)/([a-f0-9\-]+)", current_url)
        if match:
            survey_period_id = match.group(2)
            logging.info(f"Detected surveyPeriodId: {survey_period_id}")
        else:
            logging.warning(f"Could not parse surveyPeriodId from URL. Using default fallback: {survey_period_id}")

        # Resolve Kabupaten UUIDs programmatically
        kab_codes = ["7201", "7202", "7203", "7204", "7205", "7206", "7207", "7208", "7209", "7210", "7211", "7212", "7271"]
        
        # We will query levels to get the exact mapping
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
                logging.error(f"Error fetching uuid for {code}: {e}")

        logging.info(f"Resolved {len(uuid_map)} kabupaten UUIDs.")

        datatable_url = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode"
        
        grand_total = 0
        target_total = 0
        nontarget_total = 0

        print("\n=== KABUPATEN DATA COUNTS ===")
        print(f"{'Kab Code':<10} | {'Kab Name':<30} | {'Total Hit (Semua)':<20} | {'Target':<10} | {'Non-Target':<10}")
        print("-" * 90)

        for code in kab_codes:
            if code not in uuid_map:
                print(f"{code:<10} | {'[NOT RESOLVED]':<30} | {'N/A':<20} | {'N/A':<10} | {'N/A':<10}")
                continue
            
            kab_id = uuid_map[code]["id"]
            kab_name = uuid_map[code]["name"]

            # Query total (Semua)
            payload_semua = {
                "start": 0,
                "length": 1,
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

            # Query Target
            payload_target = {
                "start": 0,
                "length": 1,
                "columns": [{"data": "id"}],
                "order": [],
                "search": {"value": "", "regex": False},
                "assignmentExtraParam": {
                    "region1Id": "a00c8aef-afc4-4d4f-b80d-789a15450ef9",
                    "region2Id": kab_id,
                    "surveyPeriodId": survey_period_id,
                    "assignmentErrorStatusType": -1,
                    "filterTargetType": "target"
                }
            }

            # Query Non-Target
            payload_nontarget = {
                "start": 0,
                "length": 1,
                "columns": [{"data": "id"}],
                "order": [],
                "search": {"value": "", "regex": False},
                "assignmentExtraParam": {
                    "region1Id": "a00c8aef-afc4-4d4f-b80d-789a15450ef9",
                    "region2Id": kab_id,
                    "surveyPeriodId": survey_period_id,
                    "assignmentErrorStatusType": -1,
                    "filterTargetType": "non-target"
                }
            }

            try:
                res_semua = await page.evaluate(f"fetch('{datatable_url}', {{ method: 'POST', headers: {{ 'Content-Type': 'application/json', 'X-XSRF-TOKEN': '{token}' }}, body: JSON.stringify({json.dumps(payload_semua)}) }}).then(r => r.json())")
                res_target = await page.evaluate(f"fetch('{datatable_url}', {{ method: 'POST', headers: {{ 'Content-Type': 'application/json', 'X-XSRF-TOKEN': '{token}' }}, body: JSON.stringify({json.dumps(payload_target)}) }}).then(r => r.json())")
                res_nontarget = await page.evaluate(f"fetch('{datatable_url}', {{ method: 'POST', headers: {{ 'Content-Type': 'application/json', 'X-XSRF-TOKEN': '{token}' }}, body: JSON.stringify({json.dumps(payload_nontarget)}) }}).then(r => r.json())")
                
                hits_semua = res_semua.get("totalHit", 0)
                hits_target = res_target.get("totalHit", 0)
                hits_nontarget = res_nontarget.get("totalHit", 0)
                
                print(f"{code:<10} | {kab_name:<30} | {hits_semua:<20} | {hits_target:<10} | {hits_nontarget:<10}")
                grand_total += hits_semua
                target_total += hits_target
                nontarget_total += hits_nontarget
            except Exception as e:
                print(f"{code:<10} | {kab_name:<30} | ERROR: {e}")

        print("-" * 90)
        print(f"{'TOTAL':<10} | {'':<30} | {grand_total:<20} | {target_total:<10} | {nontarget_total:<10}\n")

if __name__ == "__main__":
    asyncio.run(main())
