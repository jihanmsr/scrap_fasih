import asyncio
import os
import json
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

        async def fetch_count(kab_id, filter_type):
            payload = {
                "start": 0, "length": 1, "columns": [{"data": "id"}], "order": [], "search": {"value": "", "regex": False},
                "assignmentExtraParam": {
                    "region1Id": "5214ecb2-bef1-4a86-9446-451cf430928e",
                    "region2Id": kab_id,
                    "surveyPeriodId": "fd68e454-ba45-4b85-8205-f3bf777ded24",
                    "assignmentErrorStatusType": -1,
                    "filterTargetType": filter_type
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
            
            if "error" in res:
                return -1, res["error"]
            
            # totalHit is the total records in that category
            total_hit = res.get("totalHit", 0)
            return total_hit, None

        print(f"{'Kabupaten':<30} | {'BPS Target API':<15} | {'BPS Non-Target API':<18}")
        print("-" * 70)
        
        sum_targets = 0
        sum_nontargets = 0
        
        for k in kabs:
            t_count, err_t = await fetch_count(k["id"], "target")
            nt_count, err_nt = await fetch_count(k["id"], "non-target")
            
            print(f"{k['name']:<30} | {t_count:<15} | {nt_count:<18}")
            if t_count != -1:
                sum_targets += t_count
            if nt_count != -1:
                sum_nontargets += nt_count
            await asyncio.sleep(0.5)

        print("-" * 70)
        print(f"{'TOTAL':<30} | {sum_targets:<15} | {sum_nontargets:<18}")

if __name__ == "__main__":
    asyncio.run(main())
