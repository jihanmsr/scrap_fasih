import asyncio
import json
from dotenv import load_dotenv
import os
import logging

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = None
if SUPABASE_URL and SUPABASE_KEY and "MASUKKAN" not in SUPABASE_URL:
    try:
        from supabase import create_client
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        logging.info("Koneksi Supabase berhasil diinisialisasi.")
    except Exception as e:
        logging.error(f"Gagal menginisialisasi Supabase: {e}")
import logging
import os
import time
from datetime import datetime
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Mapping label kabkot
KAB_MAP = {
    "7201": "[01] BANGGAI KEPULAUAN",
    "7202": "[02] BANGGAI",
    "7203": "[03] MOROWALI",
    "7204": "[04] POSO",
    "7205": "[05] DONGGALA",
    "7206": "[06] TOLI-TOLI",
    "7207": "[07] BUOL",
    "7208": "[08] PARIGI MOUTONG",
    "7209": "[09] TOJO UNA-UNA",
    "7210": "[10] SIGI",
    "7211": "[11] BANGGAI LAUT",
    "7212": "[12] MOROWALI UTARA",
    "7271": "[71] PALU"
}

# Supabase init (Opsional)
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

async def scrape_assign():
    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
            logging.info("Terkoneksi ke Chrome lokal (port 9222).")
        except Exception as e:
            logging.error(f"Gagal koneksi Chrome: {e}. Pastikan Chrome dijalankan dengan --remote-debugging-port=9222")
            return

        context = browser.contexts[0]
        page = await context.new_page()
        try:
            await page.goto("https://fasih-sm.bps.go.id/app/dashboard", timeout=60000, wait_until="domcontentloaded")
        except Exception as e:
            logging.warning(f"Navigasi awal timeout/gagal (tapi lanjut untuk cek cookies): {e}")
        await page.wait_for_timeout(3000)
        
        cookies = await context.cookies()
        token = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), None)
        if not token:
            logging.error("XSRF-TOKEN tidak ditemukan. Harap login FASIH.")
            return
            
        from urllib.parse import unquote
        token = unquote(token)
        
        # Sensus Ekonomi Umum
        survey_period_id = "fd68e454-ba45-4b85-8205-f3bf777ded24"
        region1Id = "5214ecb2-bef1-4a86-9446-451cf430928e" # Sulawesi Tengah
        
        url = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/report-user-assignment"
        payload = {
            "surveyPeriodId": survey_period_id,
            "region1Id": region1Id
        }
        
        logging.info("Menarik data Assign Petugas dari BPS...")
        res = await page.evaluate("""
            async ({url, payload, token}) => {
                try {
                    const r = await fetch(url, {
                        method: "POST",
                        headers: { "Content-Type": "application/json", "X-XSRF-TOKEN": token },
                        body: JSON.stringify(payload)
                    });
                    if (!r.ok) return { error: await r.text() };
                    return await r.json();
                } catch (e) {
                    return { error: e.toString() };
                }
            }
        """, {"url": url, "payload": payload, "token": token})
        
        if isinstance(res, dict) and res.get("error"):
            logging.error(f"Gagal menarik data dari server BPS: {res.get('error')}")
            return
            
        logging.info("Berhasil mendapatkan data Assign Petugas.")
        
        # Proses data JSON
        processed_data = []
        for item in res:
            kode_kab = item.get("label")
            if not kode_kab or kode_kab not in KAB_MAP:
                continue
                
            nama_kab = KAB_MAP[kode_kab]
            values = item.get("values", [])
            
            total = 0
            assigned = 0
            have_not_assigned = 0
            
            for v in values:
                label = v.get("label", "").lower()
                val = v.get("value", 0)
                if label == "total":
                    total = val
                elif label == "assigned":
                    assigned = val
                elif label == "have-not-assigned":
                    have_not_assigned = val
                    
            processed_data.append({
                "kode_kab": kode_kab,
                "nama_kab": nama_kab,
                "total": total,
                "assigned": assigned,
                "have_not_assigned": have_not_assigned,
                "timestamp": datetime.now().isoformat()
            })
            
        # Fetch all UB companies to get SLS-level assignments
        logging.info("Memulai pengambilan data SLS-level penugasan untuk Sensus Ekonomi UB...")
        ub_survey_period_id = "37526b20-81c8-42f5-a895-6190137d7394"
        ub_prov_id = "a00c8aef-afc4-4d4f-b80d-789a15450ef9"
        datatable_url = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode"
        
        UB_KAB_MAP = {
            "7201": {"id": "9c9b2d79-9fb1-4ce7-b0f1-6b7bb5511beb", "name": "[01] BANGGAI KEPULAUAN"},
            "7202": {"id": "34165dd5-372e-42fa-99c6-0cc19a9b4d0b", "name": "[02] BANGGAI"},
            "7203": {"id": "48c4e5d0-5525-41a8-a4ba-2cc38cd9c424", "name": "[03] MOROWALI"},
            "7204": {"id": "e18368ae-d1cd-4d43-a74d-5b9ddac5dd22", "name": "[04] POSO"},
            "7205": {"id": "c075c4b4-7eb0-4d72-9c16-5103088fb5eb", "name": "[05] DONGGALA"},
            "7206": {"id": "d3a28bfa-b611-488b-8255-369da5cedbf7", "name": "[06] TOLI-TOLI"},
            "7207": {"id": "dfe4c643-3282-40db-a5fd-cb288a4f592d", "name": "[07] BUOL"},
            "7208": {"id": "f18109d2-fc8b-4b9c-886a-dc242d21206e", "name": "[08] PARIGI MOUTONG"},
            "7209": {"id": "4d01eba1-5ae9-4603-82a6-2c831aea9905", "name": "[09] TOJO UNA-UNA"},
            "7210": {"id": "2a240d3a-67ee-45b2-ae78-4b4b3a909a90", "name": "[10] SIGI"},
            "7211": {"id": "288c5680-f6d5-4783-a946-d5a06f547c02", "name": "[11] BANGGAI LAUT"},
            "7212": {"id": "a5324f17-7a00-436f-b468-2fc59fcf605d", "name": "[12] MOROWALI UTARA"},
            "7271": {"id": "1acfedb4-276e-44d6-9e45-6d43588536d6", "name": "[71] PALU"}
        }
        
        all_ub_companies = []
        for kab_code, kab_cfg in UB_KAB_MAP.items():
            start = 0
            length = 100
            while True:
                payload_dt = {
                    "start": start,
                    "length": length,
                    "columns": [{"data": "id"}],
                    "order": [],
                    "search": {"value": "", "regex": False},
                    "assignmentExtraParam": {
                        "region1Id": ub_prov_id,
                        "region2Id": kab_cfg["id"],
                        "surveyPeriodId": ub_survey_period_id,
                        "assignmentErrorStatusType": -1,
                        "filterTargetType": ""
                    }
                }
                
                res_dt = await page.evaluate("""
                    async ({url, payload, token}) => {
                        try {
                            const r = await fetch(url, {
                                method: "POST",
                                headers: { "Content-Type": "application/json", "X-XSRF-TOKEN": token },
                                body: JSON.stringify(payload)
                            });
                            return await r.json();
                        } catch (e) {
                            return null;
                        }
                    }
                """, {"url": datatable_url, "payload": payload_dt, "token": token})
                
                if not res_dt or "searchData" not in res_dt:
                    break
                    
                records = res_dt["searchData"]
                if not records:
                    break
                    
                all_ub_companies.extend(records)
                start += length
                if start >= res_dt.get("totalHit", 0):
                    break
                    
        # Group by SLS
        sls_dict = {}
        for comp in all_ub_companies:
            region = comp.get("region", {})
            lvl1 = region.get("level1", {})
            lvl2 = lvl1.get("level2", {}) or {}
            lvl3 = lvl2.get("level3", {}) or {}
            lvl4 = lvl3.get("level4", {}) or {}
            lvl5 = lvl4.get("level5", {}) or {}
            
            kab_name = lvl2.get("name", "LAINNYA")
            kec_name = lvl3.get("name", "LAINNYA")
            desa_name = lvl4.get("name", "LAINNYA")
            sls_name = lvl5.get("name", "LAINNYA")
            sls_code = lvl5.get("fullCode", "LAINNYA")
            
            officer = comp.get("currentUserUsername")
            officer_fullname = comp.get("currentUserFullname", "-")
            is_assigned = bool(officer)
            
            if sls_code not in sls_dict:
                sls_dict[sls_code] = {
                    "sls_code": sls_code,
                    "sls_name": sls_name,
                    "desa_name": desa_name,
                    "kec_name": kec_name,
                    "kab_name": kab_name,
                    "total": 0,
                    "assigned": 0,
                    "unassigned": 0,
                    "officers": set()
                }
                
            sls_dict[sls_code]["total"] += 1
            if is_assigned:
                sls_dict[sls_code]["assigned"] += 1
                if officer_fullname and officer_fullname != "-":
                    sls_dict[sls_code]["officers"].add(f"{officer_fullname} ({officer})")
                else:
                    sls_dict[sls_code]["officers"].add(officer)
            else:
                sls_dict[sls_code]["unassigned"] += 1
                
        processed_sls = []
        for code, data in sls_dict.items():
            data["officers"] = list(data["officers"])
            processed_sls.append(data)
            
        # Simpan ke assign_data.js
        js_content = f"window.ASSIGN_DATA = {json.dumps(processed_data, indent=4)};\n"
        js_content += f"window.ASSIGN_SLS_DATA = {json.dumps(processed_sls, indent=4)};\n"
        with open("assign_data.js", "w", encoding="utf-8") as f:
            f.write(js_content)
        logging.info("Data dan data SLS berhasil disimpan ke assign_data.js")

        if supabase:
            try:
                tanggal_hari_ini = datetime.now().strftime("%Y-%m-%d")
                # Hapus hari ini biar gak dobel
                supabase.table("assign_logs").delete().eq("tanggal", tanggal_hari_ini).execute()
                
                records_to_insert = []
                for item in processed_data:
                    records_to_insert.append({
                        "tanggal": tanggal_hari_ini,
                        "kode_kab": item["kode_kab"],
                        "nama_kab": item["nama_kab"],
                        "total": item["total"],
                        "assigned": item["assigned"],
                        "have_not_assigned": item["have_not_assigned"]
                    })
                    
                if records_to_insert:
                    supabase.table("assign_logs").insert(records_to_insert).execute()
                    logging.info(f"Berhasil mengunggah {len(records_to_insert)} baris Assign Petugas ke Supabase.")
            except Exception as e:
                logging.error(f"Gagal upload Assign Petugas ke Supabase: {e}")
        await page.close()
        

        
def main():
    while True:
        logging.info("=== Memulai Sinkronisasi Assign Petugas ===")
        asyncio.run(scrape_assign())
        
        # Delay 6 jam (sehari 4 kali) = 21600 detik
        delay = 21600
        logging.info(f"Menunggu {delay} detik untuk sinkronisasi berikutnya...")
        time.sleep(delay)

if __name__ == "__main__":
    main()
