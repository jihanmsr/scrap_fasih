import os
import time
import logging
from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

USER_DATA_DIR = "playwright_chrome_profile"

def run_inspect():
    with sync_playwright() as p:
        logging.info("Membuka browser...")
        context = p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=False
        )
        page = context.pages[0] if context.pages else context.new_page()
        
        target_url = "https://fasih-sm.bps.go.id/app/surveys/ecddb52e-f392-403c-a963-47391f217010/37526b20-81c8-42f5-a895-6190137d7394/data"
        page.goto(target_url)
        
        # Wait for table
        while True:
            try:
                filter_btn = page.locator("button").filter(has=page.locator("svg.tabler-icon-filter")).first
                if filter_btn.count() > 0 and filter_btn.is_visible():
                    break
            except Exception:
                pass
            time.sleep(2)
            
        logging.info("Tabel data terdeteksi. Mencari tombol pagination...")
        
        # Cari semua tombol di bagian bawah halaman
        buttons = page.locator("button").all()
        logging.info(f"Ditemukan {len(buttons)} total tombol di halaman.")
        for idx, btn in enumerate(buttons):
            text = btn.inner_text().strip()
            html = btn.evaluate("el => el.outerHTML")
            # Filter tombol yang tampak seperti tombol pagination (misal ada angka, chevron, atau class pagination)
            if any(x in html for x in ["chevron", "arrow", "page", "next", "prev", "icon"]):
                print(f"Button {idx}: Text: '{text}' | HTML: {html[:200]}")
                
        context.close()

if __name__ == "__main__":
    run_inspect()
