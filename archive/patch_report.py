import sys

with open('report_progress_petugas.py', 'r', encoding='utf-8') as f:
    code = f.read()

target = '''    # Buat Ringkasan (Group by Wilayah & Petugas)
    df_umum_summary = None
    if df_umum_detail is not None and not df_umum_detail.empty:
        df_umum_summary = df_umum_detail.groupby(["Kabupaten", "Kecamatan", "Desa", "Nama SLS", "Nama Sub-SLS", "Nama Petugas"]).agg(
            Total_Target=("ID Target", "count"),
            Selesai=("Status", lambda x: sum(x.isin(selesai_statuses))),
            Belum_Selesai=("Status", lambda x: sum(~x.isin(selesai_statuses)))
        ).reset_index()
        df_umum_summary["% Capaian"] = (df_umum_summary["Selesai"] / df_umum_summary["Total_Target"] * 100).round(2)
        
    df_ub_summary = None
    if df_ub_detail is not None and not df_ub_detail.empty:
        df_ub_summary = df_ub_detail.groupby(["Kabupaten", "Kecamatan", "Desa", "Nama SLS", "Nama Sub-SLS", "Nama Petugas"]).agg(
            Total_Target=("ID Target", "count"),
            Selesai=("Status", lambda x: sum(x.isin(selesai_statuses))),
            Belum_Selesai=("Status", lambda x: sum(~x.isin(selesai_statuses)))
        ).reset_index()
        df_ub_summary["% Capaian"] = (df_ub_summary["Selesai"] / df_ub_summary["Total_Target"] * 100).round(2)'''

replacement = '''    # Buat Ringkasan per Petugas (tanpa grouping SLS)
    df_umum_summary = None
    if df_umum_detail is not None and not df_umum_detail.empty:
        df_umum_summary = df_umum_detail.groupby(["Nama Petugas"]).agg(
            Total_Target=("ID Target", "count"),
            Selesai=("Status", lambda x: sum(x.isin(selesai_statuses))),
            Belum_Selesai=("Status", lambda x: sum(~x.isin(selesai_statuses)))
        ).reset_index()
        df_umum_summary["% Capaian"] = (df_umum_summary["Selesai"] / df_umum_summary["Total_Target"] * 100).round(2)
        df_umum_summary = df_umum_summary.sort_values("Total_Target", ascending=False)
        
    df_ub_summary = None
    if df_ub_detail is not None and not df_ub_detail.empty:
        df_ub_summary = df_ub_detail.groupby(["Nama Petugas"]).agg(
            Total_Target=("ID Target", "count"),
            Selesai=("Status", lambda x: sum(x.isin(selesai_statuses))),
            Belum_Selesai=("Status", lambda x: sum(~x.isin(selesai_statuses)))
        ).reset_index()
        df_ub_summary["% Capaian"] = (df_ub_summary["Selesai"] / df_ub_summary["Total_Target"] * 100).round(2)
        df_ub_summary = df_ub_summary.sort_values("Total_Target", ascending=False)'''

if target in code:
    code = code.replace(target, replacement)
    
    target2 = '''        if df_umum_summary is not None and not df_umum_summary.empty:
            df_umum_summary.to_excel(writer, sheet_name="Ringkasan SE Umum", index=False)
        if df_ub_summary is not None and not df_ub_summary.empty:
            df_ub_summary.to_excel(writer, sheet_name="Ringkasan SE UB", index=False)'''

    replacement2 = '''        if df_umum_summary is not None and not df_umum_summary.empty:
            df_umum_summary.to_excel(writer, sheet_name="Rekap Petugas SE Umum", index=False)
        if df_ub_summary is not None and not df_ub_summary.empty:
            df_ub_summary.to_excel(writer, sheet_name="Rekap Petugas SE UB", index=False)'''
            
    code = code.replace(target2, replacement2)
    
    with open('report_progress_petugas.py', 'w', encoding='utf-8') as f:
        f.write(code)
    print('Patched report_progress_petugas.py successfully!')
else:
    print('Target not found!')
