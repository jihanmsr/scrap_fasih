import asyncio
import json
from dotenv import load_dotenv
import os
import time
import logging
import datetime
import socket
import subprocess
import shutil
from playwright.async_api import async_playwright

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = None
if SUPABASE_URL and SUPABASE_KEY and "MASUKKAN" not in SUPABASE_URL:
    try:
        from supabase import create_client
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        logging.info("Koneksi Supabase berhasil diinisialisasi.")
    except Exception as e:
        logging.error(f"Gagal menginisialisasi Supabase: {e}")

USER_DATA_DIR = "playwright_chrome_profile"

def check_port_open(port=9222):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0
    except:
        return False

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
                print(f"[INFO] Membersihkan cache Chrome: {path}")
            except Exception as e:
                print(f"[WARNING] Gagal membersihkan cache Chrome {path}: {e}")

def launch_chrome_if_needed():
    for port in [9223, 9222]:
        if check_port_open(port):
            print(f"[INFO] Chrome remote debugging port {port} sudah aktif. Menggunakan instansi yang ada.")
            return
    
    port = 9222
    print("[INFO] Chrome remote debugging port 9223 dan 9222 tidak aktif. Mencoba meluncurkan browser...")
    chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    
    # Hapus lock file jika ada agar Chrome bisa berjalan lancar
    lock_file = os.path.join(USER_DATA_DIR, "SingletonLock")
    if os.path.lexists(lock_file):
        try:
            os.remove(lock_file)
            print("[INFO] File SingletonLock berhasil dihapus untuk mencegah error lock profile.")
        except Exception as e:
            print(f"[WARNING] Gagal menghapus SingletonLock: {e}")
    
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
            print(f"[INFO] Browser Chrome berhasil diluncurkan dan siap di port {port}.")
            return
    print("[ERROR] Gagal mendeteksi port 9222 setelah meluncurkan Chrome.")

async def get_authenticated_context(p):
    abs_user_data_dir = os.path.abspath(USER_DATA_DIR)
    os.makedirs(abs_user_data_dir, exist_ok=True)
    chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

    browser = None
    context = None
    page = None

    for port in [9223, 9222]:
        if check_port_open(port):
            print(f"[INFO] Remote debugging port {port} terdeteksi. Mencoba sambung via CDP...")
            try:
                browser = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
                context = browser.contexts[0] if browser.contexts else browser.new_context()
                page = context.pages[0] if context.pages else context.new_page()
                print(f"[INFO] Berhasil tersambung ke browser via CDP di port {port}.")
                break
            except Exception as e:
                print(f"[WARNING] Gagal connect_over_cdp di port {port}: {e}.")
                browser = None

    async def try_launch_persistent():
        return await p.chromium.launch_persistent_context(
            user_data_dir=abs_user_data_dir,
            headless=False,
            executable_path=chrome_path,
            args=["--no-first-run", "--no-default-browser-check", "--disable-background-networking", "--disable-background-timer-throttling"]
        )

    if page is None:
        print("[INFO] Meluncurkan browser melalui Playwright persistent context...")
        try:
            context = await try_launch_persistent()
            page = context.pages[0] if context.pages else await context.new_page()
        except Exception as e:
            print(f"[WARNING] Playwright persistent context gagal diluncurkan: {e}")
            cleanup_chrome_cache(abs_user_data_dir)
            print("[INFO] Membersihkan cache user data dan mencoba ulang.")
            try:
                context = await try_launch_persistent()
                page = context.pages[0] if context.pages else await context.new_page()
            except Exception as e2:
                print(f"[WARNING] Gagal meluncurkan Playwright persistent context setelah retry: {e2}")
                print("[INFO] Coba buka browser Playwright headful sebagai fallback...")
                try:
                    browser = await p.chromium.launch(headless=False)
                    context = await browser.new_context()
                    page = await context.new_page()
                    print("[INFO] Browser Playwright headful berhasil diluncurkan.")
                except Exception as e3:
                    print(f"[ERROR] Playwright headful launch gagal: {e3}")
                    raise RuntimeError("Browser setup failed completely")

    return browser, context, page

def is_tambahan(code_identity):
    if not code_identity:
        return False
    parts = [p.strip() for p in code_identity.split(" - ")]
    if len(parts) < 2:
        return False
    source = parts[1].upper()
    known_sources = {"DTSEN", "UMK", "UM", "UMB", "UMKM", "SE2026", "SE26", "PDRB", "PAPI", "CAWI", "CAPI", "UB"}
    if source in known_sources:
        return False
    if source.startswith("SE26") or source.startswith("SE2026"):
        return False
    return True

def classify_tambahan(code_identity, data1, data6):
    code_id_upper = (code_identity or "").upper()
    data1_upper = (data1 or "").upper()
    data6_upper = (data6 or "").upper()
    
    # Check if empty/kosong building
    if "BANGUNAN KOSONG" in data1_upper or "RUMAH KOSONG" in data1_upper or "KOSONG" in data1_upper or "BANGUNAN KOSONG" in code_id_upper or "RUMAH KOSONG" in code_id_upper:
        return "Bangunan/Rumah Kosong", False
        
    # Check if Keluarga Usaha (Household with business)
    if "1. YA" in code_id_upper or "1.YA" in code_id_upper:
        return "Keluarga Usaha", True
        
    # Check if Keluarga Bukan Usaha
    if "2. TIDAK" in code_id_upper or "2.TIDAK" in code_id_upper:
        return "Keluarga (Bukan Usaha)", False
        
    # Check if data6 has KELUARGA
    if "KELUARGA" in data6_upper:
        if "UMKM" in data6_upper or "UMB" in data6_upper:
            return "Keluarga Usaha", True
        return "Keluarga", False
        
    # If it contains slash / and seems like a person name
    if "/" in data1_upper:
        if "UMKM" in data6_upper or "UMB" in data6_upper:
            return "Keluarga Usaha", True
        return "Keluarga", False
        
    # Otherwise, it's a business/non-household
    if "BANGUNAN_LAIN" in data6_upper or "BANGUNAN LAIN" in data6_upper:
        return "Bangunan Lain / Usaha", True
    if "UMKM" in data6_upper:
        return "Usaha (UMKM)", True
    if "UMB" in data6_upper:
        return "Usaha (UMB)", True
        
    return "Usaha Baru", True


async def generate_report():
    launch_chrome_if_needed()
    async with async_playwright() as p:
        try:
            browser, context, page = await get_authenticated_context(p)
        except Exception as e:
            print("Gagal mendapatkan browser context:", e)
            return

        # Cari tab aktif yang sudah membuka fasih-sm
        for p_page in context.pages:
            if "fasih-sm.bps.go.id" in p_page.url:
                page = p_page
                print(f"Menemukan tab aktif FASIH: {page.url}")
                break
        
        if "fasih-sm.bps.go.id" not in page.url:
            print(f"Tab FASIH tidak aktif (URL saat ini: {page.url}). Navigasi...")
            try:
                await page.goto("https://fasih-sm.bps.go.id/app/dashboard", timeout=60000, wait_until="domcontentloaded")
            except Exception as e:
                print("Gagal navigasi ke dashboard url:", e)

        cookies = await page.context.cookies()
        xsrf_token_raw = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), "")
        
        from urllib.parse import unquote
        xsrf_token = unquote(xsrf_token_raw)
        
        datatable_url = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode"

        async def fetch_api_safely(url, payload, token, timeout_seconds=120, max_retries=3):
            for attempt in range(1, max_retries + 1):
                try:
                    res = await page.evaluate("""
                        async ({url, payload, token, timeoutMs}) => {
                            const controller = new AbortController();
                            const id = setTimeout(() => controller.abort(), timeoutMs);
                            try {
                                const r = await fetch(url, {
                                    method: "POST",
                                    headers: { "Content-Type": "application/json", "X-XSRF-TOKEN": token },
                                    body: JSON.stringify(payload),
                                    signal: controller.signal
                                });
                                clearTimeout(id);
                                if (!r.ok) return { error: `HTTP ${r.status}: ${await r.text()}`, status: r.status };
                                const text = await r.text();
                                try {
                                    return JSON.parse(text);
                                } catch(e) {
                                    return { error: "Invalid JSON", text: text.substring(0, 200) };
                                }
                            } catch(e) {
                                clearTimeout(id);
                                return { error: e.toString() };
                            }
                        }
                    """, {"url": url, "payload": payload, "token": token, "timeoutMs": timeout_seconds * 1000})
                    # Retry on 5xx server errors
                    if isinstance(res, dict) and res.get("error"):
                        status = res.get("status", 0)
                        if status in (502, 503, 504) and attempt < max_retries:
                            wait_sec = 10 * attempt
                            print(f"    [RETRY {attempt}/{max_retries}] Server error {status}, menunggu {wait_sec}s...")
                            await asyncio.sleep(wait_sec)
                            continue
                    return res
                except Exception as e:
                    if attempt < max_retries:
                        wait_sec = 10 * attempt
                        print(f"    [RETRY {attempt}/{max_retries}] Exception: {e}, menunggu {wait_sec}s...")
                        await asyncio.sleep(wait_sec)
                    else:
                        return {"error": str(e)}

        async def check_session_valid(token):
            if not token:
                return False
            test_payload = {
                "start": 0, "length": 1, "columns": [{"data": "id"}], "order": [], "search": {"value": "", "regex": False},
                "assignmentExtraParam": {
                    "region1Id": "a00c8aef-afc4-4d4f-b80d-789a15450ef9",
                    "surveyPeriodId": "37526b20-81c8-42f5-a895-6190137d7394",
                    "assignmentErrorStatusType": -1
                }
            }
            res = await fetch_api_safely(datatable_url, test_payload, token)
            if not res or "error" in res:
                return False
            return "searchData" in res or "searchAggregation" in res

        # Ensure session is valid
        first_expired = True
        while True:
            # Re-fetch cookies
            cookies = await page.context.cookies()
            xsrf_token_raw = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), "")
            xsrf_token = unquote(xsrf_token_raw)

            is_valid = await check_session_valid(xsrf_token)
            if is_valid:
                break
                
            if first_expired:
                print("\n" + "="*70)
                print("SESI LOGIN KADALUARSA ATAU BELUM LOGIN")
                print("Silakan login/re-login FASIH di browser Chrome...")
                print("Script akan mendeteksi login Anda secara otomatis.")
                print("="*70)
                first_expired = False
                
            await asyncio.sleep(15)

        # Define surveys
        surveys = {
            "se_umum": {
                "period_id": "fd68e454-ba45-4b85-8205-f3bf777ded24",
                "prov_id": "5214ecb2-bef1-4a86-9446-451cf430928e",
                "label": "Sensus Ekonomi 2026 (Umum)",
                                "kabs": [
                    {"code": "01", "name": "[01] BANGGAI KEPULAUAN", "id": "bc32354f-1245-426f-b2cf-a5733e1295ad"},
                    {"code": "02", "name": "[02] BANGGAI", "id": "530e9ca5-86ba-434e-9b04-405102e6d900"},
                    {"code": "03", "name": "[03] MOROWALI", "id": "9783f0c1-f047-477f-8840-11eae7cf70e2"},
                    {"code": "04", "name": "[04] POSO", "id": "fb9cd9f0-c4c0-4a37-9041-57190693f625"},
                    {"code": "05", "name": "[05] DONGGALA", "id": "289f1ff3-a6ad-4c9b-a49f-7b454d03a33f"},
                    {"code": "06", "name": "[06] TOLI-TOLI", "id": "d833fdce-ebfb-429b-a1bb-8966239fd8e4"},
                    {"code": "07", "name": "[07] BUOL", "id": "c523694a-2e72-4570-9489-da2d7b119fe7"},
                    {"code": "08", "name": "[08] PARIGI MOUTONG", "id": "25c59fd9-afd5-4c1a-9dfb-42bb697a7434"},
                    {"code": "09", "name": "[09] TOJO UNA-UNA", "id": "736c4c22-51d1-44be-8b2c-aa197d9459a4"},
                    {"code": "10", "name": "[10] SIGI", "id": "0061da62-2a47-4dee-b8d0-239b33e2c59d"},
                    {"code": "11", "name": "[11] BANGGAI LAUT", "id": "eed1a3e7-b81d-4fc7-b0d6-61257c1449b2"},
                    {"code": "12", "name": "[12] MOROWALI UTARA", "id": "d05ef8fd-b5e4-414f-9a83-8cdea03e0767"},
                    {"code": "71", "name": "[71] PALU", "id": "4ab6ca2f-7952-4e8e-a94d-b6dd933e5d44"}
                ]
            },
            "se_ub": {
                "period_id": "37526b20-81c8-42f5-a895-6190137d7394",
                "prov_id": "a00c8aef-afc4-4d4f-b80d-789a15450ef9",
                "label": "Sensus Ekonomi 2026 - UB (Usaha Besar)",
                "kabs": [
                    {"code": "01", "name": "[01] BANGGAI KEPULAUAN", "id": "9c9b2d79-9fb1-4ce7-b0f1-6b7bb5511beb"},
                    {"code": "02", "name": "[02] BANGGAI", "id": "34165dd5-372e-42fa-99c6-0cc19a9b4d0b"},
                    {"code": "03", "name": "[03] MOROWALI", "id": "48c4e5d0-5525-41a8-a4ba-2cc38cd9c424"},
                    {"code": "04", "name": "[04] POSO", "id": "e18368ae-d1cd-4d43-a74d-5b9ddac5dd22"},
                    {"code": "05", "name": "[05] DONGGALA", "id": "c075c4b4-7eb0-4d72-9c16-5103088fb5eb"},
                    {"code": "06", "name": "[06] TOLI-TOLI", "id": "d3a28bfa-b611-488b-8255-369da5cedbf7"},
                    {"code": "07", "name": "[07] BUOL", "id": "dfe4c643-3282-40db-a5fd-cb288a4f592d"},
                    {"code": "08", "name": "[08] PARIGI MOUTONG", "id": "f18109d2-fc8b-4b9c-886a-dc242d21206e"},
                    {"code": "09", "name": "[09] TOJO UNA-UNA", "id": "4d01eba1-5ae9-4603-82a6-2c831aea9905"},
                    {"code": "10", "name": "[10] SIGI", "id": "2a240d3a-67ee-45b2-ae78-4b4b3a909a90"},
                    {"code": "11", "name": "[11] BANGGAI LAUT", "id": "288c5680-f6d5-4783-a946-d5a06f547c02"},
                    {"code": "12", "name": "[12] MOROWALI UTARA", "id": "a5324f17-7a00-436f-b468-2fc59fcf605d"},
                    {"code": "71", "name": "[71] PALU", "id": "1acfedb4-276e-44d6-9e45-6d43588536d6"}
                ]
            }
        }
        
        # Mapping first 4 characters of codeIdentity to kabupaten name
        code_to_name = {f"72{k['code']}": k["name"] for k in surveys["se_umum"]["kabs"]}
        
        # Load region_map_sulteng.json
        region_map = {}
        try:
            with open("region_map_sulteng.json", "r", encoding="utf-8") as f:
                region_map = json.load(f)
            print("[INFO] region_map_sulteng.json berhasil dimuat.")
        except Exception as e:
            print(f"[WARNING] Gagal memuat region_map_sulteng.json: {e}")

        # Build mapping from kec_id to kec_code using region_map_sulteng_full.json
        kec_id_to_code = {}
        try:
            with open("region_map_sulteng_full.json", "r", encoding="utf-8") as f:
                full_map = json.load(f)
            for kab_code, kab_data in full_map.get("kabupaten", {}).items():
                for kec_code, kec_data in kab_data.get("kecamatan", {}).items():
                    kec_id = kec_data.get("kec_id")
                    if kec_id:
                        kec_id_to_code[kec_id] = kec_code
            print(f"[INFO] region_map_sulteng_full.json loaded. Mapped {len(kec_id_to_code)} kecamatan UUIDs to codes.")
        except Exception as e:
            print(f"[WARNING] Gagal memuat region_map_sulteng_full.json: {e}")

        output_data = {}
        
        for survey_key, survey_cfg in surveys.items():
            print(f"\n=========================================")
            print(f"Memproses Survey: {survey_cfg['label']}")
            print(f"=========================================")
            
            period_id = survey_cfg["period_id"]
            
            # Fetch target totals at Kecamatan level via Report API
            kec_prelist_map = {}
            report_url = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/report-user-assignment"
            print("Mengambil rincian target Kecamatan dari Report API...")
            for kab in survey_cfg["kabs"]:
                import re
                match = re.search(r"\[(\d+)\]", kab["name"])
                kab_code = "72" + match.group(1) if match else ""
                if kab_code:
                    payload_report = {
                        "surveyPeriodId": period_id,
                        "region1Id": survey_cfg["prov_id"],
                        "region2Id": kab["id"]
                    }
                    res_report = None
                    for retry_kab in range(3):
                        res_report = await fetch_api_safely(report_url, payload_report, xsrf_token, timeout_seconds=180)
                        if isinstance(res_report, dict) and res_report.get("error"):
                            wait_sec = 15 * (retry_kab + 1)
                            print(f"  [ERROR] Gagal memproses {kab['name']}: {res_report['error'][:80]}")
                            if retry_kab < 2:
                                print(f"  [RETRY {retry_kab+1}/3] Mencoba ulang dalam {wait_sec}s...")
                                await asyncio.sleep(wait_sec)
                            else:
                                print(f"  [SKIP] {kab['name']} dilewati setelah 3x gagal.")
                        else:
                            break
                    if res_report and isinstance(res_report, list):
                        for item in res_report:
                            kec_key = item.get("key")
                            kec_lbl = item.get("label")
                            values = item.get("values", [])
                            total = 0
                            for v in values:
                                if v.get("label", "").lower() == "total":
                                    total = v.get("value", 0)
                                    break
                            if kec_key:
                                kec_prelist_map[kec_key] = total
                            if kec_lbl:
                                kec_prelist_map[kec_lbl] = total

            # Initialize final report dict
            report_data = {}
            for k in survey_cfg["kabs"]:
                import re
                match = re.search(r"\[(\d+)\]", k["name"])
                kab_code = "72" + match.group(1) if match else ""
                
                kec_list_initial = []
                kec_items = region_map.get(kab_code, {}).get("kecamatan", [])
                for kec in kec_items:
                    if kec["name"] == "-":
                        continue
                    
                    kec_code = kec_id_to_code.get(kec["id"])
                    total_prelist = 0
                    if kec_code and kec_code in kec_prelist_map:
                        total_prelist = kec_prelist_map[kec_code]
                    else:
                        total_prelist = kec_prelist_map.get(kec["id"], 0)

                    kec_list_initial.append({
                        "kec_name": kec["name"],
                        "kec_id": kec["id"],
                        "total_prelist": total_prelist,
                        "total_draft": 0,
                        "total_open": 0,
                        "total_submitted": 0,
                        "total_rejected": 0,
                        "total_approved": 0,
                        "today_completed": 0,
                        "yesterday_completed": 0,
                        "two_days_ago_completed": 0,
                        "today_completed_breakdown": {},
                        "yesterday_completed_breakdown": {},
                        "two_days_ago_completed_breakdown": {},
                        "new_usaha_today": 0,
                        "new_usaha_yesterday": 0,
                        "new_usaha_overall": 0,
                        "new_rumah_today": 0,
                        "new_rumah_yesterday": 0,
                        "new_rumah_overall": 0,
                        "new_businesses": []
                    })

                report_data[k["name"]] = {
                    "kabupaten": k["name"],
                    "total_prelist": 0,
                    "total_draft": 0,
                    "total_open": 0,
                    "total_submitted": 0,
                    "total_rejected": 0,
                    "total_approved": 0,
                    "today_completed": 0,
                    "yesterday_completed": 0,
                    "two_days_ago_completed": 0,
                    "today_completed_breakdown": {},
                    "yesterday_completed_breakdown": {},
                    "two_days_ago_completed_breakdown": {},
                    "new_usaha_today": 0,
                    "new_usaha_yesterday": 0,
                    "new_rumah_today": 0,
                    "new_rumah_yesterday": 0,
                    "new_usaha_overall": 0,
                    "new_rumah_overall": 0,
                    "new_businesses": [],
                    "kecamatan_list": kec_list_initial
                }
                
            datatable_url = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode"

            for kab in survey_cfg["kabs"]:
                payload = {
                    "start": 0, "length": 1, "columns": [{"data": "id"}], "order": [], "search": {"value": "", "regex": False},
                    "assignmentExtraParam": {
                        "region1Id": survey_cfg["prov_id"],
                        "region2Id": kab["id"],
                        "surveyPeriodId": period_id,
                        "assignmentErrorStatusType": -1,
                        "filterTargetType": "target"
                    }
                }
                payload_nontarget = {
                    "start": 0, "length": 1000, "columns": [
                        {"data": "id"},
                        {"data": "codeIdentity"},
                        {"data": "data1"},
                        {"data": "data6"},
                        {"data": "assignmentStatusAlias"},
                        {"data": "region"}
                    ], "order": [], "search": {"value": "", "regex": False},
                    "assignmentExtraParam": {
                        "region1Id": survey_cfg["prov_id"],
                        "region2Id": kab["id"],
                        "surveyPeriodId": period_id,
                        "assignmentErrorStatusType": -1,
                        "filterTargetType": "non-target"
                    }
                }
                
                res, res_nontarget = await asyncio.gather(
                    fetch_api_safely(datatable_url, payload, xsrf_token),
                    fetch_api_safely(datatable_url, payload_nontarget, xsrf_token)
                )
                
                if not res or "error" in res:
                    print(f"  [ERROR] Gagal memproses {kab['name']}: {res.get('error') if res else 'Unknown error'}")
                    continue
                
                # 1. Parse targets (prelist)
                prelist_target = 0
                draft_target = 0
                open_target = 0
                submitted_target = 0
                rejected_target = 0
                approved_target = 0
                
                agg_target = res.get("searchAggregation", [])
                for item in agg_target:
                    key = item.get("keyAggregation", "")
                    count = item.get("docCount", 0)
                    prelist_target += count
                    if key == "DRAFT":
                        draft_target += count
                    elif key == "OPEN":
                        open_target += count
                    elif "SUBMITTED" in key:
                        submitted_target += count
                    elif "REJECTED" in key:
                        rejected_target += count
                    elif "APPROVED" in key:
                        approved_target += count
                
                if prelist_target == 0:
                    prelist_target = res.get("totalHit", 0)
 
                # 2. Parse non-targets (tambahan)
                draft_nontarget = 0
                open_nontarget = 0
                submitted_nontarget = 0
                rejected_nontarget = 0
                approved_nontarget = 0
                
                tambahan_usaha = 0
                tambahan_rumah_baru = 0
                
                nontarget_records = res_nontarget.get("searchData", []) if res_nontarget else []
                
                for item in nontarget_records:
                    code_id = item.get("codeIdentity") or ""
                    if not is_tambahan(code_id):
                        continue
                    status = item.get("assignmentStatusAlias", "")
                    data1_val = item.get("data1") or ""
                    data6_val = str(item.get("data6") or "").upper()
                    jenis_lbl, is_usaha_derived = classify_tambahan(code_id, data1_val, data6_val)
                    is_rumah = not is_usaha_derived
                    
                    status_upper = status.upper()
                    
                    # Track Kecamatan for non-targets
                    kec_id = None
                    n_region = item.get("region", {})
                    if n_region:
                        n_lvl3 = n_region.get("level1", {}).get("level2", {}).get("level3", {}) or {}
                        kec_id = n_lvl3.get("id")
                    
                    kec_stats = None
                    if kec_id:
                        for k_item in report_data[kab["name"]]["kecamatan_list"]:
                            if k_item["kec_id"] == kec_id:
                                kec_stats = k_item
                                break
                    
                    # Klasifikasikan jenis tambahan terlebih dahulu (berlaku untuk semua status)
                    if is_rumah:
                        tambahan_rumah_baru += 1
                        if kec_stats:
                            kec_stats["new_rumah_overall"] += 1
                    else:
                        tambahan_usaha += 1
                        if kec_stats:
                            kec_stats["new_usaha_overall"] += 1

                    if status_upper == "DRAFT":
                        draft_nontarget += 1
                        if kec_stats:
                            kec_stats["total_draft"] += 1
                    elif status_upper == "OPEN":
                        open_nontarget += 1
                        if kec_stats:
                            kec_stats["total_open"] += 1
                    elif "SUBMITTED" in status_upper:
                        submitted_nontarget += 1
                        if kec_stats:
                            kec_stats["total_submitted"] += 1
                    elif "REJECTED" in status_upper:
                        rejected_nontarget += 1
                        if kec_stats:
                            kec_stats["total_submitted"] += 1
                            kec_stats["total_rejected"] += 1
                    elif "APPROVED" in status_upper:
                        approved_nontarget += 1
                        if kec_stats:
                            kec_stats["total_submitted"] += 1
                            kec_stats["total_approved"] += 1
                
                # Hitung metrik final gabungan Kabupaten
                total_prelist = prelist_target + tambahan_usaha + tambahan_rumah_baru
                total_draft = draft_target + draft_nontarget
                total_open = open_target + open_nontarget
                total_submitted = submitted_target + approved_target + rejected_target + (submitted_nontarget + rejected_nontarget + approved_nontarget)
                total_rejected = rejected_target + rejected_nontarget
                total_approved = approved_target + approved_nontarget
                
                report_data[kab["name"]]["total_prelist"] = total_prelist
                report_data[kab["name"]]["total_draft"] = total_draft
                report_data[kab["name"]]["total_open"] = total_open
                report_data[kab["name"]]["total_submitted"] = total_submitted
                report_data[kab["name"]]["total_rejected"] = total_rejected
                report_data[kab["name"]]["total_approved"] = total_approved
                report_data[kab["name"]]["new_usaha_overall"] = tambahan_usaha
                report_data[kab["name"]]["new_rumah_overall"] = tambahan_rumah_baru
                print(f"  {kab['name']}: Prelist={total_prelist}, UsahaBaruOverall={tambahan_usaha}, RumahBaruOverall={tambahan_rumah_baru}, Draft={total_draft}, Open={total_open}, Submitted={total_submitted}")

            # Calculate province totals by summing up county/kabupaten totals
            prov_original_total = sum(report_data[k["name"]]["total_prelist"] for k in survey_cfg["kabs"])
            prov_new_total = sum(report_data[k["name"]]["new_usaha_overall"] for k in survey_cfg["kabs"])
            prov_new_rumah_total = sum(report_data[k["name"]]["new_rumah_overall"] for k in survey_cfg["kabs"])
            output_data[f"{survey_key}_prov_total"] = prov_original_total
            output_data[f"{survey_key}_prov_new_total"] = prov_new_total
            output_data[f"{survey_key}_prov_new_rumah_total"] = prov_new_rumah_total
            # 2. Fetch daily progress details province-wide
            active_statuses = [
                "SUBMITTED RESPONDENT",
                "SUBMITTED BY Pencacah",
                "DRAFT",
                "REJECTED BY Pengawas",
                "REJECTED BY Admin Kabupaten",
                "APPROVED BY Pengawas",
                "REVOKED BY Pengawas"
            ]
            all_records = []
            
            print("Mengambil rincian data progres harian tingkat provinsi...")
            for status in active_statuses:
                start = 0
                while True:
                    payload = {
                        "start": start,
                        "length": 100,
                        "columns": [
                            {"data": "id"},
                            {"data": "codeIdentity"},
                            {"data": "data1"},
                            {"data": "data6"},
                            {"data": "dateCreated"},
                            {"data": "dateModified"},
                            {"data": "assignmentStatusAlias"},
                            {"data": "region"}
                        ],
                        "order": [],
                        "search": {"value": "", "regex": False},
                        "assignmentExtraParam": {
                            "region1Id": survey_cfg["prov_id"],
                            "surveyPeriodId": period_id,
                            "assignmentStatusAlias": status,
                            "assignmentErrorStatusType": -1,
                            "filterTargetType": ""
                        }
                    }
                    res = await fetch_api_safely(datatable_url, payload, xsrf_token)
                    if not res or "error" in res:
                        print(f"  [ERROR] Gagal mengambil rincian harian status {status} (start: {start}): {res.get('error') if res else 'Unknown error'}")
                        break
                    
                    records_part = res.get("searchData", [])
                    if not records_part:
                        break
                        
                    all_records.extend(records_part)
                    start += 100
                    if start >= res.get("totalHit", 0):
                        break
                    await asyncio.sleep(0.1)
                    
                print(f"  Selesai fetch status {status}: {len(all_records)} total records so far.")

            # WITA Timezone for Sulawesi Tengah
            local_tz = datetime.timezone(datetime.timedelta(hours=8))
            today = datetime.datetime.now(local_tz).date()
            yesterday = today - datetime.timedelta(days=1)
            two_days_ago = today - datetime.timedelta(days=2)
            
            # 3. Calculate daily progress from timestamps
            print("Mengolah riwayat tanggal dan mengelompokkan ke Kabupaten & Kecamatan...")
            kab_id_to_name = {k["id"]: k["name"] for k in survey_cfg["kabs"]}
            kab_code_to_name = {f"72{k['code']}": k["name"] for k in survey_cfg["kabs"]}
            
            for r in all_records:
                kab_name = None
                kec_id = None
                
                # Try getting from nested region object
                region = r.get("region", {})
                if region:
                    lvl2 = region.get("level1", {}).get("level2", {}) or {}
                    kab_id = lvl2.get("id")
                    if kab_id and kab_id in kab_id_to_name:
                        kab_name = kab_id_to_name[kab_id]
                    else:
                        kab_code = lvl2.get("fullCode")
                        if kab_code and kab_code in kab_code_to_name:
                            kab_name = kab_code_to_name[kab_code]
                    
                    lvl3 = lvl2.get("level3", {}) or {}
                    kec_id = lvl3.get("id")
                
                # Fallback to codeIdentity regex/parsing
                if not kab_name:
                    code_identity = r.get("codeIdentity")
                    if code_identity:
                        import re
                        match = re.search(r"\b(72\d{2})\b", code_identity)
                        if match:
                            kab_name = kab_code_to_name.get(match.group(1))
                        else:
                            if len(code_identity) >= 4:
                                kab_name = kab_code_to_name.get(code_identity[:4])
                
                if not kab_name:
                    continue
                    
                status_alias = r.get("assignmentStatusAlias")
                is_target = not is_tambahan(r.get("codeIdentity") or "")
                
                # Find Kecamatan stats reference
                kec_stats = None
                if kec_id and kab_name in report_data:
                    for k_item in report_data[kab_name]["kecamatan_list"]:
                        if k_item["kec_id"] == kec_id:
                            kec_stats = k_item
                            break

                # Fallback: match by kec_name using levelRegions from the record (for UB survey where kec_ids may differ)
                if not kec_stats and kab_name in report_data:
                    level_regions = r.get("levelRegions") or []
                    kec_name_from_region = None
                    for lr in level_regions:
                        if lr.get("level") == 3:
                            kec_name_from_region = (lr.get("name") or "").upper().strip()
                            break
                    if kec_name_from_region:
                        for k_item in report_data[kab_name]["kecamatan_list"]:
                            if k_item["kec_name"].upper().strip() == kec_name_from_region:
                                kec_stats = k_item
                                break

                # Count active target states at Kecamatan level if not OPEN
                if is_target and kec_stats:
                    if status_alias == "DRAFT":
                        kec_stats["total_draft"] += 1
                    elif status_alias in [
                        "SUBMITTED RESPONDENT", "SUBMITTED BY Pencacah",
                        "APPROVED BY Pengawas", "REJECTED BY Pengawas",
                        "REJECTED BY Admin Kabupaten", "REVOKED BY Pengawas"
                    ]:
                        kec_stats["total_submitted"] += 1
                    if "REJECTED" in (status_alias or ""):
                        kec_stats["total_rejected"] += 1
                    elif "APPROVED" in (status_alias or ""):
                        kec_stats["total_approved"] += 1

                # Check completions
                if status_alias in [
                    "SUBMITTED RESPONDENT",
                    "SUBMITTED BY Pencacah",
                    "APPROVED BY Pengawas",
                    "REJECTED BY Pengawas",
                    "REJECTED BY Admin Kabupaten",
                    "REVOKED BY Pengawas"
                ]:
                    mod_date_str = r.get("dateModified")
                    if mod_date_str:
                        try:
                            # Parse date and convert to WITA
                            dt = datetime.datetime.fromisoformat(mod_date_str.replace("Z", "+00:00"))
                            mod_date = dt.astimezone(local_tz).date()
                            
                            if mod_date == today:
                                report_data[kab_name]["today_completed"] += 1
                                bd = report_data[kab_name].setdefault("today_completed_breakdown", {})
                                bd[status_alias] = bd.get(status_alias, 0) + 1
                                
                                if kec_stats:
                                    kec_stats["today_completed"] += 1
                                    kbd = kec_stats.setdefault("today_completed_breakdown", {})
                                    kbd[status_alias] = kbd.get(status_alias, 0) + 1
                            elif mod_date == yesterday:
                                report_data[kab_name]["yesterday_completed"] += 1
                                bd = report_data[kab_name].setdefault("yesterday_completed_breakdown", {})
                                bd[status_alias] = bd.get(status_alias, 0) + 1
                                
                                if kec_stats:
                                    kec_stats["yesterday_completed"] += 1
                                    kbd = kec_stats.setdefault("yesterday_completed_breakdown", {})
                                    kbd[status_alias] = kbd.get(status_alias, 0) + 1
                            elif mod_date == two_days_ago:
                                report_data[kab_name]["two_days_ago_completed"] += 1
                                bd = report_data[kab_name].setdefault("two_days_ago_completed_breakdown", {})
                                bd[status_alias] = bd.get(status_alias, 0) + 1
                                
                                if kec_stats:
                                    kec_stats["two_days_ago_completed"] += 1
                                    kbd = kec_stats.setdefault("two_days_ago_completed_breakdown", {})
                                    kbd[status_alias] = kbd.get(status_alias, 0) + 1
                        except Exception as ex:
                            pass
                            
                # Check creations (New Usahas) on all fetched records
                create_date_str = r.get("dateCreated")
                if create_date_str:
                    try:
                        dt = datetime.datetime.fromisoformat(create_date_str.replace("Z", "+00:00"))
                        create_date = dt.astimezone(local_tz).date()
                        comp_name = r.get("data1") or "-"
                        code_id = r.get("codeIdentity") or "-"
                        if is_tambahan(code_id):
                            data6_val = str(r.get("data6") or "").upper()
                            jenis_lbl, is_usaha_derived = classify_tambahan(code_id, comp_name, data6_val)
                            is_rumah = not is_usaha_derived
                            
                            if create_date == today:
                                if is_rumah:
                                    report_data[kab_name]["new_rumah_today"] += 1
                                    if kec_stats:
                                        kec_stats["new_rumah_today"] += 1
                                else:
                                    report_data[kab_name]["new_usaha_today"] += 1
                                    if kec_stats:
                                        kec_stats["new_usaha_today"] += 1
                            elif create_date == yesterday:
                                if is_rumah:
                                    report_data[kab_name]["new_rumah_yesterday"] += 1
                                    if kec_stats:
                                        kec_stats["new_rumah_yesterday"] += 1
                                else:
                                    report_data[kab_name]["new_usaha_yesterday"] += 1
                                    if kec_stats:
                                        kec_stats["new_usaha_yesterday"] += 1
                            
                            # Always append to new_businesses list
                            date_lbl = "today" if create_date == today else ("yesterday" if create_date == yesterday else "older")
                            biz_item = {
                                "name": comp_name,
                                "code": code_id,
                                "date": date_lbl,
                                "status": status_alias,
                                "type": "rumah" if is_rumah else "usaha",
                                "kecName": kec_stats["kec_name"] if kec_stats else "-",
                                "jenis": jenis_lbl
                            }
                            report_data[kab_name]["new_businesses"].append(biz_item)
                            if kec_stats:
                                kec_stats.setdefault("new_businesses", []).append(biz_item)

                    except Exception as ex:
                        pass

            # 4. Format percentages and sisa
            final_list = []
            for kab_name, stats in report_data.items():
                prelist = stats["total_prelist"]
                completed = stats["total_submitted"]
                
                pct = round((completed / prelist * 100) if prelist > 0 else 0.0, 2)
                
                # Format Kecamatan list details
                formatted_kecs = []
                for kec_s in stats["kecamatan_list"]:
                    # Calculate open targets
                    k_prelist = kec_s["total_prelist"] + kec_s["new_usaha_overall"] + kec_s["new_rumah_overall"]
                    k_draft = kec_s["total_draft"]
                    k_sub = kec_s["total_submitted"]
                    k_open = max(0, k_prelist - k_sub - k_draft)
                    kec_s["total_prelist"] = k_prelist
                    kec_s["total_open"] = k_open
                    kec_s["persentase"] = round((k_sub / k_prelist * 100) if k_prelist > 0 else 0.0, 2)
                    formatted_kecs.append(kec_s)
                
                final_list.append({
                    "kabupaten": kab_name,
                    "total_prelist": prelist,
                    "total_draft": stats["total_draft"],
                    "total_open": stats["total_open"],
                    "total_submitted": completed,
                    "total_rejected": stats["total_rejected"],
                    "total_approved": stats["total_approved"],
                    "persentase": pct,
                    "today_completed": stats["today_completed"],
                    "yesterday_completed": stats["yesterday_completed"],
                    "two_days_ago_completed": stats["two_days_ago_completed"],
                    "today_completed_breakdown": stats.get("today_completed_breakdown", {}),
                    "yesterday_completed_breakdown": stats.get("yesterday_completed_breakdown", {}),
                    "two_days_ago_completed_breakdown": stats.get("two_days_ago_completed_breakdown", {}),
                    "new_usaha_today": stats["new_usaha_today"],
                    "new_usaha_yesterday": stats["new_usaha_yesterday"],
                    "new_rumah_today": stats["new_rumah_today"],
                    "new_rumah_yesterday": stats["new_rumah_yesterday"],
                    "new_usaha_overall": stats.get("new_usaha_overall", 0),
                    "new_rumah_overall": stats.get("new_rumah_overall", 0),
                    "new_businesses": stats["new_businesses"],
                    "kecamatan_list": formatted_kecs
                })
            
            output_data[survey_key] = final_list

        # Write to JS
        local_tz = datetime.timezone(datetime.timedelta(hours=8))
        now_str = datetime.datetime.now(local_tz).isoformat()
        final_js_obj = {
            "updated_at": now_str,
            "se_umum": output_data["se_umum"],
            "se_ub": output_data["se_ub"],
            "se_umum_prov_total": output_data.get("se_umum_prov_total", 0),
            "se_ub_prov_total": output_data.get("se_ub_prov_total", 0),
            "se_umum_prov_new_total": output_data.get("se_umum_prov_new_total", 0),
            "se_ub_prov_new_total": output_data.get("se_ub_prov_new_total", 0),
            "se_umum_prov_new_rumah_total": output_data.get("se_umum_prov_new_rumah_total", 0),
            "se_ub_prov_new_rumah_total": output_data.get("se_ub_prov_new_rumah_total", 0)
        }
        with open("ipas_data.js", "w", encoding="utf-8") as f:
            f.write(f"window.IPAS_DATA = {json.dumps(final_js_obj, ensure_ascii=False, indent=2)};\n")
            
        print("\nLaporan rekap Sensus Ekonomi berhasil di-generate ke ipas_data.js!")

        # Upload to Supabase dashboard_store
        if supabase:
            try:
                print("Mengunggah data IPAS ke Supabase...")
                # delete existing
                supabase.table("dashboard_store").delete().eq("key", "ipas_data").execute()
                # insert new
                supabase.table("dashboard_store").insert({"key": "ipas_data", "value": final_js_obj}).execute()
                print("Berhasil mengunggah data IPAS ke Supabase.")
            except Exception as e:
                print(f"Gagal mengunggah data IPAS ke Supabase: {e}")

async def main_loop():
    delay_seconds = 300 # 5 minutes
    while True:
        print(f"\n=========================================")
        print(f"Memulai siklus update data rekap: {datetime.datetime.now()}")
        print(f"=========================================")
        try:
            await generate_report()
        except Exception as e:
            print("Gagal generate report:", e)
        print(f"\nSiklus selesai. Menunggu {delay_seconds} detik untuk update berikutnya...")
        await asyncio.sleep(delay_seconds)

if __name__ == "__main__":
    asyncio.run(main_loop())
