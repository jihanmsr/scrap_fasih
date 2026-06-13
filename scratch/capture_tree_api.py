import asyncio
from playwright.async_api import async_playwright
from urllib.parse import unquote

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9223")
        context = browser.contexts[0]
        
        page = None
        for p_page in context.pages:
            if "fasih-sm.bps.go.id" in p_page.url:
                page = p_page
                break
        if not page:
            print("No page found")
            return
            
        print(f"Connected to page: {page.url}")
        
        captured = []
        def handle_request(request):
            if "by-region/children" in request.url:
                captured.append((request.method, request.url, request.post_data))
                print(f"Captured: [{request.method}] {request.url}")
            
        page.on("request", handle_request)
        
        # Navigate directly to the Petugas page (Pencacah role)
        # Using the active surveyPeriodId from the browser to ensure it loads
        survey_period_id = "37526b20-81c8-42f5-a895-6190137d7394"
        pencacah_id = "6d7d919a-45e5-4779-bb87-2905b49fd31a"
        target_url = f"https://fasih-sm.bps.go.id/app/surveys/ecddb52e-f392-403c-a963-47391f217010/{survey_period_id}/user?role={pencacah_id}"
        
        print(f"Navigating to {target_url}...")
        await page.goto(target_url)
        await page.wait_for_load_state("domcontentloaded")
        await asyncio.sleep(4)
        
        # Click "Per Wilayah"
        print("Clicking 'Per Wilayah'...")
        try:
            await page.click("text=Per Wilayah")
            await asyncio.sleep(3)
        except Exception as e:
            print("Failed to click Per Wilayah:", e)
            
        # Find the expand arrow or Sulawesi Tengah item and click it
        print("Looking for 'SULAWESI TENGAH' expand trigger...")
        try:
            # Let's click on the text "SULAWESI TENGAH" or the icon next to it
            await page.click("text=SULAWESI TENGAH")
            await asyncio.sleep(3)
        except Exception as e:
            print("Failed to click SULAWESI TENGAH:", e)
            
        print("\n=== CAPTURED by-region/children APIs ===")
        for method, url, data in captured:
            print(f"- {method} {url}")

asyncio.run(run())
