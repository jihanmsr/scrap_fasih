import asyncio
import copy
import json
import os
import time
import socket
import gzip
import base64
import httpx
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = None
if SUPABASE_URL and SUPABASE_KEY and "MASUKKAN" not in SUPABASE_URL:
    try:
        from supabase import create_client
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("[INFO] Koneksi Supabase berhasil diinisialisasi untuk scrape_granular_assignments.")
    except Exception as e:
        print(f"[ERROR] Gagal menginisialisasi Supabase: {e}")

USER_DATA_DIR = "playwright_chrome_profile"

def check_port_open(port=9222):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0
    except:
        return False

async def get_authenticated_context(p):
    for port in [9223, 9222]:
        if check_port_open(port):
            try:
                browser = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
                context = browser.contexts[0] if browser.contexts else await browser.new_context()
                
                has_fasih = False
                target_page = None
                for page in context.pages:
                    if "fasih-sm.bps.go.id" in page.url:
                        has_fasih = True
                        target_page = page
                        break
                        
                if has_fasih:
                    print(f"[INFO] Terhubung ke browser aktif dengan sesi FASIH di port {port}")
                    return browser, context, target_page
                else:
                    target_page = context.pages[0] if context.pages else await context.new_page()
                    fallback = (browser, context, target_page, port)
            except Exception:
                pass

    if 'fallback' in locals():
        browser, context, target_page, port = fallback
        print(f"[INFO] Terhubung ke browser di port {port} (tidak ada tab FASIH aktif)")
        return browser, context, target_page

    abs_user_data_dir = os.path.abspath(USER_DATA_DIR)
    chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    context = await p.chromium.launch_persistent_context(
        user_data_dir=abs_user_data_dir, headless=False, executable_path=chrome_path,
        args=["--no-first-run", "--no-default-browser-check"]
    )
    return None, context, context.pages[0] if context.pages else await context.new_page()

async def check_session_valid(page, token):
    if not token:
        return False
    url = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode"
    payload = {
        "start": 0, "length": 1, "columns": [{"data": "id"}], "order": [], "search": {"value": "", "regex": False},
        "assignmentExtraParam": {
            "region1Id": "a00c8aef-afc4-4d4f-b80d-789a15450ef9",
            "surveyPeriodId": "37526b20-81c8-42f5-a895-6190137d7394",
            "assignmentErrorStatusType": -1
        }
    }
    try:
        res = await page.evaluate("""
            async ({url, payload, token}) => {
                try {
                    const r = await fetch(url, {
                        method: "POST",
                        headers: { "Content-Type": "application/json", "X-XSRF-TOKEN": token },
                        body: JSON.stringify(payload)
                    });
                    if (!r.ok) return { _error: `HTTP ${r.status}` };
                    return await r.json();
                } catch (e) {
                    return { _error: e.toString() };
                }
            }
        """, {"url": url, "payload": payload, "token": token})
        
        if res and isinstance(res, dict):
            if "_error" in res:
                return False
            return "searchData" in res or "searchAggregation" in res
    except Exception:
        pass
    return False

# Region config mapping
SURVEY_CONFIGS = [
    {
        "label": "se_umum",
        "survey_period_id": "fd68e454-ba45-4b85-8205-f3bf777ded24",
        "region1_id": "5214ecb2-bef1-4a86-9446-451cf430928e",
        "kab_region_map": {
            "7201": {"id": "bc32354f-1245-426f-b2cf-a5733e1295ad", "name": "[01] BANGGAI KEPULAUAN"},
            "7202": {"id": "530e9ca5-86ba-434e-9b04-405102e6d900", "name": "[02] BANGGAI"},
            "7203": {"id": "9783f0c1-f047-477f-8840-11eae7cf70e2", "name": "[03] MOROWALI"},
            "7204": {"id": "fb9cd9f0-c4c0-4a37-9041-57190693f625", "name": "[04] POSO"},
            "7205": {"id": "289f1ff3-a6ad-4c9b-a49f-7b454d03a33f", "name": "[05] DONGGALA"},
            "7206": {"id": "d833fdce-ebfb-429b-a1bb-8966239fd8e4", "name": "[06] TOLI-TOLI"},
            "7207": {"id": "c523694a-2e72-4570-9489-da2d7b119fe7", "name": "[07] BUOL"},
            "7208": {"id": "25c59fd9-afd5-4c1a-9dfb-42bb697a7434", "name": "[08] PARIGI MOUTONG"},
            "7209": {"id": "736c4c22-51d1-44be-8b2c-aa197d9459a4", "name": "[09] TOJO UNA-UNA"},
            "7210": {"id": "0061da62-2a47-4dee-b8d0-239b33e2c59d", "name": "[10] SIGI"},
            "7211": {"id": "eed1a3e7-b81d-4fc7-b0d6-61257c1449b2", "name": "[11] BANGGAI LAUT"},
            "7212": {"id": "d05ef8fd-b5e4-414f-9a83-8cdea03e0767", "name": "[12] MOROWALI UTARA"},
            "7271": {"id": "4ab6ca2f-7952-4e8e-a94d-b6dd933e5d44", "name": "[71] PALU"},
        }
    },
    {
        "label": "se_ub",
        "survey_period_id": "37526b20-81c8-42f5-a895-6190137d7394",
        "region1_id": "a00c8aef-afc4-4d4f-b80d-789a15450ef9",
        "kab_region_map": {
            "7201": {"id": "9c9b2d79-9fb1-4ce7-b0f1-6b7bb5511beb", "name": "[01] BANGGAI KEPULAUAN"},
            "7202": {"id": "34165dd5-372e-42fa-99c6-0cc19a9b4d0b", "name": "[02] BANGGAI"},
            "7203": {"id": "48c4e5d0-5525-41a8-a4ba-2cc38cd9c424", "name": "[03] MOROWALI"},
            "7204": {"id": "e18368ae-d1cd-4d43-a74d-5b9ddac5dd22", "name": "[04] POSO"},
            "7205": {"id": "c075c4b4-7eb0-4d72-9c16-5103088fb5eb", "name": "[05] DONGGALA"},
            "7206": {"id": "d3a28bfa-b611-488b-8255-369da5cedbf7", "name": "[06] TOLI-TOLI"},
            "7207": {"id": "dfe4c643-3282-40db-a5fd-cb288a4f592d", "name": "[07] BUOL"},
            "7208": {"id": "f18109d2-fc8b-4b9c-886a-dc242d21206e", "name": "[08] PARIGI MOUTONG"},
            "7209": {"id": "4d01eba1-5ae9-4603-82a6-2c831aea9905", "name": "[09] TOJO UNA-UNA"},
            "7210": {"id": "2a240d3a-67ee-45b2-ae78-4b4b3a909a90", "name": "[10] SIGI"},
            "7211": {"id": "288c5680-f6d5-4783-a946-d5a06f547c02", "name": "[11] BANGGAI LAUT"},
            "7212": {"id": "a5324f17-7a00-436f-b468-2fc59fcf605d", "name": "[12] MOROWALI UTARA"},
            "7271": {"id": "1acfedb4-276e-44d6-9e45-6d43588536d6", "name": "[71] PALU"}
        }
    }
]

DATATABLE_URL = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode"

async def fetch_kab_granular(client, survey_period_id, region1_id, kab_id, kab_name, label, sem):
    print(f"  -> [{label}] Mulai download data wilayah: {kab_name}...")
    start = 0
    length = 1000
    all_records = []
    
    # We query datatable-all-user-survey-periode with all necessary columns
    columns_payload = [
        {"data": "id"},
        {"data": "codeIdentity"},
        {"data": "data1"}, # Target/Company Name
        {"data": "assignmentStatusAlias"},
        {"data": "currentUserUsername"},
        {"data": "currentUserFullname"},
        {"data": "dateCreated"},
        {"data": "dateModified"},
        {"data": "region"}
    ]
    
    while True:
        payload = {
            "start": start,
            "length": length,
            "columns": columns_payload,
            "order": [],
            "search": {"value": "", "regex": False},
            "assignmentExtraParam": {
                "region1Id": region1_id,
                "region2Id": kab_id,
                "surveyPeriodId": survey_period_id,
                "assignmentErrorStatusType": -1,
                "filterTargetType": ""
            }
        }
        
        res = None
        for attempt in range(4):
            async with sem:
                try:
                    r = await client.post(DATATABLE_URL, json=payload)
                    if r.status_code == 200:
                        res = r.json()
                        break
                    else:
                        res = {"_error": f"HTTP {r.status_code}"}
                except Exception as e:
                    res = {"_error": str(e)}
            await asyncio.sleep(0.1)
        
        if not res or "_error" in res or "searchData" not in res:
            print(f"      [ERROR] Fatal gagal ambil page data {start} untuk {kab_name}. Error: {res.get('_error') if res else 'None'}")
            break
            
        records = res["searchData"]
        if not records:
            break
            
        all_records.extend(records)
        print(f"      [{kab_name}] Downloaded {len(all_records)} / {res.get('totalHit', 0)} targets...")
        
        if len(records) < length or len(all_records) >= res.get("totalHit", 0):
            break
            
        start += length
        
    print(f"  -> [{label}] Selesai {kab_name}. Total: {len(all_records)} target.")
    return all_records

# Shared progress counter for SE Umum by Desa
progress_lock = asyncio.Lock()
completed_desas = 0
total_desas = 0

async def fetch_desa_granular(client, survey_period_id, region1_id, kab_id, kec_id, desa_id, kab_name, kec_name, desa_name, label, sem, raw_data_list, sls_list=None):
    global completed_desas, total_desas
    columns_payload = [
        {"data": "id"},
        {"data": "codeIdentity"},
        {"data": "data1"},
        {"data": "assignmentStatusAlias"},
        {"data": "currentUserUsername"},
        {"data": "currentUserFullname"},
        {"data": "dateCreated"},
        {"data": "dateModified"},
        {"data": "region"}
    ]
    
    payload = {
        "start": 0,
        "length": 1000,
        "columns": columns_payload,
        "order": [],
        "search": {"value": "", "regex": False},
        "assignmentExtraParam": {
            "region1Id": region1_id,
            "region2Id": kab_id,
            "region3Id": kec_id,
            "region4Id": desa_id,
            "surveyPeriodId": survey_period_id,
            "assignmentErrorStatusType": -1,
            "filterTargetType": ""
        }
    }
    
    res = None
    for attempt in range(4):
        async with sem:
            try:
                r = await client.post(DATATABLE_URL, json=payload)
                if r.status_code == 200:
                    res = r.json()
                    break
                else:
                    res = {"_error": f"HTTP {r.status_code}"}
            except Exception as e:
                res = {"_error": str(e)}
        await asyncio.sleep(0.05)
        if res and isinstance(res, dict) and "_error" not in res:
            break
        else:
            await asyncio.sleep(1.0)
            
    records = []
    if res and isinstance(res, dict) and "searchData" in res:
        records = res["searchData"]
        total_hit = res.get("totalHit", 0)
        
        # If the Desa has more than 1000 records, split by SLS or target vs non-target
        if total_hit > 1000:
            records = []
            if sls_list and len(sls_list) > 0:
                # Query each SLS inside the Desa
                for sls in sls_list:
                    sls_payload = copy.deepcopy(payload)
                    # We inject region5Id to filter by this SLS specifically
                    sls_payload["assignmentExtraParam"]["region5Id"] = sls.get("sls_id")
                    
                    res_sls = None
                    for attempt in range(4):
                        async with sem:
                            try:
                                r_sls = await client.post(DATATABLE_URL, json=sls_payload)
                                if r_sls.status_code == 200:
                                    res_sls = r_sls.json()
                                    break
                                else:
                                    res_sls = {"_error": f"HTTP {r_sls.status_code}"}
                            except Exception as e:
                                res_sls = {"_error": str(e)}
                        await asyncio.sleep(0.05)
                        if res_sls and isinstance(res_sls, dict) and "_error" not in res_sls:
                            break
                        else:
                            await asyncio.sleep(1.0)
                    
                    if res_sls and "searchData" in res_sls:
                        records.extend(res_sls["searchData"])
            else:
                # Fallback to target vs non-target split
                for target_type in ["target", "non-target"]:
                    payload["assignmentExtraParam"]["filterTargetType"] = target_type
                    res_split = None
                    for attempt in range(4):
                        async with sem:
                            try:
                                r_split = await client.post(DATATABLE_URL, json=payload)
                                if r_split.status_code == 200:
                                    res_split = r_split.json()
                                    break
                                else:
                                    res_split = {"_error": f"HTTP {r_split.status_code}"}
                            except Exception as e:
                                res_split = {"_error": str(e)}
                        await asyncio.sleep(0.05)
                        if res_split and isinstance(res_split, dict) and "_error" not in res_split:
                            break
                        else:
                            await asyncio.sleep(1.0)
                    
                    if res_split and "searchData" in res_split:
                        records.extend(res_split["searchData"])
                    
    if records:
        raw_data_list.extend(records)
        
    async with progress_lock:
        completed_desas += 1
        if completed_desas % 50 == 0 or completed_desas == total_desas:
            print(f"      [PROGRESS] SE Umum: Downloaded {completed_desas} / {total_desas} desas...", flush=True)
            
    return records

def parse_date_to_epoch(date_str):
    if not date_str:
        return 0
    try:
        cleaned = date_str.strip()
        if cleaned.endswith("Z"):
            cleaned = cleaned[:-1] + "+00:00"
        dt = datetime.fromisoformat(cleaned)
        return int(dt.timestamp())
    except Exception:
        return 0

def get_wita_date_string(epoch_secs):
    if not epoch_secs:
        return None
    dt_utc = datetime.fromtimestamp(epoch_secs, tz=timezone.utc)
    wita_offset = timezone(timedelta(hours=8))
    dt_wita = dt_utc.astimezone(wita_offset)
    return dt_wita.strftime("%Y-%m-%d")

def save_local_data_intermediate(raw_se_umum_data, raw_se_ub_data):
    if not raw_se_umum_data and not raw_se_ub_data:
        return
        
    print("\n[COMPRESSION - INTERMEDIATE] Memulai pengolahan dan kompresi data...")
    
    regions_dict = {}
    regions_list = []
    petugas_dict = {}
    petugas_list = []
    statuses_dict = {}
    statuses_list = []
    
    def get_region_idx(comp, fallback_kab_name):
        region = comp.get("region", {})
        lvl1 = region.get("level1", {}) or {}
        lvl2 = lvl1.get("level2", {}) or {}
        lvl3 = lvl2.get("level3", {}) or {}
        lvl4 = lvl3.get("level4", {}) or {}
        lvl5 = lvl4.get("level5", {}) or {}
        
        kab_code = lvl2.get("fullCode") or ""
        kab_name = lvl2.get("name") or fallback_kab_name
        kec_code = lvl3.get("fullCode") or ""
        kec_name = lvl3.get("name") or "-"
        desa_code = lvl4.get("fullCode") or ""
        desa_name = lvl4.get("name") or "-"
        sls_code = lvl5.get("fullCode") or ""
        sls_name = lvl5.get("name") or "-"
        
        key = (kab_code, kab_name, kec_code, kec_name, desa_code, desa_name, sls_code, sls_name)
        if key not in regions_dict:
            regions_dict[key] = len(regions_list)
            regions_list.append(list(key))
        return regions_dict[key]
        
    def get_petugas_idx(username, fullname):
        if not username:
            return -1
        key = (username, fullname or "-")
        if key not in petugas_dict:
            petugas_dict[key] = len(petugas_list)
            petugas_list.append(list(key))
        return petugas_dict[key]
        
    def get_status_idx(status):
        if not status:
            status = "-"
        status_clean = status.strip().upper()
        if status_clean not in statuses_dict:
            statuses_dict[status_clean] = len(statuses_list)
            statuses_list.append(status_clean)
        return statuses_dict[status_clean]
        
    compressed_targets = []
    daily_counts_dict = {}
    
    # Process SE Umum
    for r in raw_se_umum_data:
        tid = r.get("id")
        code_id = r.get("codeIdentity")
        name = r.get("data1") or "-"
        status = r.get("assignmentStatusAlias") or "OPEN"
        username = r.get("currentUserUsername")
        fullname = r.get("currentUserFullname")
        date_mod_str = r.get("dateModified")
        epoch_mod = parse_date_to_epoch(date_mod_str)
        
        reg_idx = get_region_idx(r, "SULAWESI TENGAH")
        pet_idx = get_petugas_idx(username, fullname)
        stat_idx = get_status_idx(status)
        
        compressed_targets.append([
            tid, code_id, name, stat_idx, pet_idx, reg_idx, epoch_mod, 0
        ])
        
        status_upper = status.upper()
        if status_upper != "OPEN" and epoch_mod > 0:
            wita_date = get_wita_date_string(epoch_mod)
            if wita_date:
                kab_name = regions_list[reg_idx][1]
                agg_key = (wita_date, kab_name, "se_umum")
                daily_counts_dict[agg_key] = daily_counts_dict.get(agg_key, 0) + 1
                
    # Process SE UB
    for r in raw_se_ub_data:
        tid = r.get("id")
        code_id = r.get("codeIdentity")
        name = r.get("data1") or "-"
        status = r.get("assignmentStatusAlias") or "OPEN"
        username = r.get("currentUserUsername")
        fullname = r.get("currentUserFullname")
        date_mod_str = r.get("dateModified")
        epoch_mod = parse_date_to_epoch(date_mod_str)
        
        reg_idx = get_region_idx(r, "SULAWESI TENGAH")
        pet_idx = get_petugas_idx(username, fullname)
        stat_idx = get_status_idx(status)
        
        compressed_targets.append([
            tid, code_id, name, stat_idx, pet_idx, reg_idx, epoch_mod, 1
        ])
        
        status_upper = status.upper()
        if status_upper != "OPEN" and epoch_mod > 0:
            wita_date = get_wita_date_string(epoch_mod)
            if wita_date:
                kab_name = regions_list[reg_idx][1]
                agg_key = (wita_date, kab_name, "se_ub")
                daily_counts_dict[agg_key] = daily_counts_dict.get(agg_key, 0) + 1

    # Flatten daily counts
    daily_stats_data = []
    for (date_str, kab_name, s_type), cnt in daily_counts_dict.items():
        daily_stats_data.append({
            "date": date_str,
            "kab_name": kab_name,
            "survey_type": s_type,
            "count": cnt
        })
        
    print(f"Compressed {len(compressed_targets)} targets.")
    
    # Save payload
    granular_payload = {
        "updated_at": datetime.now().isoformat(),
        "regions": regions_list,
        "petugas": petugas_list,
        "statuses": statuses_list,
        "targets": compressed_targets
    }
    
    raw_json_str = json.dumps(granular_payload, ensure_ascii=False)
    compressed_bytes = gzip.compress(raw_json_str.encode('utf-8'))
    base64_str = base64.b64encode(compressed_bytes).decode('utf-8')
    
    # Local cache save
    with open("granular_assignments.json", "w", encoding="utf-8") as f:
        json.dump({"compressed_data": base64_str, "updated_at": datetime.now().isoformat()}, f, indent=2)
    with open("daily_submission_stats.json", "w", encoding="utf-8") as f:
        json.dump(daily_stats_data, f, indent=2)
        
    # Write Javascript files for fallback local load
    with open("granular_assignments.js", "w", encoding="utf-8") as f:
        f.write(f"window.COMPRESSED_GRANULAR_ASSIGNMENTS = '{base64_str}';\n")
        f.write(f"window.GRANULAR_ASSIGNMENTS_UPDATED_AT = '{datetime.now().isoformat()}';\n")
    with open("daily_submission_stats.js", "w", encoding="utf-8") as f:
        f.write(f"window.DAILY_SUBMISSION_STATS = {json.dumps(daily_stats_data, indent=2)};\n")
    print("✅ [INTERMEDIATE SAVE SUCCESS] Progress berhasil disimpan ke file lokal.\n", flush=True)

async def scrape_all_granular():
    print("[START] Mulai proses penarikan seluruh data secara granular...")
    
    remarks_dict = {}
    
    # 1. Connect to Playwright
    async with async_playwright() as p:
        browser, context, page = await get_authenticated_context(p)
        print(f"[INFO] Terhubung ke browser. URL Tab Aktif: {page.url}")
        
        # Navigasi jika tidak di fasih
        if "fasih-sm.bps.go.id" not in page.url:
            print("[INFO] Membuka halaman dashboard FASIH...")
            try:
                await page.goto("https://fasih-sm.bps.go.id/app/dashboard", timeout=60000, wait_until="domcontentloaded")
            except Exception as e:
                print(f"[WARNING] Navigasi lambat: {e}")
        
        # 2. Get and verify session cookie
        cookies = await context.cookies()
        cookie_dict = {c["name"]: c["value"] for c in cookies}
        token_raw = cookie_dict.get("XSRF-TOKEN", "")
        
        from urllib.parse import unquote
        token = unquote(token_raw) if token_raw else ""
        
        # Wait for valid session
        attempt_count = 0
        while not await check_session_valid(page, token):
            attempt_count += 1
            print("\n==============================================================")
            print("[WARNING] Sesi FASIH tidak valid atau telah kedaluwarsa.")
            print("Harap LOGIN atau REFRESH halaman FASIH di browser Chrome Anda.")
            print("Script mendeteksi secara otomatis setiap 15 detik...")
            print("==============================================================\n", flush=True)
            
            # Reload page on alternate attempts to force refresh cookie
            if attempt_count % 2 == 1:
                print("[INFO] Mencoba memuat ulang halaman untuk memicu pembaruan cookie...", flush=True)
                try:
                    await page.reload(timeout=30000)
                except Exception as e:
                    print(f"[WARNING] Gagal memuat ulang halaman: {e}", flush=True)
                    
            await asyncio.sleep(15)
            cookies = await context.cookies()
            cookie_dict = {c["name"]: c["value"] for c in cookies}
            token_raw = cookie_dict.get("XSRF-TOKEN", "")
            token = unquote(token_raw) if token_raw else ""
            
        print("[SUCCESS] Sesi terverifikasi! Memulai scraping data granular...")
        
        # We will loop through the configurations
        raw_se_umum_data = []
        raw_se_ub_data = []
        
        # Initialize HTTPX async client with cookies and headers from browser context
        limits = httpx.Limits(max_keepalive_connections=20, max_connections=40)
        async with httpx.AsyncClient(limits=limits, timeout=60.0) as client:
            client.headers.update({
                "Content-Type": "application/json",
                "X-XSRF-TOKEN": token,
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/json, text/plain, */*"
            })
            for c in cookies:
                client.cookies.set(
                    c['name'],
                    c['value'],
                    domain=c.get('domain', 'fasih-sm.bps.go.id'),
                    path=c.get('path', '/')
                )
                
            # Concurrency limit (3 concurrent requests for UB, 15 for SE Umum)
            sem = asyncio.Semaphore(3)
            
            # Run SE Umum (by Desa in parallel)
            global completed_desas, total_desas
            cfg_umum = SURVEY_CONFIGS[0]
            print(f"\n--- Memulai Scraping {cfg_umum['label'].upper()} ---")
            
            try:
                with open("region_map_sulteng_full.json", "r") as f:
                    region_map_full = json.load(f)
            except Exception as e:
                print(f"[ERROR] Gagal memuat region_map_sulteng_full.json: {e}")
                region_map_full = {}
                
            sem_umum = asyncio.Semaphore(15)
            tasks_umum = []
            for kab_code, kab_cfg in cfg_umum["kab_region_map"].items():
                kab_data = region_map_full.get("kabupaten", {}).get(kab_code, {})
                if not kab_data:
                    print(f"[WARNING] Kabupaten {kab_code} tidak ditemukan di region_map_sulteng_full.json")
                    continue
                for kec_code, kec_data in kab_data.get("kecamatan", {}).items():
                    kec_name = kec_data.get("kec_name", "-")
                    for desa_code, desa_data in kec_data.get("desa", {}).items():
                        desa_name = desa_data.get("desa_name", "-")
                        tasks_umum.append(
                            fetch_desa_granular(
                                client, 
                                cfg_umum["survey_period_id"], 
                                cfg_umum["region1_id"], 
                                kab_cfg["id"], 
                                kec_data["kec_id"], 
                                desa_data["desa_id"], 
                                kab_cfg["name"], 
                                kec_name, 
                                desa_name, 
                                "SE Umum", 
                                sem_umum,
                                raw_se_umum_data,
                                sls_list=desa_data.get("sls", [])
                            )
                        )
                        
            total_desas = len(tasks_umum)
            completed_desas = 0
            print(f"[INFO] Total Desa yang akan di-query untuk SE Umum: {total_desas}")
            
            # Start background periodic local saver
            scraping_done = False
            
            async def periodic_saver():
                while not scraping_done:
                    await asyncio.sleep(120)  # save every 2 minutes
                    try:
                        save_local_data_intermediate(raw_se_umum_data, raw_se_ub_data)
                    except Exception as ex:
                        print(f"[WARNING] Gagal melakukan periodic save: {ex}", flush=True)
                        
            saver_task = asyncio.create_task(periodic_saver())
            
            try:
                results_umum = await asyncio.gather(*tasks_umum)
                for r in results_umum:
                    raw_se_umum_data.extend(r)
            finally:
                # Run intermediate save before SE UB starts
                save_local_data_intermediate(raw_se_umum_data, raw_se_ub_data)
                
            # Run SE UB (by Kabupaten since total UB targets are very small)
            cfg_ub = SURVEY_CONFIGS[1]
            print(f"\n--- Memulai Scraping {cfg_ub['label'].upper()} ---")
            tasks_ub = [
                fetch_kab_granular(client, cfg_ub["survey_period_id"], cfg_ub["region1_id"], kab_cfg["id"], kab_cfg["name"], "SE UB", sem)
                for kab_id, kab_cfg in cfg_ub["kab_region_map"].items()
            ]
            results_ub = await asyncio.gather(*tasks_ub)
            for r in results_ub:
                raw_se_ub_data.extend(r)
                
            print(f"\n[DONE] Scraping datatable selesai. Total Raw Umum: {len(raw_se_umum_data)} | Total Raw UB: {len(raw_se_ub_data)}")
            
            # --- FETCH REMARKS UNTUK STATUS REJECTED/REVOKED ---
            print("\n--- Memulai Fetching Remarks untuk Target Ditolak/Dibatalkan ---")
            rejected_targets = []
            for r in raw_se_umum_data + raw_se_ub_data:
                status = str(r.get("assignmentStatusAlias", "")).upper()
                if "REJECTED" in status or "REVOKED" in status:
                    rejected_targets.append(r.get("id"))
            
            # Buang duplikat id
            rejected_targets = list(set([tid for tid in rejected_targets if tid]))
            
            if rejected_targets:
                print(f"[INFO] Ditemukan {len(rejected_targets)} target dengan status REJECTED/REVOKED. Mengambil catatan (remarks)...")
                sem_remarks = asyncio.Semaphore(10)
                
                async def _fetch_remark(tid):
                    url = f"https://fasih-sm.bps.go.id/app/api/survey-response/api/v1/remarks?assignmentId={tid}"
                    for attempt in range(3):
                        async with sem_remarks:
                            try:
                                r = await client.get(url)
                                if r.status_code == 200:
                                    data = r.json()
                                    if isinstance(data, list) and len(data) > 0:
                                        # Ambil remark terbaru / gabungkan
                                        remarks_texts = []
                                        for rm in data:
                                            txt = rm.get("remark", "")
                                            by = rm.get("currentUserFullname", "Pengawas")
                                            if txt: remarks_texts.append(f"{by}: {txt}")
                                        if remarks_texts:
                                            remarks_dict[tid] = " | ".join(remarks_texts)
                                    break
                            except Exception:
                                pass
                        await asyncio.sleep(0.5)
                
                tasks_remarks = [_fetch_remark(tid) for tid in rejected_targets]
                await asyncio.gather(*tasks_remarks)
                print(f"[INFO] Berhasil mengambil catatan untuk {len(remarks_dict)} target.")
            else:
                print("[INFO] Tidak ada target REJECTED/REVOKED.")
            
            # Stop the periodic saver
            scraping_done = True
            saver_task.cancel()

            
            print(f"\n[DONE] Scraping selesai. Total Raw Umum: {len(raw_se_umum_data)} | Total Raw UB: {len(raw_se_ub_data)}")
        
        # 3. Process and compress data
        print("\n[COMPRESSION] Memulai pengolahan dan kompresi data...")
        
        # Dictionaries to remove duplicates
        regions_dict = {}
        regions_list = []
        
        petugas_dict = {}
        petugas_list = []
        
        statuses_dict = {}
        statuses_list = []
        
        def get_region_idx(comp, fallback_kab_name):
            region = comp.get("region", {})
            lvl1 = region.get("level1", {}) or {}
            lvl2 = lvl1.get("level2", {}) or {}
            lvl3 = lvl2.get("level3", {}) or {}
            lvl4 = lvl3.get("level4", {}) or {}
            lvl5 = lvl4.get("level5", {}) or {}
            
            kab_code = lvl2.get("fullCode") or ""
            kab_name = lvl2.get("name") or fallback_kab_name
            kec_code = lvl3.get("fullCode") or ""
            kec_name = lvl3.get("name") or "-"
            desa_code = lvl4.get("fullCode") or ""
            desa_name = lvl4.get("name") or "-"
            sls_code = lvl5.get("fullCode") or ""
            sls_name = lvl5.get("name") or "-"
            
            key = (kab_code, kab_name, kec_code, kec_name, desa_code, desa_name, sls_code, sls_name)
            if key not in regions_dict:
                regions_dict[key] = len(regions_list)
                regions_list.append(list(key))
            return regions_dict[key]
            
        def get_petugas_idx(username, fullname):
            if not username:
                return -1
            key = (username, fullname or "-")
            if key not in petugas_dict:
                petugas_dict[key] = len(petugas_list)
                petugas_list.append(list(key))
            return petugas_dict[key]
            
        def get_status_idx(status):
            if not status:
                status = "-"
            status_clean = status.strip().upper()
            if status_clean not in statuses_dict:
                statuses_dict[status_clean] = len(statuses_list)
                statuses_list.append(status_clean)
            return statuses_dict[status_clean]
            
        compressed_targets = []
        daily_counts_dict = {} # key: (date, kab_name, survey_type) -> count
        
        # Process SE Umum
        for r in raw_se_umum_data:
            # Get properties
            tid = r.get("id")
            code_id = r.get("codeIdentity")
            name = r.get("data1") or "-"
            status = r.get("assignmentStatusAlias") or "OPEN"
            username = r.get("currentUserUsername")
            fullname = r.get("currentUserFullname")
            date_mod_str = r.get("dateModified")
            epoch_mod = parse_date_to_epoch(date_mod_str)
            
            # Map indices
            reg_idx = get_region_idx(r, "SULAWESI TENGAH")
            pet_idx = get_petugas_idx(username, fullname)
            stat_idx = get_status_idx(status)
            
            # Survey Type: 0 for se_umum, 1 for se_ub
            compressed_targets.append([
                tid, code_id, name, stat_idx, pet_idx, reg_idx, epoch_mod, 0
            ])
            
            # Daily aggregation for non-OPEN statuses (Submissions/Approvals)
            status_upper = status.upper()
            if status_upper != "OPEN" and epoch_mod > 0:
                wita_date = get_wita_date_string(epoch_mod)
                if wita_date:
                    # Get kabupaten name for grouping
                    kab_name = regions_list[reg_idx][1]
                    agg_key = (wita_date, kab_name, "se_umum")
                    daily_counts_dict[agg_key] = daily_counts_dict.get(agg_key, 0) + 1
                    
        # Process SE UB
        for r in raw_se_ub_data:
            tid = r.get("id")
            code_id = r.get("codeIdentity")
            name = r.get("data1") or "-"
            status = r.get("assignmentStatusAlias") or "OPEN"
            username = r.get("currentUserUsername")
            fullname = r.get("currentUserFullname")
            date_mod_str = r.get("dateModified")
            epoch_mod = parse_date_to_epoch(date_mod_str)
            
            reg_idx = get_region_idx(r, "SULAWESI TENGAH")
            pet_idx = get_petugas_idx(username, fullname)
            stat_idx = get_status_idx(status)
            
            compressed_targets.append([
                tid, code_id, name, stat_idx, pet_idx, reg_idx, epoch_mod, 1
            ])
            
            status_upper = status.upper()
            if status_upper != "OPEN" and epoch_mod > 0:
                wita_date = get_wita_date_string(epoch_mod)
                if wita_date:
                    kab_name = regions_list[reg_idx][1]
                    agg_key = (wita_date, kab_name, "se_ub")
                    daily_counts_dict[agg_key] = daily_counts_dict.get(agg_key, 0) + 1

        # Flatten daily counts
        daily_stats_data = []
        for (date_str, kab_name, s_type), cnt in daily_counts_dict.items():
            daily_stats_data.append({
                "date": date_str,
                "kab_name": kab_name,
                "survey_type": s_type,
                "count": cnt
            })
            
        print(f"Compressed {len(compressed_targets)} targets.")
        print(f"Generated {len(daily_stats_data)} daily submission summary rows.")
        
        # Save payload
        granular_payload = {
            "updated_at": datetime.now().isoformat(),
            "regions": regions_list,
            "petugas": petugas_list,
            "statuses": statuses_list,
            "targets": compressed_targets,
            "remarks": remarks_dict
        }
        
        # Calculate size before compression
        raw_json_str = json.dumps(granular_payload, ensure_ascii=False)
        raw_size_mb = len(raw_json_str.encode('utf-8')) / (1024 * 1024)
        print(f"Raw payload size: {raw_size_mb:.2f} MB")
        
        # Compress using gzip and encode base64
        compressed_bytes = gzip.compress(raw_json_str.encode('utf-8'))
        base64_str = base64.b64encode(compressed_bytes).decode('utf-8')
        compressed_size_mb = len(base64_str.encode('utf-8')) / (1024 * 1024)
        print(f"Gzipped + Base64 payload size: {compressed_size_mb:.2f} MB (saved ~{((1 - compressed_size_mb/raw_size_mb)*100):.1f}%)")
        
        # Local cache save
        with open("granular_assignments.json", "w", encoding="utf-8") as f:
            json.dump({"compressed_data": base64_str, "updated_at": datetime.now().isoformat()}, f, indent=2)
        print("✅ Data disimpan secara lokal ke granular_assignments.json")
        
        with open("daily_submission_stats.json", "w", encoding="utf-8") as f:
            json.dump(daily_stats_data, f, indent=2)
        print("✅ Data timeline harian disimpan secara lokal ke daily_submission_stats.json")
        
        # Write Javascript files for fallback local load
        with open("granular_assignments.js", "w", encoding="utf-8") as f:
            f.write(f"window.COMPRESSED_GRANULAR_ASSIGNMENTS = '{base64_str}';\n")
            f.write(f"window.GRANULAR_ASSIGNMENTS_UPDATED_AT = '{datetime.now().isoformat()}';\n")
        print("✅ Data disimpan secara lokal ke granular_assignments.js")
        
        with open("daily_submission_stats.js", "w", encoding="utf-8") as f:
            f.write(f"window.DAILY_SUBMISSION_STATS = {json.dumps(daily_stats_data, indent=2)};\n")
        print("✅ Data timeline harian disimpan secara lokal ke daily_submission_stats.js")

        # 4. Upload to Supabase
        if supabase:
            try:
                print("Mengunggah data ke Supabase...")
                # 1. Update daily_submission_stats
                supabase.table("dashboard_store").delete().eq("key", "daily_submission_stats").execute()
                supabase.table("dashboard_store").insert({"key": "daily_submission_stats", "value": daily_stats_data}).execute()
                print(" -> Success: daily_submission_stats uploaded.")
                
                # 2. Update granular_assignments
                granular_store_value = {
                    "compressed_data": base64_str,
                    "updated_at": datetime.now().isoformat()
                }
                supabase.table("dashboard_store").delete().eq("key", "granular_assignments").execute()
                supabase.table("dashboard_store").insert({"key": "granular_assignments", "value": granular_store_value}).execute()
                print(" -> Success: granular_assignments uploaded.")
                
                # 3. Save daily snapshots for granular and stats
                today_str = datetime.now().strftime("%Y-%m-%d")
                daily_stats_key = f"daily_submission_stats:{today_str}"
                supabase.table("dashboard_store").delete().eq("key", daily_stats_key).execute()
                supabase.table("dashboard_store").insert({"key": daily_stats_key, "value": daily_stats_data}).execute()
                
                daily_granular_key = f"granular_assignments:{today_str}"
                supabase.table("dashboard_store").delete().eq("key", daily_granular_key).execute()
                supabase.table("dashboard_store").insert({"key": daily_granular_key, "value": granular_store_value}).execute()
                
                print(f" -> Success: Daily snapshots ({today_str}) uploaded.")
                print("✅ SINKRONISASI SUPABASE BERHASIL!")
                
            except Exception as e:
                print(f"[ERROR] Gagal mengunggah ke Supabase: {e}")
                
        if browser:
            await browser.close()

        # 5. Cleanup Browser (OOM Mitigation)
        print("\n[CLEANUP] Membersihkan resource Playwright/Chrome untuk mencegah Memory Leak...")
        try:
            if page: await page.close()
            if context: await context.close()
            if browser: await browser.close()
            print(" -> Success: Browser resources cleaned up.")
        except Exception as e:
            print(f" -> Warning: Gagal membersihkan browser resources: {e}")

if __name__ == "__main__":
    asyncio.run(scrape_all_granular())
