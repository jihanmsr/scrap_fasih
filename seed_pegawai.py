import os
import json
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def seed_pegawai():
    print("Membaca hasil_pegawai.json...")
    with open('hasil_pegawai.json', 'r') as f:
        data = json.load(f)
        
    # Ambil field yang diperlukan: username, password (sama dengan username), nama, kab_code (wilayahid)
    pegawai_list = []
    seen = set()
    for p in data:
        uname = p.get('username')
        if not uname: continue
        if uname in seen: continue
        seen.add(uname)
        
        pegawai_list.append({
            "username": uname,
            "password": uname,
            "nama": p.get('nama', ''),
            "kab_code": p.get('wilayahid', '').split('_')[0] if p.get('wilayahid') else ''
        })
        
    print(f"Menyiapkan {len(pegawai_list)} data pegawai unik untuk diunggah...")
    
    # Supabase membatasi insert batch maksimal 1000-2000 per request, kita pecah jadi 500
    batch_size = 500
    for i in range(0, len(pegawai_list), batch_size):
        batch = pegawai_list[i:i+batch_size]
        print(f"Mengunggah batch {i+1} sampai {i+len(batch)}...")
        try:
            supabase.table('pegawai').upsert(batch).execute()
        except Exception as e:
            print(f"Gagal mengunggah batch: {e}")
            
    print("Selesai! Data pegawai berhasil dimasukkan ke database.")

if __name__ == "__main__":
    seed_pegawai()
