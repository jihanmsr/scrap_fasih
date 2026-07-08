import sys
import os
import json
from datetime import datetime, timedelta, timezone

# Tambahkan current path agar bisa load config
sys.path.insert(0, '.')
from merge_granulars import load_supabase_config

def update_ipas_data_total():
    try:
        supabase = load_supabase_config()
        print("[FAST SYNC] Mengambil ipas_data saat ini dari Supabase...")
        res = supabase.table("dashboard_store").select("value").eq("key", "ipas_data").single().execute()
        ipas_data = res.data.get("value") if res.data else None
        
        if not ipas_data:
            print("[ERROR] ipas_data tidak ditemukan di Supabase.")
            return

        # Load assign_data dari master granular gabungan lokal
        print("[FAST SYNC] Membaca data assign terbaru dari granular lokal...")
        with open("assign_data.js", "r", encoding="utf-8") as f:
            content = f.read()
        
        # Ekstrak data ASSIGN_DATA_UMUM dari JS content
        import re
        match = re.search(r"window\.ASSIGN_DATA_UMUM\s*=\s*(\[.*?\]);", content, re.DOTALL)
        if not match:
            print("[ERROR] Gagal mengekstrak ASSIGN_DATA_UMUM dari assign_data.js")
            return
            
        assign_umum = json.loads(match.group(1))
        
        # Hitung total target per kab
        kab_targets = {}
        total_all_umum = 0
        for item in assign_umum:
            kab_code = item.get("kode_kab")
            kab_total = item.get("total", 0)
            kab_targets[kab_code] = kab_total
            total_all_umum += kab_total
            
        print(f"[FAST SYNC] Total target se_umum dari granular: {total_all_umum:,}")
        
        # Perbarui ipas_data.se_umum_prov_total dan total tiap kabupaten
        se_umum_list = ipas_data.get("se_umum", [])
        updated_se_umum = []
        for row in se_umum_list:
            kab_code = row.get("kab_code")
            if kab_code in kab_targets:
                row["total_target"] = kab_targets[kab_code]
                # Hitung ulang sisa
                row["sisa"] = row["total_target"] - row.get("selesai", 0)
            updated_se_umum.append(row)
            
        ipas_data["se_umum"] = updated_se_umum
        ipas_data["se_umum_prov_total"] = total_all_umum
        
        # Atur timestamp ke waktu sekarang (WITA)
        wita_now = datetime.now(timezone.utc) + timedelta(hours=8)
        now_str = wita_now.strftime("%Y-%m-%d %H:%M:%S")
        ipas_data["updated_at"] = now_str
        
        print(f"[FAST SYNC] Menyimpan ipas_data baru ke Supabase dengan updated_at={now_str}...")
        supabase.table("dashboard_store").upsert({"key": "ipas_data", "value": ipas_data}, on_conflict="key").execute()
        
        # Simpan snapshot harian ipas_data juga
        today_str = wita_now.strftime("%Y-%m-%d")
        daily_key = f"ipas_data:{today_str}"
        supabase.table("dashboard_store").upsert({"key": daily_key, "value": ipas_data}, on_conflict="key").execute()
        
        print("✅ SUCCESS! ipas_data berhasil disinkronkan ke Supabase.")
        
    except Exception as e:
        print(f"[ERROR] Gagal sinkronisasi cepat ipas_data: {e}")

if __name__ == "__main__":
    update_ipas_data_total()
