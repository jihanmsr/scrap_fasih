import asyncio
import json
import base64
import gzip
import os
import socket
from playwright.async_api import async_playwright

def check_port_open(port=9222):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0
    except:
        return False

async def main():
    script_dir = "/Users/jihanmaisaroh/scrap_fasih"
    morut_json = os.path.join(script_dir, "granular_assignments_se_umum_7212.json")
    
    with open(morut_json, "r", encoding="utf-8") as f:
        data = json.load(f)
    comp = data.get("compressed_data")
    raw = json.loads(gzip.decompress(base64.b64decode(comp)).decode('utf-8'))
    
    statuses_list = raw.get("statuses", [])
    targets = raw.get("targets", [])
    
    completed_tid = None
    for t in targets:
        tid = t[0]
        stat_idx = t[3]
        status_str = statuses_list[stat_idx] if stat_idx < len(statuses_list) else "-"
        if status_str.upper() not in {"OPEN", "DRAFT", "-", ""}:
            completed_tid = tid
            break
            
    if not completed_tid:
        print("Tidak ada target selesai ditemukan di JSON.")
        return
        
    print(f"Target selesai untuk diuji: {completed_tid}")
    
    abs_user_data_dir = os.path.abspath("playwright_chrome_profile")
    lock_file = os.path.join(abs_user_data_dir, "SingletonLock")
    if os.path.exists(lock_file) or os.path.islink(lock_file):
        try:
            os.unlink(lock_file)
            print("[INFO] Menghapus SingletonLock untuk tes.")
        except:
            pass
            
    async with async_playwright() as p:
        port = 9223 if check_port_open(9223) else 9222
        browser = None
        if check_port_open(port):
            browser = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
            context = browser.contexts[0]
            page = context.pages[0] if context.pages else await context.new_page()
        else:
            chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
            context = await p.chromium.launch_persistent_context(
                user_data_dir=abs_user_data_dir, headless=True, executable_path=chrome_path,
                args=["--no-first-run", "--no-default-browser-check"]
            )
            page = context.pages[0] if context.pages else await context.new_page()
            await page.goto("https://fasih-sm.bps.go.id/app/dashboard")
            
        print("Fetching log...")
        js_fetch = f"""
            async () => {{
                const res = await fetch('/app/api/assignment-general/api/assignment-history/get-by-assignment-id?assignmentId={completed_tid}');
                return await res.json();
            }}
        """
        res_json = await page.evaluate(js_fetch)
        print("RAW RESPONSE FROM BPS:")
        print(json.dumps(res_json, indent=4))
        
        if browser:
            await browser.disconnect()
        else:
            await context.close()

if __name__ == "__main__":
    asyncio.run(main())
