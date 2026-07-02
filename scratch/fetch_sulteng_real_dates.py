import asyncio
import json
import base64
import gzip
import os
import socket
from datetime import datetime, timezone, timedelta
from urllib.parse import unquote
from playwright.async_api import async_playwright
import pandas as pd
from openpyxl import load_workbook

# WITA timezone offset helper
def parse_iso_to_wita_date(iso_str):
    try:
        cleaned = iso_str.strip()
        if cleaned.endswith("Z"):
            cleaned = cleaned[:-1] + "+00:00"
        dt_utc = datetime.fromisoformat(cleaned)
        wita_offset = timezone(timedelta(hours=8))
        dt_wita = dt_utc.astimezone(wita_offset)
        return dt_wita.strftime("%Y-%m-%d")
    except Exception:
        return None

def check_port_open(port=9222):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0
    except:
        return False

async def get_browser_context(p):
    port = 9223 if check_port_open(9223) else 9222
    if check_port_open(port):
        print(f"[INFO] Menghubungkan ke browser di port {port}...")
        try:
            browser = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
            context = browser.contexts[0]
            page = None
            for p_page in context.pages:
                if "fasih-sm.bps.go.id" in p_page.url:
                    page = p_page
                    break
            if not page:
                page = await context.new_page()
                await page.goto("https://fasih-sm.bps.go.id/app/dashboard")
            return browser, context, page, True
        except Exception as e:
            print(f"[WARNING] Gagal connect CDP: {e}. Mencoba fallback...")
            
    # Fallback: launch persistent context
    print("[INFO] Port CDP tertutup. Mencoba membuka Chrome profile secara lokal...")
    try:
        abs_user_data_dir = os.path.abspath("playwright_chrome_profile")
        
        # Unlock profile if locked by a crashed process
        lock_file = os.path.join(abs_user_data_dir, "SingletonLock")
        if os.path.exists(lock_file) or os.path.islink(lock_file):
            try:
                os.unlink(lock_file)
                print("[INFO] Menghapus SingletonLock untuk membuka kunci profile.")
            except Exception as le:
                pass
                
        socket_file = os.path.join(abs_user_data_dir, "SingletonSocket")
        if os.path.exists(socket_file) or os.path.islink(socket_file):
            try:
                os.unlink(socket_file)
            except:
                pass
                
        chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        extra_args = ["--no-first-run", "--no-default-browser-check", "--disable-blink-features=AutomationControlled"]
        
        context = await p.chromium.launch_persistent_context(
            user_data_dir=abs_user_data_dir, headless=False, executable_path=chrome_path,
            ignore_default_args=["--enable-automation"],
            args=extra_args
        )
        page = context.pages[0] if context.pages else await context.new_page()
        print("[INFO] Membuka halaman dashboard FASIH...")
        await page.goto("https://fasih-sm.bps.go.id/app/dashboard", timeout=45000)
        
        # Cek jika dialihkan ke halaman login
        await asyncio.sleep(3)
        if "login" in page.url:
            print("\n==============================================================")
            print("[WARNING] Sesi FASIH Anda telah kedaluwarsa.")
            print("Harap LOGIN terlebih dahulu pada jendela browser Chrome yang baru terbuka.")
            print("Script akan mendeteksi otomatis jika Anda sudah berhasil login...")
            print("==============================================================\n")
            
            while "login" in page.url:
                await asyncio.sleep(2)
                
            print("[SUCCESS] Sesi berhasil dideteksi! Melanjutkan proses...")
            
        return None, context, page, False
    except Exception as e:
        print(f"[ERROR] Fallback gagal: {e}")
        print("\n====================================================================")
        print("[PERINGATAN] Chrome profile sedang dikunci/digunakan oleh aplikasi lain.")
        print("Harap TUTUP semua jendela Google Chrome Anda terlebih dahulu,")
        print("atau buka Chrome dengan debug mode: --remote-debugging-port=9222")
        print("====================================================================\n")
        return None, None, None, False

async def main():
    script_dir = "/Users/jihanmaisaroh/scrap_fasih"
    
    # 1. Kumpulkan semua target selesai se-Sulteng dari seluruh file granular se_umum
    completed_targets = []
    print("Mendata seluruh target selesai se-Sulteng...")
    
    # List seluruh kode kabupaten Sulteng (7201 - 7212 dan 7271 Palu)
    kab_codes = ["7201", "7202", "7203", "7204", "7205", "7206", "7207", "7208", "7209", "7210", "7211", "7212", "7271"]
    
    for code in kab_codes:
        file_name = f"granular_assignments_se_umum_{code}.json"
        json_path = os.path.join(script_dir, file_name)
        if os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                comp = data.get("compressed_data")
                raw = json.loads(gzip.decompress(base64.b64decode(comp)).decode('utf-8'))
                
                statuses_list = raw.get("statuses", [])
                targets = raw.get("targets", [])
                non_selesais = {"OPEN", "DRAFT", "-", ""}
                
                kab_completed_count = 0
                for t in targets:
                    tid = t[0]
                    stat_idx = t[3]
                    status_str = statuses_list[stat_idx] if stat_idx < len(statuses_list) else "-"
                    if status_str.upper() not in non_selesais:
                        # Simpan info target id, nama kabupaten, dan tipe survey
                        completed_targets.append({
                            "id": tid,
                            "kab_name": raw.get("kabupaten_name", "UNKNOWN").upper(),
                            "survey_type": "se_umum"
                        })
                        kab_completed_count += 1
                print(f" -> {file_name}: Ditemukan {kab_completed_count} selesai.")
            except Exception as e:
                print(f" -> Gagal membaca {file_name}: {e}")
                
    total_completed = len(completed_targets)
    print(f"\nTotal Target Selesai se-Sulteng: {total_completed}")
    if total_completed == 0:
        print("[WARNING] Tidak ada target selesai untuk dilacak tanggalnya.")
        return
        
    async with async_playwright() as p:
        browser, context, page, is_cdp = await get_browser_context(p)
        if not page:
            print("[ERROR] Gagal membuka browser. Batalkan proses.")
            return
            
        print("\n--- Memulai Penarikan Tanggal Submit Asli via Evaluasi Browser (Bypass Firewall) ---")
        
        # Buat mapping target_id -> info kabupaten & survey_type
        target_info_map = {item["id"]: item for item in completed_targets}
        target_ids_only = list(target_info_map.keys())
        
        batch_size = 40
        batches = [target_ids_only[i:i + batch_size] for i in range(0, total_completed, batch_size)]
        
        print(f"Total batch: {len(batches)} (Ukuran batch: {batch_size})")
        
        js_fetch_script = """
            async (targetIds) => {
                const promises = targetIds.map(async (id) => {
                    try {
                        const res = await fetch(`/app/api/assignment-general/api/assignment-history/get-by-assignment-id?assignmentId=${id}`);
                        if (res.ok) {
                            const logs = await res.json();
                            return { id, logs, success: true };
                        }
                        return { id, error: `HTTP ${res.status}`, success: false };
                    } catch (e) {
                        return { id, error: e.toString(), success: false };
                    }
                });
                return await Promise.all(promises);
            }
        """
        
        # Penampung data harian final
        # Format: key `KABUPATEN_YYYY-MM-DD_se_umum` -> count
        daily_stats_map = {}
        
        processed_count = 0
        for b_idx, batch in enumerate(batches):
            try:
                # Cek jika dialihkan ke halaman login saat proses berjalan
                if "login" in page.url:
                    print("\n==============================================================")
                    print("[WARNING] Sesi FASIH Anda terputus mid-way!")
                    print("Harap LOGIN kembali pada jendela browser Chrome yang terbuka.")
                    print("Script akan mendeteksi otomatis jika Anda sudah berhasil login...")
                    print("==============================================================\n")
                    while "login" in page.url:
                        await asyncio.sleep(2)
                    print("[SUCCESS] Sesi berhasil dideteksi kembali! Melanjutkan...")
                    await asyncio.sleep(2)

                results = await page.evaluate(js_fetch_script, batch)
                
                for r in results:
                    processed_count += 1
                    if isinstance(r, dict) and r.get("success"):
                        history_list = r.get("logs", [])
                        
                        submit_date = None
                        if isinstance(history_list, list):
                            for log in history_list:
                                if isinstance(log, dict):
                                    status_name = str(log.get("assignmentStatusName", "")).upper()
                                    if "SUBMIT" in status_name or "APPROV" in status_name or "EDITED" in status_name:
                                        date_created = log.get("dateCreated")
                                        if date_created:
                                            submit_date = parse_iso_to_wita_date(date_created)
                                            
                        if not submit_date and isinstance(history_list, list) and len(history_list) > 0:
                            first_log = history_list[0]
                            if isinstance(first_log, dict):
                                date_created = first_log.get("dateCreated")
                                if date_created:
                                    submit_date = parse_iso_to_wita_date(date_created)
                                
                        if submit_date:
                            tid = r["id"]
                            info = target_info_map[tid]
                            kab = info["kab_name"].replace("[", "").replace("]", "").strip()
                            # Hilangkan prefiks angka kabupaten jika ada
                            kab_clean = " ".join([word for word in kab.split() if not (word.isdigit() or (word.startswith("72") and len(word)==4))])
                            
                            key = (kab_clean, submit_date, info["survey_type"])
                            daily_stats_map[key] = daily_stats_map.get(key, 0) + 1
                            
                if processed_count % 200 == 0 or processed_count == total_completed:
                    print(f"   [PROGRESS] Berhasil memproses {processed_count} / {total_completed} target...")
                    
            except Exception as e:
                print(f"[WARNING] Gagal memproses batch {b_idx}: {e}")
                try:
                    page = context.pages[0] if context.pages else await context.new_page()
                except:
                    pass
                await asyncio.sleep(3)
                
        if browser:
            await browser.disconnect()
        else:
            await context.close()
            
    if not daily_stats_map:
        print("[ERROR] Gagal menarik tanggal submit asli.")
        return
        
    # Reformat menjadi array untuk daily_submission_stats
    daily_stats_data = []
    for (kab_name, date_str, s_type), count in daily_stats_map.items():
        daily_stats_data.append({
            "date": date_str,
            "count": count,
            "kab_name": kab_name,
            "survey_type": s_type
        })
        
    # Tulis hasil ke daily_submission_stats.json dan daily_submission_stats.js
    stats_json_path = os.path.join(script_dir, "daily_submission_stats.json")
    stats_js_path = os.path.join(script_dir, "daily_submission_stats.js")
    
    with open(stats_json_path, "w", encoding="utf-8") as f:
        json.dump(daily_stats_data, f, indent=4)
    print(f"\n✅ JSON timeline harian disimpan ke {stats_json_path}")
    
    with open(stats_js_path, "w", encoding="utf-8") as f:
        f.write(f"window.DAILY_SUBMISSION_STATS = {json.dumps(daily_stats_data, indent=4)};\n")
    print(f"✅ JS timeline harian disimpan ke {stats_js_path}")
    
    # Upload ke database Supabase agar index web langsung terupdate real-time!
    from dotenv import load_dotenv
    from supabase import create_client
    load_dotenv()
    
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    if SUPABASE_URL and SUPABASE_KEY:
        try:
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            print("Menghubungkan ke database Supabase...")
            
            # Key live utama
            supabase.table("dashboard_store").delete().eq("key", "daily_submission_stats").execute()
            supabase.table("dashboard_store").insert({"key": "daily_submission_stats", "value": daily_stats_data}).execute()
            print("✅ Key 'daily_submission_stats' berhasil diperbarui di database Supabase!")
            
            # Key snapshot hari ini
            today_str = datetime.now().strftime("%Y-%m-%d")
            daily_key = f"daily_submission_stats:{today_str}"
            supabase.table("dashboard_store").delete().eq("eq", daily_key).execute() # check key matching
            supabase.table("dashboard_store").delete().eq("key", daily_key).execute()
            supabase.table("dashboard_store").insert({"key": daily_key, "value": daily_stats_data}).execute()
            print(f"✅ Key snapshot '{daily_key}' berhasil diperbarui!")
            
            print("\n🎉 SELURUH PROSES SE-SULTENG BERHASIL! DASHBOARD SIAP DI-REFRESH!")
        except Exception as e:
            print(f"[ERROR] Gagal mengunggah daily_submission_stats ke Supabase: {e}")
    else:
        print("[WARNING] Supabase credentials tidak ditemukan di .env. Hanya menyimpan lokal.")

if __name__ == "__main__":
    asyncio.run(main())
