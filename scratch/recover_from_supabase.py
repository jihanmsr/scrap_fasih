import os
import json
import pandas as pd
import datetime
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

print("Menarik kolom terpilih dari tabel email_logs...")
all_data = []
page_size = 1000
offset = 0

# Pilih hanya kolom yang benar-benar ada di tabel Supabase
select_cols = "code,company_name,email,global_status,status,timestamp,order"

while True:
    res = supabase.table("email_logs").select(select_cols).range(offset, offset + page_size - 1).execute()
    data_part = res.data
    if not data_part:
        break
    all_data.extend(data_part)
    if len(data_part) < page_size:
        break
    offset += page_size
    if offset % 10000 == 0:
        print(f"Berhasil mengunduh {offset} record...")

print(f"Berhasil menarik total {len(all_data)} record dari Supabase.")

# Buat DataFrame
df_sb = pd.DataFrame(all_data)

# Map kolom Supabase ke kolom CSV lokal
mapping = {
    "code": "Kode Identitas",
    "company_name": "Nama Perusahaan",
    "email": "Email Tujuan",
    "global_status": "Status terakhir",
    "status": "Status History",
    "timestamp": "Timestamp History",
    "order": "Urutan History"
}

# Rename columns
df_csv = df_sb.rename(columns=mapping)

# Tambahkan kolom survey_status dan kab_name dengan default '-'
df_csv["Status Dokumen"] = "-"
df_csv["Kabupaten/Kota"] = "-"

# Peta Kabupaten berdasarkan kode BPS
KAB_MAP = {
    "7201": "[01] BANGGAI KEPULAUAN", "7202": "[02] BANGGAI", "7203": "[03] MOROWALI",
    "7204": "[04] POSO", "7205": "[05] DONGGALA", "7206": "[06] TOLI-TOLI",
    "7207": "[07] BUOL", "7208": "[08] PARIGI MOUTONG", "7209": "[09] TOJO UNA-UNA",
    "7210": "[10] SIGI", "7211": "[11] BANGGAI LAUT", "7212": "[12] MOROWALI UTARA",
    "7271": "[71] PALU"
}

# Coba ekstrak Kabupaten/Kota dari Kode jika diawali dengan kode BPS
for idx, row in df_csv.iterrows():
    code = str(row["Kode Identitas"])
    if len(code) >= 4 and code[:4] in KAB_MAP:
        df_csv.at[idx, "Kabupaten/Kota"] = KAB_MAP[code[:4]]

# Pilih hanya kolom yang dibutuhkan untuk CSV
csv_cols = ["Kode Identitas", "Nama Perusahaan", "Status Dokumen", "Email Tujuan", "Status terakhir", "Status History", "Timestamp History", "Urutan History", "Kabupaten/Kota"]
df_csv = df_csv[csv_cols]

# Bersihkan duplikat
subset_cols = ['Kode Identitas', 'Status History', 'Timestamp History', 'Urutan History']
df_cleaned = df_csv.drop_duplicates(subset=subset_cols, keep='last')
print(f"Jumlah baris setelah dibersihkan: {len(df_cleaned)}")

# Tulis ke CSV
file_path = 'all_email_history.csv'
backup_path = 'backup_all_email_history.csv'
output_js = 'data.js'

print(f"Menulis file CSV bersih ke {file_path}...")
df_cleaned.to_csv(file_path, index=False)
print(f"Menulis file CSV bersih ke {backup_path}...")
df_cleaned.to_csv(backup_path, index=False)

# Tulis ke data.js
print(f"Menulis ke {output_js}...")
now_str = datetime.datetime.now().strftime("%d %b %Y, %H:%M:%S")

js_records = []
for _, row in df_cleaned.iterrows():
    def clean_val(v):
        return "" if pd.isna(v) else str(v).strip()
        
    js_records.append({
        "code": clean_val(row.get("Kode Identitas")),
        "company_name": clean_val(row.get("Nama Perusahaan")),
        "survey_status": clean_val(row.get("Status Dokumen")),
        "email": clean_val(row.get("Email Tujuan")),
        "global_status": clean_val(row.get("Status terakhir")),
        "status": clean_val(row.get("Status History")),
        "timestamp": clean_val(row.get("Timestamp History")),
        "order": int(row.get("Urutan History")) if not pd.isna(row.get("Urutan History")) else 0,
        "kab_name": clean_val(row.get("Kabupaten/Kota"))
    })

with open(output_js, "w", encoding="utf-8") as js_file:
    js_file.write(f"window.EMAIL_DATA = {json.dumps(js_records, ensure_ascii=False, indent=2)};\n")
    js_file.write(f"window.LAST_UPDATED = '{now_str}';\n")

print("✅ RECOVERY DENGAN PAGINASI DAN KOLOM KABUPATEN BERHASIL DISAJIKAN!")
