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
    port = 9223 if check_port_open(9223) else 9222
    print(f"Connecting to Chrome on port {port}...")
    
    async with async_playwright() as p:
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
        
        # Test 1: Order by column 5 (dateModified)
        payload_order_5 = {
            "start": 0,
            "length": 5,
            "columns": [
                {"data": "id"},
                {"data": "codeIdentity"},
                {"data": "data1"},
                {"data": "data6"},
                {"data": "dateCreated"},
                {"data": "dateModified"},
                {"data": "assignmentStatusAlias"},
                {"data": "region"}
            ],
            "order": [{"column": 5, "dir": "desc"}],
            "search": {"value": "", "regex": False},
            "assignmentExtraParam": {
                "region1Id": "5214ecb2-bef1-4a86-9446-451cf430928e",
                "region2Id": "bc32354f-1245-426f-b2cf-a5733e1295ad", # BANGGAI KEPULAUAN
                "region3Id": "",
                "region4Id": "",
                "region5Id": "",
                "surveyPeriodId": "fd68e454-ba45-4b85-8205-f3bf777ded24",
                "assignmentErrorStatusType": -1,
                "filterTargetType": ""
            }
        }
        
        # Test 2: Empty order
        payload_no_order = dict(payload_order_5)
        payload_no_order["order"] = []

        # Test 2: Empty order
        payload_no_order = dict(payload_order_5)
        payload_no_order["order"] = []

        # Test 3: Provincial level (No region2Id)
        payload_prov = {
            "start": 0,
            "length": 5,
            "columns": [
                {"data": "id"},
                {"data": "codeIdentity"},
                {"data": "data1"},
                {"data": "data6"},
                {"data": "dateCreated"},
                {"data": "dateModified"},
                {"data": "assignmentStatusAlias"},
                {"data": "region"}
            ],
            "order": [],
            "search": {"value": "", "regex": False},
            "assignmentExtraParam": {
                "region1Id": "5214ecb2-bef1-4a86-9446-451cf430928e",
                "surveyPeriodId": "fd68e454-ba45-4b85-8205-f3bf777ded24",
                "assignmentErrorStatusType": -1,
                "filterTargetType": ""
            }
        }

        print("\n--- Test 1: Query with order by dateModified (column 5) ---")
        res1 = await page.evaluate("""
            async ({payload, token}) => {
                const r = await fetch("https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode", {
                    method: "POST",
                    headers: { "Content-Type": "application/json", "X-XSRF-TOKEN": token },
                    body: JSON.stringify(payload)
                });
                return await r.json();
            }
        """, {"payload": payload_order_5, "token": xsrf_token})
        print(f"Total Hit (Order 5): {res1.get('totalHit')}")
        print(f"Records count: {len(res1.get('searchData', []))}")
        if "error" in res1 or "_error" in res1:
            print("Response contains error:", res1)

        print("\n--- Test 2: Query with order = [] ---")
        res2 = await page.evaluate("""
            async ({payload, token}) => {
                const r = await fetch("https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode", {
                    method: "POST",
                    headers: { "Content-Type": "application/json", "X-XSRF-TOKEN": token },
                    body: JSON.stringify(payload)
                });
                return await r.json();
            }
        """, {"payload": payload_no_order, "token": xsrf_token})
        print(f"Total Hit (No Order): {res2.get('totalHit')}")
        print(f"Records count: {len(res2.get('searchData', []))}")
        if "error" in res2 or "_error" in res2:
            print("Response contains error:", res2)

        print("\n--- Test 3: Provincial Level (No region2Id) ---")
        res3 = await page.evaluate("""
            async ({payload, token}) => {
                const r = await fetch("https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode", {
                    method: "POST",
                    headers: { "Content-Type": "application/json", "X-XSRF-TOKEN": token },
                    body: JSON.stringify(payload)
                });
                return await r.json();
            }
        """, {"payload": payload_prov, "token": xsrf_token})
        print(f"Total Hit (Prov): {res3.get('totalHit')}")
        print(f"Records count: {len(res3.get('searchData', []))}")
        if "error" in res3 or "_error" in res3:
            print("Response contains error:", res3)

if __name__ == "__main__":
    asyncio.run(main())
