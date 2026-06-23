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
            print("Connected to page:", page.url)
        except Exception as e:
            print("Failed to connect:", e)
            return

        cookies = await page.context.cookies()
        xsrf_token_raw = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), "")
        xsrf_token = unquote(xsrf_token_raw)
        print("XSRF-TOKEN:", xsrf_token[:20] + "...")

        # A very simple datatable request
        payload = {
            "start": 0, "length": 1, "columns": [{"data": "id"}], "order": [], "search": {"value": "", "regex": False},
            "assignmentExtraParam": {
                "region1Id": "5214ecb2-bef1-4a86-9446-451cf430928e", # Prov Sulteng
                "surveyPeriodId": "fd68e454-ba45-4b85-8205-f3bf777ded24", # SE Umum
                "assignmentErrorStatusType": -1,
                "filterTargetType": "target"
            }
        }
        
        print("Sending fetch request...")
        res = await page.evaluate("""
            async ({payload, token}) => {
                const r = await fetch("https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode", {
                    method: "POST",
                    headers: { "Content-Type": "application/json", "X-XSRF-TOKEN": token },
                    body: JSON.stringify(payload)
                });
                if (!r.ok) return { error: `HTTP ${r.status}` };
                return await r.json();
            }
        """, {"payload": payload, "token": xsrf_token})
        
        print("Response keys:", list(res.keys()) if isinstance(res, dict) else type(res))
        if isinstance(res, dict) and "error" in res:
            print("Error message:", res["error"])
        elif isinstance(res, dict):
            print("totalHit:", res.get("totalHit"))
            print("searchAggregation items count:", len(res.get("searchAggregation", [])))

if __name__ == "__main__":
    asyncio.run(main())
