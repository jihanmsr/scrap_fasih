"""
intercept_assign.py
-------------------
Script untuk menangkap (intercept) request assign petugas dari browser FASIH.

CARA PAKAI:
1. Tutup semua Chrome yang sedang berjalan
2. Jalankan script ini: python3 intercept_assign.py
3. Browser Chromium akan terbuka otomatis (sudah login jika profil ada sesinya)
4. Di FASIH, buka halaman assignment Toli-Toli
5. Lakukan assign 1 petugas secara manual (klik tombol assign)
6. Script otomatis menangkap URL endpoint + payload-nya
7. Output disimpan ke: captured_assign_request.json
8. Tekan Ctrl+C setelah selesai
"""

import json
import time
import os
from playwright.sync_api import sync_playwright

CHROME_PATH = "/Users/jihanmaisaroh/Library/Caches/ms-playwright/chromium-1208/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"

# Profil yang sudah ada sesi login FASIH
USER_DATA_DIR = os.path.abspath("playwright_chrome_profile")

OUTPUT_FILE = "captured_assign_request.json"

# Keywords yang kemungkinan ada di endpoint assign
ASSIGN_KEYWORDS = [
    "assign",
    "officer",
    "petugas",
    "user-assignment",
    "set-user",
    "update-user",
]

captured = []


def is_assign_url(url: str) -> bool:
    url_lower = url.lower()
    return (
        any(kw in url_lower for kw in ASSIGN_KEYWORDS)
        and "fasih-sm.bps.go.id" in url_lower
    )


def main():
    print("=" * 65)
    print("  INTERCEPT ASSIGN FASIH")
    print("=" * 65)
    print(f"[INFO] Menggunakan profil: {USER_DATA_DIR}")
    print("[INFO] Membuka browser Chromium...")

    with sync_playwright() as p:
        # Hapus SingletonLock agar profil bisa dibuka kembali
        lock_file = os.path.join(USER_DATA_DIR, "SingletonLock")
        if os.path.lexists(lock_file):
            try:
                os.remove(lock_file)
                print("[INFO] SingletonLock dihapus.")
            except Exception as e:
                print(f"[WARNING] Gagal hapus SingletonLock: {e}")

        # Launch dengan profil yang sudah ada (sudah login FASIH)
        try:
            context = p.chromium.launch_persistent_context(
                user_data_dir=USER_DATA_DIR,
                headless=False,
                executable_path=CHROME_PATH,
                args=[
                    "--no-first-run",
                    "--no-default-browser-check",
                    "--disable-background-networking",
                ],
                ignore_https_errors=True,
            )
            print("[INFO] Browser berhasil dibuka.")
        except Exception as e:
            print(f"[ERROR] Gagal membuka browser: {e}")
            print()
            print("Kemungkinan penyebab:")
            print("  - Masih ada Chrome/Chromium yang berjalan dengan profil yang sama")
            print("  - Solusi: Tutup semua Chrome dulu, lalu jalankan ulang script ini")
            return

        # Cari tab FASIH yang sudah ada, atau buka baru
        page = None
        for pg in context.pages:
            if "fasih-sm.bps.go.id" in pg.url:
                page = pg
                print(f"[INFO] Menemukan tab FASIH: {pg.url}")
                break

        if not page:
            page = context.new_page()
            fasih_url = "https://fasih-sm.bps.go.id/app/dashboard"
            print(f"[INFO] Membuka FASIH: {fasih_url}")
            try:
                page.goto(fasih_url, timeout=30000, wait_until="domcontentloaded")
            except Exception as e:
                print(f"[WARNING] Timeout saat buka FASIH (lanjut saja): {e}")

        def on_request(request):
            if request.method in ("POST", "PUT", "PATCH", "DELETE") and is_assign_url(request.url):
                try:
                    body = request.post_data
                except Exception:
                    body = None

                entry = {
                    "method": request.method,
                    "url": request.url,
                    "headers": dict(request.headers),
                    "body_raw": body,
                    "body_parsed": None,
                    "response_status": None,
                    "response_body": None,
                }

                if body:
                    try:
                        entry["body_parsed"] = json.loads(body)
                    except Exception:
                        pass

                captured.append(entry)
                print(f"\n🎯 REQUEST TERTANGKAP! [{request.method}] {request.url}")
                if entry["body_parsed"]:
                    print(f"   Payload:\n{json.dumps(entry['body_parsed'], indent=4, ensure_ascii=False)[:800]}")
                elif body:
                    print(f"   Body raw: {str(body)[:300]}")

        def on_response(response):
            if response.request.method in ("POST", "PUT", "PATCH", "DELETE") and is_assign_url(response.request.url):
                try:
                    resp_body = response.json()
                except Exception:
                    try:
                        resp_body = response.text()
                    except Exception:
                        resp_body = None

                for entry in reversed(captured):
                    if entry["url"] == response.request.url and entry["response_status"] is None:
                        entry["response_status"] = response.status
                        entry["response_body"] = resp_body
                        print(f"   ↩ Response [{response.status}]: {str(resp_body)[:400]}")
                        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                            json.dump(captured, f, indent=2, ensure_ascii=False)
                        print(f"   💾 Disimpan ke {OUTPUT_FILE}")
                        break

        # Pasang listener ke semua page yang ada
        for pg in context.pages:
            pg.on("request", on_request)
            pg.on("response", on_response)

        # Pasang ke page baru yang dibuka nanti
        def on_new_page(new_page):
            new_page.on("request", on_request)
            new_page.on("response", on_response)
            print(f"[INFO] Listener dipasang ke tab baru: {new_page.url or '(loading...)'}")

        context.on("page", on_new_page)

        print()
        print("=" * 65)
        print("✅ INTERCEPT AKTIF! Browser sudah terbuka.")
        print("=" * 65)
        print("Langkah selanjutnya:")
        print("  1. Login ke FASIH jika belum (atau sudah otomatis login)")
        print("  2. Buka halaman Assignment survey Toli-Toli")
        print("  3. Assign 1 petugas secara manual (klik tombol assign)")
        print("  4. Script otomatis menangkap request-nya")
        print()
        print("Tekan Ctrl+C di terminal ini setelah selesai.")
        print("=" * 65 + "\n")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n[INFO] Intercept dihentikan oleh user.")

        # Simpan final
        if captured:
            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                json.dump(captured, f, indent=2, ensure_ascii=False)
            print(f"\n✅ Total {len(captured)} request assign tertangkap!")
            print(f"📁 File: {os.path.abspath(OUTPUT_FILE)}")
            print("\n📋 Ringkasan:")
            for i, entry in enumerate(captured):
                print(f"  [{i+1}] {entry['method']} {entry['url']}")
                print(f"       Response: {entry.get('response_status')}")
        else:
            print("\n⚠️  Tidak ada request assign yang tertangkap.")
            print("Pastikan kamu klik tombol assign di FASIH sebelum Ctrl+C.")

        context.close()


if __name__ == "__main__":
    main()
