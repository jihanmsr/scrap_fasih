import copy
import os
import requests
import json
import csv
import datetime
import time
from session_manager_petugas import get_session

# processed_codes = {
#     f.removeprefix("response_").removesuffix(".json")
#     for f in os.listdir("responses")
#     if f.startswith("response_") and f.endswith(".json")
# }

import datetime
today_str = datetime.datetime.now().strftime("%Y-%m-%d")
OUTPUT_DIR = "petugas"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def fetch_with_retry(url, headers, payload, max_wait_minutes=10):
    start_time = time.time()
    max_wait_seconds = max_wait_minutes * 60
    wait_interval = 30 # seconds
    
    while True:
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            data = None
            try:
                data = response.json()
            except:
                pass
                
            if response.status_code == 200 and data:
                return response, data
            
            elapsed = time.time() - start_time
            if elapsed >= max_wait_seconds:
                return response, data
                
            print(f"    Tidak ada data atau status {response.status_code}, mencoba refresh session... ({int(elapsed)}s/{max_wait_seconds}s)")
        except Exception as e:
            elapsed = time.time() - start_time
            if elapsed >= max_wait_seconds:
                raise e
            print(f"    Gagal request ({e}), mencoba refresh session... ({int(elapsed)}s/{max_wait_seconds}s)")
            
        if os.path.exists("session_cache.json"):
            try:
                os.remove("session_cache.json")
            except:
                pass
        try:
            _, new_headers, _, _, _= get_session()
            if new_headers:
                headers.clear()
                headers.update(new_headers)
                print("    Session berhasil di-refresh.")
        except Exception as e_session:
            print(f"    Gagal refresh session: {e_session}")
            
        time.sleep(wait_interval)

def main():
    prov_id = '5214ecb2-bef1-4a86-9446-451cf430928e'

    # Load semua kode_kab dari kab.json
    try:
        with open("kab.json", "r", encoding="utf-8") as f:
            kab_data = json.load(f)
        import sys
        target_kab = sys.argv[1] if len(sys.argv) > 1 else None
        kab_list = kab_data.get("data", [])
        if target_kab:
            kab_list = [k for k in kab_list if k.get("fullCode") == target_kab]
    except Exception as e:
        print(f"Gagal memuat kab.json: {e}")
        return

    try:
        cookie_string, headers, url, payload, xsrf_token = get_session()
        url = 'https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/report-progress-by-responsibility'
        headers_new = {
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.9,id;q=0.8",
            "content-length": "437",
            "content-type": "application/json",
            "cookie": "cf_clearance=EP5e_0NslEu2HYwCG40U1ckBjtZhq7mjHDorv5BLxeA-1781054642-1.2.1.1-T1y9MlFGscl7innw7oppxDj4fm9Zc1H37BdLHrYO7kJCCr9w.ctvTdBTKNh22fbg88ZVPpjGiB.y2VINIlCDP_C9e5Lj1yTabR4.ja_NoCaz3k1PikFFTjcC68CA9F9BKJ2aBZglCtm5xi1Om_7Ygjjnlr7QYjB6KyK5.R.A73LEC.QHoGOKV0ljw9_hBcROTXF7ChB1ltw.HOnNo5cKGYuWX4kPgi0ZsEYNUznmLvTImBG94oGWHbhfaquoUTZnb2FA4WJpvkUp7wOcMrvXnJUgOV3n03TXUrwTpFCb27VRZu7eD2d4Mt.xaoZ.0CgmoIgn9GsYd4R5lb_1Am3o5A; f5avraaaaaaaaaaaaaaaa_session_=PKEAECPOBLDADACNIPICJADBBOIIAKABIJPBCCNJELOJBOBGGCMONIMGEMKMOGKFOKODOANPCKNEIJJDIFHAKHJLHNGDCJCELLKNNIGBDEKFDLDFGEADMNKBKFNIMHHN; db8ca2b43ed851cc93e71fd5fd72bff7=0b924d8abfc1350b731af80335a195b4; XSRF-TOKEN=cb213019-f8dc-4b33-8c0f-418ddae0d4a9; SESSION=b5313488-74b9-4ca2-bbf6-1fbc1087a6b6; TS00000000076=0868f8be6fab28007c3444123f4e2cec7c6aabe2fbcabf8d6bb1414a84987bff767d75044010d4e2edd78cd7fa0be59608246ed9fc09d00009a7b0ecf851c6e272922d588c46d62c0f9b0a91b9899539883ccd3874dcfd9e70de04f7f73313b8f1cf1ed5428de70889173abc1d204078ed3572b50cb4d2dadad88a445f21f3b890de8a8e1b041b6bcfe216fae818931adfec0647f412d8c65fb913eb3347ca9392caafeb12e05f0dac9729b26b19b61b99d69a3347185da5e0aaf74ff675f7f29f5105cf1ff42743e6e2b38ce1987a201af51d62e0ca6cd3e0fa7c454befeae744ad1a7db2ae96fee4df7ebb17411bfa0ffb3f539d6c7f52880fd01637586b54748ca8198076f6cd; TSPD_101_DID=0868f8be6fab28007c3444123f4e2cec7c6aabe2fbcabf8d6bb1414a84987bff767d75044010d4e2edd78cd7fa0be59608246ed9fc063800870b52eebae0865412b33af3f441bd8bd0bb0034ad810e51232be4a82087381cecba62f8060c9ef32e9d7079ee414358412e3869f66fbb29; TS011f2d1a=01266d26d08cd409c1f4e9a2e12e2c9376e0bab88b47b51e770887a8addee59c09936902db83886f7580b187c74b45a1f777c5512c; TSPD_101=0868f8be6fab28007a15cfa7f19f61174d234c645c147561c735cd1870cf23f1534854e07ab8e4dd71cb81d5ea849011087044fd77051800b683941b2e71c2c35ca1732140a3428bba23ce13beb1c95e; TS5220f739077=0868f8be6fab2800c7f816e8795d19cb5edf7e30f5bfd134bf43d153482f9a9426ddb668fdffaa7598bcc18e8ef5785208760ef3b91720003d5223775216993e75eb3a41b4d8c840868348b299b76d9b7f44adc0a7161766; TSf1edb2d2027=0868f8be6fab2000c647a0879359d52e08e0d81f8626ef10e188414f8d930ade305e261e09f315ac08b74beb95113000aeba6e8799241e59f996e52c28a7a4eff9583af2a6ddd66e78b8ea4973161f507bb781f2b6727c9204735091d2a1c15e",
            "origin": "https://fasih-sm.bps.go.id",
            "priority": "u=1, i",
            "sec-ch-ua": '"Not;A=Brand";v="8", "Chromium";v="150", "Google Chrome";v="150"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36",
            "x-xsrf-token": "cb213019-f8dc-4b33-8c0f-418ddae0d4a9"
        }

        headers_new['cookie'] = cookie_string
        headers_new['x-xsrf-token'] = xsrf_token
        pengawas_id = '93bcf446-c4c1-4462-8ed0-4b0f7ae89e52'
        pencacah_id = '6d7d919a-45e5-4779-bb87-2905b49fd31a'

        def fetch_role_data(role_id, role_name, kode_kab, payload_new):
            print(f"Mendapatkan data untuk {role_name}")
            payload_new["surveyRoleId"] = role_id
            payload_new["size"] = 5
            payload_new["page"] = 0
            
            response, data = fetch_with_retry(url, headers_new, payload_new)
            if not data:
                print(f"Gagal mendapatkan data awal {role_name}")
                return
            
            total_elements = data.get("totalElements", 0)
            if total_elements == 0 and "data" in data and isinstance(data["data"], dict):
                total_elements = data["data"].get("totalElements", 0)
                
            print(f"Total elements {role_name}: {total_elements}")
            
            if total_elements > 5:
                total_pages = (total_elements + 4) // 5
                for page in range(1, total_pages):
                    print(f"  Fetching page {page}/{total_pages - 1} untuk {role_name}...")
                    payload_new["page"] = page
                    response_page, data_page = fetch_with_retry(url, headers_new, payload_new)
                    
                    if data_page:
                        # Append the new data to our accumulated `data` object
                        if "data" in data and isinstance(data["data"], list) and "data" in data_page:
                            data["data"].extend(data_page["data"])
                        elif "content" in data and isinstance(data["content"], list) and "content" in data_page:
                            data["content"].extend(data_page["content"])
                        elif "data" in data and isinstance(data["data"], dict) and "content" in data["data"] and isinstance(data["data"]["content"], list) and "data" in data_page and "content" in data_page.get("data", {}):
                            data["data"]["content"].extend(data_page["data"]["content"])
                            
                    time.sleep(0.5)

            # Save once after the loop is complete
            with open(os.path.join(OUTPUT_DIR, f"response_{role_name}_{kode_kab}_{today_str}.json"), "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
                
            
            # -- Append ke CSV --
            csv_file = f"/Users/jihanmaisaroh/scrap_fasih/fast_petugas_all_{today_str}.csv"
            
            # Buat header jika file belum ada
            file_exists = os.path.exists(csv_file)
            with open(csv_file, mode='a', newline='', encoding='utf-8') as f_csv:
                writer = csv.writer(f_csv)
                if not file_exists:
                    writer.writerow(["Email", "Role", "Region Code", "Total Target", "OPEN", "DRAFT", "SUBMITTED BY Pencacah", "SUBMITTED RESPONDENT", "APPROVED BY Pengawas", "REJECTED BY Pengawas", "REVOKED BY Pengawas", "EDITED BY Pengawas", "EDITED BY Admin Kabupaten", "REJECTED BY Admin Kabupaten", "COMPLETED BY Admin Kabupaten"])
                
                content_list = []
                if "data" in data and isinstance(data["data"], list):
                    content_list = data["data"]
                elif "content" in data and isinstance(data["content"], list):
                    content_list = data["content"]
                elif "data" in data and isinstance(data["data"], dict) and "content" in data["data"]:
                    content_list = data["data"]["content"]

                for row in content_list:
                    email = row.get("email", "")
                    # role_name is pengawas or pencacah, Capitalize it
                    role_c = "Pengawas" if role_name == "pengawas" else "Pencacah"
                    for r_sum in row.get("regionSummary", []):
                        reg_code = r_sum.get("regionCode", "")
                        status_breakdown = r_sum.get("statusBreakdown", [])
                        counts = { "OPEN": 0, "DRAFT": 0, "SUBMITTED BY PENCACAH": 0, "SUBMITTED RESPONDENT": 0, "APPROVED BY PENGAWAS": 0, "REJECTED BY PENGAWAS": 0, "REVOKED BY PENGAWAS": 0, "EDITED BY PENGAWAS": 0, "EDITED BY ADMIN KABUPATEN": 0, "REJECTED BY ADMIN KABUPATEN": 0, "COMPLETED BY ADMIN KABUPATEN": 0 }
                        total = r_sum.get("total", 0)
                        for st in status_breakdown:
                            st_name = st.get("status", "").upper()
                            if st_name in counts: counts[st_name] = st.get("count", 0)
                            else: counts[st_name] = st.get("count", 0)
                        writer.writerow([email, role_c, reg_code, total, counts.get("OPEN",0), counts.get("DRAFT",0), counts.get("SUBMITTED BY PENCACAH",0), counts.get("SUBMITTED RESPONDENT",0), counts.get("APPROVED BY PENGAWAS",0), counts.get("REJECTED BY PENGAWAS",0), counts.get("REVOKED BY PENGAWAS",0), counts.get("EDITED BY PENGAWAS",0), counts.get("EDITED BY ADMIN KABUPATEN",0), counts.get("REJECTED BY ADMIN KABUPATEN",0), counts.get("COMPLETED BY ADMIN KABUPATEN",0)])
            # -------------------

            print(f"Berhasil mendapatkan Response tingkat {role_name}")

        # Loop semua kabupaten
        for kab_item in kab_list:
            kode_kab = kab_item.get("fullCode")
            kab_id = kab_item.get("id")
            kab_name = kab_item.get("name", "")

            print(f"\n=== Memproses kabupaten: {kode_kab} - {kab_name} ===")

            # Skip jika output sudah ada untuk kedua role
            output_pengawas = os.path.join(OUTPUT_DIR, f"response_pengawas_{kode_kab}_{today_str}.json")
            output_pencacah = os.path.join(OUTPUT_DIR, f"response_pencacah_{kode_kab}_{today_str}.json")
            if os.path.exists(output_pengawas) and os.path.exists(output_pencacah):
                print(f"  Sudah ada, skip.")
                continue

            payload_new = {
                "surveyPeriodId": "fd68e454-ba45-4b85-8205-f3bf777ded24",
                "surveyRoleId": pengawas_id,
                "size": 5,
                "page": 0,
                "search": "",
                "target": "TARGET_ONLY",
                "region": {
                    "region1Id": "5214ecb2-bef1-4a86-9446-451cf430928e",
                    "region2Id": kab_id,
                    "region3Id": None,
                    "region4Id": None,
                    "region5Id": None,
                    "region6Id": None,
                    "region7Id": None,
                    "region8Id": None,
                    "region9Id": None,
                    "region10Id": None
                },
                "regionSummaryLevel": 6
            }

            try:
                fetch_role_data(pengawas_id, "pengawas", kode_kab, payload_new)
                fetch_role_data(pencacah_id, "pencacah", kode_kab, payload_new)
            except Exception as e:
                print(f"    Gagal request {kode_kab}: {e}")

            time.sleep(0.5)

    except Exception as e:
        print(f"Error saat login atau ekstraksi: {e}")

if __name__ == "__main__":
    main()
