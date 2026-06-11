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
    port = 9222
    if check_port_open(port):
        print("[INFO] Chrome remote debugging port 9222 aktif.")
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
        "region1_id": "5214ecb2-bef1-4a86-9446-451cf430928e"
    },
    {
        "label": "SE UB",
        "survey_period_id": "37526b20-81c8-42f5-a895-6190137d7394",
        "region1_id": "a00c8aef-afc4-4d4f-b80d-789a15450ef9"
    }
]

REPORT_URL = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/report-user-assignment"

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
            print(f"[WARNING] Gagal request (attempt {attempt+1}/3): {e}")
            await asyncio.sleep(2)
    return {"error": "Max retries exceeded"}

async def fetch_report(context, token, survey_period_id, region1_id, label):
    print(f"[{label}] Menarik rekap dari REPORT API...")
    payload = {"surveyPeriodId": survey_period_id, "region1Id": region1_id}
    res = await evaluate_fetch_with_retry(context, token, REPORT_URL, payload)

    if not res or (isinstance(res, dict) and "error" in res):
        print(f"[ERROR] [{label}] Gagal tarik laporan.")
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

async def get_authenticated_context(p):
    abs_user_data_dir = os.path.abspath(USER_DATA_DIR)
    os.makedirs(abs_user_data_dir, exist_ok=True)
    chrome_path = "/Users/jihanmaisaroh/Library/Caches/ms-playwright/chromium-1208/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"

    browser = None
    if check_port_open(9222):
        try:
            browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
            context = browser.contexts[0] if browser.contexts else await browser.new_context()
            return browser, context, context.pages[0] if context.pages else await context.new_page()
        except:
            pass

    context = await p.chromium.launch_persistent_context(
        user_data_dir=abs_user_data_dir, headless=False, executable_path=chrome_path,
        args=["--no-first-run", "--no-default-browser-check"]
    )
    return browser, context, context.pages[0] if context.pages else await context.new_page()

async def scrape_assign():
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

        processed_data_umum = await fetch_report(context, token, SURVEY_CONFIGS[0]["survey_period_id"], SURVEY_CONFIGS[0]["region1_id"], "SE Umum")
        processed_data_ub = await fetch_report(context, token, SURVEY_CONFIGS[1]["survey_period_id"], SURVEY_CONFIGS[1]["region1_id"], "SE UB")

        js_content  = f"window.ASSIGN_DATA_UMUM = {json.dumps(processed_data_umum, indent=4, ensure_ascii=False)};\n"
        js_content += f"window.ASSIGN_DATA_UB   = {json.dumps(processed_data_ub,   indent=4, ensure_ascii=False)};\n"
        js_content += """
const activeSubtab = localStorage.getItem('active_assign_subtab') || 'se2026';
if (activeSubtab === 'se2026') {
    window.ASSIGN_DATA = window.ASSIGN_DATA_UMUM || [];
} else {
    window.ASSIGN_DATA = window.ASSIGN_DATA_UB || [];
}

function filterAssignData(type) {
    localStorage.setItem('active_assign_subtab', type);
    const btnUmum = document.getElementById("subtab-btn-se2026");
    const btnUB = document.getElementById("subtab-btn-ub");
    const chartTitle = document.getElementById("assign-chart-title");

    if (type === 'se2026') {
        if(btnUmum) { btnUmum.style.backgroundColor = 'var(--primary)'; btnUmum.style.color = 'white'; }
        if(btnUB) { btnUB.style.backgroundColor = 'transparent'; btnUB.style.color = 'var(--text-secondary)'; }
        if(chartTitle) chartTitle.innerText = "Status Assign Petugas (Semua Usaha - Umum)";
        window.ASSIGN_DATA = window.ASSIGN_DATA_UMUM;
    } else {
        if(btnUB) { btnUB.style.backgroundColor = 'var(--primary)'; btnUB.style.color = 'white'; }
        if(btnUmum) { btnUmum.style.backgroundColor = 'transparent'; btnUmum.style.color = 'var(--text-secondary)'; }
        if(chartTitle) chartTitle.innerText = "Status Assign Petugas (Usaha Besar - UB)";
        window.ASSIGN_DATA = window.ASSIGN_DATA_UB;
    }

    if (typeof renderAssignChart === 'function') renderAssignChart();
    if (typeof renderKabSummaryTable === 'function') renderKabSummaryTable();
}
"""
        with open("assign_data.js", "w", encoding="utf-8") as f:
            f.write(js_content)
        print("\n✅ DONE! Data Assign Petugas berhasil ditarik dan file assign_data.js diperbarui.")
        await page.close()

def main():
    while True:
        asyncio.run(scrape_assign())
        time.sleep(1800) # Cek setiap 30 menit (ini lebih cepat jadi bisa lebih sering)

if __name__ == "__main__":
    main()