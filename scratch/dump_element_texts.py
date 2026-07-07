import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        print("Connecting to browser...")
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        context = browser.contexts[0]
        
        # Inject localStorage before load
        await context.add_init_script("localStorage.setItem('active_tab', 'se_umum');")
        
        local_page = next((pg for pg in context.pages if "index.html" in pg.url), None)
        if not local_page:
            local_page = await context.new_page()
            
        print("Loading local index.html...")
        await local_page.goto("file:///Users/jihanmaisaroh/scrap_fasih/index.html")
        await asyncio.sleep(6) # Wait 6 seconds for Supabase load to complete
        
        print("\n--- CARD TEXTS ---")
        try:
            prelist = await local_page.inner_text("#se_umum-stat-total-prelist")
            print(f"Prelist: {prelist}")
        except Exception as e:
            print("Prelist error:", e)
            
        try:
            submitted = await local_page.inner_text("#se_umum-stat-total-submitted")
            print(f"Submitted: {submitted}")
        except Exception as e:
            print("Submitted error:", e)
            
        try:
            # Check expanded container HTML
            html = await local_page.inner_html("#se_umum-stats-expanded")
            print("\nExpanded Stats HTML:")
            print(html)
        except Exception as e:
            print("Expanded stats error:", e)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
