import asyncio
import os
import socket
from playwright.async_api import async_playwright
from urllib.parse import unquote

def check_port_open(port=9222):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0
    except:
        return False

async def main():
    async with async_playwright() as p:
        port = 9223 if check_port_open(9223) else 9222
        print(f"Connecting to Chrome on port {port}...")
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
        except Exception as e:
            print("Failed to connect to browser context:", e)
            return

        # Register request interceptor
        async def on_request(request):
            url = request.url
            if "api" in url:
                print(f"[API REQ] {request.method} {url}")
                if request.post_data:
                    print(f"   Payload: {request.post_data[:200]}")

        async def on_response(response):
            url = response.url
            if "api" in url:
                try:
                    # check if response is json
                    content_type = response.headers.get("content-type", "")
                    if "json" in content_type:
                        print(f"[API RES] {response.status} {url}")
                        text = await response.text()
                        print(f"   Response: {text[:500]}")
                except Exception:
                    pass

        page.on("request", on_request)
        page.on("response", on_response)
        
        print("\n=== NETWORK INTERCEPTOR ACTIVE ===")
        print("Buka browser Chrome Anda, masuk ke halaman monitoring/alokasi petugas,")
        print("lalu silakan KLIK detail target yang REJECTED / REVOKED untuk melihat")
        print("request API apa yang dikirim oleh website FASIH BPS.")
        print("Tekan Ctrl+C di terminal ini jika sudah selesai.")
        print("===================================\n")
        
        # Keep running
        while True:
            await asyncio.sleep(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopped.")
