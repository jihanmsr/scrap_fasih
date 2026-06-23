import asyncio
import json
import os
from playwright.async_api import async_playwright
from urllib.parse import unquote
from scrape_granular_core import get_authenticated_context

async def main():
    async with async_playwright() as p:
        try:
            browser, context, page = await get_authenticated_context(p)
        except Exception as e:
            print("Gagal connect ke browser:", e)
            return

        cookies = await context.cookies()
        token_raw = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), "")
        token = unquote(token_raw) if token_raw else ""
        
        # Navigate to dashboard first if not on domain
        if "fasih-sm.bps.go.id" not in page.url:
            print("Navigasi ke fasih-sm.bps.go.id...")
            await page.goto("https://fasih-sm.bps.go.id/app/dashboard")
            await asyncio.sleep(2)
            # Re-read token
            cookies = await context.cookies()
            token_raw = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), "")
            token = unquote(token_raw) if token_raw else ""
            
        url = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/report-progress-assignment"
        payload = {
            "surveyPeriodId": "fd68e454-ba45-4b85-8205-f3bf777ded24", # SE Umum
            "assignmentStatusAlias": None,
            "assignmentErrorStatusType": -1,
            "data1": None, "data2": None, "data3": None, "data4": None, "data5": None,
            "data6": None, "data7": None, "data8": None, "data9": None, "data10": None,
            "regionId": None,
            "currentUserId": None,
            "userIdResponsibility": None
        }
        
        print("Evaluating fetch in page...")
        resp = await page.evaluate("""
            async ({url, payload, token}) => {
                const r = await fetch(url, {
                    method: "POST",
                    headers: { "Content-Type": "application/json", "X-XSRF-TOKEN": token },
                    body: JSON.stringify(payload)
                });
                if (!r.ok) return { _error: `HTTP ${r.status}` };
                return await r.json();
            }
        """, {"url": url, "payload": payload, "token": token})
        
        if isinstance(resp, dict) and resp.get("success"):
            print("Response success: True")
            data = resp.get("data", {})
            print("Keys of data:", list(data.keys()) if isinstance(data, dict) else type(data))
            # Save response to inspect
            with open("scratch/report_progress_assignment_response.json", "w") as f:
                json.dump(resp, f, indent=2)
            print("Response saved to scratch/report_progress_assignment_response.json")
            if isinstance(data, dict):
                # Print a small part of the structure
                for k, v in list(data.items())[:5]:
                    if isinstance(v, list):
                        print(f"  Key '{k}': list length {len(v)}")
                        if len(v) > 0:
                            print(f"    Sample item: {v[0]}")
                    else:
                        print(f"  Key '{k}': {str(v)[:200]}")
        else:
            print("Response error:", resp)
            
        if browser:
            await browser.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
