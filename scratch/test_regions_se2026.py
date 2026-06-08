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
        
        group_id = "a45adac1-e711-4c15-b3f9-1f30fc151565" # SENSUS EKONOMI 2026 region group ID
        
        # Test 1: Fetch children by full code = 72, level = 1
        url1 = f"https://fasih-sm.bps.go.id/app/api/region/api/v1/region/custom-by-smallest-code-and-level?groupId={group_id}&smallestLevelFullCode=72&level=1"
        res1 = await page.evaluate("""
            async ({url, token}) => {
                try {
                    const r = await fetch(url, {
                        headers: { "X-XSRF-TOKEN": token }
                    });
                    return await r.json();
                } catch (e) {
                    return { error: e.toString() };
                }
            }
        """, {"url": url1, "token": token})
        
        print("\nTest 1 (level=1, smallestLevelFullCode=72) success:", res1.get("success"))
        if res1.get("success") and "data" in res1 and "children" in res1["data"]:
            children = res1["data"]["children"]
            print(f"Found {len(children)} children:")
            for c in children:
                print(f"  Code: {c.get('code')} | Name: {c.get('name')} | ID: {c.get('id')}")
        else:
            print("Data format:", list(res1.get("data", {}).keys()) if res1.get("data") else "No data")

        # Test 2: Fetch level 2 by looping kab codes
        print("\nTest 2: looping kab codes...")
        kab_codes = ["7201", "7202", "7203", "7204", "7205", "7206", "7207", "7208", "7209", "7210", "7211", "7212", "7271"]
        resolved = []
        for code in kab_codes:
            url2 = f"https://fasih-sm.bps.go.id/app/api/region/api/v1/region/custom-by-smallest-code-and-level?groupId={group_id}&smallestLevelFullCode={code}&level=2"
            res2 = await page.evaluate("""
                async ({url, token}) => {
                    try {
                        const r = await fetch(url, {
                            headers: { "X-XSRF-TOKEN": token }
                        });
                        return await r.json();
                    } catch (e) {
                        return { error: e.toString() };
                    }
                }
            """, {"url": url2, "token": token})
            if res2.get("success") and res2.get("data"):
                level1 = res2["data"].get("level1", {})
                level2 = level1.get("level2", {})
                prov_id = level1.get("id")
                prov_name = level1.get("name")
                if level2:
                    resolved.append({
                        "prov_id": prov_id,
                        "prov_name": prov_name,
                        "kab_id": level2.get("id"),
                        "kab_code": level2.get("code"),
                        "kab_name": level2.get("name")
                    })
        print(f"Resolved {len(resolved)} kabupatens:")
        for r in resolved:
            print(f"  Prov: {r['prov_name']} ({r['prov_id'][:8]}) | Kab: [{r['kab_code']}] {r['kab_name']} ({r['kab_id']})")

if __name__ == "__main__":
    asyncio.run(main())
