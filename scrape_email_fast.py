import os
import csv
import json
import time
import logging
import socket
import subprocess
import shutil
import concurrent.futures
import pandas as pd
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
load_dotenv()

USER_DATA_DIR = "playwright_chrome_profile_email" 
OUTPUT_CSV = "all_email_history.csv"
OUTPUT_JS = "data.js"
FORCE_RE_SCRAPE = False

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
            except Exception:
                pass

def launch_chrome_if_needed():
    port = 9223
    if check_port_open(port):
        logging.info(f"Chrome remote debugging port {port} sudah aktif.")
        return
    
    logging.info(f"Mencoba meluncurkan browser Chrome di port {port}...")
    chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    
    lock_file = os.path.join(USER_DATA_DIR, "SingletonLock")
    if os.path.exists(lock_file):
        try:
            os.remove(lock_file)
        except:
            pass
    
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
    
    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    for _ in range(15):
        time.sleep(1)
        if check_port_open(port):
            logging.info(f"Browser Chrome berhasil diluncurkan!")
            return
    logging.error("Gagal meluncurkan Chrome.")

def create_http_session(cookies, xsrf_token):
    import httpx
    session = httpx.Client(http2=True, verify=False)
    for c in cookies:
        session.cookies.set(
            c['name'],
            c['value'],
            domain=c.get('domain', 'fasih-sm.bps.go.id'),
            path=c.get('path', '/')
        )
    headers = {
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9,id-ID;q=0.8,id;q=0.7",
        "Content-Type": "application/json",
        "Origin": "https://fasih-sm.bps.go.id",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
        "x-xsrf-token": xsrf_token
    }
    session.headers.update(headers)
    return session

def get_valid_session(context, page):
    while True:
        cookies = context.cookies()
        xsrf_token = None
        for cookie in cookies:
            if cookie['name'] == 'XSRF-TOKEN':
                from urllib.parse import unquote
                xsrf_token = unquote(cookie['value'])
                break
        if xsrf_token:
            return xsrf_token, cookies
        print("Sesi BPS FASIH tidak aktif atau Anda belum login.")
        print("Silakan login di jendela Chrome yang baru terbuka, lalu tunggu beberapa detik...")
        time.sleep(5)

def fetch_email_data(args):
    comp, http_session, survey_period_id = args
    code_identity = comp.get("codeIdentity", "-")
    uid = comp.get("id")
    code = uid if uid else code_identity
    assignment_id = uid
    company_name = comp.get("data1", "-")
    survey_status = comp.get("assignmentStatusAlias", "-")
    email_target = comp.get("email", "-")
    kab_name = comp.get("kab_name", "-")

    email_datatable_url = "https://fasih-sm.bps.go.id/app/api/email/api/v1/email-schedule/datatable"
    
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

    import json
    payload_str = json.dumps(email_payload, separators=(',', ':'))
    
    try:
        res = http_session.post(email_datatable_url, content=payload_str, timeout=30)
        if res.status_code == 200:
            content_type = res.headers.get("Content-Type", "").lower()
            if "html" not in content_type:
                res_json = res.json()
                emails_part = res_json.get("searchData", [])
                status_raw = "-"
                ts = "-"
                global_status = "-"
                
                if emails_part:
                    latest = emails_part[0]
                    status_raw = str(latest.get("status", "-"))
                    ts = str(latest.get("updatedAt", "-"))
                    
                    if status_raw == "processed":
                        global_status = "delivered"
                    elif status_raw in ["deferred", "queued"]:
                        global_status = "queued"
                    else:
                        global_status = status_raw
                
                return {
                    "code": code,
                    "company_name": company_name,
                    "survey_status": survey_status,
                    "email": email_target,
                    "global_status": global_status,
                    "status": status_raw,
                    "timestamp": ts,
                    "order": 0,
                    "kab_name": kab_name
                }
    except Exception as e:
        pass
    
    return {
        "code": code,
        "company_name": company_name,
        "survey_status": survey_status,
        "email": email_target,
        "global_status": "-",
        "status": "-",
        "timestamp": "-",
        "order": 0,
        "kab_name": kab_name
    }

def main():
    launch_chrome_if_needed()

    with sync_playwright() as p:
        browser = None
        context = None
        if check_port_open(9223):
            browser = p.chromium.connect_over_cdp("http://localhost:9223")
            context = browser.contexts[0] if browser.contexts else browser.new_context()
        else:
            print("Gagal menyambung ke Chrome CDP.")
            return
            
        page = context.pages[0] if context.pages else context.new_page()
        xsrf_token, cookies = get_valid_session(context, page)
        
        http_session = create_http_session(cookies, xsrf_token)
        
        current_url = page.url
        import re
        survey_period_id = "37526b20-81c8-42f5-a895-6190137d7394"
        match = re.search(r"/surveys/([a-f0-9\-]+)/([a-f0-9\-]+)", current_url)
        if match:
            survey_period_id = match.group(2)
        
        kab_map = {
            "[01] BANGGAI KEPULAUAN": "9c9b2d79-9fb1-4ce7-b0f1-6b7bb5511beb",
            "[02] BANGGAI": "34165dd5-372e-42fa-99c6-0cc19a9b4d0b",
            "[03] MOROWALI": "48c4e5d0-5525-41a8-a4ba-2cc38cd9c424",
            "[04] POSO": "e18368ae-d1cd-4d43-a74d-5b9ddac5dd22",
            "[05] DONGGALA": "c075c4b4-7eb0-4d72-9c16-5103088fb5eb",
            "[06] TOLI-TOLI": "d3a28bfa-b611-488b-8255-369da5cedbf7",
            "[07] BUOL": "dfe4c643-3282-40db-a5fd-cb288a4f592d",
            "[08] PARIGI MOUTONG": "f18109d2-fc8b-4b9c-886a-dc242d21206e",
            "[09] TOJO UNA-UNA": "4d01eba1-5ae9-4603-82a6-2c831aea9905",
            "[10] SIGI": "2a240d3a-67ee-45b2-ae78-4b4b3a909a90",
            "[11] BANGGAI LAUT": "288c5680-f6d5-4783-a946-d5a06f547c02",
            "[12] MOROWALI UTARA": "a5324f17-7a00-436f-b468-2fc59fcf605d",
            "[71] PALU": "1acfedb4-276e-44d6-9e45-6d43588536d6"
        }

        datatable_url = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode"
        all_companies_data = []

        print("Sedang mengambil daftar perusahaan dari API Datatable...")
        for kab_name, kab_id in kab_map.items():
            start_index = 0
            while True:
                payload = {
                    "start": start_index,
                    "length": 100,
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
                        "filterTargetType": "target"
                    }
                }
                import json
                try:
                    res = http_session.post(datatable_url, content=json.dumps(payload), timeout=60)
                    if res.status_code == 200:
                        res_json = res.json()
                        companies_part = res_json.get("searchData", [])
                        totalHit = res_json.get("totalHit", 0)
                        
                        for c in companies_part:
                            c["kab_name"] = kab_name
                        all_companies_data.extend(companies_part)
                        
                        start_index += 100
                        if start_index >= totalHit:
                            break
                    else:
                        print(f"Error {res.status_code} di {kab_name}")
                        break
                except Exception as e:
                    print(f"Error region {kab_name}: {e}")
                    break

        print(f"Total perusahaan ditemukan: {len(all_companies_data)}")
        
        if len(all_companies_data) == 0:
            print("Tidak ada data perusahaan. Cek apakah Anda di halaman UB.")
            return

        args_list = [(c, http_session, survey_period_id) for c in all_companies_data]
        all_records = []

        print(f"Mulai menarik status email dengan 20 jalur sekaligus secara paralel...")
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            results = executor.map(fetch_email_data, args_list)
            for idx, res in enumerate(results):
                all_records.append(res)
                if (idx + 1) % 100 == 0:
                    print(f"Progress: {idx+1} / {len(all_companies_data)} selesai...")

        elapsed = time.time() - start_time
        print(f"SELESAI! Menarik {len(all_records)} email dalam {elapsed:.2f} detik.")

        df = pd.DataFrame(all_records)
        df.to_csv(OUTPUT_CSV, index=False)
        
        import datetime
        now_str = datetime.datetime.now().strftime("%d %b %Y, %H:%M:%S")
        js_data = df.to_dict(orient="records")
        with open(OUTPUT_JS, "w", encoding="utf-8") as js_file:
            js_file.write(f"window.EMAIL_DATA = {json.dumps(js_data, ensure_ascii=False, indent=2)};\n")
            js_file.write(f"window.LAST_UPDATED = '{now_str}';\n")
            
        print("Data berhasil disimpan ke data.js dan all_email_history.csv")

if __name__ == "__main__":
    main()
