import os
import json
import csv
import time
import logging
import pandas as pd
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
from supabase import create_client, Client

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load Supabase config
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY and "MASUKKAN" not in SUPABASE_URL and "http" in SUPABASE_URL:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        logging.info("Koneksi Supabase berhasil diinisialisasi.")
    except Exception as e:
        logging.error(f"Gagal menginisialisasi Supabase: {e}")

USER_DATA_DIR = "playwright_chrome_profile"
OUTPUT_CSV = "all_email_history.csv"
OUTPUT_BOUNCED_EXCEL = "bounced_emails.xlsx"
OUTPUT_JS = "data.js"

def save_realtime_data(all_records):
    try:
        df = pd.DataFrame(all_records)
        if not df.empty:
            # Simpan data.js untuk dashboard
            import datetime
            now_str = datetime.datetime.now().strftime("%d %b %Y, %H:%M:%S")
            js_data = df.to_dict(orient="records")
            with open(OUTPUT_JS, "w", encoding="utf-8") as js_file:
                js_file.write(f"window.EMAIL_DATA = {json.dumps(js_data, ensure_ascii=False, indent=2)};\n")
                js_file.write(f"window.LAST_UPDATED = '{now_str}';\n")
            
            # Rekap Excel Bounced
            bounced_emails = df[df['status'].str.lower() == 'bounced']['email'].unique()
            df_bounced = df[df['email'].isin(bounced_emails)]
            df_bounced.to_excel(OUTPUT_BOUNCED_EXCEL, index=False)

            # Kirim data ke Supabase jika terkonfigurasi
            if supabase:
                logging.info("Menyinkronkan data ke Supabase...")
                # Format data agar sesuai dengan kolom tabel Supabase
                db_records = []
                for r in js_data:
                    db_records.append({
                        "code": str(r.get("code", "-")),
                        "company_name": str(r.get("company_name", "-")),
                        "email": str(r.get("email", "-")),
                        "global_status": str(r.get("global_status", "-")),
                        "status": str(r.get("status", "-")),
                        "timestamp": str(r.get("timestamp", "-")),
                        "order": int(r.get("order", 0))
                    })
                
                # Kosongkan tabel lama lalu isi dengan data terbaru (karena data history berurutan)
                supabase.table("email_logs").delete().neq("code", "FORCE_DELETE_ALL_XYZ").execute()
                supabase.table("email_logs").insert(db_records).execute()
                logging.info(f"Sinkronisasi Supabase berhasil! Mengunggah {len(db_records)} records.")
    except Exception as e:
        logging.error(f"Gagal menulis data/sinkronisasi real-time: {e}")

def get_authenticated_context(p, headless=False):
    logging.info("Membuka browser dengan profil Chrome lokal...")
    context = p.chromium.launch_persistent_context(
        user_data_dir=USER_DATA_DIR,
        headless=headless,
        viewport={"width": 1280, "height": 800}
    )
    page = context.pages[0] if context.pages else context.new_page()
    
    # Akses halaman awal
    login_url = "https://fasih-sm.bps.go.id/survey-collection/survey"
    page.goto(login_url)
    
    print("\n" + "="*70)
    print("SILAKAN LOGIN SSO DI BROWSER CHROMIUM YANG TERBUKA.")
    print("Setelah login berhasil, script akan otomatis mendeteksi dan navigasi.")
    print("Atau, jika sudah masuk, Anda bisa menekan ENTER di terminal ini.")
    print("="*70 + "\n")
    
    target_data_url = "https://fasih-sm.bps.go.id/app/surveys/ecddb52e-f392-403c-a963-47391f217010/37526b20-81c8-42f5-a895-6190137d7394/data"
    
    # Deteksi otomatis login, atau tunggu ENTER
    import select
    import sys
    
    while True:
        if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
            sys.stdin.readline() # consume input
            logging.info("Konfirmasi manual diterima via ENTER.")
            break
            
        try:
            current_url = page.url
            if "fasih-sm.bps.go.id" in current_url and "sso" not in current_url.lower() and "login" not in current_url.lower():
                logging.info("Login terdeteksi secara otomatis!")
                break
        except Exception:
            pass
            
        logging.info("Menunggu login SSO di browser (atau tekan ENTER jika sudah login)...")
        time.sleep(3)
        
    logging.info(f"Navigasi otomatis ke halaman target: {target_data_url}")
    page.goto(target_data_url)
    time.sleep(3)
    
    return context, page

def scrape_data():
    # Load existing data to resume/prevent overwrite
    all_records = []
    processed_codes = set()
    if os.path.exists(OUTPUT_CSV):
        logging.info(f"Membaca data yang sudah ada dari {OUTPUT_CSV}...")
        try:
            with open(OUTPUT_CSV, mode="r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader, None)
                for row in reader:
                    if len(row) >= 7:
                        all_records.append({
                            "code": row[0],
                            "company_name": row[1],
                            "email": row[2],
                            "global_status": row[3],
                            "status": row[4],
                            "timestamp": row[5],
                            "order": int(row[6]) if row[6].isdigit() else 0
                        })
                        if row[0] != "-":
                            processed_codes.add(row[0])
            logging.info(f"Berhasil memuat {len(processed_codes)} perusahaan yang sudah diproses sebelumnya.")
        except Exception as e:
            logging.warning(f"Gagal membaca CSV lama: {e}")

    with sync_playwright() as p:
        context, page = get_authenticated_context(p, headless=False)
        
        base_url = "https://fasih-sm.bps.go.id/app/surveys/ecddb52e-f392-403c-a963-47391f217010/37526b20-81c8-42f5-a895-6190137d7394/data"
        total_pages = 127
        
        csv_exists = os.path.exists(OUTPUT_CSV)
        with open(OUTPUT_CSV, mode="a", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            if not csv_exists:
                writer.writerow(["Kode Identitas", "Nama Perusahaan", "Email Tujuan", "Status terakhir", "Status History", "Timestamp History", "Urutan History"])
            
            for page_num in range(1, total_pages + 1):
                logging.info(f"=== Memproses Halaman {page_num} dari {total_pages} ===")
                
                # Navigasi ke halaman target dengan mekanisme retry jika timeout
                success = False
                for attempt in range(3):
                    try:
                        page.goto(f"{base_url}?page={page_num}&perPage=10", timeout=45000)
                        success = True
                        break
                    except Exception as e:
                        logging.warning(f"Timeout/Error saat membuka halaman {page_num} (percobaan {attempt+1}/3): {e}")
                        time.sleep(5)
                
                if not success:
                    logging.error(f"Gagal memuat halaman {page_num} setelah 3 percobaan. Melewati halaman ini.")
                    continue
                
                # Tunggu daftar data termuat
                try:
                    page.wait_for_load_state("networkidle", timeout=10000)
                except Exception:
                    pass
                time.sleep(3)  # Jeda aman agar seluruh data termuat

                # Deteksi jika dialihkan ke halaman login SSO BPS
                if "sso" in page.url.lower() or "login" in page.url.lower():
                    logging.warning("=== DETEKSI: Sesi Login SSO BPS Kedaluwarsa! ===")
                    print("\n" + "!"*70)
                    print("SESI LOGIN KEDALUWARSA. SILAKAN LOGIN KEMBALI DI BROWSER CHROMIUM.")
                    print("Script akan otomatis mendeteksi ketika Anda sudah login kembali.")
                    print("!"*70 + "\n")
                    
                    # Tunggu sampai pengguna login kembali
                    while "sso" in page.url.lower() or "login" in page.url.lower():
                        time.sleep(3)
                        
                    logging.info("Sesi login terdeteksi aktif kembali! Membuka ulang halaman data...")
                    page.goto(f"{base_url}?page={page_num}&perPage=10", timeout=45000)
                    time.sleep(4)
                
                # Pastikan berada di tampilan List (≡)
                try:
                    list_button = page.locator("button[aria-label='Daftar'], button[aria-label='List'], [data-slot=toggle-group-item]").nth(1)
                    if list_button.count() > 0:
                        if list_button.get_attribute("aria-checked") != "true":
                            logging.info("Beralih ke tampilan List (≡)...")
                            list_button.click()
                            time.sleep(3) # Jeda lebih lama untuk transisi layout
                except Exception as e:
                    logging.warning(f"Gagal memeriksa/mengklik tombol List: {e}")
                
                # Cari semua tombol tiga titik (⋮) di setiap baris/card data (hanya vertikal untuk aksi baris)
                dots_buttons = page.locator("button").filter(has=page.locator("svg.tabler-icon-dots-vertical")).all()
                
                if not dots_buttons:
                    logging.warning(f"Tidak menemukan tombol tiga titik (⋮) di halaman {page_num}. Mencoba reload...")
                    page.reload()
                    time.sleep(4)
                    dots_buttons = page.locator("button").filter(has=page.locator("svg.tabler-icon-dots-vertical")).all()
                
                logging.info(f"Menemukan {len(dots_buttons)} baris data (tombol ⋮) di halaman {page_num}")
                
                for idx, btn in enumerate(dots_buttons):
                    try:
                        # 1. Ambil Kode Identitas terlebih dahulu untuk mengecek apakah sudah diproses
                        parent_card = btn.locator("xpath=ancestor::div[contains(@class, 'border') or contains(@class, 'rounded') or contains(@class, 'p-4')][1]")
                        card_text = parent_card.inner_text()
                        lines = [line.strip() for line in card_text.split("\n") if line.strip()]
                        
                        code = "-"
                        for line in lines:
                            if "- UB -" in line:
                                code = line
                                break
                        
                        if code != "-" and code in processed_codes:
                            logging.info(f"-> Skip (Sudah diproses): {code}")
                            continue
                            
                        # Klik tombol tiga titik (⋮)
                        btn.click()
                        time.sleep(0.5)
                        
                        # Self-healing check: pastikan menu popup muncul
                        riwayat_menu_item = page.locator("div[role='menuitem']").filter(has_text="Riwayat Broadcast").first
                        try:
                            riwayat_menu_item.wait_for(state="visible", timeout=2000)
                        except Exception:
                            # Jika tidak muncul, coba klik ulang (mungkin layout bergeser sedikit saat load)
                            logging.info("Menu pop-up tidak terdeteksi, mencoba klik ulang tombol tiga titik...")
                            btn.click()
                            time.sleep(1)
                            riwayat_menu_item.wait_for(state="visible", timeout=3000)
                        
                        # 2. Ambil Nama Perusahaan dari card (lines dan code sudah diambil sebelumnya)
                        company_name = "-"
                        for i, line in enumerate(lines):
                            if "Nama Perusahaan" in line and i + 1 < len(lines):
                                company_name = lines[i+1]
                                break
                        
                        # Jika pencarian Nama Perusahaan di atas gagal, coba ambil baris kedua (di bawah Kode Identitas)
                        if company_name == "-" and len(lines) >= 3:
                            company_name = lines[2] if "Nama" not in lines[2] else lines[3]
                        
                        # 3. Klik "Riwayat Broadcast" dari pop-up menu
                        if riwayat_menu_item.count() > 0:
                            riwayat_menu_item.click()
                            time.sleep(1.5) # Tunggu dialog riwayat terbuka
                            
                            # 4. Cari semua card broadcast di dalam dialog
                            broadcast_headers = page.locator("div[role='dialog'] div.f\\:cursor-pointer").all()
                            
                            processed_count = 0
                            for b_card in broadcast_headers:
                                # Ambil email dari header card
                                email_el = b_card.locator("h4").first
                                email = email_el.inner_text().strip() if email_el.count() > 0 else "-"
                                
                                # Pastikan card ini sesuai dengan Kode Identitas target (code)
                                card_text = b_card.inner_text()
                                if code == "-" or code not in card_text:
                                    continue
                                
                                processed_count += 1
                                # Klik header/card untuk expand riwayat detail
                                b_card.click()
                                
                                # Tunggu agar log riwayat memuat dan dirender (sehingga tidak kosong / -)
                                first_box = page.locator("div[role='dialog'] div.f\\:mb-3.f\\:flex-1.f\\:rounded-lg.f\\:border.f\\:bg-card.f\\:p-3").first
                                try:
                                    # Tunggu box log pengiriman pertama muncul secara dinamis
                                    first_box.wait_for(state="visible", timeout=4000)
                                except Exception:
                                    pass
                                
                                # Ambil semua box riwayat yang terlihat di dialog saat ini
                                boxes = page.locator("div[role='dialog'] div.f\\:mb-3.f\\:flex-1.f\\:rounded-lg.f\\:border.f\\:bg-card.f\\:p-3").all()
                                
                                history_items = []
                                for box in boxes:
                                    status_hist_el = box.locator("div.f\\:inline-flex").first
                                    status_hist = status_hist_el.inner_text().strip().lower() if status_hist_el.count() > 0 else "-"
                                    
                                    time_hist_el = box.locator("span.f\\:shrink-0.f\\:text-muted-foreground.f\\:text-xs").first
                                    time_hist = time_hist_el.inner_text().strip() if time_hist_el.count() > 0 else "-"
                                    
                                    history_items.append((status_hist, time_hist))
                                
                                # Tulis ke CSV & List
                                if not history_items:
                                    writer.writerow([code, company_name, email, "-", "-", "-", 0])
                                    all_records.append({
                                        "code": code,
                                        "company_name": company_name,
                                        "email": email,
                                        "global_status": "-",
                                        "status": "-",
                                        "timestamp": "-",
                                        "order": 0
                                    })
                                else:
                                    last_status = history_items[-1][0] if history_items else "-"
                                    for order, (status_hist, time_hist) in enumerate(history_items):
                                        writer.writerow([code, company_name, email, last_status, status_hist, time_hist, order + 1])
                                        all_records.append({
                                            "code": code,
                                            "company_name": company_name,
                                            "email": email,
                                            "global_status": last_status,
                                            "status": status_hist,
                                            "timestamp": time_hist,
                                            "order": order + 1
                                        })
                                
                                # Klik lagi untuk collapse
                                b_card.click()
                                time.sleep(0.4)
                            
                            if processed_count == 0:
                                writer.writerow([code, company_name, "-", "-", "-", "-", 0])
                                all_records.append({
                                    "code": code,
                                    "company_name": company_name,
                                    "email": "-",
                                    "global_status": "-",
                                    "status": "-",
                                    "timestamp": "-",
                                    "order": 0
                                })

                            # Tutup modal/dialog riwayat dengan Escape
                            page.keyboard.press("Escape")
                            time.sleep(0.8)
                            
                            logging.info(f"-> Berhasil: {code} | {company_name} ({processed_count} email(s) processed)")
                        else:
                            logging.warning(f"Menu 'Riwayat Broadcast' tidak ditemukan untuk card indeks {idx}")
                            page.keyboard.press("Escape")
                            time.sleep(0.5)
                            
                    except Exception as e:
                        logging.error(f"Gagal memproses baris indeks {idx} di halaman {page_num}: {e}")
                        page.keyboard.press("Escape")
                        time.sleep(0.8)
                
                # Simpan data real-time ke CSV, data.js (Dashboard), dan Excel
                csv_file.flush()
                save_realtime_data(all_records)
        
        # Simpan rekap data final
        logging.info("Membuat rekap data final...")
        save_realtime_data(all_records)
        logging.info("Scraping selesai!")
        context.close()

if __name__ == "__main__":
    scrape_data()
