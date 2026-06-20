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
        
        endpoints = [
            "/app/api/survey-response/v2/api-docs",
            "/app/api/survey-response/swagger-resources",
            "/app/api/analytic/v2/api-docs",
            "/app/api/analytic/swagger-resources",
            "/app/api/survey-user/v2/api-docs",
            "/app/api/survey-user/swagger-resources",
        ]

        async def check_url(url):
            try:
                res = await page.evaluate("""
                    async ({url, token}) => {
                        const r = await fetch(url, {
                            method: "GET",
                            headers: { "X-XSRF-TOKEN": token }
                        });
                        if (!r.ok) return { _status: r.status };
                        try {
                            const json = await r.json();
                            return { _status: r.status, _keys: Object.keys(json), _json: json };
                        } catch(e) {
                            return { _status: r.status, _text: (await r.text()).substring(0, 100) };
                        }
                    }
                """, {"url": "https://fasih-sm.bps.go.id" + url, "token": xsrf_token})
                return res
            except Exception as e:
                return {"_exception": str(e)}

        for ep in endpoints:
            res = await check_url(ep)
            status = res.get("_status", "ERR")
            print(f"[{status}] {ep}")
            if "_keys" in res:
                print("   Keys:", res["_keys"])
                if "paths" in res["_json"]:
                    paths = list(res["_json"]["paths"].keys())
                    print("   Sample paths (up to 10):", paths[:10])
                    # search for remarks or comments or reject or reason
                    matches = [p for p in paths if any(w in p.lower() for w in ["remark", "comment", "reject", "reason", "log"])]
                    print("   Matches for remarks/comments/reject/logs/reason:", matches)
            elif "_text" in res:
                print("   Text snippet:", res["_text"])
            print("-" * 50)

if __name__ == "__main__":
    asyncio.run(main())
