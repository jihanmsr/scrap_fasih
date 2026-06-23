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
            print("Failed to connect:", e)
            return

        cookies = await page.context.cookies()
        xsrf_token_raw = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), "")
        xsrf_token = unquote(xsrf_token_raw)

        url = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode"

        async def fetch_agg(filter_type):
            payload = {
                "start": 0, "length": 1, "columns": [{"data": "id"}], "order": [], "search": {"value": "", "regex": False},
                "assignmentExtraParam": {
                    "region1Id": "5214ecb2-bef1-4a86-9446-451cf430928e", # Prov Sulteng
                    "region2Id": "bc32354f-1245-426f-b2cf-a5733e1295ad", # Banggai Kepulauan
                    "surveyPeriodId": "fd68e454-ba45-4b85-8205-f3bf777ded24", # SE Umum
                    "assignmentErrorStatusType": -1,
                    "filterTargetType": filter_type
                }
            }
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

        for f_type in ["target", "non-target", ""]:
            res = await fetch_agg(f_type)
            if "error" in res:
                print(f"Filter: '{f_type}' -> Error: {res['error']}")
                continue
            
            total_hit = res.get("totalHit")
            agg = res.get("searchAggregation", [])
            print(f"\nFilter: '{f_type}' -> totalHit: {total_hit}")
            print("searchAggregation:")
            for item in agg:
                print(f"  {item.get('keyAggregation')}: {item.get('docCount')}")
            print(f"  SUM of docCount: {sum(item.get('docCount', 0) for item in agg)}")

if __name__ == "__main__":
    asyncio.run(main())
