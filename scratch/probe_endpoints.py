import asyncio
import json
import os
import socket
from playwright.async_api import async_playwright
from urllib.parse import unquote

def check_port_open(port=9222):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0
    except:
        return False

async def main():
    async with async_playwright() as p:
        port = 9223 if check_port_open(9223) else 9222
        print(f"Connecting to Chrome on port {port}...")
        try:
            browser = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
            context = browser.contexts[0]
            page = None
            for p_page in context.pages:
                if "fasih-sm.bps.go.id" in p_page.url:
                    page = p_page
                    break
            if not page:
                page = await context.new_page()
                await page.goto("https://fasih-sm.bps.go.id/app/dashboard")
        except Exception as e:
            print("Failed to connect to browser context:", e)
            return

        cookies = await page.context.cookies()
        xsrf_token_raw = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), "")
        xsrf_token = unquote(xsrf_token_raw)
        
        # Test assignment ID (rejected by Pengawas)
        tid = "bae0a3a6-dcbd-40be-a48b-86733476e393"
        
        candidates = [
            # Remarks endpoints
            ("GET", f"https://fasih-sm.bps.go.id/app/api/survey-response/api/v1/remarks/by-assignment?assignmentId={tid}"),
            ("GET", f"https://fasih-sm.bps.go.id/app/api/survey-response/api/v1/remarks/assignment/{tid}"),
            ("GET", f"https://fasih-sm.bps.go.id/app/api/survey-response/api/v1/remarks-by-assignment/{tid}"),
            ("GET", f"https://fasih-sm.bps.go.id/app/api/survey-response/remarks?assignmentId={tid}"),
            ("GET", f"https://fasih-sm.bps.go.id/app/api/survey-response/remarks/by-assignment?assignmentId={tid}"),
            ("POST", "https://fasih-sm.bps.go.id/app/api/survey-response/api/v1/remarks/search", {"assignmentId": tid}),
            
            # History/logs endpoints
            ("GET", f"https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/history/{tid}"),
            ("GET", f"https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/activities/{tid}"),
            ("GET", f"https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/log-history/{tid}"),
            ("POST", f"https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/logs/{tid}", {}),
            
            # Survey response metadata/details
            ("GET", f"https://fasih-sm.bps.go.id/app/api/survey-response/api/v1/survey-responses/by-assignment/{tid}"),
            ("GET", f"https://fasih-sm.bps.go.id/app/api/survey-response/api/v1/survey-responses?assignmentId={tid}"),
        ]

        async def probe(method, url, payload=None):
            try:
                res = await page.evaluate("""
                    async ({method, url, payload, token}) => {
                        const options = {
                            method: method,
                            headers: { 
                                "Accept": "application/json", 
                                "Content-Type": "application/json",
                                "X-XSRF-TOKEN": token 
                            }
                        };
                        if (payload) {
                            options.body = JSON.stringify(payload);
                        }
                        const r = await fetch(url, options);
                        if (!r.ok) return { _status: r.status, _text: (await r.text()).substring(0, 100) };
                        try {
                            return { _status: r.status, _json: await r.json() };
                        } catch(e) {
                            return { _status: r.status, _text: (await r.text()).substring(0, 200) };
                        }
                    }
                """, {"method": method, "url": url, "payload": payload, "token": xsrf_token})
                return res
            except Exception as e:
                return {"_exception": str(e)}

        for method, url, *payload_opt in candidates:
            payload = payload_opt[0] if payload_opt else None
            res = await probe(method, url, payload)
            status = res.get("_status", "ERR")
            print(f"[{status}] {method} {url}")
            if "_json" in res:
                print("   JSON Response:", json.dumps(res["_json"], indent=2)[:400])
            elif "_text" in res:
                print("   Text Response:", res["_text"][:200])
            elif "_exception" in res:
                print("   Exception:", res["_exception"])
            print("-" * 50)

if __name__ == "__main__":
    asyncio.run(main())
