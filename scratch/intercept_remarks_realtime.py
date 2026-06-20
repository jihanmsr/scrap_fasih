import asyncio
import os
import socket
import sys
import time
from playwright.async_api import async_playwright
from urllib.parse import unquote

def check_port_open(port=9222):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0
    except:
        return False

async def main():
    duration = 180 # 3 minutes listening
    print(f"Mengaktifkan interceptor jaringan selama {duration} detik...")
    
    async with async_playwright() as p:
        port = 9223 if check_port_open(9223) else 9222
        print(f"Menghubungkan ke Chrome pada port {port}...")
        try:
            browser = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
            context = browser.contexts[0]
            
            # Cari tab aktif FASIH
            page = None
            for p_page in context.pages:
                if "fasih-sm.bps.go.id" in p_page.url:
                    page = p_page
                    break
                    
            if not page:
                print("[WARNING] Tab aktif BPS FASIH tidak ditemukan. Membuka tab baru...")
                page = await context.new_page()
                await page.goto("https://fasih-sm.bps.go.id/app/dashboard")
                
            print(f"[INFO] Sukses terhubung ke tab: {page.url}")
        except Exception as e:
            print("Gagal menghubungkan ke browser Chrome:", e)
            return

        # Request handler
        async def on_request(request):
            url = request.url
            if "api" in url and "datatable" not in url and "region" not in url:
                print(f"\n[API REQ] {request.method} {url}")
                if request.post_data:
                    print(f"   Payload: {request.post_data}")

        # Response handler
        async def on_response(response):
            url = response.url
            if "api" in url and "datatable" not in url and "region" not in url:
                try:
                    content_type = response.headers.get("content-type", "")
                    if "json" in content_type:
                        text = await response.text()
                        print(f"[API RES] {response.status} {url}")
                        print(f"   Response JSON: {text[:1500]}")
                except Exception:
                    pass

        page.on("request", on_request)
        page.on("response", on_response)
        
        print("\n" + "="*80)
        print("INTERCEPTOR AKTIF! SILAKAN LAKUKAN TINDAKAN INI DI BROWSER CHROMIUM:")
        print("1. Pergi ke tabel monitoring/target di FASIH.")
        print("2. Cari target yang REJECTED BY Pengawas atau REVOKED BY Pengawas.")
        print("3. KLIK tombol detail/remarks/catatan atau aksi log status pada target tersebut.")
        print("4. Perhatikan output di terminal ini untuk melihat API yang dipanggil.")
        print("="*80 + "\n")
        
        # Poll for duration
        for sec in range(duration):
            print(f"[{duration - sec}s tersisa] Mendengarkan...", end="\r")
            await asyncio.sleep(1)
            
        print("\nWaktu mendengarkan selesai.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nDihentikan oleh pengguna.")
