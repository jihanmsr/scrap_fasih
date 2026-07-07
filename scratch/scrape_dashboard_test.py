import asyncio
import os
import sys
from playwright.async_api import async_playwright

USER_DATA_DIR = "playwright_chrome_profile"

async def main():
    async with async_playwright() as p:
        abs_user_data_dir = os.path.abspath(USER_DATA_DIR)
        chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        
        print("[INFO] Launching browser...")
        context = await p.chromium.launch_persistent_context(
            user_data_dir=abs_user_data_dir,
            headless=True,
            executable_path=chrome_path,
            args=["--no-first-run", "--no-default-browser-check", "--disable-blink-features=AutomationControlled"]
        )
        
        page = context.pages[0] if context.pages else await context.new_page()
        
        url = "https://fasih-sm.bps.go.id/app/dashboard"
        print(f"[INFO] Navigating to {url}...")
        try:
            await page.goto(url, timeout=30000)
            await page.wait_for_load_state("networkidle", timeout=10000)
        except Exception as e:
            print(f"[WARNING] Navigation timeout or error: {e}")
            
        print(f"[INFO] Current URL: {page.url}")
        
        # Check if login is required
        if "login" in page.url or "sso" in page.url:
            print("[ERROR] Browser is redirected to login page. Please login first in your active Chrome browser!")
            await context.close()
            sys.exit(1)
            
        # Give page some time to fetch dashboard data
        await page.wait_for_timeout(5000)
        
        print("\n--- DOM INSPECTION ---")
        
        # Look for any table elements on the page
        tables = await page.query_selector_all("table")
        print(f"Found {len(tables)} tables on the page.")
        
        for idx, table in enumerate(tables):
            print(f"\n--- Table {idx} ---")
            headers = []
            th_elements = await table.query_selector_all("th")
            for th in th_elements:
                headers.append((await th.inner_text()).strip())
            print(f"Headers: {headers}")
            
            rows = await table.query_selector_all("tr")
            print(f"Total rows: {len(rows)}")
            for r_idx, row in enumerate(rows[:20]):  # print first 20 rows
                cells = []
                td_elements = await row.query_selector_all("td")
                for td in td_elements:
                    cells.append((await td.inner_text()).strip())
                if cells:
                    print(f"Row {r_idx}: {cells}")
                    
        # Let's save a screenshot to verify what it sees
        screenshot_path = "scratch/dashboard_screenshot.png"
        os.makedirs("scratch", exist_ok=True)
        await page.screenshot(path=screenshot_path)
        print(f"\n[INFO] Screenshot saved to {screenshot_path}")
        
        await context.close()

if __name__ == "__main__":
    asyncio.run(main())
