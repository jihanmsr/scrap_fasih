import asyncio
import json
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = None
        for port in [9223, 9222]:
            try:
                browser = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
                break
            except Exception:
                pass
        if not browser:
            print("CDP connection failed")
            return
            
        context = browser.contexts[0]
        page = await context.new_page()
        
        results = []
        
        async def handle_request(route, request):
            if "api/v1/chart/data" in request.url and request.method == "POST":
                try:
                    post_data = request.post_data_json
                    form_data = post_data.get("form_data", {})
                    queries = post_data.get("queries", [{}])[0]
                    metrics = queries.get("metrics", [])
                    columns = queries.get("columns", [])
                    
                    label_hints = []
                    for m in metrics:
                        if isinstance(m, dict) and "label" in m:
                            label_hints.append(m["label"])
                    for c in columns:
                        if isinstance(c, dict) and "label" in c:
                            label_hints.append(c["label"])
                        elif isinstance(c, str):
                            label_hints.append(c)
                            
                    results.append({
                        "slice_id": form_data.get("slice_id"),
                        "viz_type": form_data.get("viz_type"),
                        "hints": label_hints,
                        "payload": post_data
                    })
                except Exception as e:
                    pass
            await route.continue_()
            
        await page.route("**/*", handle_request)
        
        print("Membuka dashboard dan menangkap request...")
        await page.goto("https://fasih-dashboard.bps.go.id/superset/dashboard/se2026/", timeout=60000, wait_until="networkidle")
        await asyncio.sleep(5) # wait for all charts to load
        
        with open("scratch/superset_widgets.json", "w") as f:
            json.dump(results, f, indent=2)
            
        print(f"Berhasil menangkap {len(results)} widget. Disimpan ke scratch/superset_widgets.json")
        await page.close()

asyncio.run(main())
