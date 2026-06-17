import asyncio
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
        print(f"Using XSRF token: {xsrf_token}")

        # Let's request datatable with all possible columns
        payload = {
            "start": 0, "length": 10, "columns": [
                {"data": "id"},
                {"data": "codeIdentity"},
                {"data": "dateCreated"},
                {"data": "dateModified"},
                {"data": "assignmentStatusAlias"},
                {"data": "region"}
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
            async ({payload, token}) => {
                try {
                    const res = await fetch("https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode", {
                        method: "POST",
                        headers: { "Content-Type": "application/json", "X-XSRF-TOKEN": token },
                        body: JSON.stringify(payload)
                    });
                    if (!res.ok) {
                        return { error_status: res.status, body: await res.text() };
                    }
                    return await res.json();
                } catch (e) {
                    return { error: e.toString() };
                }
            }
        """, {"payload": payload, "token": xsrf_token})

        if "error_status" in r:
            print(f"HTTP Error {r['error_status']}: {r['body']}")
        elif "error" in r:
            print(f"JS Error: {r['error']}")
        else:
            records = r.get("searchData", [])
            if records:
                print(f"Total records returned: {len(records)}")
                for idx, rec in enumerate(records):
                    print(f"\n--- Record {idx+1} ---")
                    print(f"id: {rec.get('id')}")
                    print(f"codeIdentity: {rec.get('codeIdentity')}")
                    print(f"assignmentStatusAlias: {rec.get('assignmentStatusAlias')}")
                    print(f"dateCreated: {rec.get('dateCreated')}")
                    print(f"dateModified: {rec.get('dateModified')}")
                    print(f"Keys: {list(rec.keys())}")
            else:
                print("No records returned.")

if __name__ == "__main__":
    asyncio.run(main())
