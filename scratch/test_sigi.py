import asyncio
import json
import httpx
from playwright.async_api import async_playwright

async def main():
    print("[START] Connecting to Chrome...")
    async with async_playwright() as p:
        browser = None
        for port in [9222, 9223]:
            try:
                browser = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
                print(f"[SUCCESS] Connected on port {port}")
                break
            except Exception:
                pass
        
        if not browser:
            print("[ERROR] Could not connect to Chrome.")
            return

        try:
            context = browser.contexts[0]
            # Get token and cookies from BPS page
            page = None
            for p_page in context.pages:
                if "fasih-sm.bps.go.id" in p_page.url:
                    page = p_page
                    break
            if not page:
                print("[ERROR] BPS Dashboard page not open.")
                return

            cookies = await context.cookies()
            token = await page.evaluate("() => { const match = document.cookie.match(/XSRF-TOKEN=([^;]+)/); return match ? decodeURIComponent(match[1]) : ''; }")
            print(f"[INFO] Token found: {token[:10]}...")

            limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)
            async with httpx.AsyncClient(limits=limits, timeout=30.0) as client:
                client.headers.update({
                    "Content-Type": "application/json",
                    "X-XSRF-TOKEN": token,
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                    "Accept": "application/json"
                })
                for c in cookies:
                    client.cookies.set(c['name'], c['value'], domain=c.get('domain', 'fasih-sm.bps.go.id'), path=c.get('path', '/'))

                # Query parameters for Sigi (SE Umum)
                # Sigi ID: 0061da62-2a47-4dee-b8d0-239b33e2c59d
                # Prov ID: 26db84fa-b9a3-4886-9a25-c266453965b6
                # Period ID: 41b2c589-9a22-4467-bc18-4720e2cdbf10 (SE Umum)
                
                datatable_url = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode"
                
                # Check target vs non-target counts for Sigi
                payload_target = {
                    "start": 0, "length": 1, "columns": [{"data": "id"}], "order": [], "search": {"value": "", "regex": False},
                    "assignmentExtraParam": {
                        "region1Id": "26db84fa-b9a3-4886-9a25-c266453965b6",
                        "region2Id": "0061da62-2a47-4dee-b8d0-239b33e2c59d",
                        "surveyPeriodId": "41b2c589-9a22-4467-bc18-4720e2cdbf10",
                        "assignmentErrorStatusType": -1,
                        "filterTargetType": "target"
                    }
                }
                
                payload_nontarget = {
                    "start": 0, "length": 10, "columns": [{"data": "id"}, {"data": "codeIdentity"}], "order": [], "search": {"value": "", "regex": False},
                    "assignmentExtraParam": {
                        "region1Id": "26db84fa-b9a3-4886-9a25-c266453965b6",
                        "region2Id": "0061da62-2a47-4dee-b8d0-239b33e2c59d",
                        "surveyPeriodId": "41b2c589-9a22-4467-bc18-4720e2cdbf10",
                        "assignmentErrorStatusType": -1,
                        "filterTargetType": "non-target"
                    }
                }

                res_t = await client.post(datatable_url, json=payload_target)
                res_nt = await client.post(datatable_url, json=payload_nontarget)

                print("=== TARGET RESPONSE FOR SIGI ===")
                print(f"Status Code: {res_t.status_code}")
                if res_t.status_code == 200:
                    print(f"Total Hit: {res_t.json().get('totalHit')}")
                else:
                    print(res_t.text)

                print("=== NON-TARGET RESPONSE FOR SIGI ===")
                print(f"Status Code: {res_nt.status_code}")
                if res_nt.status_code == 200:
                    print(f"Total Hit: {res_nt.json().get('totalHit')}")
                    print(f"Sample Data: {res_nt.json().get('searchData', [])[:2]}")
                else:
                    print(res_nt.text)
                    
        except Exception as e:
            print(f"[ERROR] {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
