"""
Script untuk langsung merekonstruksi daily_submission_stats di Supabase
dari snapshot ipas_data yang sudah ada.

Jalankan: python3 scratch/fix_daily_stats_now.py
"""
import json
import datetime
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY or "MASUKKAN" in SUPABASE_URL:
    print("[ERROR] Supabase credentials tidak ditemukan di .env")
    sys.exit(1)

from supabase import create_client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
print("[INFO] Koneksi Supabase berhasil.")

def clean_kab_name(kab):
    kab_clean = kab.replace("[", "").replace("]", "").strip()
    words = [word for word in kab_clean.split() if not (word.isdigit() or (word.startswith("72") and len(word)==4))]
    return " ".join(words).upper()

# 1. Ambil semua snapshot ipas_data dari Supabase
print("[INFO] Mengambil semua kunci snapshot dari Supabase...")
r = supabase.table('dashboard_store').select('key').execute()
keys = sorted([x['key'] for x in r.data if x['key'].startswith('ipas_data:') or x['key'] == 'ipas_data'])
print(f"   Ditemukan {len(keys)} kunci: {keys}")

date_data = {}
today_completed_data = {}
yesterday_completed_data = {}

for key in keys:
    if key == 'ipas_data':
        date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    else:
        date_str = key.split(':')[1]
    
    res = supabase.table('dashboard_store').select('value').eq('key', key).execute()
    if not res.data:
        continue
    val = res.data[0]['value']
    if isinstance(val, str):
        try: val = json.loads(val)
        except: continue

    date_data[date_str] = {"se_umum": {}, "se_ub": {}}
    for survey_type in ["se_umum", "se_ub"]:
        items = val.get(survey_type, [])
        for item in items:
            kab = clean_kab_name(item.get("kabupaten", ""))
            submitted = item.get("total_submitted", 0)
            date_data[date_str][survey_type][kab] = submitted
            
            # Dari ipas_data terkini, ambil today_completed & yesterday_completed
            if key == 'ipas_data':
                tc = item.get("today_completed", 0)
                yc = item.get("yesterday_completed", 0)
                if tc > 0:
                    today_completed_data.setdefault(survey_type, {})[kab] = tc
                if yc > 0:
                    yesterday_completed_data.setdefault(survey_type, {})[kab] = yc

sorted_dates = sorted(date_data.keys())
print(f"[INFO] Snapshot ditemukan untuk tanggal: {sorted_dates}")

local_tz = datetime.timezone(datetime.timedelta(hours=8))
today_wita = datetime.datetime.now(local_tz).strftime("%Y-%m-%d")
yesterday_wita = (datetime.datetime.now(local_tz) - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
print(f"[INFO] Hari ini (WITA): {today_wita}, Kemarin: {yesterday_wita}")

# 2. Rekonstruksi daily_stats dari diff snapshot (hanya hari berurutan)
daily_stats = []
for i, date_str in enumerate(sorted_dates):
    if i == 0:
        print(f"   [SKIP] {date_str} — hari pertama, tidak ada referensi sebelumnya")
        continue
    
    prev_date_str = sorted_dates[i - 1]
    try:
        curr_d = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        prev_d = datetime.datetime.strptime(prev_date_str, "%Y-%m-%d").date()
        gap_days = (curr_d - prev_d).days
    except:
        gap_days = 99
        
    if gap_days != 1:
        print(f"   [SKIP] Gap {gap_days} hari antara {prev_date_str} -> {date_str}, tidak digenerate")
        continue
    
    print(f"   [PROSES] Diff {prev_date_str} -> {date_str}:")
    for survey_type in ["se_umum", "se_ub"]:
        for kab, submitted in date_data[date_str][survey_type].items():
            prev_submitted = date_data[prev_date_str][survey_type].get(kab, None)
            if prev_submitted is None:
                continue
            daily_diff = max(0, submitted - prev_submitted)
            if daily_diff > 0:
                daily_stats.append({
                    "date": date_str, "count": daily_diff, "kab_name": kab, "survey_type": survey_type
                })
                print(f"     {kab} ({survey_type}): +{daily_diff}")

# 3. Override hari ini dan kemarin dari today_completed/yesterday_completed (lebih akurat)
print(f"\n[INFO] Override dari API today_completed/yesterday_completed:")
for survey_type in ["se_umum", "se_ub"]:
    tc_map = today_completed_data.get(survey_type, {})
    yc_map = yesterday_completed_data.get(survey_type, {})
    
    for kab, count in tc_map.items():
        if count > 0:
            daily_stats = [x for x in daily_stats if not (x["date"] == today_wita and x["kab_name"] == kab and x["survey_type"] == survey_type)]
            daily_stats.append({"date": today_wita, "count": count, "kab_name": kab, "survey_type": survey_type})
            print(f"   today ({today_wita}) {kab} ({survey_type}): {count}")
    
    for kab, count in yc_map.items():
        if count > 0:
            daily_stats = [x for x in daily_stats if not (x["date"] == yesterday_wita and x["kab_name"] == kab and x["survey_type"] == survey_type)]
            daily_stats.append({"date": yesterday_wita, "count": count, "kab_name": kab, "survey_type": survey_type})
            print(f"   yesterday ({yesterday_wita}) {kab} ({survey_type}): {count}")

print(f"\n[INFO] Total {len(daily_stats)} entri daily_stats yang akan di-upload:")
by_date = {}
for r in daily_stats:
    by_date.setdefault(r["date"], 0)
    by_date[r["date"]] += r["count"]
for d in sorted(by_date.keys()):
    print(f"   {d}: {by_date[d]:,} total submit")

# 4. Upload ke Supabase
print("\n[INFO] Mengunggah ke Supabase...")
supabase.table("dashboard_store").delete().eq("key", "daily_submission_stats").execute()
supabase.table("dashboard_store").insert({"key": "daily_submission_stats", "value": daily_stats}).execute()
print("OK Key 'daily_submission_stats' berhasil diperbarui di Supabase!")

today_str = datetime.datetime.now().strftime("%Y-%m-%d")
daily_key = f"daily_submission_stats:{today_str}"
supabase.table("dashboard_store").delete().eq("key", daily_key).execute()
supabase.table("dashboard_store").insert({"key": daily_key, "value": daily_stats}).execute()
print(f"OK Snapshot '{daily_key}' berhasil diperbarui!")
