import pandas as pd
import json

print("Memulai perbaikan dan pembersihan data...")

# 1. Baca CSV
df = pd.read_csv('all_email_history.csv')

# 2. Tentukan bobot prioritas status untuk mempertahankan riwayat terbaik
status_priority = {
    'permanent_fail': 8, 'permanent_failure': 8, 'bounced': 7, 'dropped': 6,
    'clicked': 5, 'opened': 4, 'delivered': 3, 'processed': 2, 'queued': 1, 'deferred': 0, '-': -1
}
df['priority'] = df['Status terakhir'].str.lower().str.strip().map(status_priority).fillna(-1)

# 3. Cari Kode Identitas terbaik untuk tiap Nama Perusahaan
best_codes = df.sort_values(by=['Nama Perusahaan', 'priority'], ascending=[True, False]) \
               .drop_duplicates(subset=['Nama Perusahaan'], keep='first')['Kode Identitas']

# 4. Saring dataframe untuk HANYA menyimpan history dari kode-kode yang terpilih
df_cleaned = df[df['Kode Identitas'].isin(best_codes)].drop(columns=['priority'])

# 5. Simpan kembali CSV utama
df_cleaned.to_csv('all_email_history.csv', index=False)
print(f"✅ CSV berhasil dibersihkan! Target tercapai: {len(best_codes)} perusahaan unik.")

# 6. Buat ulang data.js agar Dashboard langsung pulih
js_data = df_cleaned.to_dict(orient="records")
rename_map = {
    "Kode Identitas": "code",
    "Nama Perusahaan": "company_name",
    "Status Dokumen": "survey_status",
    "Email Tujuan": "email",
    "Status terakhir": "global_status",
    "Status History": "status",
    "Timestamp History": "timestamp",
    "Urutan History": "order"
}

formatted_js_data = []
for row in js_data:
    formatted_js_data.append({rename_map.get(k, k): v for k, v in row.items()})

import datetime
now_str = datetime.datetime.now().strftime("%d %b %Y, %H:%M:%S")
with open("data.js", "w", encoding="utf-8") as js_file:
    js_file.write(f"window.EMAIL_DATA = {json.dumps(formatted_js_data, ensure_ascii=False, indent=2)};\n")
    js_file.write(f"window.LAST_UPDATED = '{now_str}';\n")
    
print("✅ data.js berhasil diperbarui! Dashboard sekarang akan menampilkan ~1264 perusahaan.")