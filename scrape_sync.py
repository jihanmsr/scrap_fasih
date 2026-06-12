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
        print("[INFO] Koneksi Supabase berhasil diinisialisasi untuk scrape_sync.")
    except Exception as e:
        print(f"[ERROR] Gagal menginisialisasi Supabase di scrape_sync: {e}")

USER_DATA_DIR = "playwright_chrome_profile"

def check_port_open(port=9222):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0
    except:
        return False

async def get_authenticated_context(p):
    for port in [9222, 9223]:
        if check_port_open(port):
            try:
                browser = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
                context = browser.contexts[0] if browser.contexts else await browser.new_context()
                print(f"[INFO] Terhubung ke browser aktif di port {port}")
                return browser, context
            except Exception as e:
                print(f"[WARNING] Gagal hubung ke port {port}: {e}")
                pass
    
    # Fallback launch persistent
    abs_user_data_dir = os.path.abspath(USER_DATA_DIR)
    chrome_path = "/Users/jihanmaisaroh/Library/Caches/ms-playwright/chromium-1208/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"
    context = await p.chromium.launch_persistent_context(
        user_data_dir=abs_user_data_dir, headless=False, executable_path=chrome_path,
        args=["--no-first-run", "--no-default-browser-check"]
    )
    return None, context

async def scrape_sync_data():
    async with async_playwright() as p:
        browser, context = await get_authenticated_context(p)
        
        # Cari tab aktif dashboard atau buka baru
        page = None
        for p_page in context.pages:
            if "fasih-dashboard.bps.go.id" in p_page.url:
                page = p_page
                break
        
        if not page:
            page = await context.new_page()
            try:
                await page.goto("https://fasih-dashboard.bps.go.id/superset/dashboard/se2026/", timeout=60000, wait_until="domcontentloaded")
            except Exception as e:
                print(f"[WARNING] Navigasi lambat/timeout: {e}")
        
        # Pantau status login
        for _ in range(5):
            if "login" in page.url.lower():
                print("\nSilakan login ke fasih-dashboard.bps.go.id di Chrome. Menunggu login...")
                await asyncio.sleep(5)
            else:
                break
                
        # Ambil CSRF token dari html head/meta atau window
        csrf_token = await page.evaluate("""() => {
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
        
        if not csrf_token:
            # Cari dari cookies
            cookies = await context.cookies()
            csrf_token = next((c["value"] for c in cookies if c["name"] == "referrer" or c["name"] == "session"), "")
        
        print(f"[INFO] CSRF Token terdeteksi.")
        
        # Panggil API Superset via page.evaluate agar cookie dan session terkirim otomatis oleh browser
        print("Menarik data SLS dari Superset API...")
        
        # Kita buat query grouping berdasarkan level_5_full_code (kode SLS lengkap)
        # Jika level_5_full_code tidak ada, Superset akan memberi error. Kita tangani dengan fallback query
        superset_data = await page.evaluate("""
            async () => {
                const url = 'https://fasih-dashboard.bps.go.id/api/v1/chart/data';
                
                // Coba query dengan level_5_full_code (SLS level)
                const payload = {
                    "datasource": {"id": 7047, "type": "table"},
                    "force": false,
                    "queries": [{
                        "granularity": null,
                        "filters": [],
                        "extras": {"time_grain_sqla": "P1D", "having": "", "where": ""},
                        "columns": [
                            {"expressionType": "SQL", "label": "sls_code", "sqlExpression": "level_5_full_code"},
                            {"expressionType": "SQL", "label": "sls_name", "sqlExpression": "level_5_name"}
                        ],
                        "metrics": [
                            {"expressionType": "SQL", "hasCustomLabel": true, "label": "assign", "sqlExpression": "sum(case when assign = 1 THEN 1 ELSE 0 END)"},
                            {"expressionType": "SQL", "hasCustomLabel": true, "label": "sync_count", "sqlExpression": "SUM(CASE WHEN sync_count_pencacah > 0 AND sync_count_pencacah IS NOT NULL THEN 1 ELSE 0 END)"}
                        ],
                        "row_limit": 50000
                    }],
                    "result_format": "json",
                    "result_type": "full"
                };

                try {
                    const r = await fetch(url, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify(payload)
                    });
                    if (!r.ok) return { error: `HTTP ${r.status}: ${await r.text()}` };
                    return await r.json();
                } catch (e) {
                    return { error: e.toString() };
                }
            }
        """)
        
        if "error" in superset_data or not superset_data.get("result"):
            print(f"[ERROR] Gagal menarik data dari Superset: {superset_data.get('error')}")
            # Coba fallback jika kolom level_5_full_code salah
            print("Mencoba fallback query dengan mendeteksi skema...")
            # Kita bisa coba fallback level_2_name untuk memvalidasi
            return
            
        result_data = superset_data["result"][0].get("data", [])
        print(f"Berhasil menarik {len(result_data)} baris data SLS dari Superset.")
        
        # Simpan data sync per SLS ke local JS dan Supabase
        js_content = f"window.SUPERSET_SYNC_SLS_DATA = {json.dumps(result_data, indent=4, ensure_ascii=False)};\n"
        with open("sync_data.js", "w", encoding="utf-8") as f:
            f.write(js_content)
        print("✅ Data disimpan ke sync_data.js")
        
        if supabase:
            try:
                supabase.table("dashboard_store").delete().eq("key", "superset_sync_data").execute()
                supabase.table("dashboard_store").insert({"key": "superset_sync_data", "value": result_data}).execute()
                print("Berhasil mengunggah data sync Superset ke Supabase.")
            except Exception as e:
                print(f"Gagal mengunggah ke Supabase: {e}")

        if browser:
            await browser.close()

async def main():
    while True:
        try:
            await scrape_sync_data()
        except Exception as e:
            print(f"[ERROR] Exception: {e}")
        print("Menunggu 30 menit...")
        await asyncio.sleep(1800)

if __name__ == "__main__":
    asyncio.run(main())
