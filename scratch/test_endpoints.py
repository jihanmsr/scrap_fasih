import asyncio
from playwright.async_api import async_playwright
import json

async def test_endpoint(page, url, token):
    payload = {
        "start": 0,
        "length": 1,
        "columns": [{"data": "id"}],
        "order": [],
        "search": {"value": "", "regex": False},
        "assignmentExtraParam": {
            "region1Id": "a00c8aef-afc4-4d4f-b80d-789a15450ef9",
            "region2Id": "9c9b2d79-9fb1-4ce7-b0f1-6b7bb5511beb", # Banggai Kepulauan
            "surveyPeriodId": "37526b20-81c8-42f5-a895-6190137d7394",
            "assignmentErrorStatusType": -1,
            "filterTargetType": ""
        }
    }
    try:
        res_eval = await page.evaluate("""
            async ({url, payload, token}) => {
                try {
                    const r = await fetch(url, {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                            "X-XSRF-TOKEN": token
                        },
                        body: JSON.stringify(payload)
                    });
                    if (!r.ok) return { status: r.status };
                    const js = await r.json();
                    return { status: r.status, totalHit: js.totalHit, searchDataLength: js.searchData ? js.searchData.length : 0 };
                } catch (e) {
                    return { error: e.toString() };
                }
            }
        """, {"url": url, "payload": payload, "token": token})
        return res_eval
    except Exception as e:
        return {"error_outer": str(e)}

async def main():
    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
            print("Connected to Chrome.")
        except Exception as e:
            print("Failed to connect to Chrome (Make sure scrape_via_api.py is stopped first!):", e)
            return

        context = browser.contexts[0]
        page = None
        for pg in context.pages:
            if "fasih-sm.bps.go.id" in pg.url:
                page = pg
                break

        if not page:
            print("Active FASIH tab not found.")
            return

        cookies = await context.cookies()
        token = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), None)
        if not token:
            print("XSRF-TOKEN not found.")
            return

        from urllib.parse import unquote
        token = unquote(token)
        print("XSRF-TOKEN obtained.")

        endpoints = [
            "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode",
            "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-survey-periode",
            "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable",
            "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/list",
            "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user",
            "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-survey-periode"
        ]

        for url in endpoints:
            print(f"\nTesting: {url}")
            res = await test_endpoint(page, url, token)
            print("Result:", json.dumps(res, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
