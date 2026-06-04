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
        
        logging.info("Silakan login SSO BPS jika belum masuk.")
        logging.info("Menunggu sampai tabel data terdeteksi...")
        
        # Tunggu sampai tabel data/halaman utama termuat
        while True:
            try:
                # Coba cari filter button
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
        
        # Cari semua div di body yang baru muncul (dialog/popover)
        logging.info("Mencari struktur dialog/popover di DOM...")
        
        # Ambil screenshot untuk visualisasi
        page.screenshot(path="scratch/filter_open.png")
        logging.info("Screenshot disimpan ke scratch/filter_open.png")
        
        # Mari cari semua button, input, dan span di dalam elemen yang memiliki state open atau radix portal
        # Biasanya radix UI menggunakan portal di akhir body. Jadi mari cari radix portal.
        portals = page.locator("[data-radix-portal], div[role='dialog'], div[role='menu']").all()
        logging.info(f"Ditemukan {len(portals)} Radix Portals / Dialogs.")
        
        for idx, portal in enumerate(portals):
            print(f"\n--- PORTAL {idx+1} ---")
            # Cetak semua teks tombol dan span
            buttons = portal.locator("button").all()
            spans = portal.locator("span").all()
            divs = portal.locator("div[cmdk-item], [role='option']").all()
            
            print("Buttons found:")
            for b in buttons:
                print("  Text:", b.inner_text(), "Class:", b.get_attribute("class"))
            print("Spans found:")
            for s in spans:
                print("  Text:", s.inner_text(), "Class:", s.get_attribute("class"))
            print("Options (cmdk-item) found:")
            for d in divs:
                print("  Value:", d.get_attribute("data-value"), "Text:", d.inner_text())
                
        # Jika tidak ditemukan portal, cetak body HTML
        if not portals:
            logging.info("Tidak ada portal terdeteksi, mencetak seluruh konten body...")
            body_html = page.locator("body").inner_html()
            with open("scratch/body_debug.html", "w", encoding="utf-8") as f:
                f.write(body_html)
            logging.info("Konten body ditulis ke scratch/body_debug.html")

        context.close()

if __name__ == "__main__":
    run_inspect()
