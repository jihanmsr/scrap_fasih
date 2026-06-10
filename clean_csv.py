import pandas as pd

# 1. Kita baca dari file BACKUP untuk mengembalikan data yang hilang
backup_path = 'backup_all_email_history.csv'
file_path = 'all_email_history.csv'

try:
    df = pd.read_csv(backup_path)
except FileNotFoundError:
    print("File backup tidak ditemukan! Pastikan nama file backup-nya benar.")
    exit()

# 2. Cari kolom ID unik (Kode Identitas)
possible_id_cols = ['Kode Identitas', 'code', 'kode', 'id']
id_col = None

for col in possible_id_cols:
    if col in df.columns:
        id_col = col
        break

# 3. Hapus duplikat berdasarkan Kode Identitas
if id_col:
    print(f"Menghapus duplikat berdasarkan: '{id_col}'")
    df_cleaned = df.drop_duplicates(subset=[id_col], keep='last')
else:
    print("Menghapus duplikat berdasarkan: 'Nama Perusahaan'")
    df_cleaned = df.drop_duplicates(subset=['Nama Perusahaan'], keep='last')

# 4. Simpan kembali ke file utama
df_cleaned.to_csv(file_path, index=False)

print(f"Total awal (dari backup): {len(df)} baris")
print(f"Total setelah dibersihkan: {len(df_cleaned)} baris (Target kita: ~1264)")