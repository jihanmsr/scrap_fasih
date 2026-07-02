import os
import json
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client
from openpyxl import load_workbook

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: SUPABASE_URL or SUPABASE_KEY not in .env")
    exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
print("Connected to Supabase.")

# List tanggal dan key yang ingin diambil
keys_to_fetch = [
    ("2026-06-17", "ipas_data:2026-06-17"),
    ("2026-06-18", "ipas_data:2026-06-18"),
    ("2026-06-19", "ipas_data:2026-06-19"),
    ("2026-06-20", "ipas_data:2026-06-20"),
    ("2026-06-21", "ipas_data:2026-06-21"),
    ("2026-06-22", "ipas_data:2026-06-22"),
    ("2026-06-23", "ipas_data:2026-06-23"),
    ("2026-06-24", "ipas_data:2026-06-24"),
    ("2026-06-25", "ipas_data:2026-06-25"),
    ("2026-06-26", "ipas_data:2026-06-26"),
    ("2026-06-27", "ipas_data:2026-06-27"),
    ("2026-06-28", "ipas_data:2026-06-28"),
    ("2026-06-29", "ipas_data:2026-06-29")
]

history_data = []

for date_str, db_key in keys_to_fetch:
    print(f"Mengambil data untuk {date_str} ({db_key})...")
    try:
        res = supabase.table("dashboard_store").select("value").eq("key", db_key).execute()
        if res.data:
            val = res.data[0].get("value")
            se_umum = val.get("se_umum", [])
            
            # Cari Morowali Utara
            morut_kab = None
            for kab in se_umum:
                if "MOROWALI UTARA" in kab.get("kabupaten", "").upper():
                    morut_kab = kab
                    break
                    
            if morut_kab:
                # Sum total_submitted dari seluruh kecamatan
                selesai_sum = 0
                for kec in morut_kab.get("kecamatan_list", []):
                    selesai_sum += kec.get("total_submitted", 0)
                
                history_data.append({
                    "Tanggal": date_str,
                    "Total Selesai": selesai_sum
                })
                print(f"  -> Total Selesai: {selesai_sum}")
            else:
                print("  -> Morowali Utara tidak ditemukan di data.")
        else:
            print("  -> Key tidak ditemukan di DB.")
    except Exception as e:
        print(f"  -> Error: {e}")

# Tambahkan tanggal 2026-07-01 (Hari ini) dari data lokal Morut yang baru selesai discrape (7645 selesai)
print("Menambahkan data hari ini (2026-07-01)...")
history_data.append({
    "Tanggal": "2026-07-01",
    "Total Selesai": 7645
})

# Hitung submit harian (selisih hari ini dengan hari sebelumnya)
# Urutkan berdasarkan tanggal
df_history = pd.DataFrame(history_data).sort_values("Tanggal")

daily_submits = []
prev_selesai = 0
for idx, row in df_history.iterrows():
    selesai = row["Total Selesai"]
    if idx == 0:
        # Untuk hari pertama (June 17), kita asumsikan submit harian adalah selisih dari 0 atau biarkan saja
        daily = selesai
    else:
        daily = max(0, selesai - prev_selesai)
    daily_submits.append(daily)
    prev_selesai = selesai

df_history["Submit Harian"] = daily_submits

print("\nHasil Tabulasi Harian Morowali Utara:")
print(df_history.to_string(index=False))

# Update file Excel Laporan_Morowali_Utara_7212.xlsx
script_dir = "/Users/jihanmaisaroh/scrap_fasih"
excel_path = os.path.join(script_dir, "Laporan_Morowali_Utara_7212.xlsx")

if os.path.exists(excel_path):
    print(f"\nMenambahkan sheet Progres_Harian ke {excel_path}...")
    try:
        with pd.ExcelWriter(excel_path, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
            df_history.to_excel(writer, sheet_name="Progres_Harian", index=False)
            
        print("✅ Sheet Progres_Harian berhasil ditambahkan ke Excel!")
    except Exception as e:
        print(f"[ERROR] Gagal menambahkan sheet ke Excel: {e}")
else:
    print(f"[WARNING] File {excel_path} tidak ditemukan. Membuat file baru...")
    df_history.to_excel(excel_path, sheet_name="Progres_Harian", index=False)
    print("✅ Berhasil membuat file Excel baru.")

# Simpan juga ke CSV terpisah
daily_csv_path = os.path.join(script_dir, "Morowali_Utara_Progres_Harian.csv")
df_history.to_csv(daily_csv_path, index=False)
print(f"✅ CSV Progres Harian disimpan ke {daily_csv_path}")
