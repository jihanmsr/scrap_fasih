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

        # Let's fetch from report-user-assignment for BANGGAI
        # surveyPeriodId for SE Umum: fd68e454-ba45-4b85-8205-f3bf777ded24
        # region1Id (prov): 5214ecb2-bef1-4a86-9446-451cf430928e
        # region2Id (banggai): 530e9ca5-86ba-434e-9b04-405102e6d900
        payload = {
            "surveyPeriodId": "fd68e454-ba45-4b85-8205-f3bf777ded24",
            "region1Id": "5214ecb2-bef1-4a86-9446-451cf430928e",
            "region2Id": "530e9ca5-86ba-434e-9b04-405102e6d900"
        }

        print("Fetching report...")
        res = await page.evaluate("""
            async ({payload, token}) => {
                const r = await fetch("https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/report-user-assignment", {
                    method: "POST",
                    headers: { "Content-Type": "application/json", "X-XSRF-TOKEN": token },
                    body: JSON.stringify(payload)
                });
                return await r.json();
            }
        """, {"payload": payload, "token": xsrf_token})

        print(f"Report length: {len(res) if isinstance(res, list) else type(res)}")
        if isinstance(res, list):
            for item in res[:15]:
                print(f"key: {item.get('key')} | label: {item.get('label')} | values: {item.get('values')}")

if __name__ == "__main__":
    asyncio.run(main())
