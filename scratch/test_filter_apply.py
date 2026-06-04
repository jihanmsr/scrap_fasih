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
        filter_btn.click()
        time.sleep(1.5)
        
        # Cari semua button yang memiliki justify-between (atau w-full)
        dropdowns = page.locator("button.f\\:w-full").all()
        logging.info(f"Ditemukan {len(dropdowns)} dropdowns di filter dialog.")
        
        # 1. Pilih Provinsi
        dropdowns[0].click()
        time.sleep(1)
        prov_opt = page.locator("div[role='option'], [cmdk-item]").filter(has_text="SULAWESI TENGAH").first
        logging.info(f"Memilih Provinsi: {prov_opt.inner_text()}")
        prov_opt.click()
        time.sleep(1)
        
        # 2. Pilih Kabupaten/Kota (misal BANGGAI KEPULAUAN)
        dropdowns = page.locator("button.f\\:w-full").all()
        dropdowns[1].click()
        time.sleep(1)
        kab_opt = page.locator("div[role='option'], [cmdk-item]").filter(has_text="BANGGAI KEPULAUAN").first
        logging.info(f"Memilih Kab/Kot: {kab_opt.inner_text()}")
        kab_opt.click()
        time.sleep(1)
        
        # Close filter by clicking close button or pressing Escape
        logging.info("Menutup dialog filter...")
        page.keyboard.press("Escape")
        time.sleep(2)
        
        # Cek isi tabel
        page.screenshot(path="scratch/filtered_table.png")
        logging.info("Screenshot tabel hasil filter disimpan ke scratch/filtered_table.png")
        
        # Dapatkan jumlah data / halaman dari info pagination atau text di footer
        # Mari print text dari elemen pagination
        pagination_info = page.locator("div:has-text('Showing'), div:has-text('Menampilkan')").all()
        for idx, info in enumerate(pagination_info):
            text = info.inner_text().strip()
            if text:
                print(f"Pagination Info {idx+1}: {text}")
                
        context.close()

if __name__ == "__main__":
    run_test()
