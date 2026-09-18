import os
import re
import json
import time
import pandas as pd
from collections import defaultdict

def main():
    start_time = time.time()
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_js = os.path.join(base_dir, "penyisiran_keluarga_data.js")
    output_excel = os.path.join(base_dir, "Prioritas_Penyisiran_Keluarga_SE2026_18Sep.xlsx")

    print("=" * 65)
    print(" GENERATE DATA PRIORITAS PENYISIRAN KELUARGA PER SLS (9 SEPT)")
    print("=" * 65)

    # 1. Load muatan SLS
    muatan_file = os.path.join(base_dir, "muatan", "muatan_sls_72 2.xlsx")
    if not os.path.exists(muatan_file):
        muatan_file = os.path.join(base_dir, "muatan_sls_72.xlsx")

    print(f"1. Loading muatan SLS from {os.path.basename(muatan_file)}...")
    df_m = pd.read_excel(muatan_file)
    df_m['rc16'] = df_m['idsubsls_25_2'].apply(lambda x: f"{int(x):016d}" if pd.notna(x) else "")

    muatan_dict = {}
    for _, r in df_m.iterrows():
        rc = r['rc16']
        if rc:
            muatan_dict[rc] = {
                'kab': str(r.get('nmkab', '')).strip(),
                'kec': str(r.get('nmkec', '')).strip(),
                'desa': str(r.get('nmdesa', '')).strip(),
                'sls': str(r.get('nmsls', '')).strip(),
                'target_keluarga': int(r['keluarga']) if pd.notna(r.get('keluarga')) else 0
            }
    print(f"   -> {len(muatan_dict):,} SLS dimuat dari muatan")

    # 2. Load rekap realisasi keluarga yang ditemukan di Fasih
    rekap_file = os.path.join(base_dir, "Rekap SBR, UTP, Keluarga_20260918.xlsx")
    realisasi_dict = {}
    if os.path.exists(rekap_file):
        print(f"2. Loading realisasi keluarga from {os.path.basename(rekap_file)}...")
        df_r = pd.read_excel(rekap_file)
        realisasi_dict = {
            str(r['level_5_full_code']): int(r['total_keluarga'])
            for _, r in df_r.iterrows()
            if pd.notna(r.get('level_5_full_code'))
        }
        print(f"   -> {len(realisasi_dict):,} SLS realisasi keluarga dimuat")

    # 3. Load data_hilang_keluarga.js
    data_hilang_file = os.path.join(base_dir, "data_hilang_keluarga.js")
    print(f"3. Loading {os.path.basename(data_hilang_file)}...")
    with open(data_hilang_file, "r", encoding="utf-8") as f:
        text = f.read()
    raw_data = json.loads(text.split("=", 1)[1].rsplit(";", 1)[0])
    print(f"   -> {len(raw_data):,} keluarga hilang terbaca")

    # 4. Aggregasi per SLS
    sls_agg = defaultdict(lambda: {
        'kab': '', 'kec': '', 'desa': '', 'sls': '',
        'hilang_total': 0, 'pindah_ya': 0, 'pindah_tidak': 0,
        'ppl': '', 'pml': ''
    })

    def clean_bracket(val):
        if not val: return ''
        return re.sub(r'\[\d+\]\s*', '', str(val)).strip()

    def extract_code(text):
        if not text: return ''
        m = re.search(r'\[(\d+)\]', str(text))
        return m.group(1) if m else ''

    for d in raw_data:
        rc = d.get('Region_Code')
        if not rc:
            kab_c = extract_code(d.get('kab', ''))
            kec_c = extract_code(d.get('kec', ''))
            desa_c = extract_code(d.get('desa', ''))
            sls_raw = d.get('kode_sls', '')
            try:
                sls_clean = str(int(float(sls_raw))).zfill(6) if pd.notna(sls_raw) and str(sls_raw).strip() != '' else '000000'
            except:
                sls_clean = '000000'
            if kab_c and kec_c and desa_c:
                rc = f"72{kab_c}{kec_c}{desa_c}{sls_clean}"
        if not rc: continue
        s = sls_agg[rc]
        if not s['kab']:
            s['kab'] = clean_bracket(d.get('kab', ''))
            s['kec'] = clean_bracket(d.get('kec', ''))
            s['desa'] = clean_bracket(d.get('desa', ''))
            s['sls'] = str(d.get('nama_sls', '')).strip()
            s['ppl'] = d.get('ppl_master', '') or d.get('Petugas', '')
            s['pml'] = d.get('pml_master', '')
        s['hilang_total'] += 1
        if d.get('indikasi_pindah_sls') == 'Ya':
            s['pindah_ya'] += 1
        else:
            s['pindah_tidak'] += 1

    print(f"   -> {len(sls_agg):,} SLS memiliki keluarga hilang")

    # 5. Gabungkan dan hitung prioritas
    print("4. Menghitung persentase & klasifikasi prioritas penyisiran...")
    records = []
    for rc, s in sls_agg.items():
        m = muatan_dict.get(rc) or muatan_dict.get(rc[:14] + '00') or {}
        real_kel = realisasi_dict.get(rc[:14], 0)
        muat_kel = m.get('target_keluarga', 0)

        # Total beban keluarga: max antara muatan awal vs riil (ditemukan + hilang)
        total_beban = max(muat_kel, real_kel + s['hilang_total'])
        pct_hilang = round((s['hilang_total'] / total_beban * 100), 1) if total_beban > 0 else 100.0

        # Skor perhatian: kombinasi persentase hilang & volume absolut
        skor = round((pct_hilang * 0.7) + (min(s['hilang_total'], 100) * 0.3), 1)

        # Klasifikasi Prioritas
        if (pct_hilang >= 60.0 and s['hilang_total'] >= 25) or (pct_hilang >= 80.0 and s['hilang_total'] >= 15) or (s['hilang_total'] >= 100):
            kat = "PRIORITAS 1 - SISIR SEGERA"
        elif (pct_hilang >= 35.0 and s['hilang_total'] >= 10) or (s['hilang_total'] >= 30):
            kat = "PRIORITAS 2 - PERLU CEK"
        else:
            kat = "PRIORITAS 3 - WAJAR"

        kab_name = s['kab'] or m.get('kab', '')
        kec_name = s['kec'] or m.get('kec', '')
        desa_name = s['desa'] or m.get('desa', '')
        sls_name = s['sls'] or m.get('sls', '')

        records.append({
            'kabupaten': kab_name,
            'kecamatan': kec_name,
            'desa_kel': desa_name,
            'sls': sls_name,
            'id_sub_sls': rc,
            'target_muatan': total_beban,
            'realisasi_ditemukan': real_kel,
            'tidak_ditemukan': s['hilang_total'],
            'pindah_ya': s['pindah_ya'],
            'pindah_tidak': s['pindah_tidak'],
            'pct_tdk_ditemukan': pct_hilang,
            'skor_perhatian': skor,
            'kategori_sisir': kat,
            'ppl': s['ppl'] or '-',
            'pml': s['pml'] or '-'
        })

    # Sort default: skor perhatian descending
    records.sort(key=lambda x: x['skor_perhatian'], reverse=True)

    # 6. Simpan ke JS
    print(f"5. Menulis dataset ke {os.path.basename(output_js)}...")
    with open(output_js, "w", encoding="utf-8") as f:
        f.write("// Data Tabulasi Prioritas Penyisiran Keluarga per SLS - Update 18 September 2026\n")
        f.write("window.PENYISIRAN_KELUARGA_DATA = ")
        json.dump(records, f, ensure_ascii=False)
        f.write(";\n")
    print(f"   -> File {output_js} berhasil dibuat ({os.path.getsize(output_js) / 1024:.1f} KB)")

    # 7. Simpan ke Excel untuk analisis lapangan
    print(f"6. Menyimpan rekap Excel ke {os.path.basename(output_excel)}...")
    df_out = pd.DataFrame(records)
    df_out.columns = [
        'Kabupaten', 'Kecamatan', 'Desa / Kelurahan', 'Nama SLS', 'Kode SLS (16 digit)',
        'Total Beban Keluarga', 'Realisasi Ditemukan', 'Keluarga Hilang (Tdk Ditemukan)',
        'Indikasi Pindah (Ya)', 'Indikasi Pindah (Tidak)', '% Tdk Ditemukan',
        'Skor Perhatian', 'Kategori Prioritas Sisir', 'Petugas PPL', 'Petugas PML'
    ]
    with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
        df_out.to_excel(writer, sheet_name='Prioritas_Penyisiran_Keluarga', index=False)
        # Tambah sheet ringkasan per kab
        rekap_kab = df_out.groupby(['Kabupaten', 'Kategori Prioritas Sisir']).size().unstack(fill_value=0)
        rekap_kab.to_excel(writer, sheet_name='Ringkasan_Kabupaten')

    print(f"   -> File Excel {output_excel} berhasil dibuat!")
    print(f"\n[SELESAI] Dalam {time.time() - start_time:.2f} detik.")

if __name__ == "__main__":
    main()
