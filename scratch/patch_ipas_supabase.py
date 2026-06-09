import re

with open('generate_ipas_report.py', 'r') as f:
    content = f.read()

# Add Supabase import and init
supabase_init = """import json
from dotenv import load_dotenv
import os

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
"""

content = content.replace("import json\n", supabase_init)

# Add logic to upload to supabase at the end
supabase_upload = """        js_content = f"window.IPAS_DATA = {json.dumps(final_report, indent=4)};\\n"
        with open("ipas_data.js", "w", encoding="utf-8") as f:
            f.write(js_content)
        logging.info("Data berhasil disimpan ke ipas_data.js")

        if supabase:
            try:
                # Upload ke Supabase
                tanggal_hari_ini = datetime.now().strftime("%Y-%m-%d")
                
                # Hapus data hari ini dulu biar gak dobel
                supabase.table("ipas_logs").delete().eq("tanggal", tanggal_hari_ini).execute()
                
                records_to_insert = []
                for survey_type, data in final_report.items():
                    for kab_data in data:
                        code = kab_data.get("kabupaten", "").split("]")[0].replace("[", "")
                        records_to_insert.append({
                            "tanggal": tanggal_hari_ini,
                            "kode_kab": code,
                            "nama_kab": kab_data.get("kabupaten"),
                            "survey_type": survey_type,
                            "total_prelist": kab_data.get("total_prelist", 0),
                            "draft": kab_data.get("draft", 0),
                            "open": kab_data.get("open", 0),
                            "submitted": kab_data.get("total_submitted", 0)
                        })
                
                if records_to_insert:
                    res = supabase.table("ipas_logs").insert(records_to_insert).execute()
                    logging.info(f"Berhasil mengunggah {len(records_to_insert)} baris IPAS ke Supabase.")
            except Exception as e:
                logging.error(f"Gagal upload IPAS ke Supabase: {e}")
"""

content = content.replace("""        js_content = f"window.IPAS_DATA = {json.dumps(final_report, indent=4)};\\n"
        with open("ipas_data.js", "w", encoding="utf-8") as f:
            f.write(js_content)
        logging.info("Data berhasil disimpan ke ipas_data.js")""", supabase_upload)

with open('generate_ipas_report.py', 'w') as f:
    f.write(content)
