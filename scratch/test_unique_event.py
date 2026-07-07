import asyncio
import os
import sys
import uuid
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
        print("Token length:", len(token))
        
        url = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/report-progress-assignment"
        
        payloads = [{
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
        }]
        
        run_id = str(uuid.uuid4()).replace("-", "")
        event_name = f"run_sync_batch_bypass_{run_id}"
        result_event_name = f"run_sync_batch_bypass_result_{run_id}"
        
        print("Registering unique event listener:", event_name)
        await page.evaluate(f"""
            () => {{
                window.addEventListener('{event_name}', async (e) => {{
                    const {{ url, payloads, token }} = e.detail;
                    const results = [];
                    for (const payload of payloads) {{
                        try {{
                            const r = await fetch(url, {{
                                method: "POST",
                                headers: {{
                                    "Content-Type": "application/json",
                                    "x-xsrf-token": token
                                }},
                                body: JSON.stringify(payload)
                            }});
                            const text = await r.text();
                            results.push({{ ok: r.ok, status: r.status, text: text }});
                        }} catch (err) {{
                            results.push({{ error: err.toString() }});
                        }}
                    }}
                    window.dispatchEvent(new CustomEvent('{result_event_name}', {{
                        detail: results
                    }}));
                }});
            }}
        """)
        
        result_promise = page.evaluate(f"""
            () => new Promise((resolve) => {{
                window.addEventListener('{result_event_name}', (e) => {{
                    resolve(e.detail);
                }}, {{ once: true }});
            }})
        """)
        
        print("Dispatching unique event...")
        await page.evaluate(f"""
            ({{url, payloads, token}}) => {{
                window.dispatchEvent(new CustomEvent('{event_name}', {{
                    detail: {{ url, payloads, token }}
                }}));
            }}
        """, {"url": url, "payloads": payloads, "token": token})
        
        res = await result_promise
        print("\nResult:")
        for r in res:
            print("  OK:", r.get("ok"))
            print("  Status:", r.get("status"))
            print("  Text length:", len(r.get("text", "")))
            print("  Sample:", r.get("text", "")[:300])
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
