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

async def get_authenticated_context(p):
    for port in [9223, 9222]:
        if check_port_open(port):
            try:
                browser = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
                context = browser.contexts[0] if browser.contexts else browser.new_context()
                page = None
                for p_page in context.pages:
                    if "fasih-sm.bps.go.id" in p_page.url:
                        page = p_page
                        break
                if not page:
                    page = await context.new_page()
                return browser, context, page
            except Exception as e:
                print(f"Error CDP: {e}")
    raise RuntimeError("CDP not available")

async def main():
    async with async_playwright() as p:
        browser, context, page = await get_authenticated_context(p)
        
        # Navigate to fasih first to make sure origin is correct
        if "fasih-sm.bps.go.id" not in page.url:
            await page.goto("https://fasih-sm.bps.go.id/app/surveys", wait_until="domcontentloaded")
            
        cookies = await page.context.cookies()
        xsrf_token_raw = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), "")
        xsrf_token = unquote(xsrf_token_raw)
        
        # Test Datatable API for a Kecamatan in Banggai Kepulauan
        # Totikum: 815d35b4-fc43-43b5-b2ff-afc30f187298
        datatable_url = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode"
        payload = {
            "start": 0, "length": 1, "columns": [{"data": "id"}], "order": [], "search": {"value": "", "regex": False},
            "assignmentExtraParam": {
                "surveyPeriodId": "fd68e454-ba45-4b85-8205-f3bf777ded24", # se_umum
                "region1Id": "5214ecb2-bef1-4a86-9446-451cf430928e", # prov sulteng
                "region2Id": "bc32354f-1245-426f-b2cf-a5733e1295ad", # kab banggai kepulauan
                "region3Id": "815d35b4-fc43-43b5-b2ff-afc30f187298", # Totikum
                "assignmentErrorStatusType": -1,
                "filterTargetType": "target"
            }
        }
        
        res = await page.evaluate("""
            async ({url, payload, token}) => {
                const r = await fetch(url, {
                    method: "POST",
                    headers: { "Content-Type": "application/json", "X-XSRF-TOKEN": token },
                    body: JSON.stringify(payload)
                });
                const text = await r.text();
                return { status: r.status, text: text };
            }
        """, {"url": datatable_url, "payload": payload, "token": xsrf_token})
        
        print("Status code:", res["status"])
        print("Response text:", res["text"][:1000])
            
        await page.close()

if __name__ == "__main__":
    asyncio.run(main())
