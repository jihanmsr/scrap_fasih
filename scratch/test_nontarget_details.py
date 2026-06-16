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

        # Let's query non-target from Banggai Kepulauan
        payload_nontarget = {
            "start": 0, "length": 500, "columns": [
                {"data": "id"}, {"data": "codeIdentity"}, {"data": "data1"}, {"data": "data6"}, {"data": "assignmentStatusAlias"}
            ], "order": [], "search": {"value": "", "regex": False},
            "assignmentExtraParam": {
                "region1Id": "5214ecb2-bef1-4a86-9446-451cf430928e",
                "region2Id": "bc32354f-1245-426f-b2cf-a5733e1295ad",
                "surveyPeriodId": "fd68e454-ba45-4b85-8205-f3bf777ded24",
                "assignmentErrorStatusType": -1,
                "filterTargetType": "non-target"
            }
        }

        print("Fetching non-targets for Banggai Kepulauan...")
        res_nt = await fetch(payload_nontarget)
        records = res_nt.get("searchData", [])
        print(f"Total non-target records returned: {len(records)}")
        
        tambahan_count = 0
        normal_count = 0
        
        for idx, item in enumerate(records):
            code_id = item.get("codeIdentity") or ""
            parts = [p.strip() for p in code_id.split(" - ")]
            
            # check is_tambahan logic
            is_t = False
            if len(parts) >= 2:
                source = parts[1].upper()
                known_sources = {"DTSEN", "UMK", "UM", "UMB", "UMKM", "SE2026", "SE26", "PDRB", "PAPI", "CAWI", "CAPI"}
                if source not in known_sources and not source.startswith("SE26") and not source.startswith("SE2026"):
                    is_t = True
            
            if is_t:
                tambahan_count += 1
                if tambahan_count <= 20:
                    print(f"[TAMBAHAN] codeIdentity: {code_id} | data1: {item.get('data1')} | data6: {item.get('data6')} | status: {item.get('assignmentStatusAlias')}")
            else:
                normal_count += 1
                if normal_count <= 5:
                    print(f"[NORMAL] codeIdentity: {code_id} | data1: {item.get('data1')} | data6: {item.get('data6')} | status: {item.get('assignmentStatusAlias')}")

        print(f"\nSummary: Total Tambahan: {tambahan_count}, Total Normal: {normal_count}")

if __name__ == "__main__":
    asyncio.run(main())
