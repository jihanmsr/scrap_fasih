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
        
        target_ids = [
            "bae0a3a6-dcbd-40be-a48b-86733476e393",
            "556b7a73-5414-486e-ad9f-6ab1841e4cff",
            "beb7fab7-cc56-47f3-bb81-67ae4cc2df4f"
        ]

        async def test_endpoint(url):
            print(f"Testing URL: {url}")
            try:
                res = await page.evaluate("""
                    async ({url, token}) => {
                        const r = await fetch(url, {
                            method: "GET",
                            headers: { "Accept": "application/json", "X-XSRF-TOKEN": token }
                        });
                        if (!r.ok) return { _error: `HTTP ${r.status}` };
                        try {
                            return await r.json();
                        } catch(e) {
                            return await r.text();
                        }
                    }
                """, {"url": url, "token": xsrf_token})
                return res
            except Exception as e:
                return {"_exception": str(e)}

        for tid in target_ids:
            print(f"\n=========================================\nTarget ID: {tid}")
            
            # Endpoint 1: remarks
            url_remarks = f"https://fasih-sm.bps.go.id/app/api/survey-response/api/v1/remarks?assignmentId={tid}"
            res_remarks = await test_endpoint(url_remarks)
            print("REMARKS RESPONSE:")
            print(json.dumps(res_remarks, indent=2))
            
            # Endpoint 2: assignment logs
            url_logs = f"https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/logs/{tid}"
            res_logs = await test_endpoint(url_logs)
            print("LOGS RESPONSE:")
            print(json.dumps(res_logs, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
