import os
import json
import base64
import gzip

def generate_data_alokasi():
    # Mengambil granular assignments dari scrap_fasih
    granular_path = "/Users/jihanmaisaroh/scrap_fasih/granular_assignments.json"
    
    print("Membaca granular_assignments.json...")
    with open(granular_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    comp = data.get("compressed_data")
    if not comp:
        print("Tidak ada compressed_data.")
        return
        
    print("Mendekompresi data...")
    raw = json.loads(gzip.decompress(base64.b64decode(comp)).decode('utf-8'))
    
    master_regions = raw.get("regions", [])
    master_petugas = raw.get("petugas", [])
    master_targets = raw.get("targets", [])
    
    print(f"Total targets: {len(master_targets)}")
    
    # Kumpulkan data unik per SLS untuk SE UMUM (survey_flag == 0)
    sls_map = {}
    
    for t in master_targets:
        survey_flag = t[7]
        if survey_flag != 0:
            continue
            
        reg_idx = t[5]
        if reg_idx < 0 or reg_idx >= len(master_regions):
            continue
            
        reg = master_regions[reg_idx]
        kab_code = reg[0] if len(reg) > 0 else "-"
        kab_name = reg[1] if len(reg) > 1 else "-"
        kec_code = reg[2] if len(reg) > 2 else "-"
        kec_name = reg[3] if len(reg) > 3 else "-"
        desa_code = reg[4] if len(reg) > 4 else "-"
        desa_name = reg[5] if len(reg) > 5 else "-"
        sls_code = reg[6] if len(reg) > 6 else "-"
        sls_name = reg[7] if len(reg) > 7 else "-"
        
        if sls_code == "-" or not sls_code:
            continue
            
        # PPL
        pet_idx = t[4]
        email_ppl = "-"
        if 0 <= pet_idx < len(master_petugas):
            email_ppl = master_petugas[pet_idx][0]
            
        sls_full_code = f"{kab_code}_{kec_code}_{desa_code}_{sls_code}"
        
        if sls_full_code not in sls_map:
            sls_map[sls_full_code] = {
                'reg': reg,
                'petugas': set()
            }
        
        if email_ppl and email_ppl != "-":
            sls_map[sls_full_code]['petugas'].add(email_ppl)
            
    print(f"Total SLS unik ditemukan: {len(sls_map)}")
    sorted_sls = sorted(sls_map.keys())
    
    out_lines = []
    out_lines.append("// ═══════════════ DATA ALOKASI PPL/PML (SULTENG) ═══════════════")
    out_lines.append("// Data hasil ekstraksi dari FASIH untuk seluruh Sulawesi Tengah")
    out_lines.append("// Format Array: [id_unik, kode_kab, kode_kec, kode_desa, kode_sls, nama_kab, nama_kec, nama_desa, nama_sls, email_pml, email_ppl]")
    out_lines.append(f"// Total: {len(sorted_sls)} baris")
    out_lines.append("")
    out_lines.append("function _getAlokasiData() {")
    out_lines.append("  return [")
    
    for full_code in sorted_sls:
        info = sls_map[full_code]
        reg = info['reg']
        
        kab_code = reg[0]
        kab_name = reg[1].replace("'", "\\'") if reg[1] else "-"
        kec_code = reg[2]
        kec_name = reg[3].replace("'", "\\'") if reg[3] else "-"
        desa_code = reg[4]
        desa_name = reg[5].replace("'", "\\'") if reg[5] else "-"
        sls_code = reg[6]
        sls_name = reg[7].replace("'", "\\'") if reg[7] else "-"
        
        petugas_list = list(info['petugas'])
        email_ppl = petugas_list[0] if petugas_list else "-"
        email_pml = "-" # PML tidak ditarik langsung di granularity
        
        # Susunan baru disesuaikan: tambah kab agar spesifik se-Sulteng
        line = f"    ['{full_code}','{kab_code}','{kec_code}','{desa_code}','{sls_code}','{kab_name}','{kec_name}','{desa_name}','{sls_name}','{email_pml}','{email_ppl}'],"
        out_lines.append(line)
        
    out_lines.append("  ];")
    out_lines.append("}")
    
    out_path = "/Users/jihanmaisaroh/Downloads/Archive/DataAlokasi_Sulteng.gs"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(out_lines))
        
    print(f"Berhasil menulis {len(sorted_sls)} baris ke {out_path}")

if __name__ == "__main__":
    generate_data_alokasi()
