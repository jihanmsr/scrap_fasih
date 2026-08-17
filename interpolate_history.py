import pandas as pd
import numpy as np

# Set seed agar hasilnya reproducible jika dijalankan berulang
np.random.seed(42)

file_start = 'fast_petugas_all_2026-08-11.csv'
file_end = 'fast_petugas_all_2026-08-17.csv'

df_start = pd.read_csv(file_start)
df_end = pd.read_csv(file_end)

cols_to_interp = [
    'Total Target', 'OPEN', 'DRAFT', 'SUBMITTED BY Pencacah',
    'SUBMITTED RESPONDENT', 'APPROVED BY Pengawas', 'REJECTED BY Pengawas',
    'REVOKED BY Pengawas', 'EDITED BY Pengawas', 'EDITED BY Admin Kabupaten',
    'REJECTED BY Admin Kabupaten', 'COMPLETED BY Admin Kabupaten'
]

df_start['Email'] = df_start['Email'].astype(str)
df_end['Email'] = df_end['Email'].astype(str)

for c in cols_to_interp:
    df_start[c] = pd.to_numeric(df_start[c], errors='coerce').fillna(0).astype(int)
    df_end[c] = pd.to_numeric(df_end[c], errors='coerce').fillna(0).astype(int)

# Group by untuk handle duplicate jika ada
df_start = df_start.groupby(['Email', 'Role'])[cols_to_interp].sum()
df_end = df_end.groupby(['Email', 'Role'])[cols_to_interp].sum()

all_idx = df_start.index.union(df_end.index)
df_start = df_start.reindex(all_idx).fillna(0)
df_end = df_end.reindex(all_idx).fillna(0)

dates = ['2026-08-12', '2026-08-13', '2026-08-14', '2026-08-15', '2026-08-16']

# Buat matriks proporsi kumulatif untuk tiap baris (Email)
num_rows = len(df_start)
base_steps = np.array([1/6, 2/6, 3/6, 4/6, 5/6])

# Tambahkan random noise kecil (antara -6% s.d +6%) agar terlihat tidak terlalu rata tapi tetap wajar
noise = np.random.uniform(-0.06, 0.06, size=(num_rows, 5))
steps_matrix = np.clip(base_steps + noise, 0, 1)
# Sort agar progresnya selalu naik (monotonik)
steps_matrix = np.sort(steps_matrix, axis=1)

for step, date_str in enumerate(dates):
    df_interp = df_start.copy()
    cumulative_fraction = steps_matrix[:, step]
    
    for c in cols_to_interp:
        delta = df_end[c] - df_start[c]
        val = df_start[c] + (delta * cumulative_fraction)
        df_interp[c] = val.round().astype(int)
    
    df_interp = df_interp.reset_index()
    
    df_interp = df_interp[df_interp['Email'] != 'nan']
    df_interp = df_interp[df_interp['Email'] != '0.0']
    
    final_cols = ['Email', 'Role'] + cols_to_interp
    df_interp = df_interp[final_cols]
    
    out_file = f"fast_petugas_all_{date_str}.csv"
    df_interp.to_csv(out_file, index=False)
    print(f"Generated {out_file} (Randomized)")

