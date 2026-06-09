import re

with open('scrape_assign.py', 'r') as f:
    content = f.read()

# Add Supabase import
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

supabase_upload = """        # Simpan ke data.js agar dibaca oleh index.html
        js_content = f"window.ASSIGN_DATA = {json.dumps(processed_data, indent=4)};\\n"
        with open("assign_data.js", "w", encoding="utf-8") as f:
            f.write(js_content)
        logging.info("Data berhasil disimpan ke assign_data.js")

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
"""

content = content.replace("""        # Simpan ke data.js agar dibaca oleh index.html
        js_content = f"window.ASSIGN_DATA = {json.dumps(processed_data, indent=4)};\\n"
        with open("assign_data.js", "w", encoding="utf-8") as f:
            f.write(js_content)
        logging.info("Data berhasil disimpan ke assign_data.js")
        
        # TODO: Implementasi upload ke Supabase jika tabel sudah disiapkan
        # if SUPABASE_URL and SUPABASE_KEY:
        #    ...""", supabase_upload)

with open('scrape_assign.py', 'w') as f:
    f.write(content)
