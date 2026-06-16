import asyncio
import json
from playwright.async_api import async_playwright
from urllib.parse import unquote

async def main():
    async with async_playwright() as p:
        try:
            # Connect to Chrome on port 9223 or 9222
            browser = None
            for port in [9223, 9222]:
                try:
                    browser = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
                    print(f"Connected to port {port}")
                    break
                except:
                    pass
            if not browser:
                print("Could not connect to Chrome.")
                return

            context = browser.contexts[0]
            page = None
            for p_page in context.pages:
                if "fasih-sm.bps.go.id" in p_page.url:
                    page = p_page
                    break
            if not page:
                print("FASIH page not open.")
                return

            cookies = await page.context.cookies()
            xsrf_token_raw = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), "")
            xsrf_token = unquote(xsrf_token_raw)

            # Let's fetch 5 records from non-target (tambahan)
            payload = {
                "start": 0, "length": 5, "columns": [{"data": "id"}], "order": [], "search": {"value": "", "regex": False},
                "assignmentExtraParam": {
                    "region1Id": "5214ecb2-bef1-4a86-9446-451cf430928e",
                    "surveyPeriodId": "fd68e454-ba45-4b85-8205-f3bf777ded24",
                    "assignmentErrorStatusType": -1,
                    "filterTargetType": "non-target"
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
            """, {"payload": payload, "token": xsrf_token})

            search_data = res.get("searchData", [])
            print(f"Found {len(search_data)} non-target records.")
            if search_data:
                print("\nKeys in first non-target record:")
                print(list(search_data[0].keys()))
                
                print("\nSample records (keys & values):")
                for idx, item in enumerate(search_data):
                    print(f"\n--- Record {idx+1} ---")
                    # print all non-empty fields
                    filtered_item = {k: v for k, v in item.items() if v is not None and v != ""}
                    print(json.dumps(filtered_item, indent=2))
            else:
                print("No non-target records found.")

        except Exception as e:
            print("Error:", e)

if __name__ == "__main__":
    asyncio.run(main())
