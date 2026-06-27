import os
import openpyxl
from dotenv import load_dotenv
import requests
from datetime import datetime

load_dotenv()
LOCAL_API_URL = os.getenv("LOCAL_API_URL", "https://dds-api.bpssulteng.id/api.php")

def post_to_api(action, json_data):
    url = "https://103.5.51.154/api.php"
    headers = {"Host": "bpssulteng.id"}
    return requests.post(f"{url}?action={action}", json=json_data, headers=headers, verify=False)

KAB_NAMES = {
    '7201': 'Banggai Kepulauan', '7202': 'Banggai', '7203': 'Morowali',
    '7204': 'Poso', '7205': 'Donggala', '7206': 'Toli-Toli', '7207': 'Buol',
    '7208': 'Parigi Moutong', '7209': 'Tojo Una-Una', '7210': 'Sigi',
    '7211': 'Banggai Laut', '7212': 'Morowali Utara', '7271': 'Kota Palu',
}

def fmt_rp(val):
    if val is None or str(val).strip() == '': return '-'
    try: return f"Rp {int(float(val)):,}".replace(',', '.')
    except: return str(val)

def read_excel(file_path):
    wb = openpyxl.load_workbook(file_path, data_only=True)
    sheet = wb.active
    rows = list(sheet.iter_rows(values_only=True))
    return rows[0] if rows else [], rows[1:] if len(rows) > 1 else []

def process_files():
    files = {
        "A3.xlsx": "Missing Value Nilai Aset Tetap",
        "A5.xlsx": "Biaya Produksi Dominan",
        "A6.xlsx": "Keuntungan Usaha",
        "A7.xlsx": "Penyertaan Modal Korporasi"
    }
    
    all_records = {}
    
    for filename, anomaly_type in files.items():
        if not os.path.exists(filename):
            print(f"Skipping {filename} - not found.")
            continue
            
        headers, rows = read_excel(filename)
        hmap = {str(h).lower().strip(): i for i, h in enumerate(headers) if h}
        
        for row in rows:
            if not row or row[0] == 'level_2_code': continue
            
            def get_val(key):
                return row[hmap[key]] if key in hmap and hmap[key] < len(row) else None
                
            kab_code = str(get_val('level_2_code') or '').strip()
            kab_code = '72' + kab_code if len(kab_code) == 2 else kab_code
            kec_code = str(get_val('level_3_code') or '').strip()
            desa_code = str(get_val('level_4_code') or '').strip()
            sls_code = str(get_val('level_5_code') or '').strip()
            
            if not kab_code.startswith('72'): kab_code = ''
                
            level_6 = str(get_val('level_6_full_code') or '')
            if level_6 and len(level_6) >= 16:
                kab_code = level_6[:4]
                kec_code = level_6[:6]
                desa_code = level_6[:9]
                sls_code = level_6
                
            assignment_id = str(get_val('assignment_id') or '').strip()
            if not assignment_id or assignment_id == 'None': continue
            
            nama_usaha = str(get_val('nama_usaha') or '')
            nama_petugas = str(get_val('current_user_fullname') or '')
            
            catatan = ""
            total_pengeluaran = get_val('total_pengeluaran')
            biaya_produksi = get_val('biaya_produksi')
            pct = 0
            
            if filename == "A3.xlsx":
                catatan = "Rincian nilai aset tanah & bangunan (28a/32a) atau selain tanah & bangunan (28b/32b) diisi 9999 (Tidak dapat memberikan informasi)."
            elif filename == "A5.xlsx":
                if total_pengeluaran and total_pengeluaran > 0 and biaya_produksi:
                    pct = round(float(biaya_produksi) / float(total_pengeluaran) * 100, 1)
                catatan = f"Kegiatan tidak memproduksi barang sendiri, namun biaya produksi {pct}% dari total pengeluaran (Biaya Produksi: {fmt_rp(biaya_produksi)} | Total Pengeluaran: {fmt_rp(total_pengeluaran)})."
            elif filename == "A6.xlsx":
                total_pendapatan = get_val('total_pendapatan')
                catatan = f"Selisih pendapatan dan pengeluaran negatif. (Pendapatan: {fmt_rp(total_pendapatan)} | Pengeluaran: {fmt_rp(total_pengeluaran)})."
            elif filename == "A7.xlsx":
                catatan = "Status badan usaha 'Bukan Badan Usaha' (13) namun terdapat kepemilikan modal korporasi publik/non-publik > 0."
                
            record = {
                'kab_code': KAB_NAMES.get(kab_code, kab_code),
                'kec_code': kec_code,
                'desa_code': desa_code,
                'sls_code': sls_code,
                'jenis_anomali': anomaly_type,
                'catatan': catatan,
                'assignment_id': assignment_id,
                'nama_krt': nama_usaha,
                'nama_petugas': nama_petugas,
                'waktu_anomali': datetime.now().isoformat()
            }
            
            if total_pengeluaran is not None:
                try: record['total_pengeluaran'] = int(float(total_pengeluaran))
                except: pass
            if biaya_produksi is not None:
                try: record['biaya_produksi'] = int(float(biaya_produksi))
                except: pass
            if pct > 0:
                record['pct_biaya'] = float(pct)
                
            all_records[f"{assignment_id}_{anomaly_type}"] = record
            
    return all_records

def main():
    print("Reading anomalies...")
    records_dict = process_files()
    if not records_dict:
        print("No records found.")
        return
        
    print(f"Found {len(records_dict)} anomalous records.")
    
    print("Fetching existing anomalies from API...")
    res = post_to_api('get_anomali', None)
    if res.status_code == 200:
        class FakeRes: pass
        fake_res = FakeRes()
        fake_res.data = res.json()
        res = fake_res
    else:
        print("Gagal mengambil data dari API")
        res.data = []
    existing = res.data or []
    
    existing_map = {f"{r.get('assignment_id')}_{r.get('jenis_anomali')}": r for r in existing if r.get('assignment_id')}
    
    to_insert = []
    to_update = []
    
    for key, new_rec in records_dict.items():
        if key in existing_map:
            ex = existing_map[key]
            new_rec['id'] = ex['id']
            new_rec['tindak_lanjut'] = ex.get('tindak_lanjut') or ''
            new_rec['status_anomali'] = ex.get('status_anomali') or 1
            if ex.get('nama_petugas') and not new_rec.get('nama_petugas'):
                new_rec['nama_petugas'] = ex.get('nama_petugas')
            to_update.append(new_rec)
        else:
            new_rec['tindak_lanjut'] = ''
            new_rec['status_anomali'] = 1
            to_insert.append(new_rec)
            
    print(f"To insert: {len(to_insert)}, To update: {len(to_update)}")
    
    if to_insert:
        post_to_api('upsert_anomali', to_insert)
        print(f"✅ Berhasil insert {len(to_insert)} data baru ke database lokal!")

    if to_update:
        for r in to_update:
            post_to_api('update_anomali', r)
        print(f"✅ Berhasil update {len(to_update)} data lama di database lokal!")
                
    print("Done!")

if __name__ == '__main__':
    main()
