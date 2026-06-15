import asyncio
import json
import os
import sys
import socket
from datetime import datetime
from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv()
DATATABLE_URL = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode"

with open("region_map_sulteng.json", "r") as f:
    REGION_MAP = json.load(f)

with open("region_map_sulteng_full.json", "r") as f:
    REGION_MAP_FULL = json.load(f)

async def check_port_open(port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0
    except:
        return False

async def main():
    async with async_playwright() as p:
        browser = None
        for port in [9223, 9222]:
            if await check_port_open(port):
                try:
                    browser = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
                    print(f"Connected to browser on port {port}")
                    break
                except Exception as e:
                    print(f"Failed to connect to port {port}: {e}")
        if not browser:
            print("No active browser found on port 9222 or 9223")
            return

        context = browser.contexts[0]
        page = None
        for p_page in context.pages:
            if "fasih-sm.bps.go.id" in p_page.url:
                page = p_page
                break
        if not page:
            page = context.pages[0]

        cookies = await context.cookies()
        token = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), None)
        if token:
            from urllib.parse import unquote
            token = unquote(token)
        print(f"Token: {token[:15]}...")

        # Query only a single Kabupaten to test (BUOL)
        kab_cfg = {"id": "c523694a-2e72-4570-9489-da2d7b119fe7", "name": "[07] BUOL"}
        kec_list = REGION_MAP.get("7207", {}).get("kecamatan", [])
        print(f"BUOL has {len(kec_list)} kecamatans")

        sem = asyncio.Semaphore(5)

        async def fetch_one(kec):
            kec_id = kec["id"]
            kec_name = kec["name"]
            print(f"Starting Kec: {kec_name} ({kec_id})")
            payload = {
                "start": 0, "length": 50, "columns": [{"data": "id"}], "order": [],
                "search": {"value": "", "regex": False},
                "assignmentExtraParam": {
                    "region1Id": "5214ecb2-bef1-4a86-9446-451cf430928e", 
                    "region2Id": kab_cfg["id"],
                    "region3Id": kec_id,
                    "surveyPeriodId": "fd68e454-ba45-4b85-8205-f3bf777ded24", 
                    "assignmentErrorStatusType": -1, 
                    "filterTargetType": ""
                }
            }
            async with sem:
                try:
                    res = await page.evaluate("""
                        async ({url, payload, token}) => {
                            try {
                                const r = await fetch(url, {
                                    method: "POST",
                                    headers: { "Content-Type": "application/json", "X-XSRF-TOKEN": token },
                                    body: JSON.stringify(payload)
                                });
                                if (!r.ok) return { error: `HTTP ${r.status}` };
                                return await r.json();
                            } catch (e) {
                                return { error: e.toString() };
                            }
                        }
                    """, {"url": DATATABLE_URL, "payload": payload, "token": token})
                    print(f"Finished Kec: {kec_name}, hit={res.get('totalHit', 'N/A')}")
                    return res
                except Exception as e:
                    print(f"Error Kec: {kec_name}: {e}")
                    return None

        tasks = [fetch_one(kec) for kec in kec_list]
        print("Gathering tasks...")
        results = await asyncio.gather(*tasks)
        print("Completed gathering!")

asyncio.run(main())
