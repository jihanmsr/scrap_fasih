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
            
        cookies = await context.cookies()
        token = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), None)
        if token: token = unquote(token)
        
        survey_period_id = "fd68e454-ba45-4b85-8205-f3bf777ded24" # SE Umum
        # Let's call report API
        url = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/report-user-assignment"
        payload = {"surveyPeriodId": survey_period_id, "region1Id": "5214ecb2-bef1-4a86-9446-451cf430928e"}
        
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
        
        print("REPORT RESPONSE SAMPLE:")
        if res:
            # Print the values array for the first item
            print(json.dumps(res[0], indent=2))
        else:
            print("Empty response")

asyncio.run(run())
