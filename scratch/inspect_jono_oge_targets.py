import asyncio
import json
import os
from playwright.async_api import async_playwright
from urllib.parse import unquote

USER_DATA_DIR = "playwright_chrome_profile"

def check_port_open(port):
    import socket
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1.0)
            return s.connect_ex(('127.0.0.1', port)) == 0
    except Exception:
        return False

async def main():
    port = None
    for p in [9223, 9222]:
        if check_port_open(p):
            port = p
            break
            
    if not port:
        print("Chrome remote debugging not open!")
        return

    async with async_playwright() as p:
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
        token_raw = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), None)
        if not token_raw:
            print("XSRF-TOKEN not found!")
            await browser.close()
            return
            
        token = unquote(token_raw)
        
        url = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode"
        
        # Query at Desa level for Jono Oge
        payload = {
            "start": 0,
            "length": 10,
            "columns": [
                {"data": "id"},
                {"data": "codeIdentity"},
                {"data": "data1"},
                {"data": "region"}
            ],
            "order": [],
            "search": {"value": "", "regex": False},
            "assignmentExtraParam": {
                "region1Id": "5214ecb2-bef1-4a86-9446-451cf430928e",
                "region2Id": "0061da62-2a47-4dee-b8d0-239b33e2c59d",
                "region3Id": "a50bf6c3-1d07-42fc-8e4a-5fae6c646b9a",
                "region4Id": "6a3922f5-b3e1-4560-af6f-ad5b11ebcdba",
                "surveyPeriodId": "fd68e454-ba45-4b85-8205-f3bf777ded24",
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
        """, {"url": url, "payload": payload, "token": token})
        
        search_data = res.get("searchData", [])
        print("Total hits in Desa:", res.get("totalHit"))
        print("Returned targets count:", len(search_data))
        for idx, t in enumerate(search_data[:5]):
            reg = t.get("region", {})
            lvl5 = reg.get("level1", {}).get("level2", {}).get("level3", {}).get("level4", {}).get("level5", {}) or {}
            print(f"\nTarget {idx+1}:")
            print("  Name:", t.get("data1"))
            print("  Code:", t.get("codeIdentity"))
            print("  SLS Name:", lvl5.get("name"))
            print("  SLS Code:", lvl5.get("fullCode"))
            print("  SLS ID:", lvl5.get("id"))
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
