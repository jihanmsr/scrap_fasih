import os
import json
import sys
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
    
    # 1. Cek ukuran baris dan data di dashboard_store
    print("\n--- Analisis Ukuran Data di dashboard_store ---")
    try:
        r = supabase.table('dashboard_store').select('key, value').execute()
        total_chars = 0
        items_count = len(r.data)
        print(f"Total baris (keys): {items_count}")
        
        # Urutkan berdasarkan ukuran karakter string value
        key_sizes = []
        for x in r.data:
            key = x['key']
            val_str = json.dumps(x['value'])
            size_kb = len(val_str) / 1024.0
            total_chars += len(val_str)
            key_sizes.append((key, size_kb))
            
        key_sizes.sort(key=lambda x: x[1], reverse=True)
        
        print("\n10 Kunci Terbesar di database:")
        for k, sz in key_sizes[:10]:
            print(f"  - {k}: {sz:.2f} KB")
            
        total_mb = total_chars / (1024.0 * 1024.0)
        print(f"\nTotal estimasi ukuran data dashboard_store: {total_mb:.2f} MB")
        
    except Exception as e:
        print(f"[ERROR] Gagal menganalisis dashboard_store: {e}")
        
    # 2. Cek baris di tabel lain
    print("\n--- Analisis Jumlah Baris Tabel Lain ---")
    for tbl in ["email_logs", "anomali_data"]:
        try:
            r = supabase.table(tbl).select('count', count='exact').execute()
            count = r.count if hasattr(r, 'count') else (len(r.data) if r.data else 0)
            print(f"Tabel '{tbl}': {count} baris")
        except Exception as e:
            print(f"Tabel '{tbl}': Gagal menghitung ({e})")
            
    print("\n--- Info Keamanan Kebocoran Data ---")
    print("1. SSL/TLS: Semua lalu lintas data ke Supabase dienkripsi menggunakan HTTPS.")
    print("2. Row Level Security (RLS): Perlu dicek apakah RLS aktif di database Supabase Anda.")
    print("   Jika RLS mati, siapa pun yang memiliki Kunci Anon (yang ada di supabase_config.js) bisa membaca/menulis data.")
    print("   Namun, karena monitoring ini bersifat internal dan datanya ringkasan progres, risiko kebocoran data sensitif relatif rendah.")

if __name__ == "__main__":
    main()
