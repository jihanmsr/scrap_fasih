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

        async def query_datatable(filter_type):
            payload = {
                "start": 0, "length": 1, "columns": [{"data": "id"}], "order": [], "search": {"value": "", "regex": False},
                "assignmentExtraParam": {
                    "region1Id": "5214ecb2-bef1-4a86-9446-451cf430928e", # Prov Sulteng
                    "surveyPeriodId": "fd68e454-ba45-4b85-8205-f3bf777ded24", # SE Umum
                    "assignmentErrorStatusType": -1,
                    "filterTargetType": filter_type
                }
            }
            res = await page.evaluate("""
                async ({payload, token}) => {
                    const r = await fetch("https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode", {
                        method: "POST",
                        headers: { "Content-Type": "application/json", "X-XSRF-TOKEN": token },
                        body: JSON.stringify(payload)
                    });
                    return await r.json();
                }
            """, {"payload": payload, "token": xsrf_token})
            return res

        print("Querying BPS API for target counts...")
        res_target = await query_datatable("target")
        res_nontarget = await query_datatable("non-target")
        res_all = await query_datatable("")

        total_target = res_target.get("totalHit", 0)
        total_nontarget = res_nontarget.get("totalHit", 0)
        total_all = res_all.get("totalHit", 0)

        print(f"\nBPS API reported totals for Prov Sulteng (SE Umum):")
        print(f"  filterTargetType='target': {total_target}")
        print(f"  filterTargetType='non-target': {total_nontarget}")
        print(f"  filterTargetType='': {total_all}")
        print(f"  Sum of Target + Non-target: {total_target + total_nontarget}")
        print(f"  Difference (All - (Target + Non-target)): {total_all - (total_target + total_nontarget)}")

if __name__ == "__main__":
    asyncio.run(main())
