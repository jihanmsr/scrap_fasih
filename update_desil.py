import os
import pandas as pd
import json

def process_desil():
    possible_paths = [
        'Keluarga_Desil_1_sampai_5_Belum_Terdata.xlsx',
        'muatan/Keluarga_Desil_1_sampai_5_Belum_Terdata.xlsx',
        '/Users/jihanmaisaroh/latsar-pemadanan-dtsen/New 25 Agustus/Hasil_Pemadanan_Desil/Keluarga_Desil_1_sampai_5_Belum_Terdata.xlsx',
        'New 25 Agustus/Keluarga_Desil_1_sampai_5_Belum_Terdata.xlsx'
    ]
    
    file_path = None
    for p in possible_paths:
        if os.path.exists(p):
            file_path = p
            break
            
    if not file_path:
        print("File Excel Desil tidak ditemukan!")
        return

    print(f"Membaca {file_path}...")
    df = pd.read_excel(file_path)

    # Fill NA to safely check values
    df['desil_nasional'] = df['desil_nasional'].fillna(0).astype(int)
    df['desil_provinsi'] = df['desil_provinsi'].fillna(0).astype(int)
    df['desil_kabupaten_kota'] = df['desil_kabupaten_kota'].fillna(0).astype(int)
    
    all_kabs = [
        '[01] BANGGAI KEPULAUAN',
        '[02] BANGGAI',
        '[03] MOROWALI',
        '[04] POSO',
        '[05] DONGGALA',
        '[06] TOLI-TOLI',
        '[07] BUOL',
        '[08] PARIGI MOUTONG',
        '[09] TOJO UNA-UNA',
        '[10] SIGI',
        '[11] BANGGAI LAUT',
        '[12] MOROWALI UTARA',
        '[71] PALU'
    ]

    # Generate 39-column matrix
    matrix_data = {
        'kabs': all_kabs,
        'rows': {}
    }

    for desil in [1, 2, 3, 4, 5]:
        matrix_data['rows'][f'Desil {desil}'] = {}
        for kab in all_kabs:
            sub = df[df['kab'] == kab]
            matrix_data['rows'][f'Desil {desil}'][kab] = {
                'nasional': int((sub['desil_nasional'] == desil).sum()),
                'provinsi': int((sub['desil_provinsi'] == desil).sum()),
                'kabkot': int((sub['desil_kabupaten_kota'] == desil).sum())
            }
        matrix_data['rows'][f'Desil {desil}']['TOTAL SULTENG'] = {
            'nasional': int((df['desil_nasional'] == desil).sum()),
            'provinsi': int((df['desil_provinsi'] == desil).sum()),
            'kabkot': int((df['desil_kabupaten_kota'] == desil).sum())
        }

    matrix_data['rows']['TOTAL'] = {}
    for kab in all_kabs:
        sub = df[df['kab'] == kab]
        matrix_data['rows']['TOTAL'][kab] = {
            'nasional': int(((sub['desil_nasional'] >= 1) & (sub['desil_nasional'] <= 5)).sum()),
            'provinsi': int(((sub['desil_provinsi'] >= 1) & (sub['desil_provinsi'] <= 5)).sum()),
            'kabkot': int(((sub['desil_kabupaten_kota'] >= 1) & (sub['desil_kabupaten_kota'] <= 5)).sum())
        }
    matrix_data['rows']['TOTAL']['TOTAL SULTENG'] = {
        'nasional': int(((df['desil_nasional'] >= 1) & (df['desil_nasional'] <= 5)).sum()),
        'provinsi': int(((df['desil_provinsi'] >= 1) & (df['desil_provinsi'] <= 5)).sum()),
        'kabkot': int(((df['desil_kabupaten_kota'] >= 1) & (df['desil_kabupaten_kota'] <= 5)).sum())
    }

    def format_desil(row):
        cats = []
        if 1 <= row['desil_nasional'] <= 5:
            cats.append("Nasional")
        if 1 <= row['desil_provinsi'] <= 5:
            cats.append("Provinsi")
        if 1 <= row['desil_kabupaten_kota'] <= 5:
            cats.append("Kab/Kota")
        
        if not cats:
            return "Lainnya"
        return ", ".join(cats)

    df['kategori_desil'] = df.apply(format_desil, axis=1)
    
    cols_to_keep = [
        'kab', 'kec', 'desa', 'kode_sls', 'nama_sls', 'no_kk', 'nik_kk', 
        'nama_kepala_keluarga', 'status_keluarga', 'status_dokumen', 'Info_Penulusuran', 
        'Petugas', 'link_fasih', 'kategori_desil'
    ]
    
    df_out = df[cols_to_keep].fillna('-')
    json_data = df_out.to_dict(orient='records')
    
    # write to data_desil.js
    with open('data_desil.js', 'w', encoding='utf-8') as f:
        f.write('window.dataDesilMatrix = ' + json.dumps(matrix_data, ensure_ascii=False) + ';\n\n')
        f.write('window.dataHilangDesil = ' + json.dumps(json_data, ensure_ascii=False) + ';\n')

    print("Berhasil membuat data_desil.js (Matrix 39 Kolom & 38.283 Data Keluarga)")

if __name__ == '__main__':
    process_desil()
