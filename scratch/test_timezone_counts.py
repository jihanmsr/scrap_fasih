import asyncio
import json
import os
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

def parse_wib_shifted(dt_str, local_tz):
    if not dt_str:
        return None
    cleaned = dt_str.strip()
    if cleaned.endswith("+00:00"):
        cleaned = cleaned[:-6] + "+07:00"
    elif cleaned.endswith("Z"):
        cleaned = cleaned[:-1] + "+07:00"
    elif not ("+" in cleaned or "-" in cleaned or cleaned.endswith("Z")):
        cleaned = cleaned + "+07:00"
    dt = datetime.datetime.fromisoformat(cleaned)
    return dt.astimezone(local_tz)

def parse_utc(dt_str, local_tz):
    if not dt_str:
        return None
    cleaned = dt_str.strip()
    if cleaned.endswith("Z"):
        cleaned = cleaned[:-1] + "+00:00"
    dt = datetime.datetime.fromisoformat(cleaned)
    return dt.astimezone(local_tz)

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

        # Fetch active records from a single kabupaten to inspect
        datatable_url = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode"
        
        # Let's fetch the first 200 records of SE Umum that are in submitted/approved/rejected status
        payload = {
            "start": 0, "length": 500, "columns": [
                {"data": "id"}, {"data": "codeIdentity"}, {"data": "dateModified"}, {"data": "assignmentStatusAlias"}
            ], "order": [], "search": {"value": "", "regex": False},
            "assignmentExtraParam": {
                "region1Id": "5214ecb2-bef1-4a86-9446-451cf430928e",
                "surveyPeriodId": "fd68e454-ba45-4b85-8205-f3bf777ded24",
                "assignmentErrorStatusType": -1,
                "filterTargetType": ""
            }
        }

        print("Fetching records...")
        r = await page.evaluate("""
            async ({url, payload, token}) => {
                const res = await fetch(url, {
                    method: "POST",
                    headers: { "Content-Type": "application/json", "X-XSRF-TOKEN": token },
                    body: JSON.stringify(payload)
                });
                return await res.json();
            }
        """, {"url": datatable_url, "payload": payload, "token": xsrf_token})

        records = r.get("searchData", [])
        print(f"Fetched {len(records)} records.")

        local_tz = datetime.timezone(datetime.timedelta(hours=8))
        today = datetime.datetime.now(local_tz).date()
        yesterday = today - datetime.timedelta(days=1)
        two_days_ago = today - datetime.timedelta(days=2)

        print(f"Today (WITA): {today}")
        print(f"Yesterday (WITA): {yesterday}")
        print(f"Two days ago (WITA): {two_days_ago}")

        counts_wib = {"today": 0, "yesterday": 0, "two_days_ago": 0, "other": 0}
        counts_utc = {"today": 0, "yesterday": 0, "two_days_ago": 0, "other": 0}

        for rec in records:
            dm = rec.get("dateModified")
            status = rec.get("assignmentStatusAlias", "")
            if not dm or status == "OPEN":
                continue
                
            # WIB Shifted
            dt_wib = parse_wib_shifted(dm, local_tz)
            if dt_wib:
                d = dt_wib.date()
                if d == today:
                    counts_wib["today"] += 1
                elif d == yesterday:
                    counts_wib["yesterday"] += 1
                elif d == two_days_ago:
                    counts_wib["two_days_ago"] += 1
                else:
                    counts_wib["other"] += 1

            # UTC directly
            dt_utc = parse_utc(dm, local_tz)
            if dt_utc:
                d = dt_utc.date()
                if d == today:
                    counts_utc["today"] += 1
                elif d == yesterday:
                    counts_utc["yesterday"] += 1
                elif d == two_days_ago:
                    counts_utc["two_days_ago"] += 1
                else:
                    counts_utc["other"] += 1

        print("\n=== WIB shifted method ===")
        print(counts_wib)
        print("\n=== UTC directly method ===")
        print(counts_utc)

if __name__ == "__main__":
    asyncio.run(main())
