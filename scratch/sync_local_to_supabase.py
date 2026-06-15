import os
import csv
import time
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: SUPABASE_URL atau SUPABASE_KEY tidak ditemukan di .env!")
    exit(1)

print("Menghubungkan ke Supabase...")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Muat data bersih dari CSV lokal
print("Membaca all_email_history.csv...")
records = []
with open("all_email_history.csv", mode="r", encoding="utf-8") as f:
    reader = csv.reader(f)
    header = next(reader, None)
    for row in reader:
        if len(row) >= 8:
            records.append({
                "code": str(row[0]),
                "company_name": str(row[1]),
                "survey_status": str(row[2]),
                "email": str(row[3]),
                "global_status": str(row[4]),
                "status": str(row[5]),
                "timestamp": str(row[6]),
                "order": int(row[7]) if row[7].isdigit() else 0,
                "kab_name": str(row[8]) if len(row) >= 9 else "-"
            })

print(f"Total records yang akan diunggah: {len(records)}")

# Peta kolom yang valid di Supabase
available_cols = {"code", "company_name", "email", "global_status", "status", "timestamp", "order"}
try:
    sample_res = supabase.table("email_logs").select("*").limit(1).execute()
    if sample_res.data:
        available_cols = set(sample_res.data[0].keys())
except Exception as e:
    print(f"Gagal mendeteksi kolom: {e}")

print("Mengunggah data bersih ke Supabase dalam batch...")
batch_size = 400
for i in range(0, len(records), batch_size):
    batch = records[i:i+batch_size]
    db_batch = []
    for r in batch:
        item = {
            "code": r["code"],
            "company_name": r["company_name"],
            "email": r["email"],
            "global_status": r["global_status"],
            "status": r["status"],
            "timestamp": r["timestamp"],
            "order": r["order"]
        }
        if "survey_status" in available_cols:
            item["survey_status"] = r["survey_status"]
        if "kab_name" in available_cols:
            item["kab_name"] = r["kab_name"]
        elif "kabupaten" in available_cols:
            item["kabupaten"] = r["kab_name"]
            
        db_batch.append(item)
        
    try:
        supabase.table("email_logs").insert(db_batch).execute()
        print(f"  Berhasil mengunggah batch {i // batch_size + 1} ({len(db_batch)} baris)...")
    except Exception as e:
        print(f"  Gagal mengunggah batch {i // batch_size + 1}: {e}")

print("✅ SINKRONISASI SUPABASE BERHASIL! Database sudah bersih dari duplikat.")
