import os
import pandas as pd
import json
from dotenv import load_dotenv
from supabase import create_client

print("Memulai perbaikan data langsung ke Database Utama (Supabase)...")

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: SUPABASE_URL dan SUPABASE_KEY tidak ditemukan di file .env!")
    exit()

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# 1. Mengunduh semua data dari Supabase (termasuk yang 2256 baris)
print("📥 Mengunduh data dari Supabase...")
all_data = []
offset = 0
while True:
    res = supabase.table('email_logs').select('*').range(offset, offset + 999).execute()
    if not res.data:
        break
    all_data.extend(res.data)
    offset += 1000

print(f"Total baris ditemukan di database: {len(all_data)}")
if len(all_data) == 0:
    print("Data kosong, tidak ada yang perlu diperbaiki.")
    exit()

df = pd.DataFrame(all_data)

# 2. Tentukan bobot prioritas untuk mempertahankan status terbaik
status_priority = {
    'permanent_fail': 8, 'permanent_failure': 8, 'bounced': 7, 'dropped': 6,
    'clicked': 5, 'opened': 4, 'delivered': 3, 'processed': 2, 'queued': 1, 'deferred': 0, '-': -1
}
df['priority'] = df['global_status'].str.lower().str.strip().map(status_priority).fillna(-1)

# 3. KUNCI UTAMA: Gabungan Nama Perusahaan + Email
# Ini mencegah tercampurnya cabang perusahaan yang namanya sama persis tapi email beda
df['kunci_unik'] = df['company_name'].astype(str).str.strip() + "_" + df['email'].astype(str).str.strip()

# 4. Ambil ID (code) terbaik untuk setiap kunci unik tersebut
best_codes = df.sort_values(by=['kunci_unik', 'priority'], ascending=[True, False]) \
               .drop_duplicates(subset=['kunci_unik'], keep='first')['code']

df_cleaned = df[df['code'].isin(best_codes)].drop(columns=['priority', 'kunci_unik'])

# Buang kolom 'id' bawaan auto-increment Supabase jika ada agar tidak bentrok saat dimasukkan ulang
cols_to_keep = ['code', 'company_name', 'email', 'global_status', 'status', 'timestamp', 'order']
if 'survey_status' in df_cleaned.columns:
    cols_to_keep.append('survey_status')
df_cleaned = df_cleaned[cols_to_keep]

cleaned_records = df_cleaned.to_dict(orient='records')
print(f"✅ Data berhasil dibersihkan! Target tercapai: ~{len(df_cleaned['code'].unique())} perusahaan unik.")

# 5. Eksekusi ke Supabase
print("🗑️ Menghapus data lama yang ganda di database...")
supabase.table("email_logs").delete().neq("code", "FORCE_DELETE_ALL_XYZ").execute()

print("📤 Mengunggah data bersih kembali ke database...")
for i in range(0, len(cleaned_records), 400):
    supabase.table("email_logs").insert(cleaned_records[i:i+400]).execute()

# 6. Update file lokal agar sinkron
df_csv = df_cleaned.rename(columns={
    "code": "Kode Identitas", "company_name": "Nama Perusahaan", 
    "survey_status": "Status Dokumen", "email": "Email Tujuan",
    "global_status": "Status terakhir", "status": "Status History", 
    "timestamp": "Timestamp History", "order": "Urutan History"
})
if "Status Dokumen" not in df_csv.columns:
    df_csv["Status Dokumen"] = "-"
    
csv_cols = ["Kode Identitas", "Nama Perusahaan", "Status Dokumen", "Email Tujuan", "Status terakhir", "Status History", "Timestamp History", "Urutan History"]
df_csv[csv_cols].to_csv('all_email_history.csv', index=False)

import datetime
now_str = datetime.datetime.now().strftime("%d %b %Y, %H:%M:%S")
with open("data.js", "w", encoding="utf-8") as js_file:
    js_file.write(f"window.EMAIL_DATA = {json.dumps(cleaned_records, ensure_ascii=False, indent=2)};\n")
    js_file.write(f"window.LAST_UPDATED = '{now_str}';\n")

print("🎉 SELESAI! Silakan refresh halaman Dashboard Anda. Angkanya sekarang sudah normal.")