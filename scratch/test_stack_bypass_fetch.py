import asyncio
import os
import sys
import json
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
        
        print("Registering decoupled DOM event listener...")
        await page.evaluate("""
            () => {
                if (window.hasDecoupledListener) return;
                window.hasDecoupledListener = true;
                
                window.addEventListener('run-sync-bypass', async (e) => {
                    const { url, payload, token } = e.detail;
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
                        window.dispatchEvent(new CustomEvent('run-sync-bypass-result', { 
                            detail: { ok: r.ok, status: r.status, text: text } 
                        }));
                    } catch (err) {
                        window.dispatchEvent(new CustomEvent('run-sync-bypass-result', { 
                            detail: { error: err.toString() } 
                        }));
                    }
                });
            }
        """)
        
        print("Dispatching event and waiting for result...")
        # Set up a promise in page context to wait for the event
        result_promise = page.evaluate("""
            () => new Promise((resolve) => {
                window.addEventListener('run-sync-bypass-result', (e) => {
                    resolve(e.detail);
                }, { once: true });
            })
        """)
        
        # Dispatch the event
        await page.evaluate("""
            ({url, payload, token}) => {
                window.dispatchEvent(new CustomEvent('run-sync-bypass', { 
                    detail: { url, payload, token } 
                }));
            }
        """, {"url": url, "payload": payload, "token": token})
        
        res = await result_promise
        print("Bypass Result:")
        print("  OK:", res.get("ok"))
        print("  Status:", res.get("status"))
        print("  Text length:", len(res.get("text", "")))
        print("  Text sample (first 300 chars):")
        print(res.get("text", "")[:300])
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
