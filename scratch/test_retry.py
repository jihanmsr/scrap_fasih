import asyncio
import json
from playwright.async_api import async_playwright
from urllib.parse import unquote

# Copy of evaluate_fetch_with_retry from scrape_assign.py
async def evaluate_fetch_with_retry(context, token, url, payload):
    for attempt in range(3):
        page = None
        for p_page in context.pages:
            if "fasih-sm.bps.go.id" in p_page.url:
                page = p_page
                break
        if not page:
            page = context.pages[0] if context.pages else await context.new_page()

        try:
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
                    } catch (e) {
                        return { error: e.toString() };
                    }
                }
            """, {"url": url, "payload": payload, "token": token})
            return res
        except Exception as e:
            print(f"Exception on attempt {attempt+1}: {e}")
            await asyncio.sleep(2)
    return {"error": "Max retries exceeded"}

async def run():
    async with async_playwright() as p:
        browser = None
        for port in [9223, 9222]:
            try:
                browser = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
                print(f"Connected to port {port}")
                break
            except Exception:
                pass
        
        if not browser:
            print("Could not connect to Chrome")
            return
            
        context = browser.contexts[0]
        cookies = await context.cookies()
        token = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), None)
        if token: 
            token = unquote(token)
        else:
            print("No token")
            return
            
        REPORT_URL = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/report-user-assignment"
        payload = {
            "surveyPeriodId": "fd68e454-ba45-4b85-8205-f3bf777ded24",
            "region1Id": "5214ecb2-bef1-4a86-9446-451cf430928e"
        }
        
        res = await evaluate_fetch_with_retry(context, token, REPORT_URL, payload)
        print("Result from evaluate_fetch_with_retry:")
        print(json.dumps(res, indent=2) if isinstance(res, dict) or isinstance(res, list) else res)

asyncio.run(run())
