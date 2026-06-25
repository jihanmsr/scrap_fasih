import os
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def seed_anomali():
    print("Membaca Excel Metadata Anomali...")
    try:
        df = pd.read_excel('Metadata Anomali BPS Provinsi Sulawesi Tengah.xlsx')
        
        # Kolom excel: ['No', 'Case', 'Jenis Anomali', 'Referensi Anomali', 'Metadata', 'Kondisi Anomali', 'Script SQL Query', 'Keterangan']
        anomali_list = []
        for idx, row in df.iterrows():
            jenis = str(row.get('Jenis Anomali', ''))
            if jenis == 'nan': jenis = ''
            
            anomali_list.append({
                "jenis_anomali": jenis,
                "catatan": "",
                "tindak_lanjut": "",
                "status_anomali": 1,
                "nama_krt": ""
            })
            
        print(f"Menyiapkan {len(anomali_list)} baris data anomali untuk diunggah...")
        
        # Karena kita belum punya data wilayah spesifik dari Excel ini, kita jadikan ini sebagai template awal (contoh)
        # Atau jika data anomali per kasus belum ditarik dari FASIH, kita upload struktur dasar dulu.
        if anomali_list:
            response = supabase.table('anomali_data').insert(anomali_list).execute()
            print("Selesai! Data anomali awal berhasil dimasukkan ke database.")
            
    except Exception as e:
        print(f"Error membaca atau mengunggah data: {e}")

if __name__ == "__main__":
    seed_anomali()
