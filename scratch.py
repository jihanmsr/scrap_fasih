import asyncio
import json
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9223")
        context = browser.contexts[0]
        
        target_page = None
        for page in context.pages:
            if "fasih-sm.bps.go.id" in page.url:
                target_page = page
                break
        
        token = await target_page.evaluate("""() => { 
            let t = document.cookie.split('; ').find(row => row.startsWith('XSRF-TOKEN='));
            return t ? t.split('=')[1] : '';
        }""")
        
        res = await target_page.evaluate("""
            async ({url, token}) => {
                const r = await fetch(url, {
                    headers: { "Accept": "application/json", "X-XSRF-TOKEN": token }
                });
                if(!r.ok) return {error: r.statusText, status: r.status};
                return await r.json();
            }
        """, {
            "url": "https://fasih-sm.bps.go.id/app/api/survey-user/api/v1/allocations-view/by-user?surveyRoleId=7bcf696d-9c0e-4e1a-b58f-eacc79bfb499&surveyPeriodId=37526b20-81c8-42f5-a895-6190137d7394&page=0&size=10",
            "token": token
        })
        print(json.dumps(res, indent=2))
        
asyncio.run(main())
