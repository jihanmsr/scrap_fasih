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

        # Let's query for Banggai Kepulauan (region2Id: "bc32354f-1245-426f-b2cf-a5733e1295ad")
        # and Kecamatan Tinangkung (region3Id: "c2058097-f5ea-4be0-865f-4a0b22a08892")
        kab_id = "bc32354f-1245-426f-b2cf-a5733e1295ad"
        kec_id = "c2058097-f5ea-4be0-865f-4a0b22a08892"

        async def fetch_results(filter_type):
            payload = {
                "start": 0, "length": 1, "columns": [{"data": "id"}], "order": [], "search": {"value": "", "regex": False},
                "assignmentExtraParam": {
                    "region1Id": "5214ecb2-bef1-4a86-9446-451cf430928e",
                    "region2Id": kab_id,
                    "region3Id": kec_id,
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
            return res

        for ftype in ["target", "non-target", ""]:
            res = await fetch_results(ftype)
            total_hit = res.get("totalHit", 0)
            agg = res.get("searchAggregation", [])
            agg_sum = sum(item.get("docCount", 0) for item in agg)
            print(f"\nResults for filterTargetType='{ftype}':")
            print(f"  totalHit: {total_hit}")
            print(f"  searchAggregation sum: {agg_sum}")
            print("  searchAggregation details:")
            for item in agg:
                print(f"    {item.get('keyAggregation')}: {item.get('docCount')}")

if __name__ == "__main__":
    asyncio.run(main())
