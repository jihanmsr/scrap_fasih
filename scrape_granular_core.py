import asyncio
import copy
import json
import os
import sys
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
            return s.connect_ex(('127.0.0.1', port)) == 0
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
        ignore_default_args=["--enable-automation"],
        args=["--no-first-run", "--no-default-browser-check", "--disable-blink-features=AutomationControlled"]
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

session_refresh_lock = asyncio.Lock()

async def refresh_session_if_needed(client, page, context):
    async with session_refresh_lock:
        cookies = await context.cookies()
        cookie_dict = {c["name"]: c["value"] for c in cookies}
        token_raw = cookie_dict.get("XSRF-TOKEN", "")
        from urllib.parse import unquote
        token = unquote(token_raw) if token_raw else ""
        
        client_token = client.headers.get("X-XSRF-TOKEN")
        
        is_valid = False
        if token:
            is_valid = await check_session_valid(page, token)
            
        if is_valid:
            if client_token != token:
                print("[INFO] Browser session is valid, updating HTTPX client with new token/cookies.", flush=True)
                client.headers.update({"X-XSRF-TOKEN": token})
                client.cookies.clear()
                for c in cookies:
                    client.cookies.set(
                        c['name'],
                        c['value'],
                        domain=c.get('domain', 'fasih-sm.bps.go.id'),
                        path=c.get('path', '/')
                    )
                return True
            return False
            
        print("[WARNING] Sesi FASIH tidak valid atau telah kedaluwarsa. Mencoba memicu pembaruan cookie via page reload...", flush=True)
        
        attempt_count = 0
        while True:
            attempt_count += 1
            try:
                print(f"[INFO] Reloading page (attempt {attempt_count})...", flush=True)
                await page.reload(timeout=60000, wait_until="domcontentloaded")
                await asyncio.sleep(2)
            except Exception as e:
                print(f"[WARNING] Gagal memuat ulang halaman: {e}", flush=True)
                
            cookies = await context.cookies()
            cookie_dict = {c["name"]: c["value"] for c in cookies}
            token_raw = cookie_dict.get("XSRF-TOKEN", "")
            token = unquote(token_raw) if token_raw else ""
            
            if token and await check_session_valid(page, token):
                print("[SUCCESS] Sesi berhasil diperbarui dan diverifikasi!", flush=True)
                client.headers.update({"X-XSRF-TOKEN": token})
                client.cookies.clear()
                for c in cookies:
                    client.cookies.set(
                        c['name'],
                        c['value'],
                        domain=c.get('domain', 'fasih-sm.bps.go.id'),
                        path=c.get('path', '/')
                    )
                return True
                
            print("\n==============================================================")
            print("[WARNING] Harap LOGIN atau REFRESH halaman FASIH di browser Chrome Anda.")
            print("Mencoba mendeteksi secara otomatis setiap 15 detik...")
            print("==============================================================\n", flush=True)
            await asyncio.sleep(15)

async def safe_post(client, page, context, sem, url, payload, max_retries=4):
    for attempt in range(max_retries):
        is_session_issue = False
        async with sem:
            try:
                r = await client.post(url, json=payload)
                if r.status_code == 200:
                    try:
                        res = r.json()
                        if isinstance(res, dict) and ("searchData" in res or "searchAggregation" in res or "totalHit" in res):
                            return res
                    except Exception:
                        pass
                print(f"[WARNING] POST response invalid (status {r.status_code}). Possible session expiration.", flush=True)
                is_session_issue = (
                    r.status_code in [401, 403] or
                    "login" in str(r.url).lower() or
                    (r.status_code == 200 and not r.text.strip().startswith("{"))
                )
            except Exception as e:
                print(f"[WARNING] POST request exception: {e}", flush=True)
                is_session_issue = True
        
        if attempt < max_retries - 1:
            if is_session_issue:
                refreshed = await refresh_session_if_needed(client, page, context)
                if refreshed:
                    await asyncio.sleep(1.0)
                else:
                    await asyncio.sleep(5.0)
            else:
                await asyncio.sleep(1.0)
                
    return {"_error": "Max retries exceeded or session invalid"}

async def safe_get(client, page, context, sem, url, max_retries=3):
    for attempt in range(max_retries):
        is_session_issue = False
        async with sem:
            try:
                r = await client.get(url)
                if r.status_code == 200:
                    try:
                        return r.json()
                    except Exception:
                        pass
                elif r.status_code == 404:
                    return None
                    
                print(f"[WARNING] GET response invalid (status {r.status_code}). Possible session expiration.", flush=True)
                is_session_issue = (
                    r.status_code in [401, 403] or
                    "login" in str(r.url).lower() or
                    (r.status_code == 200 and not r.text.strip().startswith("["))
                )
            except Exception as e:
                print(f"[WARNING] GET request exception: {e}", flush=True)
                is_session_issue = True
                
        if attempt < max_retries - 1:
            if is_session_issue:
                refreshed = await refresh_session_if_needed(client, page, context)
                if refreshed:
                    await asyncio.sleep(1.0)
                else:
                    await asyncio.sleep(5.0)
            else:
                await asyncio.sleep(1.0)
                
    return None

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

async def fetch_kab_granular(client, page, context, survey_period_id, region1_id, kab_id, kab_name, label, sem):
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
        
        res = await safe_post(client, page, context, sem, DATATABLE_URL, payload)
        
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

async def fetch_desa_granular(client, page, context, survey_period_id, region1_id, kab_id, kec_id, desa_id, kab_name, kec_name, desa_name, label, sem, sls_list=None):
    global completed_desas, total_desas
    
    start = 0
    length = 1000
    all_records = []
    
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
        "start": start,
        "length": length,
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
    
    res = await safe_post(client, page, context, sem, DATATABLE_URL, payload)
            
    if not res or "_error" in res or "searchData" not in res:
        print(f"      [ERROR] Gagal ambil page data {start} untuk Desa {desa_name}.")
    else:
        records = res["searchData"]
        all_records.extend(records)
        total_hit = res.get("totalHit", 0)
        
        # Check if totalHit > 1000 and we have a valid sls_list to split the query
        if total_hit > 1000 and sls_list:
            print(f"      [INFO] Desa {desa_name} memiliki {total_hit} target (>1000). Menggunakan query split per SLS untuk menghindari limitasi paging BPS.", flush=True)
            
            # Map target ID -> record to avoid duplicates
            records_dict = {r["id"]: r for r in all_records}
            
            # Fetch for each SLS
            for sls in sls_list:
                sls_id = sls.get("sls_id")
                sls_name = sls.get("sls_name", "-")
                if not sls_id:
                    continue
                    
                start_sls = 0
                while True:
                    payload_sls = {
                        "start": start_sls,
                        "length": length,
                        "columns": columns_payload,
                        "order": [],
                        "search": {"value": "", "regex": False},
                        "assignmentExtraParam": {
                            "region1Id": region1_id,
                            "region2Id": kab_id,
                            "region3Id": kec_id,
                            "region4Id": desa_id,
                            "region5Id": sls_id,
                            "surveyPeriodId": survey_period_id,
                            "assignmentErrorStatusType": -1,
                            "filterTargetType": ""
                        }
                    }
                    
                    res_sls = await safe_post(client, page, context, sem, DATATABLE_URL, payload_sls)
                            
                    if not res_sls or "_error" in res_sls or "searchData" not in res_sls:
                        print(f"      [ERROR] Gagal ambil page data {start_sls} untuk SLS {sls_name} di Desa {desa_name}.")
                        break
                        
                    records_sls = res_sls["searchData"]
                    if not records_sls:
                        break
                        
                    for r in records_sls:
                        records_dict[r["id"]] = r
                        
                    if len(records_sls) < length or len(records_dict) >= total_hit:
                        break
                        
                    start_sls += length
            
            all_records = list(records_dict.values())
            print(f"      [SUCCESS] Desa {desa_name}: Berhasil menarik {len(all_records)} / {total_hit} target.", flush=True)
            
        elif total_hit > 1000:
            print(f"      [WARNING] Desa {desa_name} memiliki {total_hit} target (>1000), tetapi tidak ada sls_list untuk split query!", flush=True)
            # Try paging as fallback
            start = length
            while True:
                payload["start"] = start
                res = await safe_post(client, page, context, sem, DATATABLE_URL, payload)
                        
                if not res or "_error" in res or "searchData" not in res:
                    break
                records = res["searchData"]
                if not records:
                    break
                all_records.extend(records)
                if len(records) < length or len(all_records) >= total_hit:
                    break
                start += length
 
    async with progress_lock:
        completed_desas += 1
        if completed_desas % 50 == 0 or completed_desas == total_desas:
            print(f"      [PROGRESS] SE Umum: Downloaded {completed_desas} / {total_desas} desas...", flush=True)
            
    return all_records

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
        lvl6 = lvl5.get("level6", {}) or {}
        
        kab_code = lvl2.get("fullCode") or ""
        kab_name = lvl2.get("name") or fallback_kab_name
        kec_code = lvl3.get("fullCode") or ""
        kec_name = lvl3.get("name") or "-"
        desa_code = lvl4.get("fullCode") or ""
        desa_name = lvl4.get("name") or "-"
        sls_code = lvl5.get("fullCode") or ""
        sls_name = lvl5.get("name") or "-"
        subsls_code = lvl6.get("fullCode") or ""
        subsls_name = lvl6.get("name") or "-"
        
        key = (kab_code, kab_name, kec_code, kec_name, desa_code, desa_name, sls_code, sls_name, subsls_code, subsls_name)
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
    
    # 1. De-duplicate raw_se_umum_data
    seen_umum = {}
    for r in raw_se_umum_data:
        tid = r.get("id")
        if not tid:
            continue
        if tid not in seen_umum:
            seen_umum[tid] = r
        else:
            old_r = seen_umum[tid]
            old_status = str(old_r.get("assignmentStatusAlias", "OPEN")).strip().upper()
            new_status = str(r.get("assignmentStatusAlias", "OPEN")).strip().upper()
            if new_status != "OPEN" and old_status == "OPEN":
                seen_umum[tid] = r
            elif old_status != "OPEN" and new_status == "OPEN":
                pass
            else:
                old_epoch = parse_date_to_epoch(old_r.get("dateModified"))
                new_epoch = parse_date_to_epoch(r.get("dateModified"))
                if new_epoch > old_epoch:
                    seen_umum[tid] = r
                    
    # 2. Process SE Umum
    for r in seen_umum.values():
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
        
        pengawas_id = None
        for resp in r.get("assignmentResponsibility", []):
            if resp.get("currentSurveyRoleName") == "Pengawas":
                pengawas_id = resp.get("currentUserId")
                break
        
        pengawas_username = "-"
        pengawas_fullname = "-"
        if pengawas_id and pengawas_id in users_mapping:
            pengawas_username = users_mapping[pengawas_id]["username"]
            pengawas_fullname = users_mapping[pengawas_id]["fullname"]
            
        pengawas_idx = get_petugas_idx(pengawas_username, pengawas_fullname)
        
        compressed_targets.append([
            tid, code_id, name, stat_idx, pet_idx, reg_idx, epoch_mod, 0, pengawas_idx
        ])
        
        status_upper = status.upper()
        if status_upper != "OPEN" and status_upper != "DRAFT" and epoch_mod > 0:
            wita_date = get_wita_date_string(epoch_mod)
            if wita_date:
                kab_name = regions_list[reg_idx][1]
                agg_key = (wita_date, kab_name, "se_umum")
                daily_counts_dict[agg_key] = daily_counts_dict.get(agg_key, 0) + 1
                
    # 3. De-duplicate raw_se_ub_data
    seen_ub = {}
    for r in raw_se_ub_data:
        tid = r.get("id")
        if not tid:
            continue
        if tid not in seen_ub:
            seen_ub[tid] = r
        else:
            old_r = seen_ub[tid]
            old_status = str(old_r.get("assignmentStatusAlias", "OPEN")).strip().upper()
            new_status = str(r.get("assignmentStatusAlias", "OPEN")).strip().upper()
            if new_status != "OPEN" and old_status == "OPEN":
                seen_ub[tid] = r
            elif old_status != "OPEN" and new_status == "OPEN":
                pass
            else:
                old_epoch = parse_date_to_epoch(old_r.get("dateModified"))
                new_epoch = parse_date_to_epoch(r.get("dateModified"))
                if new_epoch > old_epoch:
                    seen_ub[tid] = r
                    
    # 4. Process SE UB
    for r in seen_ub.values():
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
        
        pengawas_id = None
        for resp in r.get("assignmentResponsibility", []):
            if resp.get("currentSurveyRoleName") == "Pengawas":
                pengawas_id = resp.get("currentUserId")
                break
        
        pengawas_username = "-"
        pengawas_fullname = "-"
        if pengawas_id and pengawas_id in users_mapping:
            pengawas_username = users_mapping[pengawas_id]["username"]
            pengawas_fullname = users_mapping[pengawas_id]["fullname"]
            
        pengawas_idx = get_petugas_idx(pengawas_username, pengawas_fullname)
        
        compressed_targets.append([
            tid, code_id, name, stat_idx, pet_idx, reg_idx, epoch_mod, 1, pengawas_idx
        ])
        
        status_upper = status.upper()
        if status_upper != "OPEN" and status_upper != "DRAFT" and epoch_mod > 0:
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
    
    # Local cache save using absolute paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    stats_json_path = os.path.join(script_dir, "daily_submission_stats.json")
    with open(stats_json_path, "w", encoding="utf-8") as f:
        json.dump(daily_stats_data, f, indent=2)
        
    # Write Javascript files for fallback local load
    stats_js_path = os.path.join(script_dir, "daily_submission_stats.js")
    with open(stats_js_path, "w", encoding="utf-8") as f:
        f.write(f"window.DAILY_SUBMISSION_STATS = {json.dumps(daily_stats_data, indent=2)};\n")
    print(f"✅ [INTERMEDIATE SAVE SUCCESS] Progress berhasil disimpan ke {stats_js_path}.\n", flush=True)

async def scrape_all_granular(survey_type_filter=None, kab_code_filter=None):
    print("[START] Mulai proses penarikan seluruh data secara granular...")
    global users_mapping
    users_mapping = {}
    try:
        import json
        script_dir = os.path.dirname(os.path.abspath(__file__))
        users_mapping_path = os.path.join(script_dir, "users_mapping.json")
        with open(users_mapping_path, "r", encoding="utf-8") as f:
            users_mapping = json.load(f)
    except:
        pass
    
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
                try:
                    print("[INFO] Mencoba memuat ulang halaman untuk memicu pembaruan cookie...")
                    await page.reload(timeout=120000, wait_until="networkidle")
                except Exception as e:
                    print(f"[WARNING] Gagal memuat ulang halaman: {e}", flush=True)
                    
            await asyncio.sleep(15)
            cookies = await context.cookies()
            cookie_dict = {c["name"]: c["value"] for c in cookies}
            token_raw = cookie_dict.get("XSRF-TOKEN", "")
            token = unquote(token_raw) if token_raw else ""
            
        print("[SUCCESS] Sesi terverifikasi! Memulai scraping data granular...")
        
        # We will loop through the configurations

        # Apply filters
        if survey_type_filter == "se_ub":
            SURVEY_CONFIGS[0]["kab_region_map"] = {}
        if survey_type_filter == "se_umum":
            SURVEY_CONFIGS[1]["kab_region_map"] = {}
            
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
            if not survey_type_filter or survey_type_filter == "se_umum":
                print(f"\n--- Memulai Scraping {cfg_umum['label'].upper()} ---")
            
            try:
                script_dir = os.path.dirname(os.path.abspath(__file__))
                region_map_full_path = os.path.join(script_dir, "region_map_sulteng_full.json")
                with open(region_map_full_path, "r") as f:
                    region_map_full = json.load(f)
            except Exception as e:
                print(f"[ERROR] Gagal memuat region_map_sulteng_full.json: {e}")
                region_map_full = {}
                
            sem_umum = asyncio.Semaphore(15)
            tasks_umum = []
            
            kab_dict_to_process = {}
            for k, v in cfg_umum["kab_region_map"].items():
                if kab_code_filter and k != kab_code_filter:
                    continue
                kab_dict_to_process[k] = v
                
            for kab_code, kab_cfg in kab_dict_to_process.items():
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
                                page,
                                context,
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
 
            kab_dict_ub = {}
            for k, v in cfg_ub["kab_region_map"].items():
                if kab_code_filter and k != kab_code_filter:
                    continue
                kab_dict_ub[k] = v
            tasks_ub = [
                fetch_kab_granular(client, page, context, cfg_ub["survey_period_id"], cfg_ub["region1_id"], kab_cfg["id"], kab_cfg["name"], "SE UB", sem)
                for kab_id, kab_cfg in kab_dict_ub.items()
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
                    data = await safe_get(client, page, context, sem_remarks, url)
                    if data and isinstance(data, list) and len(data) > 0:
                        # Ambil remark terbaru / gabungkan
                        remarks_texts = []
                        for rm in data:
                            txt = rm.get("remark", "")
                            by = rm.get("currentUserFullname", "Pengawas")
                            if txt: remarks_texts.append(f"{by}: {txt}")
                        if remarks_texts:
                            remarks_dict[tid] = " | ".join(remarks_texts)
                
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
            lvl6 = lvl5.get("level6", {}) or {}
            
            kab_code = lvl2.get("fullCode") or ""
            kab_name = lvl2.get("name") or fallback_kab_name
            kec_code = lvl3.get("fullCode") or ""
            kec_name = lvl3.get("name") or "-"
            desa_code = lvl4.get("fullCode") or ""
            desa_name = lvl4.get("name") or "-"
            sls_code = lvl5.get("fullCode") or ""
            sls_name = lvl5.get("name") or "-"
            subsls_code = lvl6.get("fullCode") or ""
            subsls_name = lvl6.get("name") or "-"
            
            key = (kab_code, kab_name, kec_code, kec_name, desa_code, desa_name, sls_code, sls_name, subsls_code, subsls_name)
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
        
        # 1. De-duplicate raw_se_umum_data
        seen_umum = {}
        for r in raw_se_umum_data:
            tid = r.get("id")
            if not tid:
                continue
            if tid not in seen_umum:
                seen_umum[tid] = r
            else:
                old_r = seen_umum[tid]
                old_status = str(old_r.get("assignmentStatusAlias", "OPEN")).strip().upper()
                new_status = str(r.get("assignmentStatusAlias", "OPEN")).strip().upper()
                if new_status != "OPEN" and old_status == "OPEN":
                    seen_umum[tid] = r
                elif old_status != "OPEN" and new_status == "OPEN":
                    pass
                else:
                    old_epoch = parse_date_to_epoch(old_r.get("dateModified"))
                    new_epoch = parse_date_to_epoch(r.get("dateModified"))
                    if new_epoch > old_epoch:
                        seen_umum[tid] = r
                        
        # 2. Process SE Umum
        for r in seen_umum.values():
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
            if status_upper != "OPEN" and status_upper != "DRAFT" and epoch_mod > 0:
                wita_date = get_wita_date_string(epoch_mod)
                if wita_date:
                    # Get kabupaten name for grouping
                    kab_name = regions_list[reg_idx][1]
                    agg_key = (wita_date, kab_name, "se_umum")
                    daily_counts_dict[agg_key] = daily_counts_dict.get(agg_key, 0) + 1
                    
        # 3. De-duplicate raw_se_ub_data
        seen_ub = {}
        for r in raw_se_ub_data:
            tid = r.get("id")
            if not tid:
                continue
            if tid not in seen_ub:
                seen_ub[tid] = r
            else:
                old_r = seen_ub[tid]
                old_status = str(old_r.get("assignmentStatusAlias", "OPEN")).strip().upper()
                new_status = str(r.get("assignmentStatusAlias", "OPEN")).strip().upper()
                if new_status != "OPEN" and old_status == "OPEN":
                    seen_ub[tid] = r
                elif old_status != "OPEN" and new_status == "OPEN":
                    pass
                else:
                    old_epoch = parse_date_to_epoch(old_r.get("dateModified"))
                    new_epoch = parse_date_to_epoch(r.get("dateModified"))
                    if new_epoch > old_epoch:
                        seen_ub[tid] = r
                        
        # 4. Process SE UB
        for r in seen_ub.values():
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
            if status_upper != "OPEN" and status_upper != "DRAFT" and epoch_mod > 0:
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
        suffix = ""
        if survey_type_filter: suffix += f"_{survey_type_filter}"
        if kab_code_filter: suffix += f"_{kab_code_filter}"
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        out_filename = os.path.join(script_dir, f"granular_assignments{suffix}.json")
        
        with open(out_filename, "w", encoding="utf-8") as f:
            json.dump({
                "compressed_data": base64_str, 
                "updated_at": datetime.now().isoformat(),
                "survey_type_filter": survey_type_filter,
                "kab_code_filter": kab_code_filter
            }, f, indent=2)
        print(f"✅ Data disimpan secara lokal ke {out_filename}")
        
        # Write JS fallback version for file:// protocol
        if suffix:
            var_suffix = suffix.strip("_").upper()
            js_out_filename = os.path.join(script_dir, f"granular_assignments{suffix}.js")
            with open(js_out_filename, "w", encoding="utf-8") as f:
                f.write(f"window.PARTITION_{var_suffix} = {{\n")
                f.write(f"  \"compressed_data\": \"{base64_str}\",\n")
                f.write(f"  \"updated_at\": \"{datetime.now().isoformat()}\"\n")
                f.write("};\n")
            print(f"✅ Data JS disimpan secara lokal ke {js_out_filename}")
            
        # JIKA INI ADALAH SCRAPING PARSIAL, KITA PANGGIL MERGE_GRANULARS.PY!
        if suffix:
            import subprocess
            print("Memanggil merge_granulars.py untuk menggabungkan partisi...")
            subprocess.Popen([sys.executable, os.path.join(script_dir, "merge_granulars.py")], cwd=script_dir)
            return # skip uploading partial to supabase here, merge_granulars will do it!

        stats_json_path = os.path.join(script_dir, "daily_submission_stats.json")
        with open(stats_json_path, "w", encoding="utf-8") as f:
            json.dump(daily_stats_data, f, indent=2)
        print(f"✅ Data timeline harian disimpan secara lokal ke {stats_json_path}")
        
        # Write Javascript files for fallback local load
        granular_js_path = os.path.join(script_dir, "granular_assignments.js")
        with open(granular_js_path, "w", encoding="utf-8") as f:
            f.write("window.COMPRESSED_GRANULAR_ASSIGNMENTS = [\n")
            chunk_size = 500000
            for i in range(0, len(base64_str), chunk_size):
                chunk = base64_str[i:i+chunk_size]
                f.write(f"  '{chunk}',\n")
            f.write("].join('');\n")
            f.write(f"window.GRANULAR_ASSIGNMENTS_UPDATED_AT = '{datetime.now().isoformat()}';\n")
        print(f"✅ Data disimpan secara lokal ke {granular_js_path}")
        
        stats_js_path = os.path.join(script_dir, "daily_submission_stats.js")
        with open(stats_js_path, "w", encoding="utf-8") as f:
            f.write(f"window.DAILY_SUBMISSION_STATS = {json.dumps(daily_stats_data, indent=2)};\n")
        print(f"✅ Data timeline harian disimpan secara lokal ke {stats_js_path}")

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
                supabase.table("dashboard_store").upsert({"key": "granular_assignments", "value": granular_store_value}).execute()
                print(" -> Success: granular_assignments uploaded.")
                
                # 3. Save daily snapshots for granular and stats
                today_str = datetime.now().strftime("%Y-%m-%d")
                daily_stats_key = f"daily_submission_stats:{today_str}"
                supabase.table("dashboard_store").delete().eq("key", daily_stats_key).execute()
                supabase.table("dashboard_store").insert({"key": daily_stats_key, "value": daily_stats_data}).execute()
                
                daily_granular_key = f"granular_assignments:{today_str}"
                supabase.table("dashboard_store").upsert({"key": daily_granular_key, "value": granular_store_value}).execute()
                
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
    import sys
    survey_filter = sys.argv[1] if len(sys.argv) > 1 else None
    kab_filter = sys.argv[2] if len(sys.argv) > 2 else None
    
    if survey_filter == "all":
        survey_filter = None
    if kab_filter == "all":
        kab_filter = None
        
    asyncio.run(scrape_all_granular(survey_filter, kab_filter))

