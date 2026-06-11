import os
import csv
import json
import time
import logging
import shutil
import subprocess
import socket
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client, Client
from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY and "MASUKKAN" not in SUPABASE_URL:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        logging.info("Koneksi Supabase berhasil diinisialisasi.")
    except Exception as e:
        logging.error(f"Gagal menginisialisasi Supabase: {e}")

# --- PERUBAHAN 1: NAMA FOLDER PROFIL DIBEDAKAN ---
USER_DATA_DIR = "playwright_chrome_profile_email" 
OUTPUT_CSV = "all_email_history.csv"
OUTPUT_JS = "data.js"
OUTPUT_BOUNCED_EXCEL = "bounced_emails.xlsx"
FORCE_RE_SCRAPE = True

# --- PERUBAHAN 2: PORT DIBEDAKAN MENJADI 9223 ---
def check_port_open(port=9223):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def cleanup_chrome_cache(user_data_dir):
    cache_dirs = [
        os.path.join(user_data_dir, "Default", "Cache"),
        os.path.join(user_data_dir, "Default", "Code Cache"),
        os.path.join(user_data_dir, "Default", "GPUCache"),
        os.path.join(user_data_dir, "Default", "Service Worker", "CacheStorage"),
    ]
    for path in cache_dirs:
        if os.path.exists(path):
            try:
                shutil.rmtree(path)
                logging.info(f"Membersihkan cache Chrome: {path}")
            except Exception as e:
                logging.warning(f"Gagal membersihkan cache Chrome {path}: {e}")


def launch_chrome_if_needed():
    port = 9223 # GANTI PORT DI SINI JUGA
    if check_port_open(port):
        logging.info(f"Chrome remote debugging port {port} sudah aktif. Menggunakan instansi yang ada.")
        return
    
    logging.info(f"Chrome remote debugging port {port} tidak aktif. Mencoba meluncurkan browser...")
    chrome_path = "/Users/jihanmaisaroh/Library/Caches/ms-playwright/chromium-1208/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"
    
    # Hapus lock file jika ada agar Chrome bisa berjalan lancar
    lock_file = os.path.join(USER_DATA_DIR, "SingletonLock")
    if os.path.exists(lock_file):
        try:
            os.remove(lock_file)
            logging.info("File SingletonLock berhasil dihapus untuk mencegah error lock profile.")
        except Exception as e:
            logging.warning(f"Gagal menghapus SingletonLock: {e}")
    
    abs_user_data_dir = os.path.abspath(USER_DATA_DIR)
    os.makedirs(abs_user_data_dir, exist_ok=True)
    cleanup_chrome_cache(abs_user_data_dir)
    
    cmd = [
        chrome_path,
        f"--remote-debugging-port={port}",
        f"--user-data-dir={abs_user_data_dir}",
        "--no-first-run",
        "--no-default-browser-check"
    ]
    
    # Launch Chrome in detached mode
    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Tunggu sampai port siap
    for _ in range(15):
        time.sleep(1)
        if check_port_open(port):
            logging.info(f"Browser Chrome berhasil diluncurkan dan siap di port {port}.")
            return
    logging.error(f"Gagal mendeteksi port {port} setelah meluncurkan Chrome.")

def get_authenticated_context(p):
    abs_user_data_dir = os.path.abspath(USER_DATA_DIR)
    os.makedirs(abs_user_data_dir, exist_ok=True)
    chrome_path = "/Users/jihanmaisaroh/Library/Caches/ms-playwright/chromium-1208/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"

    browser = None
    context = None
    page = None

    if check_port_open(9223):
        logging.info("Remote debugging port 9223 terdeteksi. Mencoba sambung via CDP...")
        try:
            browser = p.chromium.connect_over_cdp("http://localhost:9223") # GANTI PORT
            context = browser.contexts[0] if browser.contexts else browser.new_context()
            page = context.pages[0] if context.pages else context.new_page()
            logging.info("Berhasil tersambung ke browser via CDP.")
        except Exception as e:
            logging.warning(f"Gagal connect_over_cdp: {e}. Menggunakan Playwright persistent context sebagai fallback.")
            browser = None

    def try_launch_persistent():
        return p.chromium.launch_persistent_context(
            user_data_dir=abs_user_data_dir,
            headless=False,
            executable_path=chrome_path,
            args=["--no-first-run", "--no-default-browser-check", "--disable-background-networking", "--disable-background-timer-throttling"]
        )

    if page is None:
        logging.info("Meluncurkan browser melalui Playwright persistent context...")
        try:
            context = try_launch_persistent()
            page = context.pages[0] if context.pages else context.new_page()
        except Exception as e:
            logging.warning(f"Playwright persistent context gagal diluncurkan: {e}")
            cleanup_chrome_cache(abs_user_data_dir)
            logging.info("Membersihkan cache user data dan mencoba ulang.")
            try:
                context = try_launch_persistent()
                page = context.pages[0] if context.pages else context.new_page()
            except Exception as e2:
                logging.warning(f"Gagal meluncurkan Playwright persistent context setelah retry: {e2}")
                logging.info("Coba buka browser Playwright headful sebagai fallback...")
                try:
                    browser = p.chromium.launch(headless=False)
                    context = browser.new_context()
                    page = context.new_page()
                    logging.info("Browser Playwright headful berhasil diluncurkan.")
                except Exception as e3:
                    logging.warning(f"Playwright headful launch gagal: {e3}")
                    logging.info("Mode manual: tunggu user buka Chrome manual di port 9223...")
                    print("\n" + "="*70)
                    print("MANUAL MODE - BUKA CHROME DENGAN REMOTE DEBUGGING")
                    print("="*70)
                    print("Buka terminal baru dan jalankan perintah ini:")
                    print(f'  "{chrome_path}" --remote-debugging-port=9223 --user-data-dir="{abs_user_data_dir}"')
                    print()
                    print("Setelah Chrome terbuka, login ke fasih-sm.bps.go.id")
                    print("Lalu kembali ke terminal ini dan tekan ENTER.")
                    print("="*70 + "\n")
                    import sys
                    sys.stdin.readline()
                    logging.info("Mencoba koneksi CDP setelah setup manual...")
                    for attempt in range(10):
                        time.sleep(2)
                        if check_port_open(9223):
                            try:
                                browser = p.chromium.connect_over_cdp("http://localhost:9223")
                                context = browser.contexts[0] if browser.contexts else browser.new_context()
                                page = context.pages[0] if context.pages else context.new_page()
                                logging.info("Berhasil connect via CDP setelah manual setup!")
                                break
                            except Exception as cdp_err:
                                logging.warning(f"CDP connect attempt {attempt+1} gagal: {cdp_err}")
                                continue
                    if page is None:
                        logging.error("Tidak bisa connect CDP setelah manual setup. Exiting.")
                        raise RuntimeError("Browser setup failed after manual attempt")
        if page is not None and context is not None:
            page = context.pages[0] if context.pages else context.new_page()
            logging.info("Playwright context berhasil diluncurkan.")

    target_data_url = "https://fasih-sm.bps.go.id/app/surveys/ecddb52e-f392-403c-a963-47391f217010/37526b20-81c8-42f5-a895-6190137d7394/data"

    # Cari tab aktif yang sudah membuka fasih-sm
    current_page = None
    for p_page in context.pages:
        if "fasih-sm.bps.go.id" in p_page.url:
            current_page = p_page
            logging.info(f"Menemukan tab aktif dengan URL target: {current_page.url}")
            break

    if not current_page:
        logging.info("Tidak menemukan tab aktif. Membuat tab baru...")
        current_page = context.new_page()
        logging.info(f"Mencoba membuka halaman target langsung: {target_data_url}")
        try:
            current_page.goto(target_data_url, timeout=60000, wait_until="domcontentloaded")
        except Exception as e:
            logging.warning(f"Navigasi awal ke target langsung lambat/timeout: {e}")
        time.sleep(3)

    # Memantau redirect SSO selama beberapa detik pertama
    logging.info("Memantau status login dan redirect...")
    for _ in range(8):
        current_url = current_page.url
        if "sso" in current_url.lower() or "login" in current_url.lower() or "fasih-sm.bps.go.id" not in current_url:
            break
        time.sleep(1)

    current_url = current_page.url
    if "sso" in current_url.lower() or "login" in current_url.lower() or "fasih-sm.bps.go.id" not in current_url:
        print("\n" + "="*70)
        print("Sesi belum aktif atau memerlukan login SSO BPS.")
        print("SILAKAN LOGIN SSO DI BROWSER CHROMIUM YANG TERBUKA.")
        print("Setelah login berhasil, script akan otomatis mendeteksi dan navigasi.")
        print("Atau, jika sudah masuk, Anda bisa menekan ENTER di terminal ini.")
        print("="*70 + "\n")

        import select
        import sys

        while True:
            if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                sys.stdin.readline()
                logging.info("Konfirmasi manual diterima via ENTER.")
                break

            try:
                current_url = current_page.url
                if "fasih-sm.bps.go.id" in current_url and "sso" not in current_url.lower() and "login" not in current_url.lower():
                    logging.info("Login terdeteksi secara otomatis!")
                    break
            except Exception:
                pass

            logging.info("Menunggu login SSO di browser (atau tekan ENTER jika sudah login)...")
            time.sleep(3)

    # Setelah login (atau jika sesi sudah aktif), pastikan kita di target_data_url
    time.sleep(3)
    if current_page.url != target_data_url:
        logging.info(f"Mengalihkan ke halaman target data: {target_data_url}")
        try:
            current_page.goto(target_data_url, timeout=60000, wait_until="domcontentloaded")
            time.sleep(5)
        except Exception as e:
            logging.warning(f"Timeout saat membuka halaman target: {e}")

    # Deteksi halaman error BPS dan muat ulang jika ditemukan
    try:
        if "error" in current_page.title().lower() or current_page.locator("text=There's some error").count() > 0 or current_page.locator("text=unexpected condition").count() > 0:
            logging.warning("Mendeteksi halaman error BPS ('There's some error'). Mencoba memuat ulang...")
            current_page.goto(target_data_url, timeout=60000, wait_until="domcontentloaded")
            time.sleep(5)
    except Exception as e:
        logging.warning(f"Gagal memeriksa/memuat ulang halaman error: {e}")

    return browser, context, current_page

def save_local_js(all_records):
    try:
        df = pd.DataFrame(all_records)
        if not df.empty:
            import datetime
            now_str = datetime.datetime.now().strftime("%d %b %Y, %H:%M:%S")
            js_data = df.to_dict(orient="records")
            with open(OUTPUT_JS, "w", encoding="utf-8") as js_file:
                js_file.write(f"window.EMAIL_DATA = {json.dumps(js_data, ensure_ascii=False, indent=2)};\n")
                js_file.write(f"window.LAST_UPDATED = '{now_str}';\n")
            
            # Rekap Excel Bounced / Permanent Fail
            bounced_emails = df[df['global_status'].fillna('').str.lower().isin(['bounced', 'permanent_fail', 'permanent_failure'])]['email'].unique()
            df_bounced = df[df['email'].isin(bounced_emails)]
            df_bounced.to_excel(OUTPUT_BOUNCED_EXCEL, index=False)
    except Exception as e:
        logging.error(f"Gagal save local js: {e}")

def save_realtime_data(all_records):
    try:
        # Panggil save_local_js juga
        save_local_js(all_records)
        
        df = pd.DataFrame(all_records)
        if not df.empty:
            js_data = df.to_dict(orient="records")

            # Kirim data ke Supabase jika terkonfigurasi
            if supabase:
                logging.info("Menyinkronkan data ke Supabase...")
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
                
                # Truncate and insert in batches
                supabase.table("email_logs").delete().neq("code", "FORCE_DELETE_ALL_XYZ").execute()
                batch_size = 400
                for i in range(0, len(db_records), batch_size):
                    batch = db_records[i:i+batch_size]
                    supabase.table("email_logs").insert(batch).execute()
                logging.info(f"Sinkronisasi Supabase berhasil! Mengunggah {len(db_records)} records.")
    except Exception as e:
        logging.error(f"Gagal menulis data/sinkronisasi real-time: {e}")

def get_valid_session(context, page):
    import time
    import logging
    while True:
        cookies = context.cookies()
        xsrf_token = None
        for cookie in cookies:
            if cookie['name'] == 'XSRF-TOKEN':
                from urllib.parse import unquote
                xsrf_token = unquote(cookie['value'])
                break
        
        # Verify session
        session_ok = False
        if xsrf_token:
            test_url = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode"
            test_payload = {
                "start": 0,
                "length": 1,
                "columns": [{"data": "id"}],
                "order": [],
                "search": {"value": "", "regex": False},
                "assignmentExtraParam": {
                    "region1Id": "a00c8aef-afc4-4d4f-b80d-789a15450ef9",
                    "region2Id": "9c9b2d79-9fb1-4ce7-b0f1-6b7bb5511beb",
                    "surveyPeriodId": "37526b20-81c8-42f5-a895-6190137d7394",
                    "assignmentErrorStatusType": -1,
                    "filterTargetType": ""
                }
            }
            try:
                res_eval = page.evaluate("""
                    async ({url, payload, token}) => {
                        try {
                            const r = await fetch(url, {
                                method: "POST",
                                headers: {
                                    "Content-Type": "application/json",
                                    "X-XSRF-TOKEN": token
                                },
                                body: JSON.stringify(payload)
                            });
                            return r.status;
                        } catch (e) {
                            return 500;
                        }
                    }
                """, {"url": test_url, "payload": test_payload, "token": xsrf_token})
                if res_eval == 200:
                    session_ok = True
                else:
                    logging.warning(f"Verifikasi sesi mengembalikan status HTTP {res_eval}")
            except Exception as e:
                logging.warning(f"Error memverifikasi sesi: {e}")
        
        if session_ok:
            return xsrf_token, cookies
            
        print("\n" + "="*70)
        print("Sesi BPS FASIH tidak aktif atau kadaluarsa (HTTP 401/XSRF-TOKEN tidak ditemukan).")
        print("SILAKAN LOGIN SSO ATAU REFRESH HALAMAN DI BROWSER CHROMIUM YANG TERBUKA.")
        print("Setelah login berhasil, script akan otomatis mendeteksi dan melanjutkan.")
        print("Atau, Anda bisa menekan ENTER di terminal ini jika sudah login.")
        print("="*70 + "\n")
        
        import select
        import sys
        
        # Cek apakah stdin interaktif dan tidak EOF
        has_stdin = False
        try:
            has_stdin = sys.stdin.isatty()
        except Exception:
            pass

        if has_stdin:
            # Tunggu login selama 30 detik lalu cek lagi
            for _ in range(6):
                try:
                    r, _, _ = select.select([sys.stdin], [], [], 0)
                    if r:
                        line = sys.stdin.readline()
                        if line == "":  # EOF
                            has_stdin = False
                            break
                        logging.info("Konfirmasi manual diterima via ENTER.")
                        break
                except Exception:
                    pass
                time.sleep(5)
        
        if not has_stdin:
            # Stdin tidak interaktif atau EOF, cukup sleep 30 detik
            time.sleep(30)

def scrape_via_api():
    # Muat data yang sudah ada di CSV
    existing_companies = {}
    csv_source = OUTPUT_CSV
    if os.path.exists(OUTPUT_CSV):
        csv_source = OUTPUT_CSV
    elif os.path.exists("backup_" + OUTPUT_CSV):
        csv_source = "backup_" + OUTPUT_CSV
        logging.info(f"Main CSV tidak ditemukan. Menggunakan backup CSV: {csv_source}")

    if os.path.exists(csv_source):
        try:
            with open(csv_source, mode="r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader, None)
                for row in reader:
                    if len(row) >= 8:
                        code = row[0]
                        comp_name = row[1]
                        survey_status = row[2]
                        email = row[3]
                        global_status = row[4]
                        status = row[5]
                        timestamp = row[6]
                        order = int(row[7]) if row[7].isdigit() else 0
                        
                        if code not in existing_companies:
                            existing_companies[code] = []
                        existing_companies[code].append({
                            "code": code,
                            "company_name": comp_name,
                            "survey_status": survey_status,
                            "email": email,
                            "global_status": global_status,
                            "status": status,
                            "timestamp": timestamp,
                            "order": order
                        })
            logging.info(f"Berhasil memuat data historis untuk {len(existing_companies)} perusahaan dari {csv_source}.")
        except Exception as e:
            logging.warning(f"Gagal membaca CSV lama ({csv_source}): {e}")

    # --- PERUBAHAN 3: launch_chrome_if_needed DIPANGGIL SEBELUM SYNC_PLAYWRIGHT ---
    launch_chrome_if_needed()

    with sync_playwright() as p:
        browser, context, page = get_authenticated_context(p)

        # Cek dan dapatkan sesi valid
        xsrf_token, cookies = get_valid_session(context, page)

        logging.info(f"XSRF-TOKEN diperoleh: {xsrf_token[:10]}...")
        
        # Susun Cookie Header secara manual untuk request API langsung
        cookie_header = "; ".join([f"{c['name']}={c['value']}" for c in cookies])

        # Deteksi surveyPeriodId secara dinamis dari URL aktif
        survey_period_id = "37526b20-81c8-42f5-a895-6190137d7394"  # Default fallback
        import re
        current_url = page.url
        match = re.search(r"/surveys/([a-f0-9\-]+)/([a-f0-9\-]+)", current_url)
        if match:
            survey_period_id = match.group(2)
            logging.info(f"Mendeteksi surveyPeriodId secara dinamis dari URL: {survey_period_id}")

        # Resolve Kabupaten/Kota UUIDs programmatically without opening the filter UI
        logging.info("Membaca UUID untuk Kabupaten/Kota secara programmatik dari BPS...")
        kab_map = {}
        try:
            uuid_map = page.evaluate("""
                async (token) => {
                    const kabCodes = ["7201", "7202", "7203", "7204", "7205", "7206", "7207", "7208", "7209", "7210", "7211", "7212", "7271"];
                    const map = {};
                    for (const code of kabCodes) {
                        try {
                            const url = `https://fasih-sm.bps.go.id/app/api/region/api/v1/region/custom-by-smallest-code-and-level?groupId=6b0b053f-aa43-4855-ac8f-26857b735c93&smallestLevelFullCode=${code}&level=2`;
                            const res = await fetch(url, { headers: { "X-XSRF-TOKEN": token } });
                            const json = await res.json();
                            if (json && json.success && json.data) {
                                const level2 = json.data.level1.level2;
                                if (level2) {
                                    map[level2.code] = { "id": level2.id, "name": level2.name };
                                }
                            }
                        } catch (e) {}
                    }
                    return map;
                }
            """, xsrf_token)

            # Map the resolved codes to our local names list
            kab_names_static = {
                "01": "[01] BANGGAI KEPULAUAN",
                "02": "[02] BANGGAI",
                "03": "[03] MOROWALI",
                "04": "[04] POSO",
                "05": "[05] DONGGALA",
                "06": "[06] TOLI-TOLI",
                "07": "[07] BUOL",
                "08": "[08] PARIGI MOUTONG",
                "09": "[09] TOJO UNA-UNA",
                "10": "[10] SIGI",
                "11": "[11] BANGGAI LAUT",
                "12": "[12] MOROWALI UTARA",
                "71": "[71] PALU"
            }
            for code, name in kab_names_static.items():
                if code in uuid_map:
                    kab_map[name] = uuid_map[code]["id"]

            logging.info(f"Berhasil memetakan {len(kab_map)} Kabupaten/Kota ke UUID: {list(kab_map.keys())}")
        except Exception as e:
            logging.error(f"Gagal memetakan wilayah secara otomatis: {e}")
            input("Terjadi kesalahan saat memetakan wilayah. Tekan ENTER untuk keluar...")
            return

        # Panggil API Datatable untuk mengambil semua perusahaan dari semua wilayah
        logging.info("Memulai pemanggilan API Datatable untuk seluruh wilayah...")
        datatable_url = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode"
        all_companies_data = []

        for kab_name, kab_id in kab_map.items():
            logging.info(f"Memproses wilayah: {kab_name} (ID: {kab_id})...")
            
            start_index = 0
            page_length = 100
            
            while True:
                payload = {
                    "start": start_index,
                    "length": page_length,
                    "columns": [
                        {"data": "id", "orderable": True},
                        {"data": "codeIdentity", "orderable": True},
                        {"data": "data1", "orderable": True},
                        {"data": "data2", "orderable": True},
                        {"data": "data3", "orderable": True},
                        {"data": "data4", "orderable": True},
                        {"data": "data5", "orderable": True},
                        {"data": "data6", "orderable": True},
                        {"data": "data7", "orderable": True},
                        {"data": "data8", "orderable": True},
                        {"data": "data9", "orderable": True},
                        {"data": "data10", "orderable": True}
                    ],
                    "order": [],
                    "search": {"value": "", "regex": False},
                    "assignmentExtraParam": {
                        "region1Id": "a00c8aef-afc4-4d4f-b80d-789a15450ef9",
                        "region2Id": kab_id,
                        "surveyPeriodId": survey_period_id,
                        "assignmentErrorStatusType": -1,
                        "filterTargetType": ""
                    }
                }

                try:
                    res_eval = page.evaluate("""
                        async ({url, payload, token}) => {
                            const r = await fetch(url, {
                                method: "POST",
                                headers: {
                                    "Content-Type": "application/json",
                                    "X-XSRF-TOKEN": token
                                },
                                body: JSON.stringify(payload)
                            });
                            if (!r.ok) return { status: r.status, text: await r.text() };
                            return { status: r.status, json: await r.json() };
                        }
                    """, {"url": datatable_url, "payload": payload, "token": xsrf_token})
                except Exception as e:
                    logging.error(f"Gagal memanggil API Datatable untuk {kab_name} (start: {start_index}): {e}")
                    break

                if res_eval.get("status") == 401:
                    logging.warning(f"Sesi kadaluarsa (HTTP 401) saat memanggil API Datatable untuk {kab_name}. Meminta re-autentikasi...")
                    xsrf_token, cookies = get_valid_session(context, page)
                    cookie_header = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
                    continue

                if res_eval.get("status") != 200:
                    logging.error(f"Gagal memanggil API Datatable untuk {kab_name}: HTTP {res_eval.get('status')}")
                    break

                res_json = res_eval.get("json", {})
                companies_part = res_json.get("searchData", [])
                total_hits_part = res_json.get("totalHit", 0)
                
                logging.info(f"  {kab_name}: Mendapatkan {len(companies_part)} perusahaan (start: {start_index}, totalHit: {total_hits_part}).")
                
                if not companies_part:
                    break
                    
                all_companies_data.extend(companies_part)
                start_index += page_length
                
                if start_index >= total_hits_part:
                    break
                    
                time.sleep(0.3)

        companies_data = all_companies_data
        total_hits = len(companies_data)
        logging.info(f"Total keseluruhan perusahaan yang diperoleh dari semua wilayah: {total_hits}")

        all_records = []
        seen_codes = set()
        status_priority = {
            'permanent_fail': 8,
            'permanent_failure': 8,
            'bounced': 7,
            'dropped': 6,
            'clicked': 5,
            'opened': 4,
            'delivered': 3,
            'processed': 2,
            'queued': 1,
            'deferred': 0,
            '-': -1
        }

        email_datatable_url = "https://fasih-sm.bps.go.id/app/api/email/api/v1/email-schedule/datatable"

        for idx, comp in enumerate(companies_data):
            code_identity = comp.get("codeIdentity", "-")
            uid = comp.get("id")
            
            # Kita gunakan 'id' BPS sebagai primary key (disimpan di variabel code) agar tidak ter-deduplikasi secara salah
            code = uid if uid else code_identity
            seen_codes.add(code)
            
            company_name = comp.get("data1", "-")
            survey_status = comp.get("assignmentStatusAlias", "-")
            email_target = comp.get("email", "-")
            assignment_id = uid

            # 1. Cek apakah perusahaan sudah berstatus final di data lokal
            has_valid_history = False
            if not FORCE_RE_SCRAPE:
                if code in existing_companies:
                    histories = existing_companies[code]
                    if histories and histories[0]["global_status"] in ["delivered", "opened", "clicked", "permanent_fail", "permanent_failure"]:
                        has_valid_history = True
                        for h in histories:
                            h["survey_status"] = survey_status
                        all_records.extend(histories)
                else:
                    # Deteksi apabila BPS merubah ID namun perusahaannya sama
                    for old_code, old_histories in existing_companies.items():
                        if old_histories and old_histories[0]["company_name"].lower().strip() == company_name.lower().strip():
                            if old_histories[0]["global_status"] in ["delivered", "opened", "clicked", "permanent_fail", "permanent_failure"]:
                                has_valid_history = True
                                # Kita gunakan KODE BARU, tapi dengan mempertahankan riwayat lamanya
                                for h in old_histories:
                                    h["code"] = code
                                    h["survey_status"] = survey_status
                                all_records.extend(old_histories)
                            break
              
            
            if has_valid_history:
                logging.info(f"[{idx+1}/{len(companies_data)}] Skip (Sudah ada di cache): {code} | {company_name}")
                continue

            # 2. Panggil API untuk mengambil Riwayat Email (dengan retry jika status 401)
            res_eval_email = None
            res_eval_events = None
            
            for session_attempt in range(3):
                logging.info(f"[{idx+1}/{len(companies_data)}] Meminta API riwayat email: {code} | {company_name}")
                
                email_payload = {
                    "start": 0,
                    "pageNumber": 1,
                    "length": 10,
                    "search": {"value": "", "regex": True},
                    "emailScheduleParam": {
                        "assignmentId": assignment_id,
                        "surveyPeriodId": survey_period_id
                    }
                }

                # Retry mechanism if connection resets (panggilan via browser fetch)
                res_eval_email = None
                for attempt in range(1, 4):
                    try:
                        res_eval_email = page.evaluate("""
                            async ({url, payload, token}) => {
                                const r = await fetch(url, {
                                    method: "POST",
                                    headers: {
                                        "Content-Type": "application/json",
                                        "X-XSRF-TOKEN": token
                                    },
                                    body: JSON.stringify(payload)
                                });
                                if (!r.ok) return { status: r.status };
                                return { status: r.status, json: await r.json() };
                            }
                        """, {"url": email_datatable_url, "payload": email_payload, "token": xsrf_token})
                        break
                    except Exception as ex:
                        logging.warning(f"Percobaan {attempt} gagal untuk {code}: {ex}")
                        time.sleep(2)

                # --- API KEDUA: EMAIL EVENTS (UNTUK RIWAYAT BROADCAST) ---
                email_events_url = f"https://fasih-sm.bps.go.id/app/api/email/api/v1/email-events?assignmentId={assignment_id}&page=0&size=50"
                res_eval_events = None
                for attempt in range(1, 4):
                    try:
                        res_eval_events = page.evaluate("""
                            async ({url, token}) => {
                                const r = await fetch(url, {
                                    method: "GET",
                                    headers: {
                                        "Accept": "application/json",
                                        "X-XSRF-TOKEN": token
                                    }
                                });
                                if (!r.ok) return { status: r.status };
                                return { status: r.status, json: await r.json() };
                            }
                        """, {"url": email_events_url, "token": xsrf_token})
                        break
                    except Exception as ex:
                        logging.warning(f"Percobaan events {attempt} gagal untuk {code}: {ex}")
                        time.sleep(2)

                # Cek jika ada HTTP 401
                status_email = res_eval_email.get("status") if res_eval_email else None
                status_events = res_eval_events.get("status") if res_eval_events else None
                
                if status_email == 401 or status_events == 401:
                    logging.warning(f"Sesi kadaluarsa (HTTP 401) saat mengambil riwayat email untuk {code}. Meminta re-autentikasi...")
                    xsrf_token, cookies = get_valid_session(context, page)
                    cookie_header = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
                    continue
                else:
                    break

            history_items = []
            email_actual = email_target
            
            # Jika KEDUA API gagal, maka kita anggap network error dan skip
            if (not res_eval_email or res_eval_email.get("status") != 200) and (not res_eval_events or res_eval_events.get("status") != 200):
                logging.error(f"Gagal memanggil KEDUA API untuk {code}, mempertahankan data lama jika ada.")
                if code in existing_companies:
                    # Update status dokumen jika ada perubahan lalu masukkan ulang data lama
                    histories = existing_companies[code]
                    for h in histories:
                        h["survey_status"] = survey_status
                    all_records.extend(histories)
                else:
                    # Jika benar-benar baru dan gagal API
                    all_records.append({
                        "code": code,
                        "company_name": company_name,
                        "survey_status": survey_status,
                        "email": email_actual if email_actual != "-" else "-",
                        "global_status": "-",
                        "status": "-",
                        "timestamp": "-",
                        "order": 0
                    })
                continue

            if res_eval_email and res_eval_email.get("status") == 200:
                try:
                    email_json = res_eval_email.get("json", {})
                    email_records = email_json.get("searchData", [])
                    if email_records:
                        # Kita ambil email sebenarnya yang tercantum di logs
                        tm_email = email_records[0].get("email")
                        if email_actual == "-" and tm_email:
                            email_actual = tm_email
                        
                        # Loop mengambil riwayat log
                        for item in email_records:
                            hist_status = item.get("statusDescription", "-").lower().strip()
                            # Waktu pengiriman
                            hist_time = item.get("dateModified", "-")
                            if hist_time != "-":
                                try:
                                    from datetime import datetime, timezone, timedelta
                                    # Parse ISO format
                                    dt = datetime.fromisoformat(hist_time.replace("Z", "+00:00"))
                                    # default ke +08:00 (WITA) karena Makassar/Palu/Sulawesi Tengah
                                    local_tz = timezone(timedelta(hours=8))
                                    dt_local = dt.astimezone(local_tz)
                                    hist_time = dt_local.strftime("%d %b %Y, %H:%M:%S")
                                except Exception:
                                    pass
                            history_items.append((hist_status, hist_time))
                except Exception as e:
                    logging.error(f"Error parsing email-schedule JSON untuk {code}: {e}")

            if res_eval_events and res_eval_events.get("status") == 200:
                try:
                    events_json = res_eval_events.get("json", {})
                    content = events_json.get("data", {}).get("content", [])
                    import datetime
                    for item in content:
                        event_type = item.get("eventType", "")
                        if not event_type:
                            event_type = item.get("type", "")
                        if not event_type:
                            continue
                            
                        # Capitalize first letter
                        event_type = event_type.capitalize()
                        
                        ts = item.get("timestamp")
                        if ts:
                            dt = datetime.datetime.fromtimestamp(ts / 1000)
                            time_str = dt.strftime("%d %b %Y, %H:%M:%S")
                        else:
                            time_str = "-"
                            
                        history_items.append((event_type, time_str))
                except Exception as e:
                    logging.error(f"Error parsing email-events JSON untuk {code}: {e}")

            # Deduplikasi history_items
            unique_hist = []
            seen = set()
            for st, tm in history_items:
                key = (st.upper(), tm)
                if key not in seen:
                    seen.add(key)
                    unique_hist.append((st, tm))
            history_items = unique_hist

            # Sort history_items berdasarkan timestamp jika memungkinkan
            history_items.sort(key=lambda x: x[1])

            # Balik urutan log agar tertua di awal
            history_items.reverse()

            if not history_items:
                all_records.append({
                    "code": code,
                    "company_name": company_name,
                    "survey_status": survey_status,
                    "email": email_actual if email_actual != "-" else "-",
                    "global_status": "-",
                    "status": "-",
                    "timestamp": "-",
                    "order": 0
                })
            else:
                best_score = -1
                best_status = "-"
                for st, _ in history_items:
                    score = status_priority.get(st.lower().strip(), -1)
                    if score > best_score:
                        best_score = score
                        best_status = st
                
                last_status = best_status if best_status != "-" else history_items[-1][0]
                for order, (status_hist, time_hist) in enumerate(history_items):
                    all_records.append({
                        "code": code,
                        "company_name": company_name,
                        "survey_status": survey_status,
                        "email": email_actual,
                        "global_status": last_status,
                        "status": status_hist,
                        "timestamp": time_hist,
                        "order": order + 1
                    })

            # Tulis progress ke CSV setiap 20 perusahaan untuk backup lokal
            if (idx + 1) % 20 == 0 or (idx + 1) == len(companies_data):
                with open("backup_" + OUTPUT_CSV, mode="w", newline="", encoding="utf-8") as csv_file:
                    writer = csv.writer(csv_file)
                    writer.writerow(["Kode Identitas", "Nama Perusahaan", "Status Dokumen", "Email Tujuan", "Status terakhir", "Status History", "Timestamp History", "Urutan History"])
                    for r in all_records:
                        writer.writerow([
                            r["code"], r["company_name"], r["survey_status"], r["email"],
                            r["global_status"], r["status"], r["timestamp"], r["order"]
                        ])
                logging.info(f"Progress dibackup ke backup_{OUTPUT_CSV} ({idx+1}/{len(companies_data)}).")
                
                # Update dashboard lokal secara real-time!
                save_local_js(all_records)
                
            time.sleep(0.1) # Jeda kecil agar ramah server

        # Pindahkan backup menjadi file utama
        if os.path.exists("backup_" + OUTPUT_CSV):
            import shutil
            shutil.move("backup_" + OUTPUT_CSV, OUTPUT_CSV)

     # --- TAMBAHAN PENTING: KEMBALIKAN PERUSAHAAN YANG HILANG DARI API ---
        seen_company_names_lower = {comp.get("company_name", "").lower().strip() for comp in all_records}

        for code_exist, histories in existing_companies.items():
            if not histories:
                continue
            comp_name_exist = histories[0]["company_name"].lower().strip()
            
            # Kembalikan hanya jika Kode DAN Nama Perusahaan belum ada di data baru (mencegah duplikasi)
            if code_exist not in seen_codes and comp_name_exist not in seen_company_names_lower:
                all_records.extend(histories)

        # Simpan HASIL AKHIR (lengkap) ke Supabase dan data.js
        save_realtime_data(all_records)
        logging.info(f"Scraping via API selesai putaran ini. Total records: {len(all_records)}. Menunggu 5 menit sebelum scrape berikutnya...")

def main_loop():
    while True:
        try:
            logging.info("=== MEMULAI SIKLUS SCRAPING REAL-TIME ===")
            scrape_via_api()
        except Exception as e:
            logging.error(f"Terjadi kesalahan fatal pada siklus: {e}")
        
        # Jeda 5 menit (300 detik)
        logging.info("Menunggu 5 menit...")
        time.sleep(300)

if __name__ == "__main__":
    main_loop()