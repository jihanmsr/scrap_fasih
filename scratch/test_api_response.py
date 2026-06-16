import asyncio
import json
import os
import socket
from playwright.async_api import async_playwright
from urllib.parse import unquote

USER_DATA_DIR = "playwright_chrome_profile"

def check_port_open(port=9222):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0
    except:
        return False

async def main():
    async with async_playwright() as p:
        # Connect to Chrome
        port = 9223 if check_port_open(9223) else 9222
        print(f"Connecting to Chrome on port {port}...")
        try:
            browser = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
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
            print("Failed to connect to browser context:", e)
            return

        cookies = await page.context.cookies()
        xsrf_token_raw = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), "")
        xsrf_token = unquote(xsrf_token_raw)
        
        # Test query for one kabupaten (Banggai Kepulauan)
        # SE Umum period ID: fd68e454-ba45-4b85-8205-f3bf777ded24
        # Prov ID: 5214ecb2-bef1-4a86-9446-451cf430928e
        # Banggai Kepulauan ID: bc32354f-1245-426f-b2cf-a5733e1295ad
        
        payload_target = {
            "start": 0, "length": 1, "columns": [{"data": "id"}], "order": [], "search": {"value": "", "regex": False},
            "assignmentExtraParam": {
                "region1Id": "5214ecb2-bef1-4a86-9446-451cf430928e",
                "region2Id": "bc32354f-1245-426f-b2cf-a5733e1295ad",
                "surveyPeriodId": "fd68e454-ba45-4b85-8205-f3bf777ded24",
                "assignmentErrorStatusType": -1,
                "filterTargetType": "target"
            }
        }
        
        payload_nontarget = {
            "start": 0, "length": 1, "columns": [{"data": "id"}], "order": [], "search": {"value": "", "regex": False},
            "assignmentExtraParam": {
                "region1Id": "5214ecb2-bef1-4a86-9446-451cf430928e",
                "region2Id": "bc32354f-1245-426f-b2cf-a5733e1295ad",
                "surveyPeriodId": "fd68e454-ba45-4b85-8205-f3bf777ded24",
                "assignmentErrorStatusType": -1,
                "filterTargetType": "non-target"
            }
        }

        async def fetch(payload):
            return await page.evaluate("""
                async ({payload, token}) => {
                    const r = await fetch("https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode", {
                        method: "POST",
                        headers: { "Content-Type": "application/json", "X-XSRF-TOKEN": token },
                        body: JSON.stringify(payload)
                    });
                    return await r.json();
                }
            """, {"payload": payload, "token": xsrf_token})

        # Test query for daily progress (SUBMITTED RESPONDENT status)
        payload_progress = {
            "start": 0,
            "length": 5,
            "columns": [
                {"data": "id"},
                {"data": "codeIdentity"},
                {"data": "data1"},
                {"data": "dateCreated"},
                {"data": "dateModified"},
                {"data": "assignmentStatusAlias"}
            ],
            "order": [],
            "search": {"value": "", "regex": False},
            "assignmentExtraParam": {
                "region1Id": "5214ecb2-bef1-4a86-9446-451cf430928e",
                "surveyPeriodId": "fd68e454-ba45-4b85-8205-f3bf777ded24",
                "assignmentStatusAlias": "SUBMITTED RESPONDENT",
                "assignmentErrorStatusType": -1,
                "filterTargetType": ""
            }
        }

        print("\nFetching daily progress info...")
        res_progress = await fetch(payload_progress)
        print("PROGRESS RESPONSE:")
        print("totalHit:", res_progress.get("totalHit"))
        search_data_progress = res_progress.get("searchData", [])
        if search_data_progress:
            print("Sample progress record:")
            print(json.dumps(search_data_progress[0], indent=2))
            print("Distinct codeIdentity samples:")
            for item in search_data_progress[:5]:
                print(f"  - codeIdentity: {item.get('codeIdentity')}")
                region = item.get("region", {})
                lvl2 = region.get("level1", {}).get("level2", {}) or {} if region else {}
                print(f"    Region level2: {lvl2.get('fullCode')} - {lvl2.get('name')}")
        else:
            print("No daily progress records found.")

if __name__ == "__main__":
    asyncio.run(main())
