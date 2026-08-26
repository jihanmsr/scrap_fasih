import pandas as pd
import json

def process_desil():
    file_path = 'New 25 Agustus/Keluarga_Desil_1_sampai_5_Belum_Terdata.xlsx'
    df = pd.read_excel(file_path)

    # We need to extract the relevant columns and replace the specific decile numbers
    # with just the category (Nasional, Provinsi, Kab/Kota).
    
    # Fill NA to safely check values
    df['desil_nasional'] = df['desil_nasional'].fillna(0).astype(int)
    df['desil_provinsi'] = df['desil_provinsi'].fillna(0).astype(int)
    df['desil_kabupaten_kota'] = df['desil_kabupaten_kota'].fillna(0).astype(int)
    
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
    
    # Select columns to output
    # Columns in excel: kab, kec, desa, kode_sls, nama_sls, no_kk, nik_kk, nama_kepala_keluarga, jml_art, status_keluarga, status_dokumen, moda, Info_Penulusuran, Petugas, link_fasih
    cols_to_keep = [
        'kab', 'kec', 'desa', 'kode_sls', 'nama_sls', 'no_kk', 'nik_kk', 
        'nama_kepala_keluarga', 'status_keluarga', 'status_dokumen', 'Info_Penulusuran', 
        'Petugas', 'link_fasih', 'kategori_desil'
    ]
    
    df_out = df[cols_to_keep].fillna('-')
    
    # Rename for consistency if needed, but we can just use these
    
    json_data = df_out.to_dict(orient='records')
    
    # write to data_desil.js
    with open('data_desil.js', 'w', encoding='utf-8') as f:
        f.write('window.dataHilangDesil = ')
        json.dump(json_data, f, ensure_ascii=False)
        f.write(';\n')

    print("Berhasil membuat data_desil.js")

if __name__ == '__main__':
    process_desil()
