import asyncio
import json
import os
import time
import socket
import subprocess
import shutil
import re
from datetime import datetime
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
        print("[INFO] Koneksi Supabase berhasil diinisialisasi untuk scrape_assign.")
    except Exception as e:
        print(f"[ERROR] Gagal menginisialisasi Supabase di scrape_assign: {e}")

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
            except Exception:
                pass

def launch_chrome_if_needed(port=9222):
    if check_port_open(9223) or check_port_open(9222):
        print("[INFO] Chrome remote debugging aktif.")
        return
    
    print("[INFO] Meluncurkan Chrome browser...")
    chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    
    lock_file = os.path.join(USER_DATA_DIR, "SingletonLock")
    if os.path.lexists(lock_file):
        try: os.remove(lock_file)
        except Exception: pass
    
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
            return
    print("[ERROR] Gagal mendeteksi port 9222.")

KAB_MAP = {
    "7201": "[01] BANGGAI KEPULAUAN", "7202": "[02] BANGGAI", "7203": "[03] MOROWALI",
    "7204": "[04] POSO", "7205": "[05] DONGGALA", "7206": "[06] TOLI-TOLI",
    "7207": "[07] BUOL", "7208": "[08] PARIGI MOUTONG", "7209": "[09] TOJO UNA-UNA",
    "7210": "[10] SIGI", "7211": "[11] BANGGAI LAUT", "7212": "[12] MOROWALI UTARA",
    "7271": "[71] PALU"
}

SURVEY_CONFIGS = [
    {
        "label": "SE Umum",
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
        "label": "SE UB",
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
REPORT_URL    = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/report-user-assignment"

# Membaca hasil mapping UUID Kecamatan
try:
    with open("region_map_sulteng.json", "r") as f:
        REGION_MAP = json.load(f)
except Exception as e:
    REGION_MAP = {}

# Membaca hasil mapping lengkap Kabupaten -> Kecamatan -> Desa -> SLS
try:
    with open("region_map_sulteng_full.json", "r") as f:
        REGION_MAP_FULL = json.load(f)
except Exception as e:
    print("[ERROR] File region_map_sulteng_full.json tidak ditemukan. Harap jalankan scrape_regions_full.py terlebih dahulu.")
    REGION_MAP_FULL = {}

async def evaluate_fetch_with_retry(page, token, url, payload, timeout=20.0):
    kec_info = payload.get("assignmentExtraParam", {}).get("region3Id", "unknown")
    print(f"      [DEBUG-API] posting to {url} for kec {kec_info}...")

    for attempt in range(3):
        try:
            res = await page.evaluate("""
                async ({url, payload, token, timeoutMs}) => {
                    const controller = new AbortController();
                    const id = setTimeout(() => controller.abort(), timeoutMs);
                    try {
                        const r = await fetch(url, {
                            method: "POST",
                            headers: {
                                "Content-Type": "application/json",
                                "X-XSRF-TOKEN": token
                            },
                            body: JSON.stringify(payload),
                            signal: controller.signal
                        });
                        clearTimeout(id);
                        if (!r.ok) return { _error: `HTTP ${r.status}` };
                        return await r.json();
                    } catch (e) {
                        clearTimeout(id);
                        return { _error: e.toString() };
                    }
                }
            """, {"url": url, "payload": payload, "token": token, "timeoutMs": timeout * 1000})

            if res and isinstance(res, dict) and "_error" in res:
                print(f"[WARNING] evaluate_fetch_with_retry attempt {attempt+1} failed for {kec_info}: {res['_error']}")
                await asyncio.sleep(2)
            elif res:
                print(f"      [DEBUG-API] response received for {kec_info}")
                return res
        except Exception as e:
            print(f"[WARNING] evaluate_fetch_with_retry attempt {attempt+1} failed for {kec_info}: {type(e).__name__} - {e}")
            await asyncio.sleep(2)
    return {"error": "Max retries exceeded"}

async def fetch_report(page, token, survey_period_id, region1_id, label):
    print(f"\n[{label}] Menarik rekap RESMI tingkat Kabupaten dari REPORT API...")
    payload = {"surveyPeriodId": survey_period_id, "region1Id": region1_id}
    res = await evaluate_fetch_with_retry(page, token, REPORT_URL, payload, timeout=90.0)


    if not res or (isinstance(res, dict) and "error" in res):
        print(f"[ERROR] [{label}] Gagal tarik laporan resmi. Detail: {res}")
        return []

    result = []
    for item in res:
        kode_kab = item.get("label")
        if not kode_kab or kode_kab not in KAB_MAP: continue
        values = item.get("values", [])
        total = assigned = have_not = 0
        for v in values:
            lbl = v.get("label", "").lower()
            val = v.get("value", 0)
            if lbl == "total": total = val
            elif lbl == "assigned": assigned = val
            elif lbl == "have-not-assigned": have_not = val
            
        result.append({
            "kode_kab": kode_kab, 
            "nama_kab": KAB_MAP[kode_kab],
            "total": total, 
            "assigned": assigned,
            "have_not_assigned": have_not, 
            "timestamp": datetime.now().isoformat()
        })
        print(f"  -> {KAB_MAP[kode_kab]}: {total} Target | {assigned} Diassign")
        
    return sorted(result, key=lambda x: x["kode_kab"])

async def fetch_sls_by_kecamatan(page, token, survey_period_id, region1_id, kab_region_map, label):
    print(f"\n[{label}] Menarik rincian per SLS dari DATATABLE API (By Kecamatan Paralel)...")
    sls_dict = {}

    # Inisialisasi semua SLS dari region_map_sulteng_full.json agar terdaftar lengkap
    for kab_code, kab_cfg in kab_region_map.items():
        kab_name = kab_cfg["name"]
        kab_data = REGION_MAP_FULL.get("kabupaten", {}).get(kab_code, {})
        if not kab_data: continue
        
        for kec_code, kec_data in kab_data.get("kecamatan", {}).items():
            kec_name = kec_data.get("kec_name")
            for desa_code, desa_data in kec_data.get("desa", {}).items():
                desa_name = desa_data.get("desa_name")
                for sls in desa_data.get("sls", []):
                    sls_code = sls["sls_full_code"]
                    sls_dict[sls_code] = {
                        "sls_code": sls_code,
                        "sls_name": sls["sls_name"],
                        "desa_name": desa_name,
                        "kec_name": kec_name,
                        "kab_name": kab_name,
                        "total": 0, "assigned": 0, "unassigned": 0, "sync_count": 0,
                        "officers": set(), "officer_usernames": set()
                    }

    kecs_to_query = []
    for kab_code, kab_cfg in kab_region_map.items():
        kab_name = kab_cfg["name"]
        kecamatan_list = REGION_MAP.get(kab_code, {}).get("kecamatan", [])
        for kec in kecamatan_list:
            kecs_to_query.append({
                "kab_id": kab_cfg["id"],
                "kab_name": kab_name,
                "kec_id": kec["id"],
                "kec_name": kec["name"]
            })

    print(f"  -> Total Kecamatan yang akan di-query: {len(kecs_to_query)}")

    sem = asyncio.Semaphore(3)
    completed = 0

    async def fetch_one_kec(k):
        nonlocal completed
        kec_id = k["kec_id"]
        kab_id = k["kab_id"]
        kab_name = k["kab_name"]
        print(f"      [DEBUG] Starting fetch_one_kec for {k['kec_name']} ({kec_id})")
        
        async def do_fetch():
            start = 0
            length = 1000
            kec_records = []
            while True:
                payload_dt = {
                    "start": start, "length": length, "columns": [{"data": "id"}], "order": [],
                    "search": {"value": "", "regex": False},
                    "assignmentExtraParam": {
                        "region1Id": region1_id, 
                        "region2Id": kab_id,
                        "region3Id": kec_id,
                        "surveyPeriodId": survey_period_id, 
                        "assignmentErrorStatusType": -1, 
                        "filterTargetType": ""
                    }
                }
                for attempt in range(4):
                    try:
                        print(f"      [DEBUG] Waiting for semaphore for {k['kec_name']} ({kec_id}), attempt {attempt+1}")
                        async with sem:
                            print(f"      [DEBUG] Acquired semaphore for {k['kec_name']} ({kec_id})")
                            res_dt = await evaluate_fetch_with_retry(page, token, DATATABLE_URL, payload_dt)
                            await asyncio.sleep(1.0)
                        if res_dt and "searchData" in res_dt:
                            records = res_dt["searchData"]
                            if not records:
                                return kec_records
                            kec_records.extend(records)
                            
                            if len(records) < length:
                                return kec_records
                            start += length
                            if start >= res_dt.get("totalHit", 0):
                                return kec_records
                            break
                        elif res_dt and isinstance(res_dt, dict) and "error" in res_dt:
                            print(f"      [DEBUG] API error for {k['kec_name']} ({kec_id}): {res_dt}")
                            await asyncio.sleep(0.5 * (attempt + 1))
                    except Exception as ex:
                        print(f"      [DEBUG] Exception inside do_fetch for {k['kec_name']} ({kec_id}): {ex}")
                        await asyncio.sleep(0.5 * (attempt + 1))
                else:
                    break
            return kec_records

        res = await do_fetch()
        completed += 1
        if completed % 10 == 0 or completed == len(kecs_to_query):
            print(f"     Progress Kecamatan Datatable API: {completed}/{len(kecs_to_query)} Kecamatan selesai ({completed/len(kecs_to_query)*100:.1f}%)")
        return res

    tasks = [fetch_one_kec(k) for k in kecs_to_query]
    results = await asyncio.gather(*tasks)

    # Aggregate results in main thread
    for idx, kec_records in enumerate(results):
        k = kecs_to_query[idx]
        kab_name = k["kab_name"]
        for comp in kec_records:
            region = comp.get("region", {})
            lvl2 = region.get("level1", {}).get("level2", {}) or {}
            lvl3 = lvl2.get("level3", {}) or {}
            lvl4 = lvl3.get("level4", {}) or {}
            lvl5 = lvl4.get("level5", {}) or {}

            sls_code = lvl5.get("fullCode", "LAINNYA")
            if sls_code not in sls_dict:
                sls_dict[sls_code] = {
                    "sls_code": sls_code, 
                    "sls_name": lvl5.get("name", "LAINNYA"),
                    "desa_name": lvl4.get("name", "LAINNYA"), 
                    "kec_name": lvl3.get("name", "LAINNYA"),
                    "kab_name": kab_name, 
                    "total": 0, "assigned": 0, "unassigned": 0, "sync_count": 0,
                    "officers": set(), "officer_usernames": set()
                }

            sls_dict[sls_code]["total"] += 1
            
            # Check if synced (SUBMITTED or APPROVED status)
            status = comp.get("assignmentStatusAlias", "")
            if status:
                status_upper = status.upper()
                if "SUBMITTED" in status_upper or "APPROVED" in status_upper:
                    sls_dict[sls_code]["sync_count"] += 1

            officer = comp.get("currentUserUsername")
            if officer:
                sls_dict[sls_code]["assigned"] += 1
                ofc_name = comp.get("currentUserFullname", "-")
                sls_dict[sls_code]["officers"].add(f"{ofc_name} ({officer})" if ofc_name != "-" else officer)
                sls_dict[sls_code]["officer_usernames"].add(officer)
            else:
                sls_dict[sls_code]["unassigned"] += 1

    processed_sls = [data for data in sls_dict.values() if data["total"] > 0]
    print(f"     ✅ Berhasil mengenali total {len(processed_sls)} SLS untuk {label}.")
    return processed_sls



async def fetch_sls_by_report_api(context, token, survey_period_id, region1_id, kab_region_map, label):
    print(f"\n[{label}] Menarik rincian per SLS dari REPORT API (Fast)...")
    sls_dict = {}

    # Inisialisasi semua SLS dari region_map_sulteng_full.json agar terdaftar lengkap
    for kab_code, kab_cfg in kab_region_map.items():
        kab_name = kab_cfg["name"]
        kab_data = REGION_MAP_FULL.get("kabupaten", {}).get(kab_code, {})
        if not kab_data: continue
        
        for kec_code, kec_data in kab_data.get("kecamatan", {}).items():
            kec_name = kec_data.get("kec_name")
            for desa_code, desa_data in kec_data.get("desa", {}).items():
                desa_name = desa_data.get("desa_name")
                for sls in desa_data.get("sls", []):
                    sls_code = sls["sls_full_code"]
                    sls_dict[sls_code] = {
                        "sls_code": sls_code,
                        "sls_name": sls["sls_name"],
                        "desa_name": desa_name,
                        "kec_name": kec_name,
                        "kab_name": kab_name,
                        "total": 0, "assigned": 0, "unassigned": 0, "officers": []
                    }

    desas_to_query = []
    for kab_code, kab_cfg in kab_region_map.items():
        kab_data = REGION_MAP_FULL.get("kabupaten", {}).get(kab_code, {})
        if not kab_data: continue
        
        for kec_code, kec_data in kab_data.get("kecamatan", {}).items():
            for desa_code, desa_data in kec_data.get("desa", {}).items():
                desas_to_query.append({
                    "kab_id": kab_cfg["id"],
                    "kec_id": kec_data["kec_id"],
                    "desa_id": desa_data["desa_id"],
                    "desa_code": desa_code
                })
                
    print(f"  -> Total Desa yang akan di-query: {len(desas_to_query)}")
    
    sem = asyncio.Semaphore(3)
    
    async def fetch_one_desa(d):
        payload = {
            "surveyPeriodId": survey_period_id,
            "region1Id": region1_id,
            "region2Id": d["kab_id"],
            "region3Id": d["kec_id"],
            "region4Id": d["desa_id"]
        }
        
        for attempt in range(4):
            page = None
            for p_page in context.pages:
                if "fasih-sm.bps.go.id" in p_page.url:
                    page = p_page
                    break
            if not page:
                page = context.pages[0] if context.pages else await context.new_page()
                
            try:
                async with sem:
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
                    """, {"url": REPORT_URL, "payload": payload, "token": token})
                    
                    if res and isinstance(res, list):
                        return d["desa_code"], res
                    elif res and isinstance(res, dict) and "_error" in res:
                        await asyncio.sleep(0.5 * (attempt + 1))
            except Exception:
                await asyncio.sleep(0.5 * (attempt + 1))
        return d["desa_code"], []

    completed = 0
    results = []
    chunk_size = 50
    for i in range(0, len(desas_to_query), chunk_size):
        chunk = desas_to_query[i:i+chunk_size]
        tasks = [fetch_one_desa(d) for d in chunk]
        chunk_res = await asyncio.gather(*tasks)
        results.extend(chunk_res)
        completed += len(chunk)
        print(f"     Progress Report API: {completed}/{len(desas_to_query)} Desa selesai ({completed/len(desas_to_query)*100:.1f}%)")

    for desa_code, sls_reports in results:
        for item in sls_reports:
            sls_code = item.get("label")
            if not sls_code: continue
            
            values = item.get("values", [])
            total = assigned = unassigned = 0
            for v in values:
                lbl = v.get("label", "").lower()
                val = v.get("value", 0)
                if lbl == "total": total = val
                elif lbl == "assigned": assigned = val
                elif lbl == "have-not-assigned": unassigned = val
                
            if sls_code in sls_dict:
                sls_dict[sls_code]["total"] = total
                sls_dict[sls_code]["assigned"] = assigned
                sls_dict[sls_code]["unassigned"] = unassigned
            else:
                kab_code = desa_code[:4]
                kec_code = desa_code[:7]
                
                kab_name = kab_region_map.get(kab_code, {}).get("name", "LAINNYA")
                kab_data = REGION_MAP_FULL.get("kabupaten", {}).get(kab_code, {})
                kec_name = kab_data.get("kecamatan", {}).get(kec_code, {}).get("kec_name", "LAINNYA")
                desa_name = kab_data.get("kecamatan", {}).get(kec_code, {}).get("desa", {}).get(desa_code, {}).get("desa_name", "LAINNYA")
                
                sls_dict[sls_code] = {
                    "sls_code": sls_code,
                    "sls_name": "SLS BARU",
                    "desa_name": desa_name,
                    "kec_name": kec_name,
                    "kab_name": kab_name,
                    "total": total,
                    "assigned": assigned,
                    "unassigned": unassigned,
                    "officers": []
                }
                
    processed_sls = [data for data in sls_dict.values() if data["total"] > 0]
    print(f"     ✅ Berhasil menarik total {len(processed_sls)} SLS untuk {label}.")
    return processed_sls

async def fetch_sls_ub_via_datatable(page, token, survey_period_id, region1_id, kab_region_map, label):
    print(f"\n[{label}] Menarik rincian per SLS dari DATATABLE API (Provinsi)...")
    sls_dict = {}

    start = 0
    length = 1000
    
    while True:
        payload_dt = {
            "start": start, "length": length, "columns": [{"data": "id"}], "order": [],
            "search": {"value": "", "regex": False},
            "assignmentExtraParam": {
                "region1Id": region1_id, 
                "surveyPeriodId": survey_period_id, 
                "assignmentErrorStatusType": -1, 
                "filterTargetType": ""
            }
        }
        
        res_dt = await evaluate_fetch_with_retry(page, token, DATATABLE_URL, payload_dt, timeout=45.0)

        if not res_dt or "searchData" not in res_dt: break
        records = res_dt["searchData"]
        if not records: break

        for comp in records:
            region = comp.get("region", {})
            lvl1 = region.get("level1", {}) or {}
            lvl2 = lvl1.get("level2", {}) or {}
            lvl3 = lvl2.get("level3", {}) or {}
            lvl4 = lvl3.get("level4", {}) or {}
            lvl5 = lvl4.get("level5", {}) or {}

            # Ambil nama kabupaten
            kab_code = lvl2.get("fullCode")
            kab_name = kab_region_map.get(kab_code, {}).get("name", lvl2.get("name", "LAINNYA"))

            sls_code = lvl5.get("fullCode", "LAINNYA")
            if sls_code not in sls_dict:
                sls_dict[sls_code] = {
                    "sls_code": sls_code, 
                    "sls_name": lvl5.get("name", "LAINNYA"),
                    "desa_name": lvl4.get("name", "LAINNYA"), 
                    "kec_name": lvl3.get("name", "LAINNYA"),
                    "kab_name": kab_name, 
                    "total": 0, "assigned": 0, "unassigned": 0, "sync_count": 0,
                    "officers": set(), "officer_usernames": set()
                }

            sls_dict[sls_code]["total"] += 1
            
            # Check if synced (SUBMITTED or APPROVED status)
            status = comp.get("assignmentStatusAlias", "")
            if status:
                status_upper = status.upper()
                if "SUBMITTED" in status_upper or "APPROVED" in status_upper:
                    sls_dict[sls_code]["sync_count"] += 1

            officer = comp.get("currentUserUsername")
            if officer:
                sls_dict[sls_code]["assigned"] += 1
                ofc_name = comp.get("currentUserFullname", "-")
                sls_dict[sls_code]["officers"].add(f"{ofc_name} ({officer})" if ofc_name != "-" else officer)
                sls_dict[sls_code]["officer_usernames"].add(officer)
            else:
                sls_dict[sls_code]["unassigned"] += 1

        start += length
        if start >= res_dt.get("totalHit", 0): break

    processed_sls = list(sls_dict.values())
    print(f"     ✅ Berhasil menarik total {len(processed_sls)} SLS untuk {label}.")
    return processed_sls

async def fetch_petugas(context, token, survey_period_id, label):
    print(f"\n[{label}] Menarik rincian Petugas dari API...")
    users = []
    page_idx = 0
    size = 100
    
    target_page = None
    for p in context.pages:
        if "fasih-sm.bps.go.id" in p.url:
            target_page = p
            break
    if not target_page:
        target_page = context.pages[0] if context.pages else await context.new_page()

    while True:
        url = f"https://fasih-sm.bps.go.id/app/api/survey-user/api/v1/allocations-view/by-user?surveyPeriodId={survey_period_id}&page={page_idx}&size={size}"
        try:
            res = await target_page.evaluate("""
                async ({url, token}) => {
                    const r = await fetch(url, {
                        headers: { "Accept": "application/json", "X-XSRF-TOKEN": token }
                    });
                    if(!r.ok) return {error: r.statusText, status: r.status};
                    return await r.json();
                }
            """, {"url": url, "token": token})
            
            if "error" in res or not res.get("success"):
                print(f"     [Error] Gagal fetch page {page_idx}: {res}")
                break
                
            data = res.get("data", {})
            content = data.get("content", [])
            users.extend(content)
            
            print(f"     -> Terambil {len(content)} petugas dari page {page_idx+1}/{data.get('totalPages', 1)}")
            
            if data.get("isLast", True):
                break
            page_idx += 1
            await asyncio.sleep(0.5)
        except Exception as e:
            print(f"     [Exception] {e}")
            break

    print(f"     ✅ Total {len(users)} petugas berhasil ditarik.")
    return users

async def get_authenticated_context(p):
    abs_user_data_dir = os.path.abspath(USER_DATA_DIR)
    os.makedirs(abs_user_data_dir, exist_ok=True)
    chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

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
                    if context.pages:
                        target_page = context.pages[0]
                    else:
                        target_page = await context.new_page()
                    fallback = (browser, context, target_page, port)
            except Exception:
                pass

    if 'fallback' in locals():
        browser, context, target_page, port = fallback
        print(f"[INFO] Terhubung ke browser di port {port} (tidak ada tab FASIH aktif)")
        return browser, context, target_page

    context = await p.chromium.launch_persistent_context(
        user_data_dir=abs_user_data_dir, headless=False, executable_path=chrome_path,
        args=["--no-first-run", "--no-default-browser-check"]
    )
    return browser, context, context.pages[0] if context.pages else await context.new_page()

async def check_session_valid(page, token):
    if not token:
        print("[DEBUG] check_session_valid: Token is empty")
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
                const controller = new AbortController();
                const id = setTimeout(() => controller.abort(), 45000);
                try {
                    const r = await fetch(url, {
                        method: "POST",
                        headers: { "Content-Type": "application/json", "X-XSRF-TOKEN": token },
                        body: JSON.stringify(payload),
                        signal: controller.signal
                    });
                    clearTimeout(id);
                    if (!r.ok) return { _error: `HTTP ${r.status}` };
                    return await r.json();
                } catch (e) {
                    clearTimeout(id);
                    return { _error: e.toString() };
                }
            }
        """, {"url": url, "payload": payload, "token": token})
        
        if res and isinstance(res, dict):
            if "_error" in res:
                print(f"[DEBUG] check_session_valid failed: {res['_error']}")
                return False
            return "searchData" in res or "searchAggregation" in res
    except Exception as e:
        print(f"[DEBUG] check_session_valid exception: {e}")
    return False

async def scrape_assign():
    if not REGION_MAP: return

    launch_chrome_if_needed()
    async with async_playwright() as p:
        browser, context, _ = await get_authenticated_context(p)
        page = await context.new_page()
        print(f"[DEBUG] Opened new page/tab for scrape_assign: {page}")
        
        print(f"[DEBUG] Navigating new page to https://fasih-sm.bps.go.id/app/dashboard")
        try:
            await page.goto("https://fasih-sm.bps.go.id/app/dashboard", timeout=60000, wait_until="domcontentloaded")
            print(f"[DEBUG] Page navigated. page.url: {page.url}")
        except Exception as e:
            print(f"[DEBUG] Navigation failed: {e}")

        cookies = await context.cookies()
        cookie_dict = {c["name"]: c["value"] for c in cookies}
        print(f"[DEBUG] Available cookies: {list(cookie_dict.keys())}")
        token_raw = cookie_dict.get("XSRF-TOKEN", "")
        
        first_expired = True
        while True:
            from urllib.parse import unquote
            token = unquote(token_raw) if token_raw else ""
            print(f"[DEBUG] Checking session validity with token length {len(token)}")
            is_valid = await check_session_valid(page, token) if token else False
            if is_valid:
                print("[DEBUG] Session is VALID!")
                break
                
            if first_expired:
                print("\n" + "="*70)
                print("[WARNING] Sesi login FASIH kadaluarsa atau belum login.")
                print("Silakan login/re-login FASIH di browser Chrome...")
                print("Script akan mendeteksi login Anda secara otomatis.")
                print("="*70)
                first_expired = False
                
            await asyncio.sleep(15)
            cookies = await context.cookies()
            cookie_dict = {c["name"]: c["value"] for c in cookies}
            token_raw = cookie_dict.get("XSRF-TOKEN", "")

        from urllib.parse import unquote
        token = unquote(token_raw)
        print("[INFO] Sesi login terverifikasi! Memulai sinkronisasi...\n")

        # 1. Tarik Rekap Cepat Kabupaten (Resmi)
        processed_data_umum = await fetch_report(page, token, SURVEY_CONFIGS[0]["survey_period_id"], SURVEY_CONFIGS[0]["region1_id"], "SE Umum")
        processed_data_ub = await fetch_report(page, token, SURVEY_CONFIGS[1]["survey_period_id"], SURVEY_CONFIGS[1]["region1_id"], "SE UB")

        # 2. Tarik Rincian Agregat SLS (By Kecamatan / Desa Report API for Umum, Datatable for UB)
        processed_sls_umum = await fetch_sls_by_kecamatan(page, token, SURVEY_CONFIGS[0]["survey_period_id"], SURVEY_CONFIGS[0]["region1_id"], SURVEY_CONFIGS[0]["kab_region_map"], "SE Umum")
        processed_sls_ub = await fetch_sls_ub_via_datatable(page, token, SURVEY_CONFIGS[1]["survey_period_id"], SURVEY_CONFIGS[1]["region1_id"], SURVEY_CONFIGS[1]["kab_region_map"], "SE UB")

        # 3. Tarik Petugas dan Wilayah Tugasnya
        processed_petugas_umum = await fetch_petugas(context, token, SURVEY_CONFIGS[0]["survey_period_id"], "SE Umum")
        processed_petugas_ub = await fetch_petugas(context, token, SURVEY_CONFIGS[1]["survey_period_id"], "SE UB")

        # Reconstruct regions for officers to fix BPS API 5-item truncation
        def reconstruct_officer_regions(petugas_list, sls_list):
            user_sls_map = {}
            for sls in sls_list:
                for username in sls.get("officer_usernames", []):
                    if username not in user_sls_map:
                        user_sls_map[username] = []
                    user_sls_map[username].append({
                        "regionCode": sls["sls_code"] + "00",
                        "regionName": sls["sls_name"]
                    })
            
            for officer in petugas_list:
                username = officer.get("username")
                if username in user_sls_map:
                    officer["regions"] = user_sls_map[username]
                    officer["totalRegions"] = len(user_sls_map[username])
                else:
                    officer["regions"] = []
                    officer["totalRegions"] = 0

        reconstruct_officer_regions(processed_petugas_umum, processed_sls_umum)
        reconstruct_officer_regions(processed_petugas_ub, processed_sls_ub)

        # Convert sets to lists and remove officer_usernames
        for data in processed_sls_umum:
            data["officers"] = list(data["officers"])
            if "officer_usernames" in data:
                del data["officer_usernames"]
                
        for data in processed_sls_ub:
            data["officers"] = list(data["officers"])
            if "officer_usernames" in data:
                del data["officer_usernames"]

        # Validasi data kosong sebelum melakukan overwrite
        if not processed_data_umum:
            print("[ERROR] processed_data_umum (rekap kabupaten SE Umum) kosong! Sinkronisasi dibatalkan demi keamanan data dashboard.")
            return
        if not processed_sls_umum:
            print("[ERROR] processed_sls_umum (rincian SLS SE Umum) kosong! Sinkronisasi dibatalkan demi keamanan data dashboard.")
            return
        if not processed_petugas_umum:
            print("[ERROR] processed_petugas_umum (data petugas SE Umum) kosong! Sinkronisasi dibatalkan demi keamanan data dashboard.")
            return

        js_content  = f"window.ASSIGN_DATA_UMUM = {json.dumps(processed_data_umum, indent=4, ensure_ascii=False)};\n"
        js_content += f"window.ASSIGN_DATA_UB   = {json.dumps(processed_data_ub,   indent=4, ensure_ascii=False)};\n"
        js_content += f"window.ASSIGN_SLS_DATA_UMUM = {json.dumps(processed_sls_umum, indent=4, ensure_ascii=False)};\n"
        js_content += f"window.ASSIGN_SLS_DATA_UB   = {json.dumps(processed_sls_ub,   indent=4, ensure_ascii=False)};\n"
        js_content += f"window.PETUGAS_DATA_UMUM = {json.dumps(processed_petugas_umum, indent=4, ensure_ascii=False)};\n"
        js_content += f"window.PETUGAS_DATA_UB   = {json.dumps(processed_petugas_ub,   indent=4, ensure_ascii=False)};\n"
        
        js_content += """
const activeSubtab = localStorage.getItem('active_assign_subtab') || 'se2026';
if (activeSubtab === 'se2026') {
    window.ASSIGN_DATA = window.ASSIGN_DATA_UMUM || [];
    window.ASSIGN_SLS_DATA = window.ASSIGN_SLS_DATA_UMUM || [];
    window.PETUGAS_DATA = window.PETUGAS_DATA_UMUM || [];
} else {
    window.ASSIGN_DATA = window.ASSIGN_DATA_UB || [];
    window.ASSIGN_SLS_DATA = window.ASSIGN_SLS_DATA_UB || [];
    window.PETUGAS_DATA = window.PETUGAS_DATA_UB || [];
}

function filterAssignData(type) {
    localStorage.setItem('active_assign_subtab', type);
    const btnUmum = document.getElementById("subtab-btn-se2026");
    const btnUB = document.getElementById("subtab-btn-ub");
    
    const chartTitle = document.getElementById("assign-chart-title");
    const slsTitle = document.getElementById("assign-sls-title");

    if (type === 'se2026') {
        if(btnUmum) { btnUmum.style.backgroundColor = 'var(--primary)'; btnUmum.style.color = 'white'; }
        if(btnUB) { btnUB.style.backgroundColor = 'transparent'; btnUB.style.color = 'var(--text-secondary)'; }
        if(chartTitle) chartTitle.innerText = "Status Assign Petugas (Semua Usaha - Umum)";
        if(slsTitle) slsTitle.innerText = "Rincian Assignment per SLS (Umum)";
        
        window.ASSIGN_DATA = window.ASSIGN_DATA_UMUM;
        window.ASSIGN_SLS_DATA = window.ASSIGN_SLS_DATA_UMUM;
        window.PETUGAS_DATA = window.PETUGAS_DATA_UMUM;
    } else {
        if(btnUB) { btnUB.style.backgroundColor = 'var(--primary)'; btnUB.style.color = 'white'; }
        if(btnUmum) { btnUmum.style.backgroundColor = 'transparent'; btnUmum.style.color = 'var(--text-secondary)'; }
        if(chartTitle) chartTitle.innerText = "Status Assign Petugas (Usaha Besar - UB)";
        if(slsTitle) slsTitle.innerText = "Rincian Assignment per SLS (UB)";

        window.ASSIGN_DATA = window.ASSIGN_DATA_UB;
        window.ASSIGN_SLS_DATA = window.ASSIGN_SLS_DATA_UB;
        window.PETUGAS_DATA = window.PETUGAS_DATA_UB;
    }

    if (typeof renderAssignChart === 'function') renderAssignChart();
    if (typeof renderKabSummaryTable === 'function') renderKabSummaryTable();
    if (typeof renderSlsTable === 'function') {
        window.slsCurrentPage = 1;
        renderSlsTable();
    }
    if (typeof renderPetugasTable === 'function') {
        window.petugasCurrentPage = 1;
        renderPetugasTable();
    }
    if (typeof renderSyncTable === 'function') {
        window.syncCurrentPage = 1;
        renderSyncTable();
    }
}
"""
        with open("assign_data.js", "w", encoding="utf-8") as f:
            f.write(js_content)
        print("\n✅ DONE! Data Assign Petugas dan Rincian SLS berhasil ditarik dan file assign_data.js diperbarui.")

        # Upload to Supabase dashboard_store
        if supabase:
            try:
                print("Mengunggah data Assign/SLS/Petugas ke Supabase (dengan kompresi SLS)...")
                
                def compress_sls(sls_list):
                    return [
                        [
                            item.get("sls_code"),
                            item.get("sls_name"),
                            item.get("desa_name"),
                            item.get("kec_name"),
                            item.get("kab_name"),
                            item.get("total"),
                            item.get("assigned"),
                            item.get("unassigned"),
                            item.get("sync_count", 0),
                            item.get("officers", [])
                        ]
                        for item in sls_list
                    ]

                assign_db_obj = {
                    "updated_at": datetime.now().isoformat(),
                    "assign_data_umum": processed_data_umum,
                    "assign_data_ub": processed_data_ub,
                    "assign_sls_data_umum": compress_sls(processed_sls_umum),
                    "assign_sls_data_ub": compress_sls(processed_sls_ub),
                    "petugas_data_umum": processed_petugas_umum,
                    "petugas_data_ub": processed_petugas_ub
                }
                # delete existing
                supabase.table("dashboard_store").delete().eq("key", "assign_data").execute()
                # insert new
                supabase.table("dashboard_store").insert({"key": "assign_data", "value": assign_db_obj}).execute()
                print("Berhasil mengunggah data Assign/SLS/Petugas ke Supabase.")
                
                # Upload daily historical key
                today_str = datetime.now().strftime("%Y-%m-%d")
                daily_key = f"assign_data:{today_str}"
                try:
                    supabase.table("dashboard_store").delete().eq("key", daily_key).execute()
                    supabase.table("dashboard_store").insert({"key": daily_key, "value": assign_db_obj}).execute()
                    print(f"Berhasil mengunggah data harian Assign/SLS/Petugas ({daily_key}) ke Supabase.")
                except Exception as ex:
                    print(f"Gagal mengunggah data harian Assign ke Supabase: {ex}")
            except Exception as e:
                print(f"Gagal mengunggah data Assign ke Supabase: {e}")

        # ----------------------------------------------------
        # FETCH SYNC DATA FROM SUPERSET
        # ----------------------------------------------------
        try:
            print("\n[INFO] Mulai menarik data sinkronisasi dari Superset...")
            dash_page = None
            for p_page in context.pages:
                if "fasih-dashboard.bps.go.id" in p_page.url:
                    dash_page = p_page
                    break
            
            if not dash_page:
                dash_page = await context.new_page()
                try:
                    await dash_page.goto("https://fasih-dashboard.bps.go.id/superset/dashboard/se2026/", timeout=60000, wait_until="domcontentloaded")
                except Exception as e:
                    print(f"[WARNING] Navigasi lambat/timeout: {e}")
            
            for _ in range(5):
                if "login" in dash_page.url.lower():
                    print("\nSilakan login ke fasih-dashboard.bps.go.id di Chrome. Menunggu login...")
                    await asyncio.sleep(5)
                else:
                    break
                    
            # Ambil CSRF token dari html head/meta atau window
            dash_csrf_token = await dash_page.evaluate("""() => {
                const el = document.querySelector('input[name="csrf_token"]');
                if (el) return el.value;
                // Fallback cari di bootstrap data
                const bootstrapEl = document.getElementById('app');
                if (bootstrapEl) {
                    const data = bootstrapEl.getAttribute('data-bootstrap');
                    if (data) {
                        try {
                            const parsed = JSON.parse(data);
                            return parsed.csrf_token;
                        } catch(e) {}
                    }
                }
                return '';
            }""")
            
            if not dash_csrf_token:
                cookies_list = await context.cookies()
                dash_csrf_token = next((c["value"] for c in cookies_list if c["name"] == "referrer" or c["name"] == "session"), "")

            superset_data = await dash_page.evaluate("""
                async ({csrfToken}) => {
                    const url = 'https://fasih-dashboard.bps.go.id/api/v1/chart/data';
                    const payload = {
                        "datasource": {"id": 7047, "type": "table"},
                        "force": false,
                        "queries": [{
                            "granularity": null,
                            "filters": [
                                {"col": "level_1_full_code", "op": "==", "val": "72"}
                            ],
                            "extras": {"time_grain_sqla": "P1D", "having": "", "where": ""},
                            "columns": [
                                "level_2_full_code",
                                "level_3_name",
                                "level_4_name",
                                "level_5_full_code",
                                "level_5_name",
                                "assign",
                                "sync_count_pencacah"
                            ],
                            "metrics": [],
                            "row_limit": 50000,
                            "query_mode": "scan"
                        }],
                        "result_format": "json",
                        "result_type": "full"
                    };

                    try {
                        const r = await fetch(url, {
                            method: "POST",
                            headers: { 
                                "Content-Type": "application/json",
                                "X-CSRFToken": csrfToken
                            },
                            body: JSON.stringify(payload)
                        });
                        if (!r.ok) return { error: `HTTP ${r.status}: ${await r.text()}` };
                        return await r.json();
                    } catch (e) {
                        return { error: e.toString() };
                    }
                }
            """, {"csrfToken": dash_csrf_token})
            
            if "error" not in superset_data and superset_data.get("result"):
                raw_rows = superset_data["result"][0].get("data", [])
                print(f"Berhasil menarik {len(raw_rows)} baris data SLS dari Superset.")
                
                # Format dan rename keys dengan resolusi SLS code regex
                result_data = []
                for item in raw_rows:
                    sls_code = item.get("level_5_full_code")
                    if not sls_code:
                        try:
                            lvl2 = item.get("level_2_full_code") or ""
                            lvl3_name = item.get("level_3_name") or ""
                            lvl4_name = item.get("level_4_name") or ""
                            lvl5_name = item.get("level_5_name") or ""
                            
                            m3 = re.search(r'\[(\d{3})\]', lvl3_name)
                            m4 = re.search(r'\[(\d{3})\]', lvl4_name)
                            m5 = re.search(r'\[(\d{4})\]', lvl5_name)
                            
                            if len(lvl2) == 4 and m3 and m4 and m5:
                                sls_code = lvl2 + m3.group(1) + m4.group(1) + m5.group(1)
                        except Exception:
                            pass

                    result_data.append({
                        "sls_code": sls_code,
                        "sls_name": item.get("level_5_name"),
                        "assign": item.get("assign"),
                        "sync_count": item.get("sync_count_pencacah") or 0
                    })
                
                js_content_sync = f"window.SUPERSET_SYNC_SLS_DATA = {json.dumps(result_data, indent=4, ensure_ascii=False)};\n"
                with open("sync_data.js", "w", encoding="utf-8") as f:
                    f.write(js_content_sync)
                print("✅ Data disimpan ke sync_data.js")
                
                if supabase:
                    try:
                        supabase.table("dashboard_store").delete().eq("key", "superset_sync_data").execute()
                        supabase.table("dashboard_store").insert({"key": "superset_sync_data", "value": result_data}).execute()
                        print("Berhasil mengunggah data sync Superset ke Supabase.")
                        
                        # Upload daily historical sync key
                        today_str = datetime.now().strftime("%Y-%m-%d")
                        daily_sync_key = f"superset_sync_data:{today_str}"
                        try:
                            supabase.table("dashboard_store").delete().eq("key", daily_sync_key).execute()
                            supabase.table("dashboard_store").insert({"key": daily_sync_key, "value": result_data}).execute()
                            print(f"Berhasil mengunggah data sync harian ({daily_sync_key}) ke Supabase.")
                        except Exception as ex:
                            print(f"Gagal mengunggah data sync harian ke Supabase: {ex}")
                    except Exception as e:
                        print(f"Gagal mengunggah ke Supabase: {e}")
            else:
                print(f"[ERROR] Gagal menarik data dari Superset: {superset_data.get('error', 'Unknown error')}")
                
            if dash_page != page:
                await dash_page.close()
                
        except Exception as e:
            print(f"[ERROR] Exception saat menarik data Superset: {e}")

        if hasattr(context, "_http_client"):
            try:
                await context._http_client.aclose()
            except:
                pass
        await page.close()

def main():
    while True:
        asyncio.run(scrape_assign())
        time.sleep(1800) # Cek setiap 30 menit

if __name__ == "__main__":
    main()