import json
import re
import os
import pandas as pd
from datetime import datetime

def parse_js_variable(filepath, var_name):
    if not os.path.exists(filepath):
        print(f"[WARNING] File {filepath} tidak ditemukan.")
        return None
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Match window.VAR_NAME = ...;
    pattern = re.compile(rf"window\.{var_name}\s*=\s*(.*?);", re.DOTALL)
    match = pattern.search(content)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except Exception as e:
            print(f"[ERROR] Gagal memparsing JSON untuk {var_name}: {e}")
    return None

def main():
    script_dir = "/Users/jihanmaisaroh/scrap_fasih"
    ipas_js_path = os.path.join(script_dir, "ipas_data.js")
    assign_js_path = os.path.join(script_dir, "assign_data.js")
    
    # 1. Load data dari JS
    ipas_data = parse_js_variable(ipas_js_path, "IPAS_DATA")
    petugas_umum = parse_js_variable(assign_js_path, "PETUGAS_DATA_UMUM")
    
    if not ipas_data:
        print("[ERROR] Data IPAS_DATA kosong atau tidak dapat dimuat.")
        return
        
    print("Memproses data rekap Kecamatan...")
    se_umum_kabs = ipas_data.get("se_umum", [])
    kec_rows = []
    
    for kab_data in se_umum_kabs:
        kab_name = kab_data.get("kabupaten", "")
        kec_list = kab_data.get("kecamatan_list", [])
        for kec in kec_list:
            total = kec.get("total_prelist", 0)
            draft = kec.get("total_draft", 0)
            approved = kec.get("total_approved", 0)
            rejected = kec.get("total_rejected", 0)
            
            # Submitted PCL & Respondent
            sub_pcl = kec.get("total_submitted_pencacah", 0)
            sub_resp = kec.get("total_submitted_respondent", 0)
            # Edited Admin (jika ada, default 0)
            edited = kec.get("total_edited_admin", 0) 
            
            # Total Selesai (semua selain open & draft)
            selesai = kec.get("total_submitted", 0)
            belum = max(0, total - selesai)
            open_cnt = max(0, total - draft - selesai)
            
            persen = round((selesai / total * 100), 2) if total > 0 else 0.0
            
            kec_rows.append({
                "Kabupaten": kab_name,
                "Kecamatan": kec.get("kec_name", ""),
                "Total Target": total,
                "Submitted by Pencacah": sub_pcl,
                "Approved by Pengawas": approved,
                "Submitted Respondent": sub_resp,
                "Edited by Admin": edited,
                "Rejected by Pengawas": rejected,
                "Draft": draft,
                "Open": open_cnt,
                "Total Selesai": selesai,
                "Belum Selesai": belum,
                "% Capaian": persen
            })
            
    df_kecamatan = pd.DataFrame(kec_rows).sort_values(["Kabupaten", "% Capaian"], ascending=[True, True])
    
    # Hitung total baris Kecamatan
    total_target_k = df_kecamatan["Total Target"].sum()
    total_selesai_k = df_kecamatan["Total Selesai"].sum()
    total_pct_k = round((total_selesai_k / total_target_k * 100), 2) if total_target_k > 0 else 0.0
    
    total_row_k = {
        "Kabupaten": "TOTAL PROVINSI",
        "Kecamatan": "SULAWESI TENGAH",
        "Total Target": total_target_k,
        "Submitted by Pencacah": df_kecamatan["Submitted by Pencacah"].sum(),
        "Approved by Pengawas": df_kecamatan["Approved by Pengawas"].sum(),
        "Submitted Respondent": df_kecamatan["Submitted Respondent"].sum(),
        "Edited by Admin": df_kecamatan["Edited by Admin"].sum(),
        "Rejected by Pengawas": df_kecamatan["Rejected by Pengawas"].sum(),
        "Draft": df_kecamatan["Draft"].sum(),
        "Open": df_kecamatan["Open"].sum(),
        "Total Selesai": total_selesai_k,
        "Belum Selesai": df_kecamatan["Belum Selesai"].sum(),
        "% Capaian": total_pct_k
    }
    df_kecamatan = pd.concat([df_kecamatan, pd.DataFrame([total_row_k])], ignore_index=True)
    
    # 2. Load data rekap Pegawai
    peg_rows = []
    if petugas_umum:
        print("Memproses data rekap Pegawai...")
        for p in petugas_umum:
            total = p.get("target_count", 0)
            selesai = p.get("sync_count", 0)
            draft = p.get("draft_count", 0)
            open_cnt = p.get("open_count", 0)
            submitted = p.get("submitted_count", 0)
            approved = p.get("approved_count", 0)
            rejected = p.get("rejected_count", 0)
            # Default edited & revoked to 0 for display
            edited = 0
            revoked = 0
            
            # hitung belum selesai
            belum = max(0, total - selesai)
            persen = round((selesai / total * 100), 2) if total > 0 else 0.0
            
            peg_rows.append({
                "Username": p.get("username", ""),
                "Nama Pegawai": p.get("fullname", ""),
                "Total Target": total,
                "Submitted by Pencacah": submitted,
                "Approved by Pengawas": approved,
                "Submitted Respondent": 0, # API responsibility tidak memisah respondent
                "Edited by Admin": edited,
                "Rejected by Pengawas": rejected,
                "Draft": draft,
                "Open": open_cnt,
                "Total Selesai": selesai,
                "Belum Selesai": belum,
                "% Capaian": persen
            })
            
    df_pegawai = pd.DataFrame(peg_rows).sort_values("% Capaian", ascending=True)
    
    # Hitung total baris Pegawai
    total_target_p = df_pegawai["Total Target"].sum()
    total_selesai_p = df_pegawai["Total Selesai"].sum()
    total_pct_p = round((total_selesai_p / total_target_p * 100), 2) if total_target_p > 0 else 0.0
    
    total_row_p = {
        "Username": "TOTAL",
        "Nama Pegawai": "SELURUH PEGAWAI SULTENG",
        "Total Target": total_target_p,
        "Submitted by Pencacah": df_pegawai["Submitted by Pencacah"].sum(),
        "Approved by Pengawas": df_pegawai["Approved by Pengawas"].sum(),
        "Submitted Respondent": df_pegawai["Submitted Respondent"].sum(),
        "Edited by Admin": df_pegawai["Edited by Admin"].sum(),
        "Rejected by Pengawas": df_pegawai["Rejected by Pengawas"].sum(),
        "Draft": df_pegawai["Draft"].sum(),
        "Open": df_pegawai["Open"].sum(),
        "Total Selesai": total_selesai_p,
        "Belum Selesai": df_pegawai["Belum Selesai"].sum(),
        "% Capaian": total_pct_p
    }
    df_pegawai = pd.concat([df_pegawai, pd.DataFrame([total_row_p])], ignore_index=True)
    
    # Tulis Excel
    excel_path = os.path.join(script_dir, "Laporan_Rekap_Cepat_Sulteng.xlsx")
    print(f"Menulis file Excel ke {excel_path}...")
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        df_kecamatan.to_excel(writer, sheet_name="Rekap_Kecamatan", index=False)
        df_pegawai.to_excel(writer, sheet_name="Rekap_Pegawai", index=False)
        
    # Tulis CSV
    kec_csv = os.path.join(script_dir, "Sulteng_Rekap_Kecamatan.csv")
    peg_csv = os.path.join(script_dir, "Sulteng_Rekap_Pegawai.csv")
    print("Menulis file CSV...")
    df_kecamatan.to_csv(kec_csv, index=False)
    df_pegawai.to_csv(peg_csv, index=False)
    
    print("✅ Berhasil membuat semua laporan rekap cepat tingkat provinsi!")
    print(f"Total Progres Sulteng: {total_pct_k}%")
    print(f"Excel: {excel_path}")
    print(f"CSVs:\n - {kec_csv}\n - {peg_csv}")

if __name__ == "__main__":
    main()
