import asyncio
import json
from playwright.async_api import async_playwright
from urllib.parse import unquote
import socket

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
            await asyncio.sleep(2)
            
        cookies = await context.cookies()
        token_raw = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), "")
        token = unquote(token_raw) if token_raw else ""
        
        payload = {
            "start": 0, "length": 5, "columns": [
                {"data": "id"},
                {"data": "codeIdentity"},
                {"data": "dateCreated"},
                {"data": "dateModified"},
                {"data": "assignmentStatusAlias"}
            ], "order": [], "search": {"value": "", "regex": False},
            "assignmentExtraParam": {
                "region1Id": "5214ecb2-bef1-4a86-9446-451cf430928e",
                "surveyPeriodId": "fd68e454-ba45-4b85-8205-f3bf777ded24",
                "assignmentErrorStatusType": -1,
                "filterTargetType": ""
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
        """, {"payload": payload, "token": token})
        
        search_data = res.get("searchData", [])
        print("Raw records from datatable:")
        for r in search_data:
            print(f"ID: {r.get('id')} | Created: {r.get('dateCreated')} | Modified: {r.get('dateModified')} | Status: {r.get('assignmentStatusAlias')}")
            print(f"Keys: {list(r.keys())}")
            
        await browser.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
