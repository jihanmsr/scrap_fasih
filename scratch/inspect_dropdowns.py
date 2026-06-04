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
        
        # Wait for data table to load
        while True:
            try:
                filter_btn = page.locator("button").filter(has=page.locator("svg.tabler-icon-filter")).first
                if filter_btn.count() > 0 and filter_btn.is_visible():
                    logging.info("Filter button terdeteksi!")
                    break
            except Exception:
                pass
            time.sleep(2)
            
        logging.info("Mencoba mengklik tombol filter wilayah...")
        filter_btn.click()
        time.sleep(2)
        
        # Cari semua tombol "Pilih wilayah"
        wilayah_buttons = page.locator("button:has-text('Pilih wilayah')").all()
        logging.info(f"Ditemukan {len(wilayah_buttons)} tombol 'Pilih wilayah'")
        
        if len(wilayah_buttons) > 0:
            # Klik tombol Provinsi (indeks 0)
            logging.info("Mengklik tombol Provinsi (indeks 0)...")
            wilayah_buttons[0].click()
            time.sleep(2)
            
            # Ambil screenshot
            page.screenshot(path="scratch/provinsi_open.png")
            logging.info("Screenshot provinsi disimpan ke scratch/provinsi_open.png")
            
            # Ambil semua opsi yang muncul di portal
            options = page.locator("div[role='option'], [cmdk-item]").all()
            logging.info(f"Ditemukan {len(options)} opsi Provinsi.")
            for idx, opt in enumerate(options[:15]): # batasi print 15 saja
                print(f"Provinsi {idx+1}: {opt.inner_text()} | value: {opt.get_attribute('data-value')}")
                
            if len(options) > 0:
                # Pilih salah satu Provinsi secara acak/contoh, misal SULAWESI TENGAH (atau cari yang ada teksnya)
                target_prov = None
                for opt in options:
                    if "SULAWESI TENGAH" in opt.inner_text().upper():
                        target_prov = opt
                        break
                if not target_prov:
                    target_prov = options[0]
                    
                prov_name = target_prov.inner_text()
                logging.info(f"Memilih Provinsi: {prov_name}")
                target_prov.click()
                time.sleep(2)
                
                # Klik tombol Kabupaten/Kota (sekarang berada di indeks 1)
                # Dapatkan tombol-tombol "Pilih wilayah" kembali karena DOM diperbarui
                wilayah_buttons = page.locator("button:has-text('Pilih wilayah')").all()
                logging.info(f"Ditemukan {len(wilayah_buttons)} tombol 'Pilih wilayah' setelah memilih provinsi")
                
                # Biasanya tombol Kabupaten/Kota adalah yang berikutnya yang masih bertuliskan "Pilih wilayah"
                # Mari klik tombol ke-2
                if len(wilayah_buttons) > 0:
                    logging.info("Mengklik tombol Kabupaten/Kota (indeks 0 yang tersisa)...")
                    wilayah_buttons[0].click()
                    time.sleep(2)
                    
                    page.screenshot(path="scratch/kabkot_open.png")
                    logging.info("Screenshot kabupaten/kota disimpan ke scratch/kabkot_open.png")
                    
                    kab_options = page.locator("div[role='option'], [cmdk-item]").all()
                    logging.info(f"Ditemukan {len(kab_options)} opsi Kabupaten/Kota.")
                    for idx, opt in enumerate(kab_options[:15]):
                        print(f"Kab/Kot {idx+1}: {opt.inner_text()} | value: {opt.get_attribute('data-value')}")
                        
        context.close()

if __name__ == "__main__":
    run_inspect()
