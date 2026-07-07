import asyncio
import os
import sys
from playwright.async_api import async_playwright

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scrape_granular_core import get_authenticated_context

async def main():
    async with async_playwright() as p:
        print("Connecting to browser...")
        browser, context, page = await get_authenticated_context(p)
        if not page:
            print("Failed to connect.")
            return
            
        local_page = None
        for pg in context.pages:
            if "index.html" in pg.url:
                local_page = pg
                break
        if not local_page:
            local_page = context.pages[0]
            
        print("Using Page URL:", local_page.url)
        print("Testing fetch from page context with 5s timeout...")
        
        res = await local_page.evaluate("""
            async () => {
                const url = "https://dds-api.bpssulteng.id/api.php?action=get_dashboard_summary&survey=se_umum&kab=all";
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 5000);
                try {
                    const r = await fetch(url, { signal: controller.signal });
                    clearTimeout(timeoutId);
                    const text = await r.text();
                    return { success: true, status: r.status, text_length: text.length, text_sample: text.substring(0, 100) };
                } catch (e) {
                    clearTimeout(timeoutId);
                    return { success: false, error: e.toString() };
                }
            }
        """)
        print("Fetch Result:", res)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
