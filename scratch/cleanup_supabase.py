import os
from dotenv import load_dotenv
from supabase import create_client
from datetime import datetime, timedelta

def main():
    load_dotenv()
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("[ERROR] Kredensial Supabase tidak ditemukan.")
        return
        
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("Menghubungkan ke Supabase...")
    
    # 1. Ambil seluruh daftar kunci di dashboard_store
    print("Mengambil daftar kunci dari database...")
    try:
        r = supabase.table('dashboard_store').select('key').execute()
        all_keys = [x['key'] for x in r.data]
        print(f"Total kunci saat ini: {len(all_keys)}")
    except Exception as e:
        print(f"[ERROR] Gagal mengambil daftar kunci: {e}")
        return
        
    # Batas umur simpan untuk snapshot
    today = datetime.now()
    keep_assign_days = 3  # Simpan assign_data harian selama 3 hari terakhir
    keep_ipas_days = 7    # Simpan ipas_data harian selama 7 hari terakhir (untuk data H-2 dashboard)
    
    keys_to_delete = []
    
    for key in all_keys:
        # A. Hapus snapshot granular assignments lama (Sangat besar & tidak digunakan web)
        if key.startswith("granular_assignments:") or key.startswith("granular_assignments_se_umum_"):
            keys_to_delete.append(key)
            continue
            
        # B. Hapus snapshot assign_data harian yang sudah lebih dari 3 hari
        if key.startswith("assign_data:"):
            try:
                date_str = key.split(":")[1]
                key_date = datetime.strptime(date_str, "%Y-%m-%d")
                if (today - key_date).days > keep_assign_days:
                    keys_to_delete.append(key)
            except Exception:
                pass
            continue
            
        # C. Hapus snapshot ipas_data harian yang sudah lebih dari 7 hari
        if key.startswith("ipas_data:"):
            try:
                date_str = key.split(":")[1]
                key_date = datetime.strptime(date_str, "%Y-%m-%d")
                if (today - key_date).days > keep_ipas_days:
                    keys_to_delete.append(key)
            except Exception:
                pass
            continue
            
        # D. Hapus data fast lama jika ada
        if key.startswith("assign_data_fast:"):
            try:
                date_str = key.split(":")[1]
                key_date = datetime.strptime(date_str, "%Y-%m-%d")
                if (today - key_date).days > keep_assign_days:
                    keys_to_delete.append(key)
            except Exception:
                pass
            continue
            
        # E. Hapus snapshot daily submission harian lama jika ada
        if key.startswith("daily_submission_stats:"):
            try:
                date_str = key.split(":")[1]
                key_date = datetime.strptime(date_str, "%Y-%m-%d")
                if (today - key_date).days > keep_ipas_days:
                    keys_to_delete.append(key)
            except Exception:
                pass
            continue

    total_to_delete = len(keys_to_delete)
    if total_to_delete == 0:
        print("\n🎉 Database sudah bersih! Tidak ada kunci lama yang perlu dihapus.")
        return
        
    print(f"\nDitemukan {total_to_delete} kunci usang yang akan dihapus untuk menghemat ruang:")
    for k in sorted(keys_to_delete)[:15]:
        print(f"  - {k}")
    if total_to_delete > 15:
        print(f"  ... dan {total_to_delete - 15} kunci lainnya.")
        
    # Lakukan penghapusan secara aman satu per satu
    print("\nMemulai penghapusan di database...")
    deleted_count = 0
    for k in keys_to_delete:
        try:
            supabase.table("dashboard_store").delete().eq("key", k).execute()
            deleted_count += 1
        except Exception as ex:
            print(f"  [WARNING] Gagal menghapus kunci '{k}': {ex}")
            
    print(f"\n🎉 BERHASIL! {deleted_count} kunci usang telah dibersihkan dari Supabase.")
    print("Database Supabase Anda sekarang jauh lebih ringan, cepat, dan hemat ruang!")

if __name__ == "__main__":
    main()
