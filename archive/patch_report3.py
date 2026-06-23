with open('report_progress_petugas.py', 'r', encoding='utf-8') as f:
    code = f.read()

import re

# In process_detailed_assignments
target = '''            record = {
                "Pencacah": petugas_username,
                "Nama Pencacah": petugas_fullname,
                "Kode Target": code_id,
                "Nama Perusahaan / Usaha": target_name,
                "Status": status_str,
                "Terakhir Diupdate": last_modified,
                "Kabupaten": kab_name,
                "Kecamatan": kec_name,
                "Desa": desa_name,
                "Nama SLS": sls_name,
                "Nama Sub-SLS": subsls_name
            }'''

replacement = '''            pengawas_idx = target[8] if len(target) > 8 else -1
            pengawas_username = "-"
            pengawas_fullname = "-"
            if pengawas_idx >= 0 and pengawas_idx < len(petugas_list):
                pengawas_username = petugas_list[pengawas_idx][0]
                pengawas_fullname = petugas_list[pengawas_idx][1]

            record = {
                "Pengawas": pengawas_username,
                "Nama Pengawas": pengawas_fullname,
                "Pencacah": petugas_username,
                "Nama Pencacah": petugas_fullname,
                "Kode Target": code_id,
                "Nama Perusahaan / Usaha": target_name,
                "Status": status_str,
                "Terakhir Diupdate": last_modified,
                "Kabupaten": kab_name,
                "Kecamatan": kec_name,
                "Desa": desa_name,
                "Nama SLS": sls_name,
                "Nama Sub-SLS": subsls_name
            }'''

code = code.replace(target, replacement)

target2 = '''                Nama_Petugas=("Nama Pencacah", "first"),
                Total_Target=("Kode Target", "count"),'''

replacement2 = '''                Nama_Pencacah=("Nama Pencacah", "first"),
                Pengawas=("Pengawas", "first"),
                Nama_Pengawas=("Nama Pengawas", "first"),
                Total_Target=("Kode Target", "count"),'''

code = code.replace(target2, replacement2)

with open('report_progress_petugas.py', 'w', encoding='utf-8') as f:
    f.write(code)
print("Patched report_progress_petugas.py for Pengawas!")
