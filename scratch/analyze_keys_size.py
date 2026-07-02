import os
import json
from dotenv import load_dotenv
from supabase import create_client

def main():
    load_dotenv()
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("[ERROR] Kredensial Supabase tidak ditemukan.")
        return
        
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("Menghubungkan ke Supabase...")
    
    # 1. Ambil list kunci
    print("Mengambil daftar kunci dari dashboard_store...")
    try:
        r = supabase.table('dashboard_store').select('key').execute()
        keys = [x['key'] for x in r.data]
        print(f"Total kunci di DB: {len(keys)}")
        
        # 2. Ambil ukuran value secara individual (batch 1)
        print("Mengukur ukuran masing-masing kunci secara individual...")
        key_sizes = []
        
        for idx, k in enumerate(keys):
            try:
                res = supabase.table('dashboard_store').select('key, value').eq('key', k).execute()
                if res.data:
                    val_str = json.dumps(res.data[0]['value'])
                    size_kb = len(val_str) / 1024.0
                    key_sizes.append((k, size_kb))
            except Exception as ex:
                print(f"  [WARNING] Gagal mengambil ukuran kunci '{k}': {ex}")
                
        # Urutkan kunci terbesar
        key_sizes.sort(key=lambda x: x[1], reverse=True)
        
        total_size_mb = sum(x[1] for x in key_sizes) / 1024.0
        print(f"\n✅ Total Ukuran Data dashboard_store: {total_size_mb:.2f} MB")
        
        print("\n15 Kunci Terbesar di database Anda:")
        for k, sz in key_sizes[:15]:
            print(f"  - {k}: {sz:.2f} KB")
            
    except Exception as e:
        print(f"[ERROR] Gagal: {e}")

if __name__ == "__main__":
    main()
