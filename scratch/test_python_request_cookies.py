import asyncio
import os
import sys
import json
import requests
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
            
        cookies = await context.cookies()
        headers = {
            "Accept": "*/*",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
            "Origin": "https://fasih-sm.bps.go.id",
            "Referer": "https://fasih-sm.bps.go.id/app/surveys/a0429e96-51a5-477b-a415-485f9c153004/fd68e454-ba45-4b85-8205-f3bf777ded24"
        }
        
        cookie_dict = {}
        xsrf_token = ""
        for c in cookies:
            cookie_dict[c["name"]] = c["value"]
            if c["name"] == "XSRF-TOKEN":
                xsrf_token = unquote(c["value"])
                
        if xsrf_token:
            headers["X-XSRF-TOKEN"] = xsrf_token
            
        print("Current cookies in Chrome:")
        for name, value in cookie_dict.items():
            print(f"  {name}: {value[:30]}...")
            
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
        
        print("\nSending POST request from Python requests with Chrome cookies...")
        try:
            r = requests.post(url, headers=headers, cookies=cookie_dict, json=payload, verify=False, timeout=10)
            print("Response Status:", r.status_code)
            print("Response Text (first 500 chars):")
            print(r.text[:500])
        except Exception as e:
            print("Python request failed:", e)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
