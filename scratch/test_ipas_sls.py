import asyncio
from playwright.async_api import async_playwright
import json

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else await context.new_page()

        cookies = await context.cookies()
        token = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), None)
        from urllib.parse import unquote
        token = unquote(token)
        
        # Test 1: Get Kecamatan under a Kabupaten
        kab_uuid = "34165dd5-372e-42fa-99c6-0cc19a9b4d0b" # Banggai
        url_kec = f"https://fasih-sm.bps.go.id/app/api/analytic/api/v2/se-2026/report-progress-listing-usaha?aggregationType=kecamatan&regionId={kab_uuid}&isUb=false"
        
        print("Testing:", url_kec)
        res_kec = await page.evaluate(f"""
            async () => {{
                try {{
                    const r = await fetch('{url_kec}', {{ headers: {{ "X-XSRF-TOKEN": '{token}' }} }});
                    return await r.json();
                }} catch (e) {{ return {{ error: e.toString() }}; }}
            }}
        """)
        
        if "data" in res_kec and isinstance(res_kec["data"], list) and len(res_kec["data"]) > 0:
            print("Successfully got Kecamatan data. Example:")
            kec_item = res_kec["data"][0]
            print(json.dumps(kec_item, indent=2))
            
            # Use the first Kecamatan to get Desa
            kec_id = kec_item.get("regionId") # Assuming there's a regionId returned??
            if not kec_id:
                # Let's inspect what is returned
                print("No regionId found in item. Item keys:", list(kec_item.keys()))
                # Often it returns an array of objects like { "kabupaten": "...", "total": ... }
        else:
            print("Failed to get Kecamatan data:", res_kec)

if __name__ == "__main__":
    asyncio.run(main())
