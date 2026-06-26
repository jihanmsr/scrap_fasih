"""
Seed data anomali dari biaya_produksi_dominan.xlsx ke Supabase.
- Hapus data lama, import 1000 baris baru
- Kolom utama: level_6_full_code, assignment_id, total_pengeluaran, biaya_produksi
- Jenis anomali: "Biaya Produksi Dominan" (biaya_produksi >= 50% total_pengeluaran)
"""
import os
import openpyxl
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

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
    if val is None:
        return '-'
    try:
        return f"Rp {int(val):,}".replace(',', '.')
    except:
        return str(val)

def main():
    print("📖 Membaca biaya_produksi_dominan.xlsx...")
    wb = openpyxl.load_workbook('biaya_produksi_dominan.xlsx')
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    headers = rows[0]
    data_rows = rows[1:]
    print(f"   ✅ Ditemukan {len(data_rows)} baris data")

    # Hapus data lama
    print("\n🗑️  Menghapus data anomali lama...")
    try:
        result = supabase.table('anomali_data').delete().neq('id', 0).execute()
        print("   ✅ Data lama berhasil dihapus")
    except Exception as e:
        print(f"   ⚠️  Gagal hapus (mungkin tabel kosong): {e}")

    # Siapkan data baru
    print("\n🔄 Menyiapkan 1000 baris data baru...")
    records = []
    for row in data_rows:
        geotag_acc = row[0]
        lat = row[1]
        lon = row[2]
        level6 = str(row[3] or '')
        assignment_id = str(row[4] or '')
        produk_sendiri = row[6]
        total_pengeluaran = row[7]
        biaya_produksi = row[8]

        # Parse wilayah dari level_6_full_code (16 digit: 4+2+3+3+4 = kab,kec,desa,sls)
        kab_code = level6[:4] if len(level6) >= 4 else ''
        kec_code = level6[:6] if len(level6) >= 6 else ''
        desa_code = level6[:9] if len(level6) >= 9 else ''
        sls_code = level6

        kab_name = KAB_NAMES.get(kab_code, kab_code)

        # Hitung persen
        pct = 0
        if total_pengeluaran and total_pengeluaran > 0 and biaya_produksi:
            pct = round(biaya_produksi / total_pengeluaran * 100, 1)

        # Tentukan jenis anomali
        if pct > 100:
            jenis = 'Biaya Produksi Melebihi Total Pengeluaran'
        elif pct == 100:
            jenis = 'Biaya Produksi Sama dengan Total Pengeluaran'
        elif pct >= 80:
            jenis = 'Biaya Produksi Sangat Dominan (≥80%)'
        else:
            jenis = 'Biaya Produksi Dominan (≥50%)'

        catatan = (
            f"Biaya produksi: {fmt_rp(biaya_produksi)} | "
            f"Total pengeluaran: {fmt_rp(total_pengeluaran)} | "
            f"Porsi biaya produksi: {pct}%"
        )
        if lat and lon:
            catatan += f" | Koordinat: ({lat:.4f}, {lon:.4f})"

        records.append({
            'kab_code': kab_name,
            'kec_code': kec_code,
            'desa_code': desa_code,
            'sls_code': sls_code,
            'nama_petugas': '',
            'jenis_anomali': jenis,
            'nama_krt': '',
            'catatan': catatan,
            'tindak_lanjut': '',
            'status_anomali': 1,
            'assignment_id': assignment_id,
            'total_pengeluaran': int(total_pengeluaran) if total_pengeluaran else None,
            'biaya_produksi': int(biaya_produksi) if biaya_produksi else None,
            'pct_biaya': float(pct),
        })

    print(f"   ✅ {len(records)} record siap diupload")

    # Cek apakah kolom assignment_id, total_pengeluaran, biaya_produksi, pct_biaya sudah ada
    # Kalau belum, perlu ALTER TABLE dulu (kita coba insert, tangkap error)
    print("\n📤 Mengupload data ke Supabase (batch 100)...")
    batch_size = 100
    success = 0
    for i in range(0, len(records), batch_size):
        batch = records[i:i+batch_size]
        try:
            supabase.table('anomali_data').insert(batch).execute()
            success += len(batch)
            print(f"   ✅ Batch {i//batch_size + 1}: {success}/{len(records)} baris terkirim")
        except Exception as e:
            err_str = str(e)
            if 'column' in err_str.lower() and ('assignment_id' in err_str or 'biaya' in err_str or 'pct' in err_str):
                # Kolom belum ada, coba tanpa kolom ekstra
                print(f"   ⚠️  Kolom baru belum ada di DB, upload tanpa kolom ekstra...")
                batch_lite = [{k: v for k, v in r.items() if k in ('kab_code','kec_code','desa_code','sls_code','nama_petugas','jenis_anomali','nama_krt','catatan','tindak_lanjut','status_anomali')} for r in batch]
                try:
                    supabase.table('anomali_data').insert(batch_lite).execute()
                    success += len(batch_lite)
                    print(f"   ✅ Batch lite {i//batch_size + 1}: {success}/{len(records)} baris terkirim")
                except Exception as e2:
                    print(f"   ❌ Gagal juga: {e2}")
            else:
                print(f"   ❌ Gagal: {e}")

    print(f"\n🎉 SELESAI! Total {success} dari {len(records)} baris berhasil diupload.")

    # Summary distribusi
    from collections import Counter
    kab_dist = Counter(r['kab_code'] for r in records)
    print("\nDistribusi per Kab/Kota:")
    for kab, cnt in kab_dist.most_common():
        print(f"  {kab}: {cnt}")

if __name__ == '__main__':
    main()
