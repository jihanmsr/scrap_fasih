import asyncio
import json
import os
import socket
from urllib.parse import unquote
from playwright.async_api import async_playwright

USER_DATA_DIR = "playwright_chrome_profile"

def check_port_open(port=9222):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0
    except:
        return False

async def get_authenticated_context(p):
    for port in [9223, 9222]:
        if check_port_open(port):
            try:
                browser = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
                context = browser.contexts[0] if browser.contexts else browser.new_context()
                page = context.pages[0] if context.pages else await context.new_page()
                return browser, context, page
            except Exception as e:
                print(f"Error CDP: {e}")
    raise RuntimeError("CDP not available")

async def main():
    async with async_playwright() as p:
        browser, context, page = await get_authenticated_context(p)
        cookies = await page.context.cookies()
        xsrf_token_raw = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), "")
        xsrf_token = unquote(xsrf_token_raw)
        
        # Test Report API for 7201 (Banggai Kepulauan)
        report_url = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/report-user-assignment"
        payload_report = {
            "surveyPeriodId": "fd68e454-ba45-4b85-8205-f3bf777ded24", # se_umum
            "region1Id": "5214ecb2-bef1-4a86-9446-451cf430928e", # prov sulteng
            "region2Id": "bc32354f-1245-426f-b2cf-a5733e1295ad" # kab banggai kepulauan
        }
        
        res = await page.evaluate("""
            async ({url, payload, token}) => {
                const r = await fetch(url, {
                    method: "POST",
                    headers: { "Content-Type": "application/json", "X-XSRF-TOKEN": token },
                    body: JSON.stringify(payload)
                });
                return r.json();
            }
        """, {"url": report_url, "payload": payload_report, "token": xsrf_token})
        
        print(f"Report API response type: {type(res)}, length: {len(res) if isinstance(res, list) else 'N/A'}")
        if isinstance(res, list) and len(res) > 0:
            print("First item keys:", res[0].keys())
            for item in res[:5]:
                print(f"key: {item.get('key')} | label: {item.get('label')} | values: {item.get('values')}")
        else:
            print("Response:", res)
            
        await page.close()
        await browser.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
