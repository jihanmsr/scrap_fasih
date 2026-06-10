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
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = None
if SUPABASE_URL and SUPABASE_KEY and "MASUKKAN" not in SUPABASE_URL:
    try:
        from supabase import create_client
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("[INFO] Koneksi Supabase berhasil diinisialisasi.")
    except Exception as e:
        print(f"[ERROR] Gagal menginisialisasi Supabase: {e}")

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

KAB_MAP = {
    "7201": "[01] BANGGAI KEPULAUAN", "7202": "[02] BANGGAI", "7203": "[03] MOROWALI",
    "7204": "[04] POSO", "7205": "[05] DONGGALA", "7206": "[06] TOLI-TOLI",
    "7207": "[07] BUOL", "7208": "[08] PARIGI MOUTONG", "7209": "[09] TOJO UNA-UNA",
    "7210": "[10] SIGI", "7211": "[11] BANGGAI LAUT", "7212": "[12] MOROWALI UTARA",
    "7271": "[71] PALU"
}

# ID WILAYAH SUDAH DISESUAIKAN DENGAN VERCEL (BERBEDA ANTARA UMUM & UB)
SURVEY_CONFIGS = [
    {
        "label": "SE Umum",
        "survey_period_id": "fd68e454-ba45-4b85-8205-f3bf777ded24",
        "region1_id": "5214ecb2-bef1-4a86-9446-451cf430928e", # ID Prov Sulteng untuk SE Umum
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
        "region1_id": "a00c8aef-afc4-4d4f-b80d-789a15450ef9", # ID Prov Sulteng untuk SE UB
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

async def fetch_report(page, token, survey_period_id, region1_id, label):
    print(f"[{label}] Menarik rekap dari REPORT API...")
    payload = {"surveyPeriodId": survey_period_id, "region1Id": region1_id}
    res = await page.evaluate("""
        async ({url, payload, token}) => {
            try {
                const r = await fetch(url, {
                    method: "POST",
                    headers: { "Content-Type": "application/json", "X-XSRF-TOKEN": token },
                    body: JSON.stringify(payload)
                });
                if (!r.ok) return { error: `HTTP ${r.status}: ${await r.text()}` };
                return await r.json();
            } catch (e) {
                return { error: e.toString() };
            }
        }
    """, {"url": REPORT_URL, "payload": payload, "token": token})

    if isinstance(res, dict) and res.get("error"):
        print(f"[ERROR] [{label}] Gagal tarik laporan: {res['error']}")
        return {}

    result = {}
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
        result[kode_kab] = {"total": total, "assigned": assigned, "have_not_assigned": have_not}
        print(f"  -> {KAB_MAP[kode_kab]}: {total} Target | {assigned} Diassign")
    return result

async def fetch_sls_companies(page, token, survey_period_id, region1_id, kab_region_map, label):
    print(f"\n[{label}] Menarik rincian per SLS dari DATATABLE API...")
    all_companies = []
    for kab_code, kab_cfg in kab_region_map.items():
        start = 0
        length = 100
        kab_total = 0
        while True:
            payload_dt = {
                "start": start, "length": length, "columns": [{"data": "id"}], "order": [],
                "search": {"value": "", "regex": False},
                "assignmentExtraParam": {
                    "region1Id": region1_id, "region2Id": kab_cfg["id"],
                    "surveyPeriodId": survey_period_id, "assignmentErrorStatusType": -1, "filterTargetType": ""
                }
            }
            res_dt = await page.evaluate("""
                async ({url, payload, token}) => {
                    try {
                        const r = await fetch(url, { method: "POST", headers: { "Content-Type": "application/json", "X-XSRF-TOKEN": token }, body: JSON.stringify(payload) });
                        return await r.json();
                    } catch (e) { return null; }
                }
            """, {"url": DATATABLE_URL, "payload": payload_dt, "token": token})

            if not res_dt or "searchData" not in res_dt: break
            records = res_dt["searchData"]
            if not records: break

            for r in records:
                r["kab_code"] = kab_code

            all_companies.extend(records)
            kab_total += len(records)
            start += length
            if start >= res_dt.get("totalHit", 0): break
        
        print(f"  -> {kab_cfg['name']}: {kab_total} perusahaan ditarik")
    return all_companies

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

async def scrape_assign():
    launch_chrome_if_needed()
    async with async_playwright() as p:
        try:
            browser, context, page = await get_authenticated_context(p)
        except Exception as e:
            print(f"[ERROR] Gagal mendapatkan browser context: {e}")
            return
        
        # Cari tab aktif yang sudah membuka fasih-sm dan navigasikan jika bukan halaman target
        for p_page in context.pages:
            if "fasih-sm.bps.go.id" in p_page.url:
                page = p_page
                print(f"[INFO] Menemukan tab aktif FASIH: {page.url}")
                break
                
        if page.url == "about:blank":
            try: 
                await page.goto("https://fasih-sm.bps.go.id/app/dashboard", timeout=60000, wait_until="domcontentloaded")
            except: 
                pass

        print("\n" + "="*70)
        print("MENUNGGU LOGIN...")
        print("Silakan login FASIH di Chrome. Jika sudah di Dashboard, tekan ENTER di bawah.")
        print("="*70)
        
        await asyncio.to_thread(input, ">> TEKAN [ENTER] DI SINI... <<\n")
        print("\nMemproses penarikan API Sensus Umum dan UB...")
        await asyncio.sleep(3)

        cookies = await context.cookies()
        token = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), None)
        if not token:
            print("[ERROR] Token XSRF tidak ditemukan. Kamu belum login atau sesi habis.")
            return

        from urllib.parse import unquote
        token = unquote(token)
        print("[INFO] Token Otorisasi Berhasil Ditemukan! Menginisialisasi penarikan...\n")

        # ─── STEP 1 & 2: Tarik SLS dan Hitung Rekap ───
        report_per_survey = {}
        sls_per_survey = {}
        for cfg in SURVEY_CONFIGS:
            label = cfg["label"]
            all_companies = await fetch_sls_companies(page, token, cfg["survey_period_id"], cfg["region1_id"], cfg["kab_region_map"], label)
            
            # Compute report stats per kabupaten
            kab_report = {}
            for kab_code in KAB_MAP:
                kab_report[kab_code] = {"total": 0, "assigned": 0, "have_not_assigned": 0}
                
            use_official_report = False
            try:
                fetched_report = await fetch_report(page, token, cfg["survey_period_id"], cfg["region1_id"], label)
                if fetched_report:
                    kab_report.update(fetched_report)
                    use_official_report = True
            except Exception as e:
                print(f"[WARNING] Gagal mengambil real-time report dari API, menggunakan fallback hitung mandiri: {e}")
                
            sls_dict = {}
            for comp in all_companies:
                # Tag kab_code during processing
                region = comp.get("region", {})
                lvl2 = region.get("level1", {}).get("level2", {}) or {}
                lvl3 = lvl2.get("level3", {}) or {}
                lvl4 = lvl3.get("level4", {}) or {}
                lvl5 = lvl4.get("level5", {}) or {}

                # Determine kab_code from level2.code or first 4 digits of codeIdentity
                kab_code = lvl2.get("code")
                if not kab_code:
                    code_identity = comp.get("codeIdentity")
                    if code_identity and len(code_identity) >= 4:
                        kab_code = code_identity[:4]
                
                # Normalize kab_code (must be e.g. "7201")
                if kab_code:
                    if len(kab_code) == 2:
                        kab_code = "72" + kab_code
                else:
                    # Fallback to map matching if possible
                    kab_code = comp.get("kab_code", "LAINNYA")
                    if len(kab_code) == 2:
                        kab_code = "72" + kab_code
                
                officer = comp.get("currentUserUsername")
                is_assigned = bool(officer)
                
                if not use_official_report:
                    if kab_code in kab_report:
                        kab_report[kab_code]["total"] += 1
                        if is_assigned:
                            kab_report[kab_code]["assigned"] += 1
                        else:
                            kab_report[kab_code]["have_not_assigned"] += 1

                # SLS processing
                sls_code = lvl5.get("fullCode", "LAINNYA")
                if sls_code not in sls_dict:
                    sls_dict[sls_code] = {
                        "sls_code": sls_code, "sls_name": lvl5.get("name", "LAINNYA"),
                        "desa_name": lvl4.get("name", "LAINNYA"), "kec_name": lvl3.get("name", "LAINNYA"),
                        "kab_name": lvl2.get("name", "LAINNYA"), "total": 0, "assigned": 0, "unassigned": 0, "officers": set()
                    }

                sls_dict[sls_code]["total"] += 1
                if is_assigned:
                    sls_dict[sls_code]["assigned"] += 1
                    ofc_name = comp.get("currentUserFullname", "-")
                    sls_dict[sls_code]["officers"].add(f"{ofc_name} ({officer})" if ofc_name != "-" else officer)
                else:
                    sls_dict[sls_code]["unassigned"] += 1

            # Print computed stats for this survey
            print(f"\n[INFO] Rekap Hasil Hitung Mandiri dari Datatable [{label}]:")
            for kab_code, vals in sorted(kab_report.items()):
                print(f"  -> {KAB_MAP.get(kab_code, kab_code)}: {vals['total']} Target | {vals['assigned']} Diassign")

            report_per_survey[label] = kab_report

            processed_sls = []
            for data in sls_dict.values():
                data["officers"] = list(data["officers"])
                processed_sls.append(data)
            sls_per_survey[label] = processed_sls

        def make_processed_data(report_dict):
            result = []
            for kode_kab, vals in sorted(report_dict.items()):
                result.append({
                    "kode_kab": kode_kab, "nama_kab": KAB_MAP.get(kode_kab, kode_kab),
                    "total": vals["total"], "assigned": vals["assigned"],
                    "have_not_assigned": vals["have_not_assigned"], "timestamp": datetime.now().isoformat()
                })
            return result

        processed_data_umum = make_processed_data(report_per_survey.get("SE Umum", {}))
        processed_data_ub   = make_processed_data(report_per_survey.get("SE UB", {}))

        processed_sls_umum = sls_per_survey.get("SE Umum", [])
        processed_sls_ub   = sls_per_survey.get("SE UB", [])

        # ─── STEP 3: Simpan ke assign_data.js ───
        print("\n[INFO] Menyimpan ke assign_data.js untuk Website...")
        js_content  = f"window.ASSIGN_DATA_UMUM = {json.dumps(processed_data_umum, indent=4, ensure_ascii=False)};\n"
        js_content += f"window.ASSIGN_DATA_UB   = {json.dumps(processed_data_ub,   indent=4, ensure_ascii=False)};\n"
        js_content += f"window.ASSIGN_SLS_DATA_UMUM = {json.dumps(processed_sls_umum, indent=4, ensure_ascii=False)};\n"
        js_content += f"window.ASSIGN_SLS_DATA_UB   = {json.dumps(processed_sls_ub,   indent=4, ensure_ascii=False)};\n"

        js_content += """
// Set default ke UMUM/UB sesuai dengan pilihan terakhir user
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
        print("✅ DONE! Data Assign Petugas (UMUM & UB) berhasil diperbarui dan siap digunakan di UI.")
        
        await page.close()

def main():
    while True:
        asyncio.run(scrape_assign())
        time.sleep(21600)

if __name__ == "__main__":
    main()