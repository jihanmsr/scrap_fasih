import asyncio
import json
import socket
import os
from playwright.async_api import async_playwright
from urllib.parse import unquote

USER_DATA_DIR = "playwright_chrome_profile"

def check_port_open(port=9222):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0
    except:
        return False

async def main():
    async with async_playwright() as p:
        port = 9223 if check_port_open(9223) else 9222
        browser = None
        context = None
        page = None
        
        if check_port_open(port):
            print(f"Connecting to Chrome on port {port}...")
            try:
                browser = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
                context = browser.contexts[0]
                for p_page in context.pages:
                    if "fasih-sm.bps.go.id" in p_page.url:
                        page = p_page
                        break
                if not page:
                    page = await context.new_page()
                    await page.goto("https://fasih-sm.bps.go.id/app/dashboard")
            except Exception as e:
                print("Failed to connect to browser context via CDP:", e)
                
        if not page:
            print("Launching persistent Chrome...")
            abs_user_data_dir = os.path.abspath(USER_DATA_DIR)
            chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
            context = await p.chromium.launch_persistent_context(
                user_data_dir=abs_user_data_dir, headless=True, executable_path=chrome_path,
                args=["--no-first-run", "--no-default-browser-check"]
            )
            page = context.pages[0] if context.pages else await context.new_page()
            await page.goto("https://fasih-sm.bps.go.id/app/dashboard")

        cookies = await page.context.cookies()
        xsrf_token_raw = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), "")
        xsrf_token = unquote(xsrf_token_raw)

        # Fetch first page (length 500)
        payload = {
            "start": 0, "length": 500, "columns": [
                {"data": "id"},
                {"data": "codeIdentity"},
                {"data": "dateCreated"},
                {"data": "dateModified"},
                {"data": "assignmentStatusAlias"}
            ],
            "order": [{"column": 5, "dir": "desc"}],
            "search": {"value": "", "regex": False},
            "assignmentExtraParam": {
                "region1Id": "5214ecb2-bef1-4a86-9446-451cf430928e", # Prov Sulteng
                "surveyPeriodId": "fd68e454-ba45-4b85-8205-f3bf777ded24", # SE Umum
                "assignmentErrorStatusType": -1,
                "filterTargetType": ""
            }
        }

        print("Fetching first page of 500 records...")
        r = await page.evaluate("""
            async ({payload, token}) => {
                try {
                    const res = await fetch("https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode", {
                        method: "POST",
                        headers: { "Content-Type": "application/json", "X-XSRF-TOKEN": token },
                        body: JSON.stringify(payload)
                     });
                     return await res.json();
                } catch (e) {
                    return { error: e.toString() };
                }
            }
        """, {"payload": payload, "token": xsrf_token})

        if "error" in r:
            print(f"JS Error: {r['error']}")
            if browser: await browser.close()
            return
            
        records = r.get("searchData", [])
        print(f"Total hit: {r.get('totalHit')}")
        print(f"Returned: {len(records)}")
        
        # Analyze dates
        dates = []
        for idx, rec in enumerate(records):
            dates.append(rec.get("dateModified"))
            
        print("\nFirst 10 dateModified:")
        for d in dates[:10]:
            print(f"  {d}")
            
        print("\nLast 10 dateModified on this page:")
        for d in dates[-10:]:
            print(f"  {d}")

        # Let's count how many are on 2026-06-22
        today_cnt = sum(1 for d in dates if d and d.startswith("2026-06-22"))
        older_cnt = sum(1 for d in dates if d and not d.startswith("2026-06-22"))
        print(f"\nIn first page of 500: {today_cnt} are today (2026-06-22), {older_cnt} are older/other.")
        
        # Let's check if the list is sorted: is every date >= subsequent date?
        is_sorted = True
        for i in range(len(dates)-1):
            if dates[i] and dates[i+1] and dates[i] < dates[i+1]:
                is_sorted = False
                print(f"Out of order at index {i}: {dates[i]} < {dates[i+1]}")
                break
        print(f"Is strictly sorted: {is_sorted}")
        
        if browser: await browser.close()
        else: await context.close()

if __name__ == "__main__":
    asyncio.run(main())
