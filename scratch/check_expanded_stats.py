import asyncio
import os
import sys
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        print("Connecting to browser...")
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        context = browser.contexts[0]
        
        # Inject localStorage before load
        print("Injecting localStorage active_tab='se_umum'...")
        await context.add_init_script("""
            localStorage.setItem('active_tab', 'se_umum');
        """)
        
        local_page = next((pg for pg in context.pages if "index.html" in pg.url), None)
        if not local_page:
            local_page = await context.new_page()
            
        print("Disabling Chrome cache via CDP session...")
        cdp_session = await context.new_cdp_session(local_page)
        await cdp_session.send("Network.setCacheDisabled", {"cacheDisabled": True})
        
        print("Loading local index.html...")
        await local_page.goto("file:///Users/jihanmaisaroh/scrap_fasih/index.html")
        
        print("Waiting for data load...")
        for _ in range(30):
            val = await local_page.inner_text("#se_umum-stat-total-prelist")
            if val.strip() != "0" and val.strip() != "":
                print(f"Data loaded successfully! Total target = {val}")
                break
            await asyncio.sleep(0.5)
            
        print("Clicking 'Lihat Detail Lainnya'...")
        await local_page.click("#se_umum-toggle-detail")
        await asyncio.sleep(1)
        
        # Capture screenshot of expanded stats
        screenshot_path = "/Users/jihanmaisaroh/scrap_fasih/scratch/expanded_stats_verify.png"
        await local_page.screenshot(path=screenshot_path)
        print(f"Screenshot of expanded stats saved to {screenshot_path}")
        
        print("Dumping rendered expanded stats...")
        cards = await local_page.evaluate("""
            () => {
                const el = document.getElementById('se_umum-stats-expanded');
                const cardsData = [];
                el.querySelectorAll('.stat-card-compact').forEach(c => {
                    const label = c.querySelector('.stat-label')?.innerText.trim() || '';
                    const val = c.querySelector('.stat-value')?.innerText.trim() || '';
                    const subtext = c.querySelector('.stat-subtext')?.innerText.trim() || '';
                    cardsData.push({ label, val, subtext });
                });
                return cardsData;
            }
        """)
        
        for c in cards:
            print(f"Card: {c['label']} -> Value: {c['val']} ({c['subtext']})")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
