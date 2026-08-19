import pandas as pd
import csv
import glob

def process_csv_files(csv_pattern, date_str):
    files = glob.glob(csv_pattern)
    if not files:
        print("No files found!")
        return
        
    dfs = [pd.read_csv(f, dtype=str) for f in files]
    df = pd.concat(dfs, ignore_index=True)
    
    # Convert numeric columns
    for c in ['open', 'draft', 'submitted_respondent', 'submitted_by_pencacah', 
              'edited_by_pengawas', 'rejected_by_pengawas', 'approved_by_pengawas', 
              'revoked_by_pengawas', 'edited_by_admin_kabupaten', 'rejected_by_admin_kabupaten', 
              'revoked_by_admin_kabupaten', 'completed_by_admin_kabupaten']:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0).astype(int)
    
    csv_file = f"fast_petugas_all_{date_str}.csv"
    with open(csv_file, mode='w', newline='', encoding='utf-8') as f_csv:
        writer = csv.writer(f_csv)
        writer.writerow(["Email", "Role", "Total Target", "OPEN", "DRAFT", "SUBMITTED BY Pencacah", "SUBMITTED RESPONDENT", "APPROVED BY Pengawas", "REJECTED BY Pengawas", "REVOKED BY Pengawas", "EDITED BY Pengawas", "EDITED BY Admin Kabupaten", "REJECTED BY Admin Kabupaten", "COMPLETED BY Admin Kabupaten"])
        
        for _, row in df.iterrows():
            email = str(row.get('pencacah_email', '')).strip().lower()
            if not email or email == 'nan': continue
            
            total_target = sum(row.get(col, 0) for col in ['open', 'draft', 'submitted_respondent', 'submitted_by_pencacah', 'edited_by_pengawas', 'rejected_by_pengawas', 'approved_by_pengawas', 'revoked_by_pengawas', 'edited_by_admin_kabupaten', 'rejected_by_admin_kabupaten', 'revoked_by_admin_kabupaten', 'completed_by_admin_kabupaten'])
            
            writer.writerow([
                email,
                "Pencacah",
                total_target,
                row.get('open', 0),
                row.get('draft', 0),
                row.get('submitted_by_pencacah', 0),
                row.get('submitted_respondent', 0),
                row.get('approved_by_pengawas', 0),
                row.get('rejected_by_pengawas', 0),
                row.get('revoked_by_pengawas', 0),
                row.get('edited_by_pengawas', 0),
                row.get('edited_by_admin_kabupaten', 0),
                row.get('rejected_by_admin_kabupaten', 0),
                row.get('completed_by_admin_kabupaten', 0)
            ])
    print(f"Generated {csv_file}")

process_csv_files('/Users/jihanmaisaroh/scrap_fasih/sqllab_rekap_progress_petugas_20260819T091*.csv', '2026-08-19')
