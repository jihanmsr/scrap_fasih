import pandas as pd
import numpy as np
import csv

xls_file = '/Users/jihanmaisaroh/scrap_fasih/Rekap Progress Petugas 03_08.xlsx'
df = pd.read_excel(xls_file)

numeric_cols = ['open', 'draft', 'submitted_respondent', 'submitted_by_pencacah', 'edited_by_pengawas', 'rejected_by_pengawas', 'approved_by_pengawas', 'revoked_by_pengawas', 'edited_by_admin_kabupaten', 'rejected_by_admin_kabupaten', 'revoked_by_admin_kabupaten', 'completed_by_admin_kabupaten']
for col in numeric_cols:
    df[col] = df[col].fillna(0).astype(int)

df['pencacah_email'] = df['pencacah_email'].fillna('')
df['pengawas_email'] = df['pengawas_email'].fillna('')

out_csv = '/Users/jihanmaisaroh/scrap_fasih/fast_petugas_all_2026-08-03.csv'

with open(out_csv, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(["Email", "Role", "Region Code", "Total Target", "OPEN", "DRAFT", "SUBMITTED BY Pencacah", "SUBMITTED RESPONDENT", "APPROVED BY Pengawas", "REJECTED BY Pengawas", "REVOKED BY Pengawas", "EDITED BY Pengawas", "EDITED BY Admin Kabupaten", "REJECTED BY Admin Kabupaten", "COMPLETED BY Admin Kabupaten"])
    
    for _, row in df.iterrows():
        total_target = sum(row[col] for col in numeric_cols)
        reg_code = str(row['level_5_full_code'])
        
        vals = [
            row['open'], row['draft'], row['submitted_by_pencacah'], row['submitted_respondent'],
            row['approved_by_pengawas'], row['rejected_by_pengawas'], row['revoked_by_pengawas'],
            row['edited_by_pengawas'], row['edited_by_admin_kabupaten'], row['rejected_by_admin_kabupaten'],
            row['completed_by_admin_kabupaten']
        ]
        
        if str(row['pencacah_email']).strip() != '':
            writer.writerow([row['pencacah_email'].strip(), "Pencacah", reg_code, total_target] + vals)
            
        if str(row['pengawas_email']).strip() != '':
            writer.writerow([row['pengawas_email'].strip(), "Pengawas", reg_code, total_target] + vals)
            
print(f"Successfully converted {xls_file} to {out_csv}!")
