import asyncio
import os
import sys
import json
import subprocess
from urllib.parse import unquote
from playwright.async_api import async_playwright

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scrape_granular_core import get_authenticated_context

async def main():
    async with async_playwright() as p:
        print("Connecting to browser locally to extract cookies...")
        browser, context, page = await get_authenticated_context(p)
        if not page:
            print("Failed to connect.")
            return
            
        cookies = await context.cookies()
        await browser.close()
        
    # Format cookie header string
    cookie_parts = []
    xsrf_token = ""
    for c in cookies:
        cookie_parts.append(f"{c['name']}={c['value']}")
        if c['name'] == "XSRF-TOKEN":
            xsrf_token = unquote(c['value'])
            
    cookie_str = "; ".join(cookie_parts)
    
    url = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/report-progress-assignment"
    
    payload = {
        "surveyPeriodId": "fd68e454-ba45-4b85-8205-f3bf777ded24",
        "assignmentStatusAlias": None,
        "assignmentErrorStatusType": -1,
        "data1": None, "data2": None, "data3": None, "data4": None, "data5": None,
        "data6": None, "data7": None, "data8": None, "data9": None, "data10": None,
        "regionId": None,
        "region1Id": "5214ecb2-bef1-4a86-9446-451cf430928e",
        "region2Id": "bc32354f-1245-426f-b2cf-a5733e1295ad",  # Kab. Banggai (7201)
        "currentUserId": None,
        "userIdResponsibility": None
    }
    
    print("Executing curl command...")
    cmd = [
        "curl",
        "-s",
        "-X", "POST",
        url,
        "-H", "Content-Type: application/json",
        "-H", f"x-xsrf-token: {xsrf_token}",
        "-H", f"cookie: {cookie_str}",
        "-H", "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
        "-H", "Origin: https://fasih-sm.bps.go.id",
        "-H", "Referer: https://fasih-sm.bps.go.id/app/surveys/a0429e96-51a5-477b-a415-485f9c153004/fd68e454-ba45-4b85-8205-f3bf777ded24",
        "--data-raw", json.dumps(payload)
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    print("Curl Exit Code:", result.returncode)
    print("Curl Output length:", len(result.stdout))
    print("Curl Output Sample (first 500 chars):")
    print(result.stdout[:500])
    
    # Check if it is JSON
    try:
        data = json.loads(result.stdout)
        print("Success! JSON parsed correctly. Keys:", list(data.keys()))
    except Exception as e:
        print("Failed to parse output as JSON:", e)

if __name__ == "__main__":
    asyncio.run(main())
