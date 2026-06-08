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
        
        group_ids = [
            "a45adac1-e711-4c15-b3f9-1f30fc151565", # Group 1
            "6b0b053f-aa43-4855-ac8f-26857b735c93"  # Group 2
        ]
        
        for g_id in group_ids:
            print(f"\n==========================================")
            print(f"Checking group ID: {g_id}")
            print(f"==========================================")
            
            # Fetch level 1 children (Province of Sulawesi Tengah code is 72)
            url1 = f"https://fasih-sm.bps.go.id/app/api/region/api/v1/region/custom-by-smallest-code-and-level?groupId={g_id}&smallestLevelFullCode=72&level=1"
            res1 = await page.evaluate("""
                async ({url, token}) => {
                    try {
                        const r = await fetch(url, { headers: { "X-XSRF-TOKEN": token } });
                        return await r.json();
                    } catch (e) {
                        return { error: e.toString() };
                    }
                }
            """, {"url": url1, "token": token})
            
            if not res1.get("success") or not res1.get("data"):
                print("Failed to get level 1 data for this group.")
                continue
                
            prov_node = res1["data"]
            print(f"Province in this group: ID: {prov_node.get('id')} | Name: {prov_node.get('name')}")
            
            # Let's fetch children (level 2) by querying custom-by-smallest-code-and-level for each kabupaten code
            kab_codes = ["7201", "7202", "7203", "7204", "7205", "7206", "7207", "7208", "7209", "7210", "7211", "7212", "7271"]
            resolved = []
            for code in kab_codes:
                url2 = f"https://fasih-sm.bps.go.id/app/api/region/api/v1/region/custom-by-smallest-code-and-level?groupId={g_id}&smallestLevelFullCode={code}&level=2"
                res2 = await page.evaluate("""
                    async ({url, token}) => {
                        try {
                            const r = await fetch(url, { headers: { "X-XSRF-TOKEN": token } });
                            return await r.json();
                        } catch (e) {
                            return { error: e.toString() };
                        }
                    }
                """, {"url": url2, "token": token})
                if res2.get("success") and res2.get("data"):
                    level1 = res2["data"].get("level1", {})
                    level2 = level1.get("level2", {})
                    if level2:
                        resolved.append({
                            "kab_id": level2.get("id"),
                            "kab_code": level2.get("code"),
                            "kab_name": level2.get("name")
                        })
            print(f"Resolved {len(resolved)} kabupatens for group {g_id}:")
            for r in resolved:
                print(f"  Code: {r['kab_code']} | Name: {r['kab_name']} | ID: {r['kab_id']}")

if __name__ == "__main__":
    asyncio.run(main())
