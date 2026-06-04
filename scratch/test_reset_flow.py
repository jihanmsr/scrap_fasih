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
        
        # Wait for data table to load
        while True:
            try:
                filter_btn = page.locator("button").filter(has=page.locator("svg.tabler-icon-filter")).first
                if filter_btn.count() > 0 and filter_btn.is_visible():
                    break
            except Exception:
                pass
            time.sleep(2)
            
        # Buka filter
        logging.info("Membuka filter...")
        filter_btn.click()
        time.sleep(1.5)
        
        # Ambil daftar kabupaten/kota
        logging.info("Mengambil daftar kabupaten/kota...")
        prov_btn = page.locator("button:has-text('Pilih wilayah')").first
        prov_btn.click()
        time.sleep(1)
        prov_opt = page.locator("div[role='option'], [cmdk-item]").filter(has_text="SULAWESI TENGAH").first
        prov_opt.click()
        time.sleep(1)
        
        kab_btn = page.locator("button:has-text('Pilih wilayah')").first
        kab_btn.click()
        time.sleep(1)
        
        kab_options = page.locator("div[role='option'], [cmdk-item]").all()
        kab_names = [opt.inner_text().strip() for opt in kab_options if opt.inner_text().strip()]
        logging.info(f"Daftar Kabupaten/Kota ditemukan ({len(kab_names)}): {kab_names}")
        
        # Klik pilihan pertama agar dropdown kab/kot tertutup
        if kab_options:
            kab_options[0].click()
            time.sleep(1)
            
        # Sekarang mari test reset
        logging.info("Mencoba melakukan RESET...")
        reset_btn = page.locator("button:has-text('Reset')").first
        reset_btn.click()
        time.sleep(1.5)
        
        # Pilih kabupaten/kota ke-2 (misal BANGGAI) untuk verifikasi setelah reset
        logging.info("Memilih Provinsi kembali setelah reset...")
        prov_btn = page.locator("button:has-text('Pilih wilayah')").first
        prov_btn.click()
        time.sleep(1)
        prov_opt = page.locator("div[role='option'], [cmdk-item]").filter(has_text="SULAWESI TENGAH").first
        prov_opt.click()
        time.sleep(1)
        
        logging.info(f"Memilih Kabupaten/Kota ke-2 ({kab_names[1]}) setelah reset...")
        kab_btn = page.locator("button:has-text('Pilih wilayah')").first
        kab_btn.click()
        time.sleep(1)
        
        kab_opt_2 = page.locator("div[role='option'], [cmdk-item]").filter(has_text=kab_names[1]).first
        kab_opt_2.click()
        time.sleep(1)
        
        logging.info("Menutup filter dialog...")
        page.keyboard.press("Escape")
        time.sleep(2)
        
        # Selesai
        logging.info("Selesai pengetesan alur reset dan pilih filter!")
        context.close()

if __name__ == "__main__":
    run_test()
