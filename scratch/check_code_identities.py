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

        # Let's fetch 200 target records and 200 non-target records from SE Umum
        payload_target = {
            "start": 0, "length": 200, "columns": [
                {"data": "id"}, {"data": "codeIdentity"}, {"data": "data1"}, {"data": "data6"}, {"data": "assignmentStatusAlias"}
            ], "order": [], "search": {"value": "", "regex": False},
            "assignmentExtraParam": {
                "region1Id": "5214ecb2-bef1-4a86-9446-451cf430928e",
                "surveyPeriodId": "fd68e454-ba45-4b85-8205-f3bf777ded24",
                "assignmentErrorStatusType": -1,
                "filterTargetType": "target"
            }
        }

        payload_nontarget = {
            "start": 0, "length": 200, "columns": [
                {"data": "id"}, {"data": "codeIdentity"}, {"data": "data1"}, {"data": "data6"}, {"data": "assignmentStatusAlias"}
            ], "order": [], "search": {"value": "", "regex": False},
            "assignmentExtraParam": {
                "region1Id": "5214ecb2-bef1-4a86-9446-451cf430928e",
                "surveyPeriodId": "fd68e454-ba45-4b85-8205-f3bf777ded24",
                "assignmentErrorStatusType": -1,
                "filterTargetType": "non-target"
            }
        }

        print("Fetching targets...")
        res_t = await fetch(payload_target)
        print("Fetching non-targets...")
        res_nt = await fetch(payload_nontarget)

        print("\n=== SAMPLE TARGETS ===")
        for item in res_t.get("searchData", [])[:30]:
            print(f"codeIdentity: {item.get('codeIdentity')} | data1: {item.get('data1')} | data6: {item.get('data6')}")

        print("\n=== SAMPLE NON-TARGETS ===")
        for item in res_nt.get("searchData", [])[:30]:
            print(f"codeIdentity: {item.get('codeIdentity')} | data1: {item.get('data1')} | data6: {item.get('data6')}")

if __name__ == "__main__":
    asyncio.run(main())
