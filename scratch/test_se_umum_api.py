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

        async def test_endpoint(label, region1Id, surveyPeriodId):
            payload = {
                "start": 0, "length": 1, "columns": [{"data": "id"}], "order": [], "search": {"value": "", "regex": False},
                "assignmentExtraParam": {
                    "region1Id": region1Id,
                    "surveyPeriodId": surveyPeriodId,
                    "assignmentErrorStatusType": -1,
                    "filterTargetType": "target"
                }
            }
            url = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode"
            res = await page.evaluate("""
                async ({url, payload, token}) => {
                    try {
                        const r = await fetch(url, {
                            method: "POST",
                            headers: { "Content-Type": "application/json", "X-XSRF-TOKEN": token },
                            body: JSON.stringify(payload)
                        });
                        const text = await r.text();
                        return { status: r.status, is_ok: r.ok, text_preview: text.substring(0, 1000) };
                    } catch(e) {
                        return { error: e.toString() };
                    }
                }
            """, {"url": url, "payload": payload, "token": xsrf_token})
            print(f"\n--- Result for {label} ---")
            print(f"Status: {res.get('status')} | OK: {res.get('is_ok')}")
            if "error" in res:
                print(f"Error: {res['error']}")
            else:
                print(f"Preview: {res.get('text_preview')}")

        # Test SE UB
        await test_endpoint("SE UB", "a00c8aef-afc4-4d4f-b80d-789a15450ef9", "37526b20-81c8-42f5-a895-6190137d7394")
        # Test SE Umum
        await test_endpoint("SE Umum", "5214ecb2-bef1-4a86-9446-451cf430928e", "fd68e454-ba45-4b85-8205-f3bf777ded24")

if __name__ == "__main__":
    asyncio.run(main())
