import json
import base64
import gzip
import pandas as pd
import os
from datetime import datetime

def main():
    script_dir = "/Users/jihanmaisaroh/scrap_fasih"
    json_path = os.path.join(script_dir, "granular_assignments_se_umum_7212.json")
    
    if not os.path.exists(json_path):
        print(f"[ERROR] File {json_path} tidak ditemukan!")
        return
        
    print(f"Membaca {json_path}...")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    compressed_data = data.get("compressed_data")
    if not compressed_data:
        print("[ERROR] compressed_data tidak ditemukan!")
        return
        
    print("Mendekompresi data...")
    compressed_bytes = base64.b64decode(compressed_data)
    raw_json_str = gzip.decompress(compressed_bytes).decode('utf-8')
    payload = json.loads(raw_json_str)
    
    regions_list = payload.get("regions", [])
    petugas_list = payload.get("petugas", [])
    statuses_list = payload.get("statuses", [])
    targets = payload.get("targets", [])
    
    print(f"Berhasil memuat {len(targets)} target.")
    
    rows = []
    kecamatan_data = {}
    pegawai_data = {}
    
    for t in targets:
        code_id = t[1]
        target_name = t[2]
        stat_idx = t[3]
        pet_idx = t[4]
        reg_idx = t[5]
        epoch_mod = t[6]
        
        status_str = statuses_list[stat_idx] if stat_idx < len(statuses_list) else "-"
        
        if pet_idx >= 0 and pet_idx < len(petugas_list):
            pet_username, pet_fullname = petugas_list[pet_idx]
        else:
            pet_username, pet_fullname = "-", "-"
            
        if reg_idx >= 0 and reg_idx < len(regions_list):
            reg = regions_list[reg_idx]
            kab_name = reg[1]
            kec_name = reg[3]
            desa_name = reg[5]
            sls_name = reg[7]
            subsls_name = reg[9] if len(reg) > 9 else "-"
        else:
            kab_name, kec_name, desa_name, sls_name, subsls_name = "-", "-", "-", "-", "-"
            
        last_modified = "-"
        if epoch_mod > 0:
            last_modified = datetime.fromtimestamp(epoch_mod).strftime('%Y-%m-%d %H:%M:%S')
            
        row = {
            "Kabupaten": kab_name,
            "Kecamatan": kec_name,
            "Desa": desa_name,
            "Nama SLS": sls_name,
            "Nama Sub-SLS": subsls_name,
            "Kode Target": code_id,
            "Nama Perusahaan/Usaha": target_name,
            "Status": status_str,
            "Petugas Username": pet_username,
            "Petugas Nama": pet_fullname,
            "Terakhir Diupdate": last_modified
        }
        rows.append(row)
        
        # Breakdown status counters
        status_upper = status_str.upper()
        
        is_sub_pcl = 1 if status_upper == "SUBMITTED BY PENCACAH" else 0
        is_app_pml = 1 if status_upper == "APPROVED BY PENGAWAS" else 0
        is_sub_resp = 1 if status_upper == "SUBMITTED RESPONDENT" else 0
        is_edt_adm = 1 if status_upper == "EDITED BY ADMIN KABUPATEN" else 0
        is_rej_pml = 1 if status_upper == "REJECTED BY PENGAWAS" else 0
        is_rev_pml = 1 if status_upper == "REVOKED BY PENGAWAS" else 0
        is_draft = 1 if status_upper == "DRAFT" else 0
        is_open = 1 if status_upper == "OPEN" else 0
        
        is_selesai = 1 if status_upper not in ("OPEN", "DRAFT", "-", "") else 0
        is_belum = 1 - is_selesai
        
        # Agregasi Kecamatan
        if kec_name not in kecamatan_data:
            kecamatan_data[kec_name] = {
                "Total Target": 0,
                "Submitted by Pencacah": 0,
                "Approved by Pengawas": 0,
                "Submitted Respondent": 0,
                "Edited by Admin": 0,
                "Rejected by Pengawas": 0,
                "Revoked by Pengawas": 0,
                "Draft": 0,
                "Open": 0,
                "Total Selesai": 0,
                "Belum Selesai": 0
            }
        
        kec_stats = kecamatan_data[kec_name]
        kec_stats["Total Target"] += 1
        kec_stats["Submitted by Pencacah"] += is_sub_pcl
        kec_stats["Approved by Pengawas"] += is_app_pml
        kec_stats["Submitted Respondent"] += is_sub_resp
        kec_stats["Edited by Admin"] += is_edt_adm
        kec_stats["Rejected by Pengawas"] += is_rej_pml
        kec_stats["Revoked by Pengawas"] += is_rev_pml
        kec_stats["Draft"] += is_draft
        kec_stats["Open"] += is_open
        kec_stats["Total Selesai"] += is_selesai
        kec_stats["Belum Selesai"] += is_belum
        
        # Agregasi Pegawai
        if pet_username != "-":
            if pet_username not in pegawai_data:
                pegawai_data[pet_username] = {
                    "Username": pet_username,
                    "Nama Pegawai": pet_fullname,
                    "Total Target": 0,
                    "Submitted by Pencacah": 0,
                    "Approved by Pengawas": 0,
                    "Submitted Respondent": 0,
                    "Edited by Admin": 0,
                    "Rejected by Pengawas": 0,
                    "Revoked by Pengawas": 0,
                    "Draft": 0,
                    "Open": 0,
                    "Total Selesai": 0,
                    "Belum Selesai": 0
                }
            
            peg_stats = pegawai_data[pet_username]
            peg_stats["Total Target"] += 1
            peg_stats["Submitted by Pencacah"] += is_sub_pcl
            peg_stats["Approved by Pengawas"] += is_app_pml
            peg_stats["Submitted Respondent"] += is_sub_resp
            peg_stats["Edited by Admin"] += is_edt_adm
            peg_stats["Rejected by Pengawas"] += is_rej_pml
            peg_stats["Revoked by Pengawas"] += is_rev_pml
            peg_stats["Draft"] += is_draft
            peg_stats["Open"] += is_open
            peg_stats["Total Selesai"] += is_selesai
            peg_stats["Belum Selesai"] += is_belum

    df_detail = pd.DataFrame(rows)
    
    # Buat dataframe kecamatan
    kec_rows = []
    for kec, s in kecamatan_data.items():
        total = s["Total Target"]
        selesai = s["Total Selesai"]
        persen = round((selesai / total * 100), 2) if total > 0 else 0.0
        kec_rows.append({
            "Kecamatan": kec,
            "Total Target": total,
            "Submitted by Pencacah": s["Submitted by Pencacah"],
            "Approved by Pengawas": s["Approved by Pengawas"],
            "Submitted Respondent": s["Submitted Respondent"],
            "Edited by Admin": s["Edited by Admin"],
            "Rejected by Pengawas": s["Rejected by Pengawas"],
            "Revoked by Pengawas": s["Revoked by Pengawas"],
            "Draft": s["Draft"],
            "Open": s["Open"],
            "Total Selesai": selesai,
            "Belum Selesai": s["Belum Selesai"],
            "% Capaian": persen
        })
    df_kecamatan = pd.DataFrame(kec_rows).sort_values("% Capaian", ascending=True)
    
    # Tambahkan baris TOTAL di bawah Kecamatan
    total_target_k = df_kecamatan["Total Target"].sum()
    total_selesai_k = df_kecamatan["Total Selesai"].sum()
    total_pct_k = round((total_selesai_k / total_target_k * 100), 2) if total_target_k > 0 else 0.0
    
    total_row_k = {
        "Kecamatan": "TOTAL MOROWALI UTARA",
        "Total Target": total_target_k,
        "Submitted by Pencacah": df_kecamatan["Submitted by Pencacah"].sum(),
        "Approved by Pengawas": df_kecamatan["Approved by Pengawas"].sum(),
        "Submitted Respondent": df_kecamatan["Submitted Respondent"].sum(),
        "Edited by Admin": df_kecamatan["Edited by Admin"].sum(),
        "Rejected by Pengawas": df_kecamatan["Rejected by Pengawas"].sum(),
        "Revoked by Pengawas": df_kecamatan["Revoked by Pengawas"].sum(),
        "Draft": df_kecamatan["Draft"].sum(),
        "Open": df_kecamatan["Open"].sum(),
        "Total Selesai": total_selesai_k,
        "Belum Selesai": df_kecamatan["Belum Selesai"].sum(),
        "% Capaian": total_pct_k
    }
    df_kecamatan = pd.concat([df_kecamatan, pd.DataFrame([total_row_k])], ignore_index=True)
    
    # Buat dataframe pegawai
    peg_rows = []
    for peg, s in pegawai_data.items():
        total = s["Total Target"]
        selesai = s["Total Selesai"]
        persen = round((selesai / total * 100), 2) if total > 0 else 0.0
        peg_rows.append({
            "Username": s["Username"],
            "Nama Pegawai": s["Nama Pegawai"],
            "Total Target": total,
            "Submitted by Pencacah": s["Submitted by Pencacah"],
            "Approved by Pengawas": s["Approved by Pengawas"],
            "Submitted Respondent": s["Submitted Respondent"],
            "Edited by Admin": s["Edited by Admin"],
            "Rejected by Pengawas": s["Rejected by Pengawas"],
            "Revoked by Pengawas": s["Revoked by Pengawas"],
            "Draft": s["Draft"],
            "Open": s["Open"],
            "Total Selesai": selesai,
            "Belum Selesai": s["Belum Selesai"],
            "% Capaian": persen
        })
    df_pegawai = pd.DataFrame(peg_rows).sort_values("% Capaian", ascending=True)
    
    # Tambahkan baris TOTAL di bawah Pegawai
    total_target_p = df_pegawai["Total Target"].sum()
    total_selesai_p = df_pegawai["Total Selesai"].sum()
    total_pct_p = round((total_selesai_p / total_target_p * 100), 2) if total_target_p > 0 else 0.0
    
    total_row_p = {
        "Username": "TOTAL",
        "Nama Pegawai": "SELURUH PEGAWAI",
        "Total Target": total_target_p,
        "Submitted by Pencacah": df_pegawai["Submitted by Pencacah"].sum(),
        "Approved by Pengawas": df_pegawai["Approved by Pengawas"].sum(),
        "Submitted Respondent": df_pegawai["Submitted Respondent"].sum(),
        "Edited by Admin": df_pegawai["Edited by Admin"].sum(),
        "Rejected by Pengawas": df_pegawai["Rejected by Pengawas"].sum(),
        "Revoked by Pengawas": df_pegawai["Revoked by Pengawas"].sum(),
        "Draft": df_pegawai["Draft"].sum(),
        "Open": df_pegawai["Open"].sum(),
        "Total Selesai": total_selesai_p,
        "Belum Selesai": df_pegawai["Belum Selesai"].sum(),
        "% Capaian": total_pct_p
    }
    df_pegawai = pd.concat([df_pegawai, pd.DataFrame([total_row_p])], ignore_index=True)
    
    # Tulis Excel
    excel_path = os.path.join(script_dir, "Laporan_Morowali_Utara_7212.xlsx")
    print(f"Menulis file Excel ke {excel_path}...")
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        df_detail.to_excel(writer, sheet_name="Detail_Data", index=False)
        df_kecamatan.to_excel(writer, sheet_name="Rekap_Kecamatan", index=False)
        df_pegawai.to_excel(writer, sheet_name="Rekap_Pegawai", index=False)
        
    # Tulis CSV Terpisah
    detail_csv = os.path.join(script_dir, "Morowali_Utara_Detail_Data.csv")
    kec_csv = os.path.join(script_dir, "Morowali_Utara_Rekap_Kecamatan.csv")
    peg_csv = os.path.join(script_dir, "Morowali_Utara_Rekap_Pegawai.csv")
    
    print("Menulis file CSV...")
    df_detail.to_csv(detail_csv, index=False)
    df_kecamatan.to_csv(kec_csv, index=False)
    df_pegawai.to_csv(peg_csv, index=False)
    
    print("✅ Berhasil membuat semua laporan Morowali Utara!")
    print(f"Total Progres Morowali Utara: {total_pct_k}%")
    print(f"Excel: {excel_path}")
    print(f"CSVs:\n - {detail_csv}\n - {kec_csv}\n - {peg_csv}")

if __name__ == "__main__":
    main()
