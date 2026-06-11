import asyncio
import json
import os
import time
import socket
import subprocess
import shutil
from datetime import datetime
from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv()
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

def launch_chrome_if_needed():
    if check_port_open(9223) or check_port_open(9222):
        print("[INFO] Chrome remote debugging aktif.")
        return
    
    print("[INFO] Meluncurkan Chrome browser...")
    chrome_path = "/Users/jihanmaisaroh/Library/Caches/ms-playwright/chromium-1208/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"
    
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

async def evaluate_fetch_with_retry(context, token, url, payload):
    for attempt in range(3):
        page = None
        for p_page in context.pages:
            if "fasih-sm.bps.go.id" in p_page.url:
                page = p_page
                break
        if not page:
            page = context.pages[0] if context.pages else await context.new_page()

        try:
            res = await page.evaluate("""
                async ({url, payload, token}) => {
                    try {
                        const r = await fetch(url, {
                            method: "POST",
                            headers: { "Content-Type": "application/json", "X-XSRF-TOKEN": token },
                            body: JSON.stringify(payload)
                        });
                        if (!r.ok) return { error: `HTTP ${r.status}` };
                        return await r.json();
                    } catch (e) {
                        return { error: e.toString() };
                    }
                }
            """, {"url": url, "payload": payload, "token": token})
            return res
        except Exception as e:
            await asyncio.sleep(2)
    return {"error": "Max retries exceeded"}

async def fetch_report(context, token, survey_period_id, region1_id, label):
    print(f"\n[{label}] Menarik rekap RESMI tingkat Kabupaten dari REPORT API...")
    payload = {"surveyPeriodId": survey_period_id, "region1Id": region1_id}
    res = await evaluate_fetch_with_retry(context, token, REPORT_URL, payload)

    if not res or (isinstance(res, dict) and "error" in res):
        print(f"[ERROR] [{label}] Gagal tarik laporan resmi.")
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

async def fetch_sls_by_kecamatan(context, token, survey_period_id, region1_id, kab_region_map, label):
    print(f"\n[{label}] Menarik rincian per SLS dari DATATABLE API (By Kecamatan)...")
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
                        "total": 0, "assigned": 0, "unassigned": 0, "officers": set()
                    }

    for kab_code, kab_cfg in kab_region_map.items():
        kab_name = kab_cfg["name"]
        kecamatan_list = REGION_MAP.get(kab_code, {}).get("kecamatan", [])
        
        print(f"  -> Memproses Kab. {kab_name} ({len(kecamatan_list)} Kecamatan)")

        for kec in kecamatan_list:
            kec_id = kec["id"]
            start = 0
            length = 1000 # Kita bisa request lebih besar karena sudah di-filter per kecamatan
            
            while True:
                payload_dt = {
                    "start": start, "length": length, "columns": [{"data": "id"}], "order": [],
                    "search": {"value": "", "regex": False},
                    "assignmentExtraParam": {
                        "region1Id": region1_id, 
                        "region2Id": kab_cfg["id"],
                        "region3Id": kec_id,
                        "surveyPeriodId": survey_period_id, 
                        "assignmentErrorStatusType": -1, 
                        "filterTargetType": ""
                    }
                }
                
                res_dt = await evaluate_fetch_with_retry(context, token, DATATABLE_URL, payload_dt)

                if not res_dt or "searchData" not in res_dt: break
                records = res_dt["searchData"]
                if not records: break

                # ON-THE-FLY AGGREGATION
                for comp in records:
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
                            "total": 0, "assigned": 0, "unassigned": 0, "officers": set()
                        }

                    sls_dict[sls_code]["total"] += 1
                    officer = comp.get("currentUserUsername")
                    if officer:
                        sls_dict[sls_code]["assigned"] += 1
                        ofc_name = comp.get("currentUserFullname", "-")
                        sls_dict[sls_code]["officers"].add(f"{ofc_name} ({officer})" if ofc_name != "-" else officer)
                    else:
                        sls_dict[sls_code]["unassigned"] += 1

                start += length
                if start >= res_dt.get("totalHit", 0): break

    # Convert set ke list untuk JSON serialization
    processed_sls = []
    for data in sls_dict.values():
        if data["total"] > 0:
            data["officers"] = list(data["officers"])
            processed_sls.append(data)
        
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
    
    sem = asyncio.Semaphore(15)
    
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

async def get_authenticated_context(p):
    abs_user_data_dir = os.path.abspath(USER_DATA_DIR)
    os.makedirs(abs_user_data_dir, exist_ok=True)
    chrome_path = "/Users/jihanmaisaroh/Library/Caches/ms-playwright/chromium-1208/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"

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

async def scrape_assign():
    if not REGION_MAP: return

    launch_chrome_if_needed()
    async with async_playwright() as p:
        browser, context, page = await get_authenticated_context(p)
        
        for p_page in context.pages:
            if "fasih-sm.bps.go.id" in p_page.url:
                page = p_page
                break
                
        if page.url == "about:blank":
            try: await page.goto("https://fasih-sm.bps.go.id/app/dashboard", timeout=60000, wait_until="domcontentloaded")
            except: pass

        cookies = await context.cookies()
        token = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), None)
        
        if not token:
            print("\nSilakan login FASIH di Chrome. Tekan ENTER jika sudah.")
            await asyncio.to_thread(input, ">> TEKAN [ENTER] DI SINI... <<\n")
            cookies = await context.cookies()
            token = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), None)
            
        if not token:
            print("[ERROR] Token tidak ditemukan.")
            return

        from urllib.parse import unquote
        token = unquote(token)
        print("[INFO] Token ditemukan! Memulai sinkronisasi...\n")

        # 1. Tarik Rekap Cepat Kabupaten (Resmi)
        processed_data_umum = await fetch_report(context, token, SURVEY_CONFIGS[0]["survey_period_id"], SURVEY_CONFIGS[0]["region1_id"], "SE Umum")
        processed_data_ub = await fetch_report(context, token, SURVEY_CONFIGS[1]["survey_period_id"], SURVEY_CONFIGS[1]["region1_id"], "SE UB")

        # 2. Tarik Rincian Agregat SLS (By Kecamatan / Desa Report API)
        processed_sls_umum = await fetch_sls_by_report_api(context, token, SURVEY_CONFIGS[0]["survey_period_id"], SURVEY_CONFIGS[0]["region1_id"], SURVEY_CONFIGS[0]["kab_region_map"], "SE Umum")
        processed_sls_ub = await fetch_sls_by_report_api(context, token, SURVEY_CONFIGS[1]["survey_period_id"], SURVEY_CONFIGS[1]["region1_id"], SURVEY_CONFIGS[1]["kab_region_map"], "SE UB")

        js_content  = f"window.ASSIGN_DATA_UMUM = {json.dumps(processed_data_umum, indent=4, ensure_ascii=False)};\n"
        js_content += f"window.ASSIGN_DATA_UB   = {json.dumps(processed_data_ub,   indent=4, ensure_ascii=False)};\n"
        js_content += f"window.ASSIGN_SLS_DATA_UMUM = {json.dumps(processed_sls_umum, indent=4, ensure_ascii=False)};\n"
        js_content += f"window.ASSIGN_SLS_DATA_UB   = {json.dumps(processed_sls_ub,   indent=4, ensure_ascii=False)};\n"
        
        js_content += """
const activeSubtab = localStorage.getItem('active_assign_subtab') || 'se2026';
if (activeSubtab === 'se2026') {
    window.ASSIGN_DATA = window.ASSIGN_DATA_UMUM || [];
    window.ASSIGN_SLS_DATA = window.ASSIGN_SLS_DATA_UMUM || [];
} else {
    window.ASSIGN_DATA = window.ASSIGN_DATA_UB || [];
    window.ASSIGN_SLS_DATA = window.ASSIGN_SLS_DATA_UB || [];
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
    } else {
        if(btnUB) { btnUB.style.backgroundColor = 'var(--primary)'; btnUB.style.color = 'white'; }
        if(btnUmum) { btnUmum.style.backgroundColor = 'transparent'; btnUmum.style.color = 'var(--text-secondary)'; }
        if(chartTitle) chartTitle.innerText = "Status Assign Petugas (Usaha Besar - UB)";
        if(slsTitle) slsTitle.innerText = "Rincian Assignment per SLS (UB)";

        window.ASSIGN_DATA = window.ASSIGN_DATA_UB;
        window.ASSIGN_SLS_DATA = window.ASSIGN_SLS_DATA_UB;
    }

    if (typeof renderAssignChart === 'function') renderAssignChart();
    if (typeof renderKabSummaryTable === 'function') renderKabSummaryTable();
    if (typeof renderSlsTable === 'function') {
        window.slsCurrentPage = 1;
        renderSlsTable();
    }
}
"""
        with open("assign_data.js", "w", encoding="utf-8") as f:
            f.write(js_content)
        print("\n✅ DONE! Data Assign Petugas dan Rincian SLS berhasil ditarik dan file assign_data.js diperbarui.")
        await page.close()

def main():
    while True:
        asyncio.run(scrape_assign())
        time.sleep(1800) # Cek setiap 30 menit

if __name__ == "__main__":
    main()