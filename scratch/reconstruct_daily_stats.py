import os
import json
from dotenv import load_dotenv
from supabase import create_client
from datetime import datetime, timedelta

def clean_kab_name(kab):
    # Remove prefix like "[01] " or numeric ids
    kab_clean = kab.replace("[", "").replace("]", "").strip()
    words = [word for word in kab_clean.split() if not (word.isdigit() or (word.startswith("72") and len(word)==4))]
    return " ".join(words).upper()

def main():
    load_dotenv()
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("[ERROR] Supabase credentials not found in env.")
        return
        
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("Menghubungkan ke Supabase...")
    
    # 1. Ambil semua kunci ipas_data:<date>
    r = supabase.table('dashboard_store').select('key').execute()
    keys = sorted([x['key'] for x in r.data if x['key'].startswith('ipas_data:') or x['key'] == 'ipas_data'])
    print(f"Ditemukan {len(keys)} kunci ipas_data di DB.")
    
    # Map date_str -> {survey_type -> {kab_name -> total_submitted}}
    date_data = {}
    
    for key in keys:
        # Tentukan tanggal
        if key == 'ipas_data':
            # Anggap tanggal hari ini
            date_str = datetime.now().strftime("%Y-%m-%d")
        else:
            date_str = key.split(':')[1]
            
        print(f"Fetching {key}...")
        res = supabase.table('dashboard_store').select('value').eq('key', key).execute()
        if not res.data:
            continue
            
        val = res.data[0]['value']
        # Pastikan dictionary
        if isinstance(val, str):
            try:
                val = json.loads(val)
            except:
                continue
                
        date_data[date_str] = {"se_umum": {}, "se_ub": {}}
        
        for survey_type in ["se_umum", "se_ub"]:
            items = val.get(survey_type, [])
            for item in items:
                kab = clean_kab_name(item.get("kabupaten", ""))
                submitted = item.get("total_submitted", 0)
                date_data[date_str][survey_type][kab] = submitted
                
    # Urutkan tanggal
    sorted_dates = sorted(date_data.keys())
    print("\nTanggal terkumpul:", sorted_dates)
    
    # 2. Rekonstruksi submit harian berdasarkan perbedaan kumulatif
    daily_stats = []
    
    for i, date_str in enumerate(sorted_dates):
        if i == 0:
            # Untuk tanggal pertama, submit harian = total selesai pada hari itu
            for survey_type in ["se_umum", "se_ub"]:
                for kab, submitted in date_data[date_str][survey_type].items():
                    daily_stats.append({
                        "date": date_str,
                        "count": submitted,
                        "kab_name": kab,
                        "survey_type": survey_type
                    })
        else:
            prev_date_str = sorted_dates[i - 1]
            # Hitung selisih hari ini dengan hari sebelumnya
            for survey_type in ["se_umum", "se_ub"]:
                for kab, submitted in date_data[date_str][survey_type].items():
                    prev_submitted = date_data[prev_date_str][survey_type].get(kab, 0)
                    daily_diff = max(0, submitted - prev_submitted)
                    
                    # Jika ada gap hari (misal selisih 2 hari karena weekend tidak disinkronisasi),
                    # kita bisa bagi rata ke hari-hari tersebut atau tulis di tanggal ini.
                    # Demi kesederhanaan dan akurasi grafik, kita tulis di tanggal ini saja.
                    daily_stats.append({
                        "date": date_str,
                        "count": daily_diff,
                        "kab_name": kab,
                        "survey_type": survey_type
                    })
                    
    print(f"\nHasil rekonstruksi harian: {len(daily_stats)} baris entri data.")
    
    # 3. Upload hasil daily_submission_stats ke Supabase
    supabase.table("dashboard_store").delete().eq("key", "daily_submission_stats").execute()
    supabase.table("dashboard_store").insert({"key": "daily_submission_stats", "value": daily_stats}).execute()
    print("✅ Kunci 'daily_submission_stats' berhasil di-reconstruct dan diperbarui di Supabase!")
    
    # Tulis juga untuk snapshot hari ini
    today_str = datetime.now().strftime("%Y-%m-%d")
    daily_key = f"daily_submission_stats:{today_str}"
    supabase.table("dashboard_store").delete().eq("key", daily_key).execute()
    supabase.table("dashboard_store").insert({"key": daily_key, "value": daily_stats}).execute()
    print(f"✅ Kunci snapshot '{daily_key}' berhasil diperbarui!")

if __name__ == "__main__":
    main()
