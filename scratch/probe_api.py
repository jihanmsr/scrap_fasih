import os
import time
import socket
import subprocess
from playwright.sync_api import sync_playwright

USER_DATA_DIR = "playwright_chrome_profile"

def check_port_open(port=9222):
	with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
		return s.connect_ex(('localhost', port)) == 0

def launch_chrome_if_needed():
	port = 9222
	if check_port_open(port):
		print("Chrome remote debugging port 9222 sudah aktif.")
		return
	
	print("Chrome remote debugging port 9222 tidak aktif. Mencoba meluncurkan browser...")
	chrome_path = "/Users/jihanmaisaroh/Library/Caches/ms-playwright/chromium-1208/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"
	
	lock_file = os.path.join(USER_DATA_DIR, "SingletonLock")
	if os.path.exists(lock_file):
		try:
			os.remove(lock_file)
		except Exception:
			pass
	
	abs_user_data_dir = os.path.abspath(USER_DATA_DIR)
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
			print("Browser Chrome berhasil diluncurkan.")
			return

def probe():
    launch_chrome_if_needed()
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0]
        
        target_data_url = "https://fasih-sm.bps.go.id/app/surveys/ecddb52e-f392-403c-a963-47391f217010/37526b20-81c8-42f5-a895-6190137d7394/data"
        page = None
        for p_page in context.pages:
            if "fasih-sm" in p_page.url:
                page = p_page
                break
        if not page:
            page = context.new_page()
            page.goto(target_data_url)
            time.sleep(5)
            
        cookies = context.cookies()
        xsrf_token = None
        for cookie in cookies:
            if cookie['name'] == 'XSRF-TOKEN':
                from urllib.parse import unquote
                xsrf_token = unquote(cookie['value'])
                break
        
        print(f"URL Halaman: {page.url}")
        print(f"XSRF Token: {xsrf_token}")
        
        payload = {
            "start": 0,
            "length": 1500,
            "columns": [
                {"data": "id", "orderable": True},
                {"data": "codeIdentity", "orderable": True},
                {"data": "data1", "orderable": True}
            ],
            "order": [],
            "search": {"value": "", "regex": False},
            "assignmentExtraParam": {
                "region1Id": "a00c8aef-afc4-4d4f-b80d-789a15450ef9",
                "region2Id": "1acfedb4-276e-44d6-9e45-6d43588536d6",
                "surveyPeriodId": "37526b20-81c8-42f5-a895-6190137d7394",
                "assignmentErrorStatusType": -1,
                "filterTargetType": "TARGET_ONLY"
            }
        }
        
        datatable_url = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode"
        
        res = page.evaluate("""
            async ({url, payload, token}) => {
                const r = await fetch(url, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "X-XSRF-TOKEN": token
                    },
                    body: JSON.stringify(payload)
                });
                return { status: r.status, text: await r.text() };
            }
        """, {"url": datatable_url, "payload": payload, "token": xsrf_token})
        
        print(f"Status API: {res['status']}")
        print(f"Response API: {res['text']}")

if __name__ == "__main__":
    probe()
