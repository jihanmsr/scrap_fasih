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

def save_csv_data(all_records):
    try:
        with open(OUTPUT_CSV, mode="w", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(["Kode Identitas", "Nama Perusahaan", "Status Dokumen", "Email Tujuan", "Status terakhir", "Status History", "Timestamp History", "Urutan History"])
            for r in all_records:
                writer.writerow([
                    r.get("code", "-"),
                    r.get("company_name", "-"),
                    r.get("survey_status", "-"),
                    r.get("email", "-"),
                    r.get("global_status", "-"),
                    r.get("status", "-"),
                    r.get("timestamp", "-"),
                    r.get("order", 0)
                ])
    except Exception as e:
        logging.error(f"Gagal menyimpan CSV: {e}")

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

            # Simpan CSV hasil pembaruan
            save_csv_data(all_records)

            # Kirim data ke Supabase jika terkonfigurasi
            if supabase:
                logging.info("Menyinkronkan data ke Supabase...")
                # Format data agar sesuai dengan kolom tabel Supabase
                available_cols = set()
                try:
                    sample_res = supabase.table("email_logs").select("*").limit(1).execute()
                    if sample_res.data:
                        available_cols = set(sample_res.data[0].keys())
                    else:
                        available_cols = {"code", "company_name", "email", "global_status", "status", "timestamp", "order"}
                except Exception as e:
                    logging.warning(f"Gagal mendeteksi kolom Supabase: {e}")
                    available_cols = {"code", "company_name", "email", "global_status", "status", "timestamp", "order"}

                db_records = []
                for r in js_data:
                    rec = {
                        "code": str(r.get("code", "-")),
                        "company_name": str(r.get("company_name", "-")),
                        "email": str(r.get("email", "-")),
                        "global_status": str(r.get("global_status", "-")),
                        "status": str(r.get("status", "-")),
                        "timestamp": str(r.get("timestamp", "-")),
                        "order": int(r.get("order", 0))
                    }
                    if "survey_status" in available_cols:
                        rec["survey_status"] = str(r.get("survey_status", "-"))
                    db_records.append(rec)
                
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
    try:
        page.goto(login_url, timeout=90000, wait_until="domcontentloaded")
    except Exception as e:
        logging.warning(f"Timeout saat membuka halaman awal, script akan lanjut: {e}")
    
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
    try:
        page.goto(target_data_url, timeout=90000, wait_until="domcontentloaded")
    except Exception as e:
        logging.warning(f"Timeout saat navigasi (mungkin karena jaringan lambat), script akan lanjut: {e}")
    time.sleep(5)
    
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
                        # Mendukung pembacaan format baru (8 kolom) dan format lama (7 kolom)
                        if len(row) >= 8:
                            all_records.append({
                                "code": row[0],
                                "company_name": row[1],
                                "survey_status": row[2],
                                "email": row[3],
                                "global_status": row[4],
                                "status": row[5],
                                "timestamp": row[6],
                                "order": int(row[7]) if row[7].isdigit() else 0
                            })
                            if row[0] != "-":
                                processed_codes.add(row[0])
                        else:
                            all_records.append({
                                "code": row[0],
                                "company_name": row[1],
                                "survey_status": "-",
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
        
        csv_exists = os.path.exists(OUTPUT_CSV)
        with open(OUTPUT_CSV, mode="a", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            if not csv_exists:
                writer.writerow(["Kode Identitas", "Nama Perusahaan", "Status Dokumen", "Email Tujuan", "Status terakhir", "Status History", "Timestamp History", "Urutan History"])
            
            def select_dropdown_option(target_text):
                try:
                    page.wait_for_selector("[cmdk-item], div[role='option']", timeout=30000)
                    options = page.locator("[cmdk-item], div[role='option']").all()
                    for opt in options:
                        opt_text = opt.inner_text().strip()
                        if target_text.upper() in opt_text.upper():
                            opt.click(force=True)
                            return True
                except Exception as e:
                    logging.warning(f"Gagal memilih opsi '{target_text}': {e}")
                return False

            # Buka filter pertama kali untuk memetakan kabupaten/kota
            logging.info("Membuka filter wilayah untuk mendeteksi Kabupaten/Kota...")
            filter_btn = page.locator("button").filter(has=page.locator("svg.tabler-icon-filter")).first
            filter_btn.click(force=True)
            time.sleep(1.5)

            # Pilih Provinsi SULAWESI TENGAH (dropdown index 0)
            dropdown_buttons = page.locator("div[role='dialog'] button.f\\:justify-between, [data-radix-portal] button.f\\:justify-between").all()
            dropdown_buttons[0].click(force=True)
            time.sleep(1)
            select_dropdown_option("SULAWESI TENGAH")
            time.sleep(1)

            # Klik dropdown Kabupaten/Kota (dropdown index 1)
            # Ambil kembali list button karena DOM ter-update setelah memilih provinsi
            dropdown_buttons = page.locator("div[role='dialog'] button.f\\:justify-between, [data-radix-portal] button.f\\:justify-between").all()
            dropdown_buttons[1].click(force=True)
            page.wait_for_selector("[cmdk-item], div[role='option']", timeout=30000)
            time.sleep(1)
            
            kab_options = page.locator("div[role='option'], [cmdk-item]").all()
            kab_names = [opt.inner_text().strip() for opt in kab_options if opt.inner_text().strip()]
            logging.info(f"Ditemukan {len(kab_names)} Kabupaten/Kota untuk diproses: {kab_names}")

            # Tutup filter sementara
            page.keyboard.press("Escape")
            time.sleep(1.5)

            for kab_name in kab_names:
                logging.info(f"=== Memulai Scraping Wilayah: {kab_name} ===")
                
                # Buka filter
                filter_btn.click(force=True)
                time.sleep(1.5)
                
                # Reset filter agar kembali bersih
                reset_btn = page.locator("button:has-text('Reset')").first
                if reset_btn.count() > 0:
                    reset_btn.click(force=True)
                    time.sleep(1.5)
                
                # Ambil dropdown_buttons setelah reset
                dropdown_buttons = page.locator("div[role='dialog'] button.f\\:justify-between, [data-radix-portal] button.f\\:justify-between").all()
                
                # Pilih Provinsi
                dropdown_buttons[0].click(force=True)
                time.sleep(1)
                select_dropdown_option("SULAWESI TENGAH")
                time.sleep(1.5)
                
                # Pilih Kabupaten/Kota
                dropdown_buttons = page.locator("div[role='dialog'] button.f\\:justify-between, [data-radix-portal] button.f\\:justify-between").all()
                dropdown_buttons[1].click(force=True)
                time.sleep(1)
                select_dropdown_option(kab_name)
                time.sleep(1.5)
                
                # Tutup dialog filter
                page.keyboard.press("Escape")
                time.sleep(2)
                
                page_num = 1
                while True:
                    logging.info(f"=== Kab/Kot: {kab_name} | Memproses Halaman {page_num} ===")
                    
                    # Deteksi jika dialihkan ke halaman login SSO BPS
                    if "sso" in page.url.lower() or "login" in page.url.lower():
                        logging.warning("=== DETEKSI: Sesi Login SSO BPS Kedaluwarsa! ===")
                        print("\n" + "!"*70)
                        print("SESI LOGIN KEDALUWARSA. SILAKAN LOGIN KEMBALI DI BROWSER CHROMIUM.")
                        print("Script akan otomatis mendeteksi ketika Anda sudah login kembali.")
                        print("!"*70 + "\n")
                        
                        while "sso" in page.url.lower() or "login" in page.url.lower():
                            time.sleep(3)
                            
                        logging.info("Sesi login terdeteksi aktif kembali! Membuka ulang halaman data...")
                        page.goto(base_url)
                        time.sleep(4)
                    
                    # Pastikan berada di tampilan List (≡)
                    try:
                        list_button = page.locator("button[aria-label='Daftar'], button[aria-label='List'], [data-slot=toggle-group-item]").nth(1)
                        if list_button.count() > 0:
                            if list_button.get_attribute("aria-checked") != "true":
                                logging.info("Beralih ke tampilan List (≡)...")
                                list_button.click()
                                time.sleep(3)
                    except Exception as e:
                        logging.warning(f"Gagal memeriksa/mengklik tombol List: {e}")
                    
                    # Cari semua tombol tiga titik (⋮) di setiap baris/card data
                    dots_buttons = page.locator("button").filter(has=page.locator("svg.tabler-icon-dots-vertical")).all()
                    
                    if not dots_buttons:
                        logging.info(f"Tidak ada data (tombol tiga titik) di halaman {page_num} untuk {kab_name}. Selesai untuk wilayah ini.")
                        break
                    
                    logging.info(f"Menemukan {len(dots_buttons)} baris data (tombol ⋮) di halaman {page_num} untuk {kab_name}")
                    
                    for idx, btn in enumerate(dots_buttons):
                        try:
                            # 1. Ambil Kode Identitas
                            parent_card = btn.locator("xpath=ancestor::div[contains(@class, 'border') or contains(@class, 'rounded') or contains(@class, 'p-4')][1]")
                            card_text = parent_card.inner_text()
                            lines = [line.strip() for line in card_text.split("\n") if line.strip()]
                            
                            code = "-"
                            for line in lines:
                                if "- UB -" in line:
                                    code = line
                                    break
                            
                            # 2. Ambil Status Dokumen (Survey Status) dari halaman awal terlebih dahulu
                            survey_status = "-"
                            for line in lines:
                                line_upper = line.strip().upper()
                                if line_upper in ["DRAFT", "OPEN", "SUBMITTED RESPONDENT", "SUBMITTED PENGAWAS", "SUBMITTED KOSEKA", "SUBMITTED KABKOT", "SUBMITTED PROV", "APPROVED", "REJECTED"]:
                                    survey_status = line_upper
                                    break

                            if code != "-" and code in processed_codes:
                                logging.info(f"-> Update Status (Sudah ada): {code} | Status: {survey_status}")
                                updated_any = False
                                for r in all_records:
                                    if r.get("code") == code:
                                        r["survey_status"] = survey_status
                                        updated_any = True
                                if updated_any:
                                    continue
                                
                            # Klik tombol tiga titik (⋮)
                            btn.click()
                            time.sleep(0.5)
                            
                            # Pastikan menu popup muncul
                            riwayat_menu_item = page.locator("div[role='menuitem']").filter(has_text="Riwayat Broadcast").first
                            try:
                                riwayat_menu_item.wait_for(state="visible", timeout=2000)
                            except Exception:
                                logging.info("Menu pop-up tidak terdeteksi, mencoba klik ulang tombol tiga titik...")
                                btn.click()
                                time.sleep(1)
                                riwayat_menu_item.wait_for(state="visible", timeout=3000)
                            
                            # 3. Ambil Nama Perusahaan
                            company_name = "-"
                            for i, line in enumerate(lines):
                                if "Nama Perusahaan" in line and i + 1 < len(lines):
                                    company_name = lines[i+1]
                                    break
                            if company_name == "-" and len(lines) >= 3:
                                company_name = lines[2] if "Nama" not in lines[2] else lines[3]
                            
                            # 4. Klik "Riwayat Broadcast" dari pop-up menu
                            if riwayat_menu_item.count() > 0:
                                riwayat_menu_item.click()
                                time.sleep(1.5)
                                
                                broadcast_headers = page.locator("div[role='dialog'] div.f\\:cursor-pointer").all()
                                processed_count = 0
                                for b_card in broadcast_headers:
                                    email_el = b_card.locator("h4").first
                                    email = email_el.inner_text().strip() if email_el.count() > 0 else "-"
                                    
                                    card_text = b_card.inner_text()
                                    if code == "-" or code not in card_text:
                                        continue
                                    
                                    processed_count += 1
                                    b_card.click()
                                    
                                    first_box = page.locator("div[role='dialog'] div.f\\:mb-3.f\\:flex-1.f\\:rounded-lg.f\\:border.f\\:bg-card.f\\:p-3").first
                                    try:
                                        first_box.wait_for(state="visible", timeout=4000)
                                    except Exception:
                                        pass
                                    
                                    boxes = page.locator("div[role='dialog'] div.f\\:mb-3.f\\:flex-1.f\\:rounded-lg.f\\:border.f\\:bg-card.f\\:p-3").all()
                                    history_items = []
                                    for box in boxes:
                                        status_hist_el = box.locator("div.f\\:inline-flex").first
                                        status_hist = status_hist_el.inner_text().strip().lower() if status_hist_el.count() > 0 else "-"
                                        
                                        time_hist_el = box.locator("span.f\\:shrink-0.f\\:text-muted-foreground.f\\:text-xs").first
                                        time_hist = time_hist_el.inner_text().strip() if time_hist_el.count() > 0 else "-"
                                        
                                        history_items.append((status_hist, time_hist))
                                    
                                    if not history_items:
                                        writer.writerow([code, company_name, survey_status, email, "-", "-", "-", 0])
                                        all_records.append({
                                            "code": code,
                                            "company_name": company_name,
                                            "survey_status": survey_status,
                                            "email": email,
                                            "global_status": "-",
                                            "status": "-",
                                            "timestamp": "-",
                                            "order": 0
                                        })
                                    else:
                                        last_status = history_items[-1][0] if history_items else "-"
                                        for order, (status_hist, time_hist) in enumerate(history_items):
                                            writer.writerow([code, company_name, survey_status, email, last_status, status_hist, time_hist, order + 1])
                                            all_records.append({
                                                "code": code,
                                                "company_name": company_name,
                                                "survey_status": survey_status,
                                                "email": email,
                                                "global_status": last_status,
                                                "status": status_hist,
                                                "timestamp": time_hist,
                                                "order": order + 1
                                            })
                                    
                                    b_card.click()
                                    time.sleep(0.4)
                                
                                if processed_count == 0:
                                    writer.writerow([code, company_name, survey_status, "-", "-", "-", "-", 0])
                                    all_records.append({
                                        "code": code,
                                        "company_name": company_name,
                                        "survey_status": survey_status,
                                        "email": "-",
                                        "global_status": "-",
                                        "status": "-",
                                        "timestamp": "-",
                                        "order": 0
                                    })
                                    
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
                    
                    csv_file.flush()
                    save_realtime_data(all_records)
                    
                    # Tunggu sebentar agar DOM selesai loading/rendering
                    time.sleep(2)
                    
                    # Beralih ke halaman berikutnya menggunakan tombol pagination 'Next'
                    next_btn = page.locator("button[aria-label='Go to next page']").first
                    
                    # Jika tidak langsung terdeteksi, tunggu sekali lagi (karena render React/Radix lambat)
                    if next_btn.count() == 0:
                        time.sleep(2)
                        next_btn = page.locator("button[aria-label='Go to next page']").first
                        
                    if next_btn.count() == 0 or not next_btn.is_enabled() or next_btn.get_attribute("disabled") is not None:
                        logging.info(f"Selesai memproses halaman terakhir untuk {kab_name}.")
                        break
                    
                    logging.info("Beralih ke halaman berikutnya...")
                    next_btn.click(force=True)
                    time.sleep(4)
                    page_num += 1

        logging.info("Membuat rekap data final...")
        save_realtime_data(all_records)
        logging.info("Scraping selesai!")
        context.close()

if __name__ == "__main__":
    scrape_data()
