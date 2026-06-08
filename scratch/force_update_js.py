import pandas as pd
import json
import datetime
import os

OUTPUT_CSV = "backup_all_email_history.csv"
OUTPUT_JS = "data.js"

if os.path.exists(OUTPUT_CSV):
    try:
        df = pd.read_csv(OUTPUT_CSV)
        now_str = datetime.datetime.now().strftime("%d %b %Y, %H:%M:%S")
        
        # rename columns back to internal keys if needed, or just use as is.
        # Wait, the backup CSV has columns: "Kode Identitas", "Nama Perusahaan", "Status Dokumen", "Email Tujuan", "Status terakhir", "Status History", "Timestamp History", "Urutan History"
        # The JS expects: code, company_name, survey_status, email, global_status, status, timestamp, order
        
        df = df.rename(columns={
            "Kode Identitas": "code",
            "Nama Perusahaan": "company_name",
            "Status Dokumen": "survey_status",
            "Email Tujuan": "email",
            "Status terakhir": "global_status",
            "Status History": "status",
            "Timestamp History": "timestamp",
            "Urutan History": "order"
        })
        
        js_data = df.to_dict(orient="records")
        with open(OUTPUT_JS, "w", encoding="utf-8") as js_file:
            js_file.write(f"window.EMAIL_DATA = {json.dumps(js_data, ensure_ascii=False, indent=2)};\n")
            js_file.write(f"window.LAST_UPDATED = '{now_str} (Forced Sync)';\n")
        print(f"Sukses update data.js dengan {len(df)} records!")
    except Exception as e:
        print("Error:", e)
