import os
import glob
import pandas as pd
import requests
import math

API_URL = "https://dds-api.bpssulteng.id/api.php?action=upsert_anomali"

def clean_float(val):
    if pd.isna(val):
        return None
    try:
        fval = float(val)
        if math.isnan(fval) or math.isinf(fval):
            return None
        return fval
    except:
        return None

def detect_anomali_and_format(row, cols):
    jenis = "Unknown"
    catatan = ""
    biaya = None
    pengeluaran = None
    pct = None

    if 'persentase_biaya_produksi' in cols:
        jenis = "Biaya Produksi Dominan"
        bp = clean_float(row.get('biaya_produksi')) or 0
        tp = clean_float(row.get('total_pengeluaran')) or 0
        pc = clean_float(row.get('persentase_biaya_produksi')) or 0
        catatan = f"💡 Biaya produksi: Rp {bp} | Total pengeluaran: Rp {tp} | Porsi biaya produksi: {pc}%"
        biaya = bp
        pengeluaran = tp
        pct = pc
    elif 'gaji' in cols and 'biaya_pembelian' in cols:
        jenis = "Missing Value Pengeluaran"
        catatan = f"💡 Terindikasi isian 9999 pada rincian pengeluaran."
    elif 'aset_tanah_bln' in cols:
        jenis = "Missing Value Nilai Aset Tetap"
        catatan = f"💡 Terindikasi isian 9999 pada rincian nilai aset."
    elif 'nik_dtsen' in cols and 'umur_ak' in cols:
        jenis = "Anomali Keluarga / Anggota Keluarga"
        catatan = f"💡 Cek konsistensi data NIK/Umur/Pendidikan."
    elif 'pendapatan_lain' in cols and 'nilai_pendapatan' in cols:
        jenis = "Missing Value Pendapatan"
        catatan = f"💡 Terindikasi isian 9999 pada rincian pendapatan."
    else:
        jenis = "Anomali Lainnya"
        catatan = "💡 Perlu pengecekan lanjutan."

    return jenis, catatan, biaya, pengeluaran, pct

def main():
    csv_files = glob.glob("anomali/*.csv")
    payloads = []

    for f in csv_files:
        df = pd.read_csv(f)
        cols = df.columns.tolist()
        
        for idx, row in df.iterrows():
            if 'assignment_id' not in cols or pd.isna(row['assignment_id']):
                continue
            
            jenis, catatan, biaya, pengeluaran, pct = detect_anomali_and_format(row, cols)
            
            # Extract region codes if possible
            level_6 = str(row.get('level_6_full_code', ''))
            kab = level_6[2:4] if len(level_6) >= 4 else None
            kec = level_6[4:7] if len(level_6) >= 7 else None
            desa = level_6[7:10] if len(level_6) >= 10 else None
            sls = level_6[10:14] if len(level_6) >= 14 else None
            
            payloads.append({
                "assignment_id": str(row['assignment_id']),
                "jenis_anomali": jenis,
                "catatan": catatan,
                "kab_code": kab,
                "kec_code": kec,
                "desa_code": desa,
                "sls_code": sls,
                "nama_krt": str(row.get('nama_usaha', '')) if pd.notna(row.get('nama_usaha')) else str(row.get('nama_dtsen', '')),
                "nama_petugas": str(row.get('pengusaha_var_label', '')) if pd.notna(row.get('pengusaha_var_label')) else '',
                "biaya_produksi": biaya,
                "total_pengeluaran": pengeluaran,
                "pct_biaya": pct,
                "status_anomali": 1
            })

    print(f"Total data anomali yang akan diupload: {len(payloads)}")
    
    chunk_size = 500
    for i in range(0, len(payloads), chunk_size):
        chunk = payloads[i:i+chunk_size]
        try:
            res = requests.post(API_URL, json=chunk)
            print(f"Upload chunk {i//chunk_size + 1}: {res.status_code} - {res.text}")
        except Exception as e:
            print(f"Error uploading chunk {i//chunk_size + 1}: {e}")

if __name__ == "__main__":
    main()
