import asyncio
import json
import base64
import gzip
import os
import socket
from datetime import datetime, timezone, timedelta
from playwright.async_api import async_playwright
from supabase import create_client
from dotenv import load_dotenv

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
    print("[INFO] Port CDP tertutup. Membuka browser Chrome secara visual...")
    try:
        abs_user_data_dir = os.path.abspath("playwright_chrome_profile")
        
        # Unlock profile
        lock_file = os.path.join(abs_user_data_dir, "SingletonLock")
        if os.path.exists(lock_file) or os.path.islink(lock_file):
            try: os.unlink(lock_file)
            except: pass
        socket_file = os.path.join(abs_user_data_dir, "SingletonSocket")
        if os.path.exists(socket_file) or os.path.islink(socket_file):
            try: os.unlink(socket_file)
            except: pass
            
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
        return None, None, None, False

async def main():
    script_dir = "/Users/jihanmaisaroh/scrap_fasih"
    db_path = os.path.join(script_dir, "target_real_dates.json")
    
    # 1. Load database lokal yang sudah ada
    cached_dates = {}
    if os.path.exists(db_path):
        try:
            with open(db_path, "r", encoding="utf-8") as f:
                cached_dates = json.load(f)
            print(f"[INFO] Loaded {len(cached_dates)} target dates dari database lokal.")
        except Exception as e:
            print(f"[WARNING] Gagal membaca database lokal: {e}. Membuat baru...")
            
    # 2. Baca seluruh data granular se-Sulteng untuk mendata target selesai saat ini
    completed_targets = {} # target_id -> {status_str, kab_name, survey_type}
    kab_codes = ["7201", "7202", "7203", "7204", "7205", "7206", "7207", "7208", "7209", "7210", "7211", "7212", "7271"]
    
    print("\nMendata seluruh target selesai se-Sulteng dari data granular...")
    non_selesais = {"OPEN", "DRAFT", "-", ""}
    
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
                regions_list = raw.get("regions", [])
                
                for t in targets:
                    tid = t[0]
                    stat_idx = t[3]
                    reg_idx = t[5] if len(t) > 5 else 0
                    
                    # Resolve kab_name dynamically from regions list
                    reg_info = regions_list[reg_idx] if reg_idx < len(regions_list) else ["-", "UNKNOWN"]
                    kab_raw = reg_info[1] if len(reg_info) > 1 else "UNKNOWN"
                    
                    # Clean kabupaten name
                    kab_clean = " ".join([word for word in kab_raw.split() if not (word.isdigit() or (word.startswith("72") and len(word)==4))]).upper()
                    
                    status_str = statuses_list[stat_idx] if stat_idx < len(statuses_list) else "-"
                    if status_str.upper() not in non_selesais:
                        completed_targets[tid] = {
                            "status": status_str,
                            "kab_name": kab_clean,
                            "survey_type": "se_umum"
                        }
                        
                        # Extract and parse timestamp if available in granular file
                        epoch_val = t[6] if len(t) > 6 else 0
                        if epoch_val > 0:
                            try:
                                # Check if millisecond or second timestamp
                                dt_sec = epoch_val / 1000.0 if epoch_val > 10**11 else float(epoch_val)
                                dt_utc = datetime.fromtimestamp(dt_sec, tz=timezone.utc)
                                wita_offset = timezone(timedelta(hours=8))
                                dt_wita = dt_utc.astimezone(wita_offset)
                                submit_date = dt_wita.strftime("%Y-%m-%d")
                                
                                # Directly insert into cached_dates to skip API fetching!
                                cached_dates[tid] = {
                                    "date": submit_date,
                                    "status": status_str
                                }
                            except Exception as pe:
                                pass
                kab_completed_count = sum(1 for t in targets if (statuses_list[t[3]].upper() if t[3] < len(statuses_list) else "-") not in non_selesais)
                print(f" -> {file_name}: Ditemukan {kab_completed_count} selesai.")
            except Exception as e:
                print(f" -> Gagal membaca {file_name}: {e}")
                
    total_completed_now = len(completed_targets)
    print(f"Total target selesai terdeteksi saat ini: {total_completed_now}")
    
    # 3. Cari target mana saja yang perlu ditarik (belum ada tanggalnya, atau statusnya berubah)
    targets_to_fetch = []
    for tid, info in completed_targets.items():
        cached = cached_dates.get(tid)
        if not cached or cached.get("status") != info["status"]:
            targets_to_fetch.append(tid)
            
    total_to_fetch = len(targets_to_fetch)
    print(f"Target baru / status berubah untuk ditarik tanggalnya: {total_to_fetch}")
    
    # Membatasi jumlah penarikan per-run agar cepat dan tidak timeout
    MAX_FETCH_LIMIT = 5000
    if total_to_fetch > MAX_FETCH_LIMIT:
        print(f"[INFO] Membatasi penarikan tanggal ke {MAX_FETCH_LIMIT} target saja per run untuk efisiensi...")
        targets_to_fetch = targets_to_fetch[:MAX_FETCH_LIMIT]
        total_to_fetch = MAX_FETCH_LIMIT
        
    # 4. Tarik data jika ada target baru
    if total_to_fetch > 0:
        async with async_playwright() as p:
            browser, context, page, is_cdp = await get_browser_context(p)
            if not page:
                print("[ERROR] Gagal membuka browser. Batalkan proses penarikan tanggal baru.")
                return
                
            print(f"\n--- Memulai Penarikan {total_to_fetch} Tanggal Baru via Evaluasi Browser ---")
            batch_size = 40
            batches = [targets_to_fetch[i:i + batch_size] for i in range(0, total_to_fetch, batch_size)]
            
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
            
            processed_count = 0
            b_idx = 0
            while b_idx < len(batches):
                batch = batches[b_idx]
                try:
                    # Sesi login check
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
                                cached_dates[tid] = {
                                    "date": submit_date,
                                    "status": completed_targets[tid]["status"]
                                }
                                
                    if processed_count % 200 == 0 or processed_count == total_to_fetch:
                        print(f"   [PROGRESS] Berhasil memproses {processed_count} / {total_to_fetch} target...")
                        
                    b_idx += 1
                except Exception as e:
                    print(f"[WARNING] Gagal memproses batch {b_idx} (akan dicoba kembali): {e}")
                    try:
                        page = context.pages[0] if context.pages else await context.new_page()
                    except Exception:
                        pass
                    await asyncio.sleep(5)
                    
            if browser:
                try:
                    await browser.close()
                except Exception as e:
                    print(f"[WARNING] Gagal menutup browser: {e}")
            else:
                try:
                    await context.close()
                except Exception as e:
                    print(f"[WARNING] Gagal menutup context: {e}")
                
        # Simpan pembaruan database lokal
        try:
            with open(db_path, "w", encoding="utf-8") as f:
                json.dump(cached_dates, f, indent=4)
            print(f"✅ Database lokal target_real_dates.json berhasil diperbarui!")
        except Exception as e:
            print(f"[ERROR] Gagal menyimpan database lokal: {e}")
            
    # 5. Kompilasi data timeline harian se-Sulteng dari database lokal
    print("\nMenyusun statistik progres harian se-Sulteng...")
    daily_stats_map = {} # (kab_name, date_str, status_str, survey_type) -> count
    
    for tid, info in completed_targets.items():
        record = cached_dates.get(tid)
        submit_date = None
        status_str = None
        if record and record.get("date"):
            submit_date = record["date"]
            status_str = record.get("status") or info["status"]
        else:
            # Fallback date untuk target selesai yang belum ter-fetch tanggal aslinya
            # agar total di grafik harian tetap cocok dengan total real-time BPS
            submit_date = "2026-06-09"
            status_str = info["status"]
            
        key = (info["kab_name"], submit_date, status_str, info["survey_type"])
        daily_stats_map[key] = daily_stats_map.get(key, 0) + 1
            
    # Format ke array untuk Supabase
    daily_stats_data = []
    for (kab_name, date_str, status_str, s_type), count in daily_stats_map.items():
        daily_stats_data.append({
            "date": date_str,
            "count": count,
            "kab_name": kab_name,
            "status": status_str,
            "survey_type": s_type
        })
        
    if not daily_stats_data:
        print("\n⚠️ [WARNING] Tidak ada data timeline harian yang dihasilkan (cached_dates kosong).")
        print("Proses penyimpanan dan pengunggahan dibatalkan untuk mencegah data yang sudah ada di Supabase terhapus.")
        return
        
    # Tulis file lokal
    stats_json_path = os.path.join(script_dir, "daily_submission_stats.json")
    stats_js_path = os.path.join(script_dir, "daily_submission_stats.js")
    
    with open(stats_json_path, "w", encoding="utf-8") as f:
        json.dump(daily_stats_data, f, indent=4)
    print(f"✅ JSON daily_submission_stats.json disimpan.")
    
    with open(stats_js_path, "w", encoding="utf-8") as f:
        f.write(f"window.DAILY_SUBMISSION_STATS = {json.dumps(daily_stats_data, indent=4)};\n")
    print(f"✅ JS daily_submission_stats.js disimpan.")
    
    # 6. Upload ke Supabase
    load_dotenv()
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    if SUPABASE_URL and SUPABASE_KEY:
        try:
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            print("Mengunggah daily_submission_stats ke Supabase...")
            
            supabase.table("dashboard_store").delete().eq("key", "daily_submission_stats").execute()
            supabase.table("dashboard_store").insert({"key": "daily_submission_stats", "value": daily_stats_data}).execute()
            print("✅ Key 'daily_submission_stats' berhasil diperbarui di Supabase!")
            
            today_str = datetime.now().strftime("%Y-%m-%d")
            daily_key = f"daily_submission_stats:{today_str}"
            supabase.table("dashboard_store").delete().eq("key", daily_key).execute()
            supabase.table("dashboard_store").insert({"key": daily_key, "value": daily_stats_data}).execute()
            print(f"✅ Key snapshot '{daily_key}' berhasil diperbarui!")
        except Exception as e:
            print(f"[ERROR] Gagal mengunggah ke Supabase: {e}")
    else:
        print("[WARNING] Credentials Supabase tidak ditemukan. Hanya simpan lokal.")

if __name__ == "__main__":
    asyncio.run(main())
