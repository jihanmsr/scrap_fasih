import asyncio
import json
from playwright.async_api import async_playwright
from urllib.parse import unquote

async def run():
    async with async_playwright() as p:
        browser = None
        for port in [9223, 9222]:
            try:
                browser = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
                print(f"Connected on port {port}")
                break
            except Exception:
                pass
        if not browser:
            print("Could not connect to Chrome")
            return
            
        context = browser.contexts[0]
        page = None
        for p_page in context.pages:
            if "fasih-sm.bps.go.id" in p_page.url:
                page = p_page
                break
        if not page:
            page = context.pages[0] if context.pages else await context.new_page()
            
        try:
            await page.goto("https://fasih-sm.bps.go.id/app/dashboard", wait_until="domcontentloaded", timeout=15000)
        except Exception:
            pass
            
        cookies = await context.cookies()
        token = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), None)
        if token: token = unquote(token)
        
        survey_period_id = "fd68e454-ba45-4b85-8205-f3bf777ded24" # SE Umum
        # Let's call datatable API
        url = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode"
        payload = {
            "start": 0,
            "length": 10,
            "columns": [{"data": "id"}],
            "order": [],
            "search": {"value": "", "regex": False},
            "assignmentExtraParam": {
                "region1Id": "5214ecb2-bef1-4a86-9446-451cf430928e", # SE Umum Sulawesi Tengah
                "surveyPeriodId": survey_period_id,
                "assignmentErrorStatusType": -1,
                "filterTargetType": ""
            }
        }
        
        res = await page.evaluate("""
            async ({url, payload, token}) => {
                const r = await fetch(url, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "X-XSRF-TOKEN": token
                    },
                    body: JSON.stringify(payload)
                });
                return await r.json();
            }
        """, {"url": url, "payload": payload, "token": token})
        
        records = res.get("searchData", [])
        if records:
            print("SAMPLE RECORD KEYS & VALUES:")
            rec = records[0]
            for k, v in rec.items():
                print(f"  {k}: {v}")
            
            # Print unique values of assignmentStatus and assignmentStatusAlias
            statuses = set()
            aliases = set()
            for r in records[:100]:
                statuses.add(r.get("assignmentStatus"))
                aliases.add(r.get("assignmentStatusAlias"))
            print("\nUnique Statuses:", statuses)
            print("Unique Aliases:", aliases)
        else:
            print("No records returned")

asyncio.run(run())
