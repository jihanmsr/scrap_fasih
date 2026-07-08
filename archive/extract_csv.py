import json
import base64
import gzip
import csv
import os
from datetime import datetime, timezone, timedelta

def convert_compressed_json_to_csv(json_filename="granular_assignments.json", csv_filename="hasil_export.csv"):
    if not os.path.exists(json_filename):
        print(f"[ERROR] File {json_filename} tidak ditemukan!")
        return

    print(f"Membaca file {json_filename}...")
    with open(json_filename, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # 1. Dekode Base64 & Dekompresi Gzip
    print("Mendekompresi data...")
    compressed_data = data.get("compressed_data", "")
    if not compressed_data:
        print("[ERROR] Tidak ada 'compressed_data' di dalam file JSON.")
        return

    compressed_bytes = base64.b64decode(compressed_data)
    raw_json_str = gzip.decompress(compressed_bytes).decode('utf-8')
    payload = json.loads(raw_json_str)

    # 2. Ambil referensi kamus data (Dictionaries)
    regions = payload.get("regions", [])
    petugas = payload.get("petugas", [])
    statuses = payload.get("statuses", [])
    targets = payload.get("targets", [])
    remarks = payload.get("remarks", {})

    print(f"Total target yang akan diekspor: {len(targets)}")

    # 3. Siapkan header CSV
    header = [
        "ID Target", "Kode Identitas", "Nama", "Status",
        "Tipe Survei", "Terakhir Dimodifikasi (WITA)",
        "PCL Username", "PCL Nama", "PML Username", "PML Nama",
        "Kode Kab", "Nama Kab", "Kode Kec", "Nama Kec",
        "Kode Desa", "Nama Desa", "Kode SLS", "Nama SLS",
        "Kode SubSLS", "Nama SubSLS", "Remarks / Catatan"
    ]

    # 4. Petakan (Mapping) dan Tulis ke CSV
    print(f"Menulis ke {csv_filename}...")
    with open(csv_filename, "w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)

        for t in targets:
            # Ambil data mentah dari array target
            tid = t[0]
            code_id = t[1]
            name = t[2]
            stat_idx = t[3]
            pet_idx = t[4]
            reg_idx = t[5]
            epoch_mod = t[6]
            survey_type = "SE UB" if t[7] == 1 else "SE Umum"
            pengawas_idx = t[8] if len(t) > 8 else -1

            # Mapping Status
            status_str = statuses[stat_idx] if stat_idx < len(statuses) else "-"

            # Mapping Petugas (PCL & PML)
            pcl = petugas[pet_idx] if 0 <= pet_idx < len(petugas) else ["-", "-"]
            pml = petugas[pengawas_idx] if 0 <= pengawas_idx < len(petugas) else ["-", "-"]

            # Mapping Region
            reg = regions[reg_idx] if reg_idx < len(regions) else [""] * 10
            # reg structure: (kab_code, kab_name, kec_code, kec_name, desa_code, desa_name, sls_code, sls_name, subsls_code, subsls_name)

            # Konversi waktu ke WITA (UTC+8)
            date_str = "-"
            if epoch_mod > 0:
                dt_utc = datetime.fromtimestamp(epoch_mod, tz=timezone.utc)
                dt_wita = dt_utc.astimezone(timezone(timedelta(hours=8)))
                date_str = dt_wita.strftime("%Y-%m-%d %H:%M:%S")

            # Mapping Remarks
            remark_str = remarks.get(tid, "-")

            # Susun baris CSV sesuai header
            row = [
                tid, code_id, name, status_str,
                survey_type, date_str,
                pcl[0], pcl[1], pml[0], pml[1],
                reg[0], reg[1], reg[2], reg[3],
                reg[4], reg[5], reg[6], reg[7],
                reg[8], reg[9], remark_str
            ]
            writer.writerow(row)

    print("✅ Selesai! Data berhasil diekspor ke CSV.")

if __name__ == "__main__":
    # Kamu bisa menyesuaikan nama file input dan output di sini jika diperlukan
    convert_compressed_json_to_csv(
        json_filename="granular_assignments.json", 
        csv_filename="hasil_export.csv"
    )