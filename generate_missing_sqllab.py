import pandas as pd

# 1. Load SQLLab to get the list of SLS already extracted
df_sql = pd.read_excel('/Users/jihanmaisaroh/scrap_fasih/sqllab_untitled_query_7_20260729T115458.xlsx')
extracted_sls = set(df_sql['level_6_full_code'].astype(str).str.strip())

# 2. Load our full FASIH scraper data
df_csv = pd.read_csv('/Users/jihanmaisaroh/scrap_fasih/fast_petugas_all_2026-07-29.csv')
df_csv['Region Code'] = df_csv['Region Code'].astype(str).str.strip()

# 3. Filter only those NOT in SQLLab
df_missing = df_csv[~df_csv['Region Code'].isin(extracted_sls)]

# 4. We can aggregate by Region Code to match the SQLLab format
# We'll split pencacah and pengawas to get their emails
df_pencacah = df_missing[df_missing['Role'].str.upper() == 'PENCACAH'].copy()
df_pengawas = df_missing[df_missing['Role'].str.upper() == 'PENGAWAS'].copy()

# Rename columns to match SQLLab for Pencacah
df_pencacah.rename(columns={
    'Region Code': 'level_6_full_code',
    'OPEN': 'open',
    'DRAFT': 'draft',
    'SUBMITTED BY Pencacah': 'submitted_by_pencacah',
    'SUBMITTED RESPONDENT': 'submitted_respondent',
    'APPROVED BY Pengawas': 'approved_by_pengawas',
    'REJECTED BY Pengawas': 'rejected_by_pengawas',
    'REVOKED BY Pengawas': 'revoked_by_pengawas',
    'EDITED BY Pengawas': 'edited_by_pengawas',
    'EDITED BY Admin Kabupaten': 'edited_by_admin_kabupaten',
    'REJECTED BY Admin Kabupaten': 'rejected_by_admin_kabupaten',
    'COMPLETED BY Admin Kabupaten': 'completed_by_admin_kabupaten',
    'Email': 'pencacah_email'
}, inplace=True)

df_pencacah['revoked_by_admin_kabupaten'] = 0

# Map Pengawas email by Region Code
pengawas_map = df_pengawas.groupby('Region Code')['Email'].first().to_dict()
df_pencacah['pengawas_email'] = df_pencacah['level_6_full_code'].map(pengawas_map)

# Select and order columns to exactly match SQLLab where possible
# SQLLab columns: level_6_full_code, open, draft, submitted_respondent, submitted_by_pencacah,
# edited_by_pengawas, rejected_by_pengawas, approved_by_pengawas, revoked_by_pengawas,
# edited_by_admin_kabupaten, rejected_by_admin_kabupaten, revoked_by_admin_kabupaten,
# completed_by_admin_kabupaten, pencacah_id, pencacah_email, pengawas_id, pengawas_email
df_pencacah['pencacah_id'] = ''
df_pencacah['pengawas_id'] = ''

cols = [
    'level_6_full_code', 'open', 'draft', 'submitted_respondent', 'submitted_by_pencacah',
    'edited_by_pengawas', 'rejected_by_pengawas', 'approved_by_pengawas', 'revoked_by_pengawas',
    'edited_by_admin_kabupaten', 'rejected_by_admin_kabupaten', 'revoked_by_admin_kabupaten',
    'completed_by_admin_kabupaten', 'pencacah_id', 'pencacah_email', 'pengawas_id', 'pengawas_email'
]

# We need to aggregate by level_6_full_code in case a region code appears multiple times for Pencacah
agg_dict = {
    'open': 'sum', 'draft': 'sum', 'submitted_respondent': 'sum', 'submitted_by_pencacah': 'sum',
    'edited_by_pengawas': 'sum', 'rejected_by_pengawas': 'sum', 'approved_by_pengawas': 'sum',
    'revoked_by_pengawas': 'sum', 'edited_by_admin_kabupaten': 'sum', 'rejected_by_admin_kabupaten': 'sum',
    'completed_by_admin_kabupaten': 'sum', 'revoked_by_admin_kabupaten': 'sum', 'pencacah_email': 'first', 'pengawas_email': 'first',
    'pencacah_id': 'first', 'pengawas_id': 'first'
}

df_final = df_pencacah.groupby('level_6_full_code').agg(agg_dict).reset_index()
df_final = df_final[cols] # Reorder

output_filename = '/Users/jihanmaisaroh/scrap_fasih/Sisa_Target_Belum_Keambil_SQLLab.xlsx'
df_final.to_excel(output_filename, index=False)
print(f"File berhasil dibuat: {output_filename}")
print(f"Total SLS yang tidak ada di SQLLab: {len(df_final)} SLS")
