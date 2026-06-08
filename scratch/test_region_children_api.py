import asyncio
from playwright.async_api import async_playwright
import json

async def main():
    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
            print("Connected to Chrome.")
        except Exception as e:
            print("Failed to connect to Chrome:", e)
            return

        context = browser.contexts[0]
        page = context.pages[0] if context.pages else await context.new_page()
        
        cookies = await context.cookies()
        token = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), None)
        if not token:
            print("XSRF-TOKEN not found.")
            return
            
        from urllib.parse import unquote
        token = unquote(token)
        
        # We will use the province ID of Sulawesi Tengah
        prov_id = "5214ecb2-bef1-4a86-9446-451cf430928e"
        
        candidate_urls = [
            f"https://fasih-sm.bps.go.id/app/api/region/api/v1/regions/children?parentId={prov_id}",
            f"https://fasih-sm.bps.go.id/app/api/region/api/v1/region/children?parentId={prov_id}",
            f"https://fasih-sm.bps.go.id/app/api/region/api/v1/regions?parentId={prov_id}",
            f"https://fasih-sm.bps.go.id/app/api/region/api/v1/region?parentId={prov_id}",
            f"https://fasih-sm.bps.go.id/app/api/region/api/v1/region/list-by-parent-id?parentId={prov_id}",
            f"https://fasih-sm.bps.go.id/app/api/region/api/v1/region/by-parent?parentId={prov_id}",
            f"https://fasih-sm.bps.go.id/app/api/region/api/v1/region/by-parent-id?parentId={prov_id}",
            f"https://fasih-sm.bps.go.id/app/api/region/api/v1/region/children-by-parent-id?parentId={prov_id}",
            f"https://fasih-sm.bps.go.id/app/api/region/api/v1/region/custom-by-smallest-code-and-level?groupId=a45adac1-e711-4c15-b3f9-1f30fc151565&parentId={prov_id}"
        ]
        
        for url in candidate_urls:
            print(f"\nTesting: {url}")
            res = await page.evaluate("""
                async ({url, token}) => {
                    try {
                        const r = await fetch(url, { headers: { "X-XSRF-TOKEN": token } });
                        if (!r.ok) return { status: r.status };
                        return { status: r.status, json: await r.json() };
                    } catch (e) {
                        return { error: e.toString() };
                    }
                }
            """, {"url": url, "token": token})
            
            print("Status:", res.get("status"))
            if res.get("status") == 200:
                js = res.get("json", {})
                print("Success:", js.get("success"))
                if isinstance(js.get("data"), list):
                    print("Data length:", len(js["data"]))
                    if len(js["data"]) > 0:
                        print("Sample item:", js["data"][0])
                elif isinstance(js.get("data"), dict):
                    print("Data keys:", list(js["data"].keys()))
                else:
                    print("Data preview:", str(js.get("data"))[:200])

if __name__ == "__main__":
    asyncio.run(main())
