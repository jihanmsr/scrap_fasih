import asyncio
import os
import sys
from urllib.parse import unquote
from playwright.async_api import async_playwright

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scrape_granular_core import get_authenticated_context

async def main():
    async with async_playwright() as p:
        print("Connecting to browser...")
        browser, context, page = await get_authenticated_context(p)
        if not page:
            print("Failed to connect.")
            return
            
        print("Active Page URL:", page.url)
        cookies = await context.cookies()
        token_raw = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), "")
        token = unquote(token_raw) if token_raw else ""
        
        url = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/report-progress-assignment"
        
        # We will try a test payload
        payload = {
            "surveyPeriodId": "fd68e454-ba45-4b85-8205-f3bf777ded24",
            "assignmentStatusAlias": None,
            "assignmentErrorStatusType": -1,
            "data1": None, "data2": None, "data3": None, "data4": None, "data5": None,
            "data6": None, "data7": None, "data8": None, "data9": None, "data10": None,
            "regionId": None,
            "region1Id": "5214ecb2-bef1-4a86-9446-451cf430928e",
            "region2Id": "bc32354f-1245-426f-b2cf-a5733e1295ad",
            "currentUserId": None,
            "userIdResponsibility": None
        }
        
        print("Testing fetch from page context...")
        res = await page.evaluate("""
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
                    const text = await r.text();
                    return { ok: r.ok, status: r.status, text: text.substring(0, 500) };
                } catch (e) {
                    return { error: e.toString() };
                }
            }
        """, {"url": url, "payload": payload, "token": token})
        
        print("Fetch Result:", res)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
