from playwright.sync_api import sync_playwright
import sys
import random
import time
import subprocess
import urllib.request
import urllib.error
import os

user_agan = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.7151.121 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.7103.114 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.7049.95 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.6998.166 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.6943.142 Safari/537.36",
]

# Pilih user agent secara acak dari list yang terverifikasi
user_agents = random.choice(user_agan)

# Reuse a single Playwright instance to avoid starting/stopping inside runtime
_PW = None
def _get_playwright():
    global _PW
    if _PW is None:
        _PW = sync_playwright().start()
    return _PW

def _stop_playwright():
    global _PW
    try:
        if _PW is not None:
            _PW.stop()
            _PW = None
    except Exception:
        pass

def login_with_sso(username, password, otp_code=None):
    """Lakukan login SSO ke MatchaPro dan kembalikan objek halaman jika berhasil."""
    pw = _get_playwright()

    chrome_path = r"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    user_data_dir = "./chrome_profile"
    debug_port = 9222
    debug_url = f"http://localhost:{debug_port}"

    try:
        urllib.request.urlopen(f"{debug_url}/json/version", timeout=1)
    except urllib.error.URLError:
        print("Membuka browser Chrome normal dengan mode debugging...")
        abs_user_data_dir = os.path.abspath(user_data_dir)
        subprocess.Popen([
            chrome_path,
            f"--remote-debugging-port={debug_port}",
            f"--user-data-dir={abs_user_data_dir}"
        ])
        time.sleep(4)

    browser = pw.chromium.connect_over_cdp(debug_url)
    context = browser.contexts[0] if browser.contexts else browser.new_context()
    page = context.pages[0] if context.pages else context.new_page()

    current_url = page.url
    if "fasih-sm.bps.go.id" in current_url and "login" not in current_url:
        print("Sudah login")
        return page, context

    try:
        # Navigasi ke halaman login
        page.goto("https://fasih-sm.bps.go.id/oauth2/authorization/ics")
        time.sleep(2)
        
        # Sekarang di halaman SSO, isi username dan password
        page.fill('input[name="username"]', username)
        page.fill('input[name="password"]', password)
        time.sleep(2)
        # Klik tombol submit
        page.click('input[type="submit"]')
        time.sleep(5)
        # Tunggu navigasi
        # page.wait_for_load_state('networkidle')

        # Cek apakah OTP diperlukan (TOTP)
        # try:
        #     otp_input = page.locator('input[name="otp"]').first
        #     if otp_input.is_visible(timeout=5000):
        #         if otp_code is None:
        #             otp_code = input("Masukkan kode OTP: ")
        #         otp_input.fill(otp_code)
        #         page.click('input[type="submit"]')  # Submit OTP
        #         page.wait_for_load_state('networkidle')
        # except:
        #     pass  # Tidak perlu OTP

        # Tunggu hingga URL berubah ke matchapro
        print('wait matchapro url')
        time.sleep(5)
        print(page.url)
        # Cek apakah login berhasil
        current_url = page.url
        if "fasih-sm.bps.go.id" in current_url and "login" not in current_url:
            print("Login berhasil!")
            return page, context  # Mengembalikan halaman dan context untuk menjaga sesi
        else:
            print("Login gagal. Periksa kredensial.")
            print(f"Current URL: {current_url}")
            try:
                context.close()
            except Exception:
                pass
            return None, None

    except Exception as e:
        print(f"Error selama login: {e}")
        try:
            page.screenshot(path="debug_error.png")
            print("Screenshot disimpan sebagai debug_error.png untuk analisa")
            context.close()
        except Exception:
            pass
        return None, None

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python login.py <username> <password> [otp_code]")
        sys.exit(1)

    username = sys.argv[1]
    password = sys.argv[2]
    otp_code = sys.argv[3] if len(sys.argv) > 3 else None

    page, context = login_with_sso(username, password, otp_code)
    if page:
        print("Objek halaman diperoleh.")
        try:
            context.close()
        except Exception:
            pass
    else:
        print("Gagal memperoleh objek halaman.")

    # Stop global Playwright instance on exit
    try:
        _stop_playwright()
    except Exception:
        pass
    
