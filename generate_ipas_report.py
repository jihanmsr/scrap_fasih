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
    port = 9222
    if check_port_open(port):
        print("[INFO] Chrome remote debugging port 9222 sudah aktif. Menggunakan instansi yang ada.")
        return
    
    print("[INFO] Chrome remote debugging port 9222 tidak aktif. Mencoba meluncurkan browser...")
    chrome_path = "/Users/jihanmaisaroh/Library/Caches/ms-playwright/chromium-1208/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"
    
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
            print("[INFO] Browser Chrome berhasil diluncurkan dan siap di port 9222.")
            return
    print("[ERROR] Gagal mendeteksi port 9222 setelah meluncurkan Chrome.")

async def get_authenticated_context(p):
    abs_user_data_dir = os.path.abspath(USER_DATA_DIR)
    os.makedirs(abs_user_data_dir, exist_ok=True)
    chrome_path = "/Users/jihanmaisaroh/Library/Caches/ms-playwright/chromium-1208/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"

    browser = None
    context = None
    page = None

    if check_port_open(9222):
        print("[INFO] Remote debugging port 9222 terdeteksi. Mencoba sambung via CDP...")
        try:
            browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
            context = browser.contexts[0] if browser.contexts else browser.new_context()
            page = context.pages[0] if context.pages else context.new_page()
            print("[INFO] Berhasil tersambung ke browser via CDP.")
        except Exception as e:
            print(f"[WARNING] Gagal connect_over_cdp: {e}. Menggunakan Playwright persistent context sebagai fallback.")
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
        
        if page.url == "about:blank":
            print("Tab FASIH tidak ditemukan. Navigasi...")
            try:
                await page.goto("https://fasih-sm.bps.go.id/app/surveys/a0429e96-51a5-477b-a415-485f9c153004/fd68e454-ba45-4b85-8205-f3bf777ded24/data", timeout=60000, wait_until="domcontentloaded")
            except Exception as e:
                print("Gagal navigasi ke data url:", e)

        cookies = await page.context.cookies()
        xsrf_token_raw = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), "")
        
        from urllib.parse import unquote
        xsrf_token = unquote(xsrf_token_raw)
        
        datatable_url = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode"

        async def fetch_api_safely(url, payload, token):
            try:
                res = await page.evaluate("""
                    async ({url, payload, token}) => {
                        try {
                            const r = await fetch(url, {
                                method: "POST",
                                headers: { "Content-Type": "application/json", "X-XSRF-TOKEN": token },
                                body: JSON.stringify(payload)
                            });
                            if (!r.ok) return { error: `HTTP ${r.status}: ${await r.text()}` };
                            const text = await r.text();
                            try {
                                return JSON.parse(text);
                            } catch(e) {
                                return { error: "Invalid JSON", text: text.substring(0, 200) };
                            }
                        } catch(e) {
                            return { error: e.toString() };
                        }
                    }
                """, {"url": url, "payload": payload, "token": token})
                return res
            except Exception as e:
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
            
            # Re-fetch cookies
            cookies = await page.context.cookies()
            xsrf_token_raw = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), "")
            xsrf_token = unquote(xsrf_token_raw)

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
        
        output_data = {}
        
        for survey_key, survey_cfg in surveys.items():
            print(f"\n=========================================")
            print(f"Memproses Survey: {survey_cfg['label']}")
            print(f"=========================================")
            
            period_id = survey_cfg["period_id"]
            
            # Initialize final report dict
            report_data = {}
            for k in survey_cfg["kabs"]:
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
                    "new_usaha_today": 0,
                    "new_usaha_yesterday": 0,
                    "new_businesses": []
                }
                
            datatable_url = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode"

            # Fetch PROVINCE TOTAL
            payload_prov = {
                "start": 0, "length": 1, "columns": [{"data": "id"}], "order": [], "search": {"value": "", "regex": False},
                "assignmentExtraParam": {
                    "region1Id": survey_cfg["prov_id"],
                    "surveyPeriodId": period_id,
                    "assignmentErrorStatusType": -1
                }
            }
            res_prov = await fetch_api_safely(datatable_url, payload_prov, xsrf_token)
            prov_total = 0
            if res_prov and "searchAggregation" in res_prov:
                prov_total = sum(i["docCount"] for i in res_prov["searchAggregation"])
            output_data[f"{survey_key}_prov_total"] = prov_total

            for kab in survey_cfg["kabs"]:

                payload = {
                    "start": 0, "length": 1, "columns": [{"data": "id"}], "order": [], "search": {"value": "", "regex": False},
                    "assignmentExtraParam": {
                        "region1Id": survey_cfg["prov_id"],
                        "region2Id": kab["id"],
                        "surveyPeriodId": period_id,
                        "assignmentErrorStatusType": -1,
                        "filterTargetType": ""
                    }
                }
                res = await fetch_api_safely(datatable_url, payload, xsrf_token)
                if not res or "error" in res:
                    print(f"  [ERROR] Gagal memproses {kab['name']}: {res.get('error') if res else 'Unknown error'}")
                    continue
                
                agg = res.get("searchAggregation", [])
                
                total_prelist = 0
                draft = 0
                open_count = 0
                submitted = 0
                rejected = 0
                approved = 0
                
                for item in agg:
                    key = item.get("keyAggregation", "")
                    count = item.get("docCount", 0)
                    total_prelist += count
                    
                    if key == "DRAFT":
                        draft += count
                    elif key == "OPEN":
                        open_count += count
                    elif "SUBMITTED" in key:
                        submitted += count
                    elif "REJECTED" in key:
                        rejected += count
                    elif "APPROVED" in key:
                        approved += count
                
                if total_prelist == 0:
                    total_prelist = res.get("totalHit", 0)
                    
                report_data[kab["name"]]["total_prelist"] = total_prelist
                report_data[kab["name"]]["total_draft"] = draft
                report_data[kab["name"]]["total_open"] = open_count
                report_data[kab["name"]]["total_submitted"] = submitted
                report_data[kab["name"]]["total_rejected"] = rejected
                report_data[kab["name"]]["total_approved"] = approved
                print(f"  {kab['name']}: Prelist={total_prelist}, Draft={draft}, Open={open_count}, Submitted={submitted}")

            # 2. Fetch daily progress details province-wide
            active_statuses = ["SUBMITTED RESPONDENT", "DRAFT", "REJECTED BY Admin Kabupaten"]
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
                            {"data": "dateCreated"},
                            {"data": "dateModified"},
                            {"data": "assignmentStatusAlias"}
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
            print("Mengolah riwayat tanggal dan mengelompokkan ke Kabupaten...")
            for r in all_records:
                code_identity = r.get("codeIdentity")
                if not code_identity or len(code_identity) < 4:
                    continue
                    
                kab_name = code_to_name.get(code_identity[:4])
                if not kab_name:
                    continue
                    
                status_alias = r.get("assignmentStatusAlias")
                
                # Check completions
                if status_alias in ["SUBMITTED RESPONDENT", "REJECTED BY Admin Kabupaten"]:
                    mod_date_str = r.get("dateModified")
                    if mod_date_str:
                        try:
                            # Parse date and convert to WITA
                            dt = datetime.datetime.fromisoformat(mod_date_str.replace("Z", "+00:00"))
                            mod_date = dt.astimezone(local_tz).date()
                            
                            if mod_date == today:
                                report_data[kab_name]["today_completed"] += 1
                            elif mod_date == yesterday:
                                report_data[kab_name]["yesterday_completed"] += 1
                            elif mod_date == two_days_ago:
                                report_data[kab_name]["two_days_ago_completed"] += 1
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
                        
                        if create_date == today:
                            report_data[kab_name]["new_usaha_today"] += 1
                            report_data[kab_name]["new_businesses"].append({
                                "name": comp_name,
                                "code": code_id,
                                "date": "today",
                                "status": status_alias
                            })
                        elif create_date == yesterday:
                            report_data[kab_name]["new_usaha_yesterday"] += 1
                            report_data[kab_name]["new_businesses"].append({
                                "name": comp_name,
                                "code": code_id,
                                "date": "yesterday",
                                "status": status_alias
                            })
                    except Exception as ex:
                        pass

            # 4. Format percentages and sisa
            final_list = []
            for kab_name, stats in report_data.items():
                prelist = stats["total_prelist"]
                completed = stats["total_submitted"]
                
                pct = round((completed / prelist * 100) if prelist > 0 else 0.0, 2)
                
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
                    "new_usaha_today": stats["new_usaha_today"],
                    "new_usaha_yesterday": stats["new_usaha_yesterday"],
                    "new_businesses": stats["new_businesses"]
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
            "se_ub_prov_total": output_data.get("se_ub_prov_total", 0)
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
