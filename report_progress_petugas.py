import json
import re
import pandas as pd
from datetime import datetime
import base64
import gzip
import csv
import gc
import os

def load_js_data(filepath, variable_name):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        pattern = re.compile(rf'window\.{variable_name}\s*=\s*(\[.*?\]|\{{.*?\}});', re.DOTALL)
        match = pattern.search(content)
        if match:
            json_str = match.group(1)
            return json.loads(json_str)
        else:
            print(f"[WARNING] {variable_name} not found in {filepath}")
            return None
    except Exception as e:
        print(f"[ERROR] Failed to load {variable_name} from {filepath}: {e}")
        return None



def process_detailed_assignments(timestamp):
    print("\n--- Mengekstrak Detail Target per Usaha/Perusahaan dari granular_assignments.json ---")
    try:
        with open("granular_assignments.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        
        compressed_data = data.get("compressed_data")
        if not compressed_data:
            print("[ERROR] compressed_data tidak ditemukan di granular_assignments.json")
            return None, None
            
        compressed_bytes = base64.b64decode(compressed_data)
        raw_json_str = gzip.decompress(compressed_bytes).decode('utf-8')
        payload = json.loads(raw_json_str)
        
        # Free memory of raw variables
        del raw_json_str
        del data
        del compressed_data
        gc.collect()
        
        regions_list = payload.get("regions", [])
        petugas_list = payload.get("petugas", [])
        statuses_list = payload.get("statuses", [])
        targets = payload.get("targets", [])
        
        print(f"-> Ditemukan {len(targets)} total target yang akan diurai.")
        
        headers = [
            "Pengawas", "Nama Pengawas", "Pencacah", "Nama Pencacah",
            "Kode Target", "Nama Perusahaan / Usaha", "Status",
            "Terakhir Diupdate", "Kabupaten", "Kecamatan", "Desa",
            "Nama SLS", "Nama Sub-SLS"
        ]
        
        filename_umum_csv = f"Detail_Usaha_SE_Umum_{timestamp}.csv"
        filename_ub_csv = f"Detail_Usaha_SE_UB_{timestamp}.csv"
        
        print(f"-> Streaming detail data ke:\n   - {filename_umum_csv}\n   - {filename_ub_csv}")
        
        f_umum = open(filename_umum_csv, "w", encoding="utf-8", newline="")
        f_ub = open(filename_ub_csv, "w", encoding="utf-8", newline="")
        
        writer_umum = csv.writer(f_umum)
        writer_ub = csv.writer(f_ub)
        
        writer_umum.writerow(headers)
        writer_ub.writerow(headers)
        
        summary_umum = {}
        summary_ub = {}
        
        selesais = {"DONE", "APPROVED", "SUBMITTED", "APPROVED_BY_SYSTEM", "REJECTED_BY_SYSTEM", "PENDING_APPROVAL"}
        
        for t in targets:
            code_id = t[1]
            target_name = t[2]
            stat_idx = t[3]
            pet_idx = t[4]
            reg_idx = t[5]
            epoch_mod = t[6]
            survey_flag = t[7]
            
            status_str = statuses_list[stat_idx] if stat_idx < len(statuses_list) else "-"
            
            if pet_idx >= 0 and pet_idx < len(petugas_list):
                petugas_username, petugas_fullname = petugas_list[pet_idx]
            else:
                petugas_username, petugas_fullname = "-", "-"
                
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
            
            pengawas_idx = t[8] if len(t) > 8 else -1
            pengawas_username = "-"
            pengawas_fullname = "-"
            if pengawas_idx >= 0 and pengawas_idx < len(petugas_list):
                pengawas_username = petugas_list[pengawas_idx][0]
                pengawas_fullname = petugas_list[pengawas_idx][1]

            row = [
                pengawas_username,
                pengawas_fullname,
                petugas_username,
                petugas_fullname,
                code_id,
                target_name,
                status_str,
                last_modified,
                kab_name,
                kec_name,
                desa_name,
                sls_name,
                subsls_name
            ]
            
            is_selesai = 1 if status_str in selesais else 0
            
            if survey_flag == 0:
                writer_umum.writerow(row)
                if petugas_username not in summary_umum:
                    summary_umum[petugas_username] = {
                        "Nama_Petugas": petugas_username,
                        "Total_Target": 0,
                        "Selesai": 0,
                        "Belum_Selesai": 0
                    }
                summary_umum[petugas_username]["Total_Target"] += 1
                summary_umum[petugas_username]["Selesai"] += is_selesai
                summary_umum[petugas_username]["Belum_Selesai"] += (1 - is_selesai)
            else:
                writer_ub.writerow(row)
                if petugas_username not in summary_ub:
                    summary_ub[petugas_username] = {
                        "Nama_Petugas": petugas_username,
                        "Total_Target": 0,
                        "Selesai": 0,
                        "Belum_Selesai": 0
                    }
                summary_ub[petugas_username]["Total_Target"] += 1
                summary_ub[petugas_username]["Selesai"] += is_selesai
                summary_ub[petugas_username]["Belum_Selesai"] += (1 - is_selesai)
                
        f_umum.close()
        f_ub.close()
        
        df_umum_summary = pd.DataFrame(list(summary_umum.values()))
        df_ub_summary = pd.DataFrame(list(summary_ub.values()))
        
        del payload
        del targets
        gc.collect()
        
        return df_umum_summary, df_ub_summary
        
    except Exception as e:
        print(f"[ERROR] Gagal mengekstrak target detail: {e}")
        return None, None

def main():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    df_umum_summary, df_ub_summary = process_detailed_assignments(timestamp)
    
    filename = f"Laporan_Progres_Petugas_{timestamp}.xlsx"
    
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        if df_umum_summary is not None and not df_umum_summary.empty:
            df_umum_summary["% Capaian"] = (df_umum_summary["Selesai"] / df_umum_summary["Total_Target"] * 100).round(2)
            df_umum_summary = df_umum_summary.sort_values(["% Capaian", "Total_Target"], ascending=[True, False])
            df_umum_summary.to_excel(writer, sheet_name="Ringkasan Petugas SE Umum", index=False)
            
        if df_ub_summary is not None and not df_ub_summary.empty:
            df_ub_summary["% Capaian"] = (df_ub_summary["Selesai"] / df_ub_summary["Total_Target"] * 100).round(2)
            df_ub_summary = df_ub_summary.sort_values(["% Capaian", "Total_Target"], ascending=[True, False])
            df_ub_summary.to_excel(writer, sheet_name="Ringkasan Petugas SE UB", index=False)
            
    print(f"\n✅ Laporan Ringkasan berhasil diekspor ke {filename}")

if __name__ == "__main__":
    main()
