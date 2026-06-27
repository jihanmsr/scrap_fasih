"""
Seed data anomali dari berbagai file Excel (A3.xlsx, A5.xlsx, A6.xlsx, A7.xlsx, biaya_produksi_dominan.xlsx)
ke Supabase dengan Smart Upsert (tanpa menghapus tindak lanjut petugas).
"""
import os
import sys
import glob
import openpyxl
from dotenv import load_dotenv
from datetime import datetime
LOCAL_API_URL = os.getenv("LOCAL_API_URL", "https://dds-api.bpssulteng.id/api.php")
import requests

def post_to_api(action, json_data):
    url = "https://103.5.51.154/api.php"
    headers = {"Host": "dds-api.bpssulteng.id"}
    return requests.post(f"{url}?action={action}", json=json_data, headers=headers, verify=False)

# Mapping kab_code ke nama kabupaten Sulteng
KAB_NAMES = {
    '7201': 'Banggai Kepulauan',
    '7202': 'Banggai',
    '7203': 'Morowali',
    '7204': 'Poso',
    '7205': 'Donggala',
    '7206': 'Toli-Toli',
    '7207': 'Buol',
    '7208': 'Parigi Moutong',
    '7209': 'Tojo Una-Una',
    '7210': 'Sigi',
    '7211': 'Banggai Laut',
    '7212': 'Morowali Utara',
    '7271': 'Kota Palu',
}

def fmt_rp(val):
    if val is None or val == '':
        return '-'
    try:
        return f"Rp {int(val):,}".replace(',', '.')
    except:
        return str(val)

def process_excel_file(filepath):
    print(f"📖 Membaca data dari '{filepath}'...")
    wb = openpyxl.load_workbook(filepath)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        print(f"   ⚠️  File '{filepath}' kosong.")
        return []
        
    headers = [str(cell).strip() if cell is not None else '' for cell in rows[0]]
    data_rows = rows[1:]
    
    def get_val(row_data, col_name, default=None):
        if col_name in headers:
            idx = headers.index(col_name)
            if idx < len(row_data):
                val = row_data[idx]
                return val if val is not None else default
        return default

    records = []
    
    # Deteksi jenis anomali dari nama file
    filename_lower = os.path.basename(filepath).lower()
    
    for idx, row in enumerate(data_rows):
        level6 = str(get_val(row, 'level_6_code') or '').strip()
        # Fallback untuk file lama biaya_produksi_dominan.xlsx
        if not level6:
            if len(row) > 3 and row[3]:
                level6 = str(row[3]).strip()
        
        assignment_id = str(get_val(row, 'assignment_id') or '').strip()
        if not assignment_id or assignment_id == 'None':
            if len(row) > 4 and row[4]:
                assignment_id = str(row[4]).strip()
                
        if not assignment_id or assignment_id == 'None' or not level6:
            continue

        # Parse wilayah dari level_6_code
        kab_code = level6[:4] if len(level6) >= 4 else ''
        kec_code = level6[:6] if len(level6) >= 6 else ''
        desa_code = level6[:9] if len(level6) >= 9 else ''
        sls_code = level6

        # Nama kab/kota
        level_2_name = get_val(row, 'level_2_name')
        kab_name = level_2_name or KAB_NAMES.get(kab_code, kab_code)

        # Nama Petugas & Nama Usaha
        nama_petugas = get_val(row, 'current_user_fullname') or ''
        nama_krt = get_val(row, 'nama_usaha') or get_val(row, 'nama_usaha_edit') or ''
        if not nama_krt and len(row) > 5:
            nama_krt = row[5] if row[5] else ''

        # Inisialisasi default
        total_pengeluaran = None
        biaya_produksi = None
        pct_biaya = 0.0
        jenis = "Data Anomali"
        catatan = ""

        # Kasus A3: Penyertaan Modal Korporasi
        if 'a3' in filename_lower:
            jenis = "Penyertaan Modal Korporasi (Bukan Badan Usaha)"
            publik = get_val(row, 'publik', 0)
            non_publik = get_val(row, 'non_publik', 0)
            badan_usaha = get_val(row, 'badan_usaha_value')
            catatan = f"Badan Usaha: {badan_usaha} | Modal Publik: {publik}% | Modal Non-Publik: {non_publik}%"
            cat_lapangan = get_val(row, 'catatan')
            if cat_lapangan:
                catatan += f" | Lapangan: {cat_lapangan}"

        # Kasus A5: Makan Bergizi Gratis (MBG) Rasio Tinggi
        elif 'a5' in filename_lower:
            jenis = "Rasio Pendapatan/Pengeluaran MBG Tinggi"
            total_pendapatan = get_val(row, 'total_pendapatan')
            total_pengeluaran_val = get_val(row, 'total_pengeluaran')
            ratio = get_val(row, 'ratio_total_pendapatan')
            catatan = f"Pendapatan: {fmt_rp(total_pendapatan)} | Pengeluaran: {fmt_rp(total_pengeluaran_val)} | Rasio: {ratio}"
            cat_lapangan = get_val(row, 'catatan')
            if cat_lapangan:
                catatan += f" | Lapangan: {cat_lapangan}"
            if total_pengeluaran_val:
                total_pengeluaran = int(total_pengeluaran_val)

        # Kasus A6: Rasio Pendapatan/Pengeluaran MBG SPPG
        elif 'a6' in filename_lower:
            jenis = "Rasio Pendapatan/Pengeluaran MBG SPPG"
            total_pendapatan_bln = get_val(row, 'total_pendapatan_bln')
            total_pengeluaran_bln = get_val(row, 'total_pengeluaran_bln')
            ratio = get_val(row, 'ratio_total_pendapatan_bln')
            catatan = f"Pendapatan Bulanan: {fmt_rp(total_pendapatan_bln)} | Pengeluaran Bulanan: {fmt_rp(total_pengeluaran_bln)} | Rasio: {ratio}"
            cat_lapangan = get_val(row, 'catatan')
            if cat_lapangan:
                catatan += f" | Lapangan: {cat_lapangan}"
            if total_pengeluaran_bln:
                total_pengeluaran = int(total_pengeluaran_bln)

        # Kasus A7: Hubungan Aset, Pekerja, dan Pendapatan
        elif 'a7' in filename_lower:
            jenis = "Hubungan Aset, Pekerja, dan Pendapatan Usaha"
            total_aset = get_val(row, 'total_aset_bln') or get_val(row, 'total_aset_thn')
            total_tk = get_val(row, 'total_tk_jk')
            total_pendapatan_bln = get_val(row, 'total_pendapatan_bln')
            catatan = f"Aset: {total_aset} | Pekerja: {total_tk} | Pendapatan Bulanan: {fmt_rp(total_pendapatan_bln)}"
            cat_lapangan = get_val(row, 'catatan')
            if cat_lapangan:
                catatan += f" | Lapangan: {cat_lapangan}"

        # Kasus Original: Biaya Produksi Dominan
        elif 'biaya_produksi_dominan' in filename_lower or not filename_lower.startswith('a'):
            total_pengeluaran_val = get_val(row, 'total_pengeluaran') or (row[7] if len(row) > 7 else None)
            biaya_produksi_val = get_val(row, 'biaya_produksi') or (row[8] if len(row) > 8 else None)
            
            if total_pengeluaran_val:
                total_pengeluaran = int(total_pengeluaran_val)
            if biaya_produksi_val:
                biaya_produksi = int(biaya_produksi_val)
                
            if total_pengeluaran and total_pengeluaran > 0 and biaya_produksi:
                pct_biaya = round(biaya_produksi / total_pengeluaran * 100, 1)

            if pct_biaya > 100:
                jenis = 'Biaya Produksi Melebihi Total Pengeluaran'
            elif pct_biaya == 100:
                jenis = 'Biaya Produksi Sama dengan Total Pengeluaran'
            elif pct_biaya >= 80:
                jenis = 'Biaya Produksi Sangat Dominan (≥80%)'
            else:
                jenis = 'Biaya Produksi Dominan (≥50%)'

            catatan = (
                f"Biaya produksi: {fmt_rp(biaya_produksi)} | "
                f"Total pengeluaran: {fmt_rp(total_pengeluaran)} | "
                f"Porsi biaya produksi: {pct_biaya}%"
            )
            cat_lapangan = get_val(row, 'catatan')
            if cat_lapangan:
                catatan += f" | Lapangan: {cat_lapangan}"

        records.append({
            'kab_code': kab_name,
            'kec_code': kec_code,
            'desa_code': desa_code,
            'sls_code': sls_code,
            'jenis_anomali': jenis,
            'catatan': catatan,
            'assignment_id': assignment_id,
            'total_pengeluaran': total_pengeluaran,
            'biaya_produksi': biaya_produksi,
            'pct_biaya': float(pct_biaya),
            'nama_petugas': nama_petugas,
            'nama_krt': nama_krt
        })
        
    print(f"   ✅ Berhasil memproses {len(records)} baris valid dari '{filepath}'")
    return records

def main():
    # 1. Tentukan file Excel yang akan dibaca
    excel_files = []
    if len(sys.argv) > 1:
        # Jika ada argumen, gunakan file tersebut
        excel_files = sys.argv[1:]
    else:
        # Cari file A*.xlsx dan biaya_produksi_dominan.xlsx
        excel_files = glob.glob('A*.xlsx') + glob.glob('biaya_produksi_dominan.xlsx')
        if not excel_files:
            print("❌ Error: Tidak ditemukan file Excel untuk di-import!")
            sys.exit(1)

    print(f"📂 Mendeteksi {len(excel_files)} file Excel untuk di-import:")
    for f in excel_files:
        print(f"   - {f}")

    # Memuat semua record dari file-file Excel
    all_excel_records = []
    for filepath in excel_files:
        if os.path.exists(filepath):
            records = process_excel_file(filepath)
            all_excel_records.extend(records)
            
    print(f"\n📊 Total data anomali yang diproses dari Excel: {len(all_excel_records)}")

    # 2. Ambil data anomali yang aktif di Supabase
    print("\n📥 Menarik data anomali aktif di Supabase...")
    existing_records = []
    try:
        res = post_to_api('get_anomali', None)
        if res.status_code == 200:
            class FakeRes: pass
            fake_res = FakeRes()
            fake_res.data = res.json()
            res = fake_res
        else:
            print("Gagal mengambil data dari API")
            res.data = []
        existing_records = res.data or []
        print(f"   ✅ Berhasil memuat {len(existing_records)} data dari database")
    except Exception as e:
        print(f"   ⚠️  Gagal menarik data lama (mungkin tabel kosong): {e}")

    # Map menggunakan composite key (assignment_id, jenis_anomali)
    existing_map = {}
    for r in existing_records:
        aid = r.get('assignment_id')
        jenis = r.get('jenis_anomali')
        if aid and jenis:
            existing_map[(aid, jenis)] = r

    # 3. Klasifikasi Insert vs Update
    records_to_insert = []
    records_to_update = []

    for rec in all_excel_records:
        key_pair = (rec['assignment_id'], rec['jenis_anomali'])
        
        if key_pair in existing_map:
            # Update metadata dan pertahankan tindak lanjut
            existing_row = existing_map[key_pair]
            rec['id'] = existing_row['id']
            rec['tindak_lanjut'] = existing_row.get('tindak_lanjut') or ''
            rec['status_anomali'] = existing_row.get('status_anomali') or 1
            rec['nama_petugas'] = rec['nama_petugas'] or existing_row.get('nama_petugas') or ''
            rec['nama_krt'] = rec['nama_krt'] or existing_row.get('nama_krt') or ''
            
            records_to_update.append(rec)
        else:
            # Data baru
            rec['tindak_lanjut'] = ''
            rec['status_anomali'] = 1
            records_to_insert.append(rec)

    # Catatan: Kita tidak menghapus anomali lama dari sumber/file lain agar data co-exist.

    # 4. Lakukan Update
    if records_to_update:
        print(f"\n📤 Memperbarui {len(records_to_update)} data lama (menjaga tindak lanjut)...")
        success_update = 0
        for rec in records_to_update:
            try:
                post_to_api('update_anomali', rec)
                success_update += 1
            except Exception as e:
                print(f"   ❌ Gagal update ID {rec.get('id')} / Assignment {rec.get('assignment_id')}: {e}")
        print(f"   ✅ Berhasil memperbarui {success_update}/{len(records_to_update)} data")

    # 5. Lakukan Insert
    if records_to_insert:
        print(f"\n📤 Memasukkan {len(records_to_insert)} data baru...")
        success_insert = 0
        batch_size = 100
        for i in range(0, len(records_to_insert), batch_size):
            batch = records_to_insert[i:i+batch_size]
            try:
                post_to_api('upsert_anomali', batch)
                success_insert += len(batch)
                print(f"   ✅ Batch {i//batch_size + 1}: {success_insert}/{len(records_to_insert)} data baru masuk")
            except Exception as e:
                print(f"   ❌ Gagal memasukkan batch: {e}")

    print(f"\n🎉 SINKRONISASI SELESAI!")
    print(f"   - Anomali Baru Dimasukkan : {success_insert if 'success_insert' in locals() else 0}")
    print(f"   - Anomali Lama Diperbarui  : {success_update if 'success_update' in locals() else 0}")

if __name__ == '__main__':
    main()
