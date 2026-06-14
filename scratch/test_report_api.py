import asyncio
import json
from playwright.async_api import async_playwright
from urllib.parse import unquote

async def run():
    async with async_playwright() as p:
        browser = None
        for port in [9223, 9222]:
            try:
                browser = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
                print(f"Connected to port {port}")
                break
            except Exception:
                pass
        
        if not browser:
            print("Could not connect to Chrome on remote debugging ports 9222 or 9223")
            return
            
        context = browser.contexts[0]
        page = None
        for p_page in context.pages:
            if "fasih" in p_page.url:
                page = p_page
                break
        if not page:
            page = context.pages[0] if context.pages else await context.new_page()
            
        cookies = await context.cookies()
        token = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), None)
        if token: 
            token = unquote(token)
        else:
            print("No XSRF-TOKEN token found")
            return
            
        print(f"Token: {token[:20]}...")
        
        REPORT_URL = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/report-user-assignment"
        
        # 1. SE Umum
        payload_umum = {
            "surveyPeriodId": "fd68e454-ba45-4b85-8205-f3bf777ded24",
            "region1Id": "5214ecb2-bef1-4a86-9446-451cf430928e"
        }
        print("\nTesting SE Umum Report API...")
        res_umum = await page.evaluate("""
            async ({url, payload, token}) => {
                try {
                    const r = await fetch(url, {
                        method: "POST",
                        headers: { "Content-Type": "application/json", "X-XSRF-TOKEN": token },
                        body: JSON.stringify(payload)
                    });
                    return { ok: r.ok, status: r.status, statusText: r.statusText, data: await r.text() };
                } catch (e) {
                    return { error: e.toString() };
                }
            }
        """, {"url": REPORT_URL, "payload": payload_umum, "token": token})
        
        print(f"SE Umum Response OK: {res_umum.get('ok')}, Status: {res_umum.get('status')}")
        if res_umum.get('ok'):
            try:
                data_json = json.loads(res_umum.get('data'))
                print("SE Umum Data sample (first 2 items):")
                print(json.dumps(data_json[:2], indent=2))
            except Exception as e:
                print("Failed to parse JSON:", e)
                print(res_umum.get('data')[:500])
        else:
            print("Error data:", res_umum)
            
        # 2. SE UB
        payload_ub = {
            "surveyPeriodId": "37526b20-81c8-42f5-a895-6190137d7394",
            "region1Id": "a00c8aef-afc4-4d4f-b80d-789a15450ef9"
        }
        print("\nTesting SE UB Report API...")
        res_ub = await page.evaluate("""
            async ({url, payload, token}) => {
                try {
                    const r = await fetch(url, {
                        method: "POST",
                        headers: { "Content-Type": "application/json", "X-XSRF-TOKEN": token },
                        body: JSON.stringify(payload)
                    });
                    return { ok: r.ok, status: r.status, statusText: r.statusText, data: await r.text() };
                } catch (e) {
                    return { error: e.toString() };
                }
            }
        """, {"url": REPORT_URL, "payload": payload_ub, "token": token})
        
        print(f"SE UB Response OK: {res_ub.get('ok')}, Status: {res_ub.get('status')}")
        if res_ub.get('ok'):
            try:
                data_json = json.loads(res_ub.get('data'))
                print("SE UB Data sample (first 2 items):")
                print(json.dumps(data_json[:2], indent=2))
            except Exception as e:
                print("Failed to parse JSON:", e)
                print(res_ub.get('data')[:500])
        else:
            print("Error data:", res_ub)

asyncio.run(run())
