import asyncio
import json
import socket
from playwright.async_api import async_playwright
from urllib.parse import unquote

def check_port_open(port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0
    except:
        return False

async def inspect():
    async with async_playwright() as p:
        browser = None
        for port in [9222, 9223]:
            if check_port_open(port):
                try:
                    browser = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
                    print(f"Connected to port {port}")
                    break
                except Exception as e:
                    print(f"Failed to connect to port {port}: {e}")
                    
        if not browser:
            print("No open CDP port found! Please start Chrome with remote debugging.")
            return
            
        context = browser.contexts[0] if browser.contexts else browser.new_context()
        page = context.pages[0] if context.pages else await context.new_page()
        
        await page.goto("https://fasih-sm.bps.go.id/app/dashboard")
        cookies = await page.context.cookies()
        xsrf_token_raw = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), "")
        xsrf_token = unquote(xsrf_token_raw)
        
        datatable_url = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode"
        period_id = "37526b20-81c8-42f5-a895-6190137d7394"
        prov_id = "a00c8aef-afc4-4d4f-b80d-789a15450ef9"
        
        payload = {
            "start": 0, "length": 5, "columns": [
                {"data": "id"},
                {"data": "codeIdentity"},
                {"data": "data1"},
                {"data": "data6"},
                {"data": "assignmentStatusAlias"},
                {"data": "region"}
            ], "order": [], "search": {"value": "", "regex": False},
            "assignmentExtraParam": {
                "region1Id": prov_id,
                "surveyPeriodId": period_id,
                "assignmentStatusAlias": "SUBMITTED RESPONDENT",
                "assignmentErrorStatusType": -1,
                "filterTargetType": ""
            }
        }
        
        res = await page.evaluate("""
            async ({url, payload, token}) => {
                const r = await fetch(url, {
                    method: "POST",
                    headers: { "Content-Type": "application/json", "X-XSRF-TOKEN": token },
                    body: JSON.stringify(payload)
                });
                return await r.json();
            }
        """, {"url": datatable_url, "payload": payload, "token": xsrf_token})
        
        print(json.dumps(res, indent=2))
        await browser.close()

if __name__ == "__main__":
    asyncio.run(inspect())
