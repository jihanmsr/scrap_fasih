import asyncio
import json
import os
import socket
from urllib.parse import unquote
from playwright.async_api import async_playwright

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
            # Connect using localhost to prevent IPv6/IPv4 lookup blocks on Mac
            browser = await p.chromium.connect_over_cdp(f"http://localhost:{port}")
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

        # Kabupaten configurations
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

        async def fetch_agg(kab_id):
            payload = {
                "start": 0, "length": 1, "columns": [{"data": "id"}], "order": [], "search": {"value": "", "regex": False},
                "assignmentExtraParam": {
                    "region1Id": "5214ecb2-bef1-4a86-9446-451cf430928e",
                    "region2Id": kab_id,
                    "surveyPeriodId": "fd68e454-ba45-4b85-8205-f3bf777ded24",
                    "assignmentErrorStatusType": -1,
                    "filterTargetType": "target"
                }
            }
            url = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode"
            res = await page.evaluate("""
                async ({url, payload, token}) => {
                    const r = await fetch(url, {
                        method: "POST",
                        headers: { "Content-Type": "application/json", "X-XSRF-TOKEN": token },
                        body: JSON.stringify(payload)
                    });
                    if (!r.ok) return { error: `HTTP ${r.status}` };
                    return await r.json();
                }
            """, {"url": url, "payload": payload, "token": xsrf_token})
            return res

        print(f"{'Kabupaten':<30} | {'totalHit':<10} | {'Sum of docCount in searchAggregation':<36}")
        print("-" * 80)
        
        grand_total_hit = 0
        grand_sum_doc_count = 0
        
        for k in kabs:
            res = await fetch_agg(k["id"])
            if "error" in res:
                print(f"{k['name']:<30} | Error: {res['error']}")
                continue
                
            total_hit = res.get("totalHit", 0)
            agg = res.get("searchAggregation", [])
            sum_doc_count = sum(item.get("docCount", 0) for item in agg)
            
            print(f"{k['name']:<30} | {total_hit:<10} | {sum_doc_count:<36}")
            grand_total_hit += total_hit
            grand_sum_doc_count += sum_doc_count
            await asyncio.sleep(0.3)

        print("-" * 80)
        print(f"{'TOTAL':<30} | {grand_total_hit:<10} | {grand_sum_doc_count:<36}")

if __name__ == "__main__":
    asyncio.run(main())
