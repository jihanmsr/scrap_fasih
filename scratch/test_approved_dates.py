import asyncio
import json
import socket
import datetime
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

        cookies = await page.context.cookies()
        xsrf_token_raw = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), "")
        xsrf_token = unquote(xsrf_token_raw)

        # Fetch APPROVED records (these are definitely completed today)
        payload = {
            "start": 0, "length": 20, "columns": [
                {"data": "id"}, {"data": "codeIdentity"}, {"data": "dateModified"}, {"data": "assignmentStatusAlias"}
            ], "order": [], "search": {"value": "", "regex": False},
            "assignmentExtraParam": {
                "region1Id": "5214ecb2-bef1-4a86-9446-451cf430928e",
                "surveyPeriodId": "fd68e454-ba45-4b85-8205-f3bf777ded24",
                "assignmentErrorStatusType": -1,
                "filterTargetType": "",
                "assignmentStatusAlias": "APPROVED BY Pengawas"
            }
        }

        print("Fetching APPROVED records...")
        r = await page.evaluate("""
            async ({url, payload, token}) => {
                const res = await fetch(url, {
                    method: "POST",
                    headers: { "Content-Type": "application/json", "X-XSRF-TOKEN": token },
                    body: JSON.stringify(payload)
                });
                return await res.json();
            }
        """, {"url": "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode", "payload": payload, "token": xsrf_token})

        records = r.get("searchData", [])
        
        local_wita = datetime.timezone(datetime.timedelta(hours=8))
        now_wita = datetime.datetime.now(local_wita)
        print(f"Now WITA: {now_wita}")
        print(f"Today WITA: {now_wita.date()}")
        
        for rec in records[:10]:
            dm = rec.get("dateModified", "")
            print(f"raw dateModified: {dm}")
            # Show what each interpretation gives
            # WIB: replace +00:00 with +07:00
            if dm.endswith("+00:00"):
                wib_str = dm[:-6] + "+07:00"
            elif dm.endswith("Z"):
                wib_str = dm[:-1] + "+07:00"
            else:
                wib_str = dm
            dt_wib = datetime.datetime.fromisoformat(wib_str).astimezone(local_wita)
            
            # UTC direct
            if dm.endswith("Z"):
                utc_str = dm[:-1] + "+00:00"
            else:
                utc_str = dm
            dt_utc = datetime.datetime.fromisoformat(utc_str).astimezone(local_wita)
            
            print(f"  WIB→WITA: {dt_wib} (date={dt_wib.date()})")
            print(f"  UTC→WITA: {dt_utc} (date={dt_utc.date()})")

if __name__ == "__main__":
    asyncio.run(main())
