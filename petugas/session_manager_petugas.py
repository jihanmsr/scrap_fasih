import os
import json
import time
from login import login_with_sso

requests_list = []

def handle_request(request):
    if request.resource_type in ["xhr", "fetch"]:
        if 'datatable-all-user-survey-periode' in request.url:
            requests_list.append({
                "url": request.url,
                "method": request.method,
                "headers": dict(request.headers),
                "payload": request.post_data
            })

def get_session():
    global requests_list
    cookie_string = None
    headers = None
    url = None
    payload = {}

    requests_list = [] # clear list
    print("Melakukan login otomatis...\n")

    username = 'moh.syafrizal'
    password = 'Sulteng2025!'

    page, browser = login_with_sso(username, password)
    if not page:
        raise Exception("Login gagal. Halaman tidak diperoleh.")

    try:
        print('get_token')
        page.on("request", handle_request)
        url_fasih = "https://fasih-sm.bps.go.id/app/surveys/a0429e96-51a5-477b-a415-485f9c153004/fd68e454-ba45-4b85-8205-f3bf777ded24"
        page.goto(url_fasih, wait_until="domcontentloaded", timeout=60000)
        
        for _ in range(3):
            try:
                page.wait_for_load_state("networkidle", timeout=60000)
            except:
                pass
                
            page.wait_for_timeout(5000)
            
            if "There's some error" in page.content():
                print("Ditemukan teks 'There's some error', melakukan refresh halaman...")
                page.reload(wait_until="domcontentloaded", timeout=60000)
                continue
                
            page.wait_for_timeout(10000)
            break

        print("selesai Menunggu load")
        print("TOTAL REQUEST:", len(requests_list))

        if len(requests_list) == 0:
            raise Exception("Gagal menangkap request datatable.")

        cookies = page.context.cookies()
        unique_cookies = {}
        for cookie in cookies:
            unique_cookies[cookie['name']] = cookie['value']
        cookie_string = "; ".join([f"{name}={value}" for name, value in unique_cookies.items()])

        url = requests_list[0]['url']
        headers = requests_list[0]['headers']
        headers["cookie"] = cookie_string
        xsrf_token = headers['x-xsrf-token']
        payload = {}

        if requests_list[0]['payload']:
            try:
                payload = json.loads(requests_list[0]['payload'])
            except json.JSONDecodeError:
                payload = requests_list[0]['payload']

        payload['length'] = 1000

    finally:
        if 'browser' in locals() and browser:
            try:
                browser.close()
            except Exception:
                pass

    return cookie_string, headers, url, payload, xsrf_token
