import sys

with open('report_progress_petugas.py', 'r', encoding='utf-8') as f:
    code = f.read()

import re

# Remove `process_petugas_progress`
code = re.sub(r'def process_petugas_progress.*?return df', '', code, flags=re.DOTALL)

# Update main
target = '''def main():
    df_umum_summary = process_petugas_progress("se_umum")
    df_ub_summary = process_petugas_progress("se_ub")
    
    df_umum_detail, df_ub_detail = process_detailed_assignments()'''

replacement = '''def main():
    df_umum_detail, df_ub_detail = process_detailed_assignments()'''

code = code.replace(target, replacement)

target2 = '''    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        # Summary Sheets
        if df_umum_summary is not None and not df_umum_summary.empty:
            df_umum_summary.to_excel(writer, sheet_name="Ringkasan SE Umum", index=False)
        if df_ub_summary is not None and not df_ub_summary.empty:
            df_ub_summary.to_excel(writer, sheet_name="Ringkasan SE UB", index=False)
            
        # Detailed Target Sheets'''

replacement2 = '''    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        # Summary Sheets (computed purely from detail to guarantee correctness)
        selesai_statuses = ["DONE", "APPROVED", "SUBMITTED", "APPROVED_BY_SYSTEM", "REJECTED_BY_SYSTEM", "PENDING_APPROVAL"]
        
        if df_umum_detail is not None and not df_umum_detail.empty:
            df_umum_summary = df_umum_detail.groupby(["Email / Username Petugas"]).agg(
                Nama_Petugas=("Email / Username Petugas", "first"),
                Total_Target=("ID Target", "count"),
                Selesai=("Status", lambda x: sum(x.isin(selesai_statuses))),
                Belum_Selesai=("Status", lambda x: sum(~x.isin(selesai_statuses)))
            ).reset_index(drop=True)
            df_umum_summary["% Capaian"] = (df_umum_summary["Selesai"] / df_umum_summary["Total_Target"] * 100).round(2)
            df_umum_summary = df_umum_summary.sort_values(["% Capaian", "Total_Target"], ascending=[True, False])
            df_umum_summary.to_excel(writer, sheet_name="Ringkasan Petugas SE Umum", index=False)
            
        if df_ub_detail is not None and not df_ub_detail.empty:
            df_ub_summary = df_ub_detail.groupby(["Email / Username Petugas"]).agg(
                Nama_Petugas=("Email / Username Petugas", "first"),
                Total_Target=("ID Target", "count"),
                Selesai=("Status", lambda x: sum(x.isin(selesai_statuses))),
                Belum_Selesai=("Status", lambda x: sum(~x.isin(selesai_statuses)))
            ).reset_index(drop=True)
            df_ub_summary["% Capaian"] = (df_ub_summary["Selesai"] / df_ub_summary["Total_Target"] * 100).round(2)
            df_ub_summary = df_ub_summary.sort_values(["% Capaian", "Total_Target"], ascending=[True, False])
            df_ub_summary.to_excel(writer, sheet_name="Ringkasan Petugas SE UB", index=False)

        # Detailed Target Sheets'''

code = code.replace(target2, replacement2)

with open('report_progress_petugas.py', 'w', encoding='utf-8') as f:
    f.write(code)
print('Patched report_progress_petugas.py cleanly!')
