import asyncio
from playwright.async_api import async_playwright
from urllib.parse import unquote

async def main():
    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
            context = browser.contexts[0]
            page = None
            for p_page in context.pages:
                if "fasih-sm.bps.go.id" in p_page.url:
                    page = p_page
                    break
            if not page:
                page = await context.new_page()
                await page.goto("https://fasih-sm.bps.go.id/app/dashboard")
                
            cookies = await context.cookies()
            token_raw = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), None)
            if not token_raw:
                print("Session status: INVALID (XSRF-TOKEN not found in cookies)")
                await browser.close()
                return
                
            token = unquote(token_raw)
            
            # Run session validation
            url = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode"
            payload = {
                "start": 0, "length": 1, "columns": [{"data": "id"}], "order": [], "search": {"value": "", "regex": False},
                "assignmentExtraParam": {
                    "region1Id": "a00c8aef-afc4-4d4f-b80d-789a15450ef9",
                    "surveyPeriodId": "37526b20-81c8-42f5-a895-6190137d7394",
                    "assignmentErrorStatusType": -1
                }
            }
            
            res = await page.evaluate("""
                async ({url, payload, token}) => {
                    try {
                        const r = await fetch(url, {
                            method: "POST",
                            headers: { "Content-Type": "application/json", "X-XSRF-TOKEN": token },
                            body: JSON.stringify(payload)
                        });
                        if (!r.ok) return { error: `HTTP ${r.status}` };
                        return await r.json();
                    } catch(e) {
                        return { error: e.toString() };
                    }
                }
            """, {"url": url, "payload": payload, "token": token})
            
            if res and isinstance(res, dict) and "error" not in res:
                print("Session status: VALID")
                print("Username:", res.get("searchData", [{}])[0].get("currentUserUsername") if res.get("searchData") else "No data returned but API call succeeded")
            else:
                print("Session status: INVALID", res.get("error") if res else "Empty response")
                
            await browser.close()
        except Exception as e:
            print("Error connecting or checking session:", e)

if __name__ == "__main__":
    asyncio.run(main())
