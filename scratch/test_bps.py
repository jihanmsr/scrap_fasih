import asyncio
import json
import socket
import httpx

DATATABLE_URL = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode"

def check_port_open(port=9223):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0
    except:
        return False

async def main():
    # Connect to browser to get active session
    port = 9223 if check_port_open(9223) else 9222
    print(f"Connecting to port {port}...")
    
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
        context = browser.contexts[0]
        cookies = await context.cookies()
        cookie_dict = {c["name"]: c["value"] for c in cookies}
        token_raw = cookie_dict.get("XSRF-TOKEN", "")
        from urllib.parse import unquote
        token = unquote(token_raw) if token_raw else ""
        await browser.close()
        
    async with httpx.AsyncClient(timeout=60.0) as client:
        client.headers.update({
            "Content-Type": "application/json",
            "X-XSRF-TOKEN": token,
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*"
        })
        for c in cookies:
            client.cookies.set(
                c['name'],
                c['value'],
                domain=c.get('domain', 'fasih-sm.bps.go.id'),
                path=c.get('path', '/')
            )
            
        region1_id = "5214ecb2-bef1-4a86-9446-451cf430928e" # SE Umum
        region2_id = "bc32354f-1245-426f-b2cf-a5733e1295ad" # Banggai Kepulauan
        survey_period_id = "fd68e454-ba45-4b85-8205-f3bf777ded24"
        
        columns_payload = [{"data": "id"}]
        
        # We try length 2000, 5000, 10000
        for length in [2000, 5000, 10000]:
            payload = {
                "start": 0,
                "length": length,
                "columns": columns_payload,
                "order": [],
                "search": {"value": "", "regex": False},
                "assignmentExtraParam": {
                    "region1Id": region1_id,
                    "region2Id": region2_id,
                    "surveyPeriodId": survey_period_id,
                    "assignmentErrorStatusType": -1,
                    "filterTargetType": ""
                }
            }
            
            try:
                r = await client.post(DATATABLE_URL, json=payload)
                if r.status_code == 200:
                    res = r.json()
                    data_len = len(res.get("searchData", []))
                    total_hit = res.get("totalHit", 0)
                    print(f"Requested length {length} -> Returned {data_len} records. totalHit: {total_hit}")
                else:
                    print(f"Requested length {length} -> HTTP Error: {r.status_code}")
            except Exception as e:
                print(f"Requested length {length} -> Exception: {e}")

if __name__ == "__main__":
    asyncio.run(main())
