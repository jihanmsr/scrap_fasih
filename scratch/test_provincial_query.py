import asyncio
import os
import sys
import json
from urllib.parse import unquote
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        print("Connecting directly to port 9222...")
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        context = browser.contexts[0]
        page = next((pg for pg in context.pages if "fasih-sm.bps.go.id" in pg.url), None)
        if not page:
            print("Failed to find FASIH tab.")
            await browser.close()
            return
            
        print("Active Page URL:", page.url)
        cookies = await context.cookies()
        token_raw = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), "")
        token = unquote(token_raw) if token_raw else ""
        
        url = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/report-progress-assignment"
        
        # Province-level payload (kabupaten region2Id is None/null)
        payload = {
            "surveyPeriodId": "fd68e454-ba45-4b85-8205-f3bf777ded24",
            "assignmentStatusAlias": None,
            "assignmentErrorStatusType": -1,
            "data1": None, "data2": None, "data3": None, "data4": None, "data5": None,
            "data6": None, "data7": None, "data8": None, "data9": None, "data10": None,
            "regionId": None,
            "region1Id": "5214ecb2-bef1-4a86-9446-451cf430928e", # Sulawesi Tengah ID
            "region2Id": None, # None means retrieve all kabupaten under this province!
            "currentUserId": None,
            "userIdResponsibility": None
        }
        
        # Dispatch bypass fetch
        result_promise = page.evaluate("""
            () => new Promise((resolve) => {
                window.addEventListener('run-sync-bypass-prov-check', (e) => {
                    resolve(e.detail);
                }, { once: true });
            })
        """)
        
        await page.evaluate("""
            async ({url, payload, token}) => {
                try {
                    const r = await fetch(url, {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                            "x-xsrf-token": token
                        },
                        body: JSON.stringify(payload)
                    });
                    const text = await r.text();
                    window.dispatchEvent(new CustomEvent('run-sync-bypass-prov-check', { 
                        detail: { ok: r.ok, status: r.status, text: text } 
                    }));
                } catch (err) {
                    window.dispatchEvent(new CustomEvent('run-sync-bypass-prov-check', { 
                        detail: { error: err.toString() } 
                    }));
                }
            }
        """, {"url": url, "payload": payload, "token": token})
        
        res = await result_promise
        print("Fetch Status:", res.get("status"))
        text = res.get("text", "")
        print("Text length:", len(text))
        print("Is valid JSON list:", text.startswith("["))
        if text.startswith("["):
            data = json.loads(text)
            print(f"Number of items in response: {len(data)}")
            if len(data) > 0:
                print("First item sample:")
                print(json.dumps(data[0], indent=2))
        else:
            print("Response sample (first 500 chars):")
            print(text[:500])
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
