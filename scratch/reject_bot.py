import asyncio
import os
import sys
import json
import socket
from playwright.async_api import async_playwright

# Konfigurasi Default
DEFAULT_SURVEY_PERIOD = "fd68e454-ba45-4b85-8205-f3bf777ded24" # SE Umum
DEFAULT_PROFILE = "playwright_chrome_profile_w2"

def check_port_open(port=9222):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0
    except:
        return False

def load_assignment_details(file_path):
    import pandas as pd
    import re
    try:
        if not os.path.exists(file_path):
            return {}
        df = pd.read_excel(file_path, header=3)
        uuid_pattern = re.compile(r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$')
        
        details = {}
        for _, row in df.iterrows():
            aid = str(row.get("Assignment ID", "")).strip()
            if uuid_pattern.match(aid):
                details[aid] = {
                    "nama_krt": str(row.get("Nama KRT", "N/A")).strip(),
                    "kecamatan": str(row.get("Nama Kecamatan", "N/A")).strip(),
                    "desa": str(row.get("Nama Desa/Kel", "N/A")).strip()
                }
        return details
    except Exception as e:
        print(f"[WARNING] Gagal membaca detail dari Excel: {e}")
        return {}

async def get_browser_context(p):
    """
    Mencoba terhubung ke browser aktif via CDP (remote debugging) terlebih dahulu.
    Jika gagal, meluncurkan Chrome persistent menggunakan profile lokal.
    """
    for port in [9223, 9222]:
        if check_port_open(port):
            print(f"[INFO] Mendeteksi browser aktif di port {port}. Menghubungkan via CDP...")
            try:
                browser = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
                context = browser.contexts[0] if browser.contexts else await browser.new_context()
                page = context.pages[0] if context.pages else await context.new_page()
                return browser, context, page, True
            except Exception as e:
                print(f"[WARNING] Gagal menghubungkan via CDP di port {port}: {e}")
                
    # Fallback ke launch persistent context
    user_data_dir = os.path.abspath(DEFAULT_PROFILE)
    chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    print(f"[INFO] Meluncurkan Chrome dengan profile: {user_data_dir}")
    
    try:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False, # Set ke False agar user bisa melihat prosesnya
            executable_path=chrome_path,
            ignore_default_args=["--enable-automation"],
            args=["--no-first-run", "--no-default-browser-check", "--disable-blink-features=AutomationControlled"]
        )
        page = context.pages[0] if context.pages else await context.new_page()
        return None, context, page, False
    except Exception as e:
        print(f"[ERROR] Gagal meluncurkan Chrome: {e}")
        return None, None, None, False

async def reject_assignment(page, assignment_id, period_id, details_map=None):
    url = f"https://fasih-sm.bps.go.id/app/assignment/{period_id}/{assignment_id}"
    print(f"\n[START] Memproses ID: {assignment_id}")
    print(f" -> Navigasi ke: {url}")
    
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(4) # Beri waktu render komponen Vue/React
        
        # Cek jika diarahkan ke halaman login
        if page.url.endswith("/app") or page.url.endswith("/app/") or "login" in page.url:
            print("[WARNING] Sesi terputus! Silakan login di browser terlebih dahulu.")
            return False, "Sesi terputus / Ter-logout"

        # 1. Tunggu tombol FAB / Open Menu
        print(" -> Mencari tombol FAB (Open Menu)...")
        fab_selector = 'button[aria-label="Open menu"], button.fab-button'
        try:
            await page.wait_for_selector(fab_selector, state="visible", timeout=12000)
        except Exception as e:
            # Cek apakah halaman menampilkan error bawaan FASIH
            has_error_message = await page.locator("text=There's some error").count() > 0 or await page.locator("text=difficulty loading this page").count() > 0
            if has_error_message:
                reason = "Halaman error (There's some error dari FASIH)"
            else:
                reason = "Tombol FAB tidak ditemukan (Kemungkinan belum disubmit / tidak punya akses wilayah)"
            
            print(f" ❌ {reason}. URL saat ini: {page.url}")
            try:
                os.makedirs("scratch", exist_ok=True)
                screenshot_path = "scratch/error_target.png"
                await page.screenshot(path=screenshot_path)
                print(f" -> Screenshot halaman saat ini disimpan di: {screenshot_path}")
            except Exception as se:
                print(f" -> Gagal menyimpan screenshot: {se}")
            return False, reason
            
        fab_button = page.locator(fab_selector)
        
        # Buka menu jika masih tertutup
        is_closed = await fab_button.evaluate("el => el.classList.contains('is-closed')")
        if is_closed:
            print(" -> Mengklik tombol FAB untuk membuka menu...")
            await fab_button.click()
            await asyncio.sleep(0.8)
            
        # 2. Cari tombol Reject di dalam menu FAB
        print(" -> Mencari tombol Reject...")
        try:
            reject_button = page.locator("div.fab-item").filter(has_text="Reject").locator("button").first
            await reject_button.wait_for(state="visible", timeout=5000)
            print(" -> Mengklik tombol Reject...")
            await reject_button.click()
            await asyncio.sleep(1)
        except Exception as e:
            print(f" ❌ Tombol Reject tidak ditemukan atau tidak bisa diklik: {e}")
            return False, "Tombol Reject tidak ditemukan/tidak aktif"
            
        # 3. Handle modal konfirmasi
        print(" -> Menunggu modal konfirmasi...")
        confirm_btn_selector = 'button:has-text("Konfirmasi"), button.bg-destructive'
        try:
            confirm_button = page.locator(confirm_btn_selector).first
            await confirm_button.wait_for(state="visible", timeout=5000)
            print(" -> Mengklik tombol Konfirmasi...")
            await confirm_button.click()
            
            # Tunggu proses selesai (biasanya ada toast message atau loading spinner menghilang)
            await asyncio.sleep(3)
            
            info = details_map.get(assignment_id, {}) if details_map else {}
            nama_krt = info.get("nama_krt", "N/A")
            kec = info.get("kecamatan", "N/A")
            desa = info.get("desa", "N/A")
            print(f" 🎉 [SUCCESS] BERHASIL REJECT: ID: {assignment_id} | KRT: {nama_krt} | Kec: {kec} | Desa: {desa}")
            return True, "Success"
        except Exception as e:
            print(f" ❌ Gagal melakukan konfirmasi penolakan: {e}")
            return False, f"Gagal konfirmasi: {e}"
            
    except Exception as e:
        print(f" ❌ Error memproses ID {assignment_id}: {e}")
        return False, f"Error: {e}"

async def main():
    # Menentukan list ID yang akan diproses
    assignment_ids = []
    
    # 1. Coba baca dari argument command line
    if len(sys.argv) > 1:
        # Jika argument berupa path file
        if os.path.isfile(sys.argv[1]):
            try:
                with open(sys.argv[1], "r") as f:
                    # Bisa file JSON atau teks biasa per baris
                    if sys.argv[1].endswith(".json"):
                        assignment_ids = json.load(f)
                    else:
                        assignment_ids = [line.strip() for line in f if line.strip()]
                print(f"[INFO] Membaca {len(assignment_ids)} ID dari file: {sys.argv[1]}")
            except Exception as e:
                print(f"[ERROR] Gagal membaca file {sys.argv[1]}: {e}")
                return
        else:
            # Jika argument berupa list ID dipisahkan spasi/koma
            assignment_ids = [x.strip() for arg in sys.argv[1:] for x in arg.replace(",", " ").split() if x.strip()]
            print(f"[INFO] Membaca {len(assignment_ids)} ID dari argumen perintah.")
            
    # 2. Coba baca dari file input default jika ada (misal scratch/ids_to_reject.json)
    if not assignment_ids:
        default_file = "scratch/ids_to_reject.json"
        if os.path.exists(default_file):
            try:
                with open(default_file, "r") as f:
                    assignment_ids = json.load(f)
                print(f"[INFO] Membaca {len(assignment_ids)} ID dari file default {default_file}")
            except Exception as e:
                pass
                
    # 3. Jika masih kosong, beri template contoh
    if not assignment_ids:
        print("\n==============================================================")
        # Sediakan template list agar user bisa mengedit script ini secara langsung
        assignment_ids = [
            # Tuliskan ID target di bawah ini, contoh:
            # "1fff7d8c-c35e-4d9f-856c-3ec53ef0d316",
        ]
        if not assignment_ids:
            print("[WARNING] Tidak ada ID target yang diberikan untuk diproses.")
            print("Cara menggunakan:")
            print("  1. Edit script ini dan isi list 'assignment_ids' di atas.")
            print("  2. Atau jalankan perintah: python3 scratch/reject_bot.py ID_1 ID_2 ID_3")
            print("  3. Atau simpan list ID dalam format JSON di scratch/ids_to_reject.json")
            print("==============================================================\n")
            return

    # Load metadata dari Excel untuk logs yang informatif
    excel_path = "/Users/jihanmaisaroh/scrap_fasih/Data_Mikro_Anomali_keluarga_5321_20260701_111359.xlsx"
    print(f"[INFO] Membaca metadata keluarga dari Excel: {excel_path} ...")
    details_map = load_assignment_details(excel_path)
    print(f"[INFO] Terbaca {len(details_map)} data keluarga untuk logging.")

    # Inisialisasi Playwright
    async with async_playwright() as p:
        browser, context, page, is_cdp = await get_browser_context(p)
        if not page:
            print("[ERROR] Gagal memulai browser context.")
            return
            
        # 1. Buka halaman utama dan langsung minta user login
        print(" -> Membuka halaman surveys...")
        try:
            await page.goto("https://fasih-sm.bps.go.id/app/surveys", wait_until="domcontentloaded", timeout=30000)
        except Exception as e:
            print(f"[WARNING] Gagal memuat halaman: {e}")
            
        print("\n==============================================================")
        print("[PETUNJUK] Silakan pastikan Anda sudah LOGIN di browser Chrome yang baru terbuka.")
        print("Jika belum login, silakan login terlebih dahulu.")
        print("Setelah Anda berada di halaman dashboard / daftar survei,")
        print("kembali ke terminal ini dan tekan ENTER untuk memulai proses reject bot...")
        print("==============================================================\n")
        
        # Menunggu input dari user secara non-blocking terhadap event loop
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, input, "Tekan ENTER jika sudah siap...")
        
        # Navigasi ulang ke surveys setelah login untuk memicu refresh state session di Playwright
        print(" -> Menyegarkan sesi...")
        try:
            await page.goto("https://fasih-sm.bps.go.id/app/surveys", wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(2)
        except Exception as e:
            pass
            
        print("[SUCCESS] Memulai proses penolakan...")
        
        def save_report(data):
            try:
                import pandas as pd
                report_df = pd.DataFrame(data)
                report_csv = "scratch/reject_report.csv"
                report_json = "scratch/reject_report.json"
                report_df.to_csv(report_csv, index=False)
                with open(report_json, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
            except Exception as e:
                pass

        success_count = 0
        fail_count = 0
        results_report = []
        
        try:
            for idx, aid in enumerate(assignment_ids):
                print(f"\n[Progress] {idx+1}/{len(assignment_ids)}")
                success, reason = await reject_assignment(page, aid, DEFAULT_SURVEY_PERIOD, details_map)
                
                info = details_map.get(aid, {})
                results_report.append({
                    "No": idx + 1,
                    "Assignment ID": aid,
                    "Nama KRT": info.get("nama_krt", "N/A"),
                    "Kecamatan": info.get("kecamatan", "N/A"),
                    "Desa": info.get("desa", "N/A"),
                    "Status": "SUCCESS" if success else "FAILED",
                    "Alasan": reason
                })
                
                if success:
                    success_count += 1
                else:
                    fail_count += 1
                
                # Simpan report secara berkala
                if (idx + 1) % 5 == 0:
                    save_report(results_report)
        finally:
            # Simpan report terakhir saat keluar / ditekan Ctrl+C
            save_report(results_report)
            
            print("\n" + "="*40)
            print("             Laporan Selesai")
            print("="*40)
            print(f" Total diproses : {len(results_report)}")
            print(f" Berhasil       : {success_count}")
            print(f" Gagal          : {len(results_report) - success_count}")
            print("="*40 + "\n")
            print(f"[INFO] Laporan hasil proses disimpan di:")
            print(f"  - CSV: scratch/reject_report.csv")
            print(f"  - JSON: scratch/reject_report.json")
            
            # Tutup browser hanya jika kita yang meluncurkannya sendiri (bukan CDP)
            if not is_cdp:
                await context.close()
            else:
                await browser.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
