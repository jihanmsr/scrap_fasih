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
        page = None
        for p_page in context.pages:
            if "fasih-dashboard.bps.go.id" in p_page.url:
                page = p_page
                break
        if not page:
            print("Dashboard page not found open")
            return
            
        print(f"Connected to page: {page.url}")
        
        # We can extract state from Redux store in page
        # Superset dashboard page usually stores slices in a Redux store under window.store
        data = await page.evaluate("""() => {
            const store = window.store || window.__store__;
            if (!store) return { error: "No Redux store found" };
            const state = store.getState();
            
            // Let's find slice entities
            const slices = state.sliceEntities?.slices || {};
            const sliceList = [];
            for (const id in slices) {
                const sl = slices[id];
                sliceList.append({
                    id: sl.slice_id,
                    name: sl.slice_name,
                    viz_type: sl.viz_type,
                    datasource: sl.datasource
                });
            }
            return {
                slices: Object.values(slices).map(sl => ({
                    id: sl.slice_id,
                    name: sl.slice_name,
                    viz_type: sl.viz_type,
                    datasource: sl.datasource
                })),
                nativeFilters: state.nativeFilters ? Object.keys(state.nativeFilters) : null,
                charts: state.charts ? Object.keys(state.charts) : null
            };
        }""")
        
        print(json.dumps(data, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
