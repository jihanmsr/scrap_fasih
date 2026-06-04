import os
import time
import logging
from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

USER_DATA_DIR = "playwright_chrome_profile"

def run_test():
    with sync_playwright() as p:
        logging.info("Membuka browser...")
        context = p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=False
        )
        page = context.pages[0] if context.pages else context.new_page()
        
        target_url = "https://fasih-sm.bps.go.id/app/surveys/ecddb52e-f392-403c-a963-47391f217010/37526b20-81c8-42f5-a895-6190137d7394/data"
        page.goto(target_url)
        
        while True:
            try:
                filter_btn = page.locator("button").filter(has=page.locator("svg.tabler-icon-filter")).first
                if filter_btn.count() > 0 and filter_btn.is_visible():
                    break
            except Exception:
                pass
            time.sleep(2)
            
        logging.info("Membuka filter...")
        filter_btn.click(force=True)
        time.sleep(1.5)
        
        # Test locator 1
        dropdowns = page.locator("div[role='dialog'] button.f\\:justify-between, [data-radix-portal] button.f\\:justify-between").all()
        logging.info(f"Locator 1: Ditemukan {len(dropdowns)} dropdowns.")
        for idx, btn in enumerate(dropdowns):
            print(f"Dropdown {idx}: Text: '{btn.inner_text().strip()}'")
            
        context.close()

if __name__ == "__main__":
    run_test()
