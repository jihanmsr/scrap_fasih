import asyncio
import json
from playwright.async_api import async_playwright
from urllib.parse import unquote

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9223")
        context = browser.contexts[0]
        page = context.pages[1]
        
        cookies = await context.cookies()
        token = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), None)
        if token: token = unquote(token)
        
        survey_period_id = "fd68e454-ba45-4b85-8205-f3bf777ded24"
        pencacah_id = "6d7d919a-45e5-4779-bb87-2905b49fd31a"
        
        params = [
            "regionSize", "regionsSize", "region_size", "regions_size",
            "regionLimit", "regionsLimit", "region_limit", "regions_limit",
            "limit", "limitRegion", "limitRegions", "limit_region", "limit_regions",
            "regionPageSize", "region_page_size",
            "maxRegions", "max_regions", "maxRegion", "max_region",
            "count", "regionCount", "region_count",
            "showAll", "show_all", "allRegions", "all_regions", "all",
            "perPage", "regionPerPage", "region_per_page",
            "expand", "embed", "depth"
        ]
        
        for p_name in params:
            # We will test both value 100 and 1000, and also True/yes for flags
            for val in [100, "true", "yes"]:
                url = f"https://fasih-sm.bps.go.id/app/api/survey-user/api/v1/allocations-view/by-user?surveyPeriodId={survey_period_id}&surveyRoleId={pencacah_id}&page=0&size=20&regionCode=7207&{p_name}={val}"
                try:
                    res = await page.evaluate(f"fetch('{url}', {{ headers: {{ 'Accept': 'application/json', 'X-XSRF-TOKEN': '{token}' }} }}).then(r => r.json())")
                    content = res.get("data", {}).get("content", [])
                    # Find afriana576@gmail.com (totalRegions=15)
                    afriana = next((u for u in content if u.get("email") == "afriana576@gmail.com"), None)
                    if afriana:
                        arr_len = len(afriana.get("regions", []))
                        if arr_len > 5:
                            print(f"🎉 SUCCESS! Parameter '{p_name}={val}' expanded regions to {arr_len} (totalRegions={afriana.get('totalRegions')})")
                            return
                except Exception as e:
                    pass
        print("❌ All parameters tested. None expanded the regions list beyond 5.")

asyncio.run(run())
