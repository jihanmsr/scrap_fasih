import asyncio
import json
import os
import socket
from playwright.async_api import async_playwright
from urllib.parse import unquote

def check_port_open(port=9222):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0
    except:
        return False

async def main():
    async with async_playwright() as p:
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
                "assignmentStatusAlias": "REJECTED BY Pengawas",
                "assignmentErrorStatusType": -1,
                "filterTargetType": ""
            }
        }

        print("Fetching rejected records...")
        res = await page.evaluate("""
            async ({payload, token}) => {
                const r = await fetch("https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode", {
                    method: "POST",
                    headers: { "Content-Type": "application/json", "X-XSRF-TOKEN": token },
                    body: JSON.stringify(payload)
                });
                return await r.json();
            }
        """, {"payload": payload_progress, "token": xsrf_token})
        
        print("REJECTED RECORDS:")
        search_data = res.get("searchData", [])
        print(f"Count: {len(search_data)}")
        if search_data:
            with open("scratch/sample_rejected_records.json", "w") as f:
                json.dump(search_data, f, indent=2)
            print("Successfully saved sample records to scratch/sample_rejected_records.json")
            # Let's inspect keys of the first record
            print("First record keys:", list(search_data[0].keys()))
            
            # Print any fields that might contain comment or reject reason
            for i, rec in enumerate(search_data):
                print(f"\nRecord {i+1} - ID: {rec.get('id')}")
                print(f"codeIdentity: {rec.get('codeIdentity')}")
                # Print assignmentResponsibility status or remarks
                resp = rec.get("assignmentResponsibility", [])
                print(f"assignmentResponsibility count: {len(resp)}")
                if resp:
                    print("Sample responsibility keys:", list(resp[0].keys()))
                    for r_idx, r in enumerate(resp):
                        print(f"  Resp {r_idx+1}: Status={r.get('assignmentResponsibilityStatusId')}, Date={r.get('dateCreated')}")
                        # print any other fields
                        other_fields = {k: v for k, v in r.items() if k not in ['id', 'surveyUserBeforeId', 'surveyUserCurrentId', 'dateCreated', 'isActive', 'beforeUserId', 'currentUserId', 'surveyPeriodId']}
                        print("  Other keys in responsibility:", other_fields)
        else:
            print("No rejected records found.")

if __name__ == "__main__":
    asyncio.run(main())
