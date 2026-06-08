import asyncio
import json
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        page = None
        for pg in browser.contexts[0].pages:
            if "fasih-sm.bps.go.id" in pg.url:
                page = pg
                break
        
        if not page:
            print("Tab FASIH tidak ditemukan.")
            return

        # Ambil XSRF-TOKEN
        cookies = await page.context.cookies()
        xsrf_token = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), "")
        
        payload = {
            "start": 0,
            "length": 10,
            "search": {"value": "", "regex": False},
            "assignmentExtraParam": {
                "region1Id": "a00c8aef-afc4-4d4f-b80d-789a15450ef9",
                "surveyPeriodId": "37526b20-81c8-42f5-a895-6190137d7394",
                "assignmentErrorStatusType": -1
            }
        }
        
        res_eval = await page.evaluate("""
            async ({payload, token}) => {
                const url = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode";
                const r = await fetch(url, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "X-XSRF-TOKEN": token
                    },
                    body: JSON.stringify(payload)
                });
                if (!r.ok) return { status: r.status, text: await r.text() };
                return { status: r.status, json: await r.json() };
            }
        """, {"payload": payload, "token": xsrf_token})
        
        print(json.dumps(res_eval, indent=2))

asyncio.run(main())
