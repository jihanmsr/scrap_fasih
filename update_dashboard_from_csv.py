import os
import csv
import json
import datetime
import re

KAB_MAPPING = {
    "7201": "[01] BANGGAI KEPULAUAN",
    "7202": "[02] BANGGAI",
    "7203": "[03] MOROWALI",
    "7204": "[04] POSO",
    "7205": "[05] DONGGALA",
    "7206": "[06] TOLI-TOLI",
    "7207": "[07] BUOL",
    "7208": "[08] PARIGI MOUTONG",
    "7209": "[09] TOJO UNA-UNA",
    "7210": "[10] SIGI",
    "7211": "[11] BANGGAI LAUT",
    "7212": "[12] MOROWALI UTARA",
    "7271": "[71] PALU"
}

def load_env():
    env = {}
    if os.path.exists(".env"):
        with open(".env", "r", encoding="utf-8") as f:
            for line in f:
                if "=" in line and not line.strip().startswith("#"):
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip()
    return env

def read_csv_data(filepath):
    # Detect delimiter using utf-8-sig to automatically strip BOM
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        first_line = f.readline()
        delimiter = ';' if ';' in first_line else ','
        
    records = {}
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        for row in reader:
            # Clean keys to remove any BOM or spaces
            clean_row = {}
            for k, v in row.items():
                if k:
                    clean_key = k.strip()
                    val = v.strip() if v else ''
                    # Convert digit values to integer
                    clean_row[clean_key] = int(val) if val.isdigit() else 0
            
            wilayah = clean_row.get('Wilayah') or clean_row.get('wilayah')
            if wilayah is None:
                continue
            records[str(wilayah).strip()] = clean_row
    return records

def load_local_ipas_data():
    filepath = "ipas_data.js"
    if not os.path.exists(filepath):
        print(f"[WARNING] {filepath} not found locally.")
        return None
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        pattern = re.compile(r'window\.IPAS_DATA\s*=\s*(\{.*?\});', re.DOTALL)
        match = pattern.search(content)
        if match:
            return json.loads(match.group(1))
        else:
            print("[WARNING] window.IPAS_DATA not found in ipas_data.js")
            return None
    except Exception as e:
        print(f"[ERROR] Failed to load local ipas_data.js: {e}")
        return None

def scale_kecamatan_list(kecamatan_list, new_kab_values):
    fields_to_scale = [
        "total_prelist", "total_draft", "total_open", "total_submitted",
        "total_rejected", "total_approved", "total_submitted_pencacah", "total_submitted_respondent"
    ]
    
    kec_sums = {}
    for field in fields_to_scale:
        kec_sums[field] = sum(k.get(field, 0) for k in kecamatan_list)
        
    for field in fields_to_scale:
        new_total = new_kab_values[field]
        prev_sum = kec_sums[field]
        
        if prev_sum == 0:
            num_kec = len(kecamatan_list)
            if num_kec > 0:
                base = new_total // num_kec
                rem = new_total % num_kec
                for idx, k in enumerate(kecamatan_list):
                    k[field] = base + (1 if idx < rem else 0)
        else:
            scale = new_total / prev_sum
            current_sum = 0
            for k in kecamatan_list:
                val = int(round(k.get(field, 0) * scale))
                k[field] = val
                current_sum += val
                
            diff = new_total - current_sum
            if diff != 0 and len(kecamatan_list) > 0:
                max_kec = max(kecamatan_list, key=lambda x: x.get(field, 0))
                max_kec[field] = max(0, max_kec.get(field, 0) + diff)
                
    for k in kecamatan_list:
        pre = k.get("total_prelist", 0)
        sub = k.get("total_submitted", 0)
        k["persentase"] = round((sub / pre * 100), 2) if pre > 0 else 0.0

def get_bd_val(breakdown, key):
    if not breakdown:
        return 0
    key_upper = key.upper()
    for k, v in breakdown.items():
        if k.upper() == key_upper:
            return v
    return 0

def reconstruct_daily_stats_in_db(supabase):
    try:
        print("[INFO] Memulai sinkronisasi otomatis grafik harian (daily_submission_stats)...")
        r = supabase.table('dashboard_store').select('key').execute()
        keys = sorted([x['key'] for x in r.data if x['key'].startswith('ipas_data:') or x['key'] == 'ipas_data'])
        
        def clean_kab_name(kab):
            kab_clean = kab.replace("[", "").replace("]", "").strip()
            words = [word for word in kab_clean.split() if not (word.isdigit() or (word.startswith("72") and len(word)==4))]
            return " ".join(words).upper()
            
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
                    
                    if key == 'ipas_data':
                        tc = item.get("today_completed", 0)
                        yc = item.get("yesterday_completed", 0)
                        if tc > 0:
                            today_completed_data.setdefault(survey_type, {})[kab] = tc
                        if yc > 0:
                            yesterday_completed_data.setdefault(survey_type, {})[kab] = yc
                    
        sorted_dates = sorted(date_data.keys())
        daily_stats = []
        
        local_tz = datetime.timezone(datetime.timedelta(hours=8))
        today_wita = datetime.datetime.now(local_tz).strftime("%Y-%m-%d")
        yesterday_wita = (datetime.datetime.now(local_tz) - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        
        for i, date_str in enumerate(sorted_dates):
            if i == 0:
                continue
            
            prev_date_str = sorted_dates[i - 1]
            try:
                curr_d = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
                prev_d = datetime.datetime.strptime(prev_date_str, "%Y-%m-%d").date()
                gap_days = (curr_d - prev_d).days
            except:
                gap_days = 99
                
            if gap_days != 1:
                print(f"   [SKIP] Gap {gap_days} hari antara {prev_date_str} dan {date_str}, tidak digenerate (akan diisi dari API)")
                continue
            
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
        
        for survey_type in ["se_umum", "se_ub"]:
            tc_map = today_completed_data.get(survey_type, {})
            yc_map = yesterday_completed_data.get(survey_type, {})
            
            for kab, count in tc_map.items():
                if count > 0:
                    daily_stats = [x for x in daily_stats if not (x["date"] == today_wita and x["kab_name"] == kab and x["survey_type"] == survey_type)]
                    daily_stats.append({
                        "date": today_wita, "count": count, "kab_name": kab, "survey_type": survey_type
                    })
            
            for kab, count in yc_map.items():
                if count > 0:
                    daily_stats = [x for x in daily_stats if not (x["date"] == yesterday_wita and x["kab_name"] == kab and x["survey_type"] == survey_type)]
                    daily_stats.append({
                        "date": yesterday_wita, "count": count, "kab_name": kab, "survey_type": survey_type
                    })
                        
        supabase.table("dashboard_store").delete().eq("key", "daily_submission_stats").execute()
        supabase.table("dashboard_store").insert({"key": "daily_submission_stats", "value": daily_stats}).execute()
        print(f" ✅ Grafik harian (daily_submission_stats) berhasil disinkronkan! Total {len(daily_stats)} entri.")
    except Exception as re:
        print(f"[WARNING] Gagal sinkronisasi grafik harian: {re}")

def main():
    import sys
    if len(sys.argv) < 2:
        print("Usage: python3 update_dashboard_from_csv.py <path_to_progress_assignment_csv>")
        sys.exit(1)
        
    csv_path = sys.argv[1]
    if not os.path.exists(csv_path):
        print(f"[ERROR] CSV file not found at: {csv_path}")
        sys.exit(1)
        
    print(f"Membaca data dari CSV: {csv_path}...")
    csv_records = read_csv_data(csv_path)
    print(f"Berhasil membaca data untuk {len(csv_records)} wilayah.")
    
    # Inisialisasi Supabase
    env = load_env()
    supabase_url = env.get("SUPABASE_URL")
    supabase_key = env.get("SUPABASE_KEY")
    
    supabase = None
    if supabase_url and supabase_key:
        try:
            from supabase import create_client
            supabase = create_client(supabase_url, supabase_key)
            print("[INFO] Berhasil terhubung ke Supabase.")
        except Exception as e:
            print(f"[ERROR] Gagal inisialisasi Supabase: {e}")
            
    # Load current ipas_data
    current_ipas = None
    if supabase:
        try:
            print("Mengambil ipas_data saat ini dari Supabase...")
            res = supabase.table("dashboard_store").select("value").eq("key", "ipas_data").execute()
            if res.data:
                current_ipas = res.data[0]['value']
                if isinstance(current_ipas, str):
                    current_ipas = json.loads(current_ipas)
                print(" ✅ ipas_data berhasil diambil dari Supabase.")
        except Exception as e:
            print(f"[WARNING] Gagal mengambil ipas_data dari Supabase: {e}")
            
    if not current_ipas:
        print("Mencoba mengambil ipas_data dari file lokal ipas_data.js...")
        current_ipas = load_local_ipas_data()
        
    if not current_ipas:
        print("[ERROR] Gagal memuat data IPAS lama. Proses dihentikan.")
        sys.exit(1)
        
    # Date Calculations (WITA)
    local_tz = datetime.timezone(datetime.timedelta(hours=8))
    now = datetime.datetime.now(local_tz)
    now_iso = now.isoformat()
    now_date_str = now.strftime("%Y-%m-%d")
    
    prev_updated_at = current_ipas.get("updated_at", "")
    if prev_updated_at:
        prev_date_str = prev_updated_at[:10]
    else:
        prev_date_str = now_date_str
        
    try:
        prev_date = datetime.datetime.strptime(prev_date_str, "%Y-%m-%d").date()
    except Exception:
        prev_date = now.date()
        
    delta_days = (now.date() - prev_date).days
    print(f"[INFO] Tanggal saat ini (WITA): {now_date_str}. Tanggal update terakhir: {prev_date_str}. Selisih: {delta_days} hari.")
    
    # Process se_umum
    new_se_umum = []
    old_se_umum = current_ipas.get("se_umum", [])
    
    for prev_kab in old_se_umum:
        kab_name = prev_kab.get("kabupaten")
        # Find wilayah code
        wilayah_code = None
        for code, name in KAB_MAPPING.items():
            if name == kab_name:
                wilayah_code = code
                break
                
        if not wilayah_code or wilayah_code not in csv_records:
            # Tetap gunakan data lama jika tidak ada di CSV
            print(f"[WARNING] Kabupaten {kab_name} tidak ditemukan di CSV. Menggunakan data lama.")
            new_se_umum.append(prev_kab)
            continue
            
        row = csv_records[wilayah_code]
        
        # Extract counts
        draft = row.get("DRAFT", 0)
        open_val = row.get("OPEN", 0)
        submitted_pencacah = row.get("SUBMITTED BY Pencacah", 0) + row.get("EDITED BY Admin Kabupaten", 0) + row.get("EDITED BY Pengawas", 0) + row.get("COMPLETED BY Admin Kabupaten", 0)
        submitted_respondent = row.get("SUBMITTED RESPONDENT", 0)
        approved = row.get("APPROVED BY Pengawas", 0)
        rejected = row.get("REJECTED BY Pengawas", 0) + row.get("REVOKED BY Pengawas", 0) + row.get("REJECTED BY Admin Kabupaten", 0)
        
        total_submitted = submitted_pencacah + submitted_respondent + approved + rejected
        total_prelist = draft + open_val + total_submitted
        persentase = round((total_submitted / total_prelist * 100), 2) if total_prelist > 0 else 0.0
        
        new_kab_values = {
            "total_prelist": total_prelist,
            "total_draft": draft,
            "total_open": open_val,
            "total_submitted": total_submitted,
            "total_rejected": rejected,
            "total_approved": approved,
            "total_submitted_pencacah": submitted_pencacah,
            "total_submitted_respondent": submitted_respondent
        }
        
        kab_obj = {
            "kabupaten": kab_name,
            "total_prelist": total_prelist,
            "total_draft": draft,
            "total_open": open_val,
            "total_submitted": total_submitted,
            "total_rejected": rejected,
            "total_approved": approved,
            "total_submitted_pencacah": submitted_pencacah,
            "total_submitted_respondent": submitted_respondent,
            "persentase": persentase,
            "new_usaha_overall": prev_kab.get("new_usaha_overall", 0),
            "new_rumah_overall": prev_kab.get("new_rumah_overall", 0),
            "new_businesses": prev_kab.get("new_businesses", []),
            "kecamatan_list": prev_kab.get("kecamatan_list", [])
        }
        
        # Scale kecamatan_list
        if kab_obj["kecamatan_list"]:
            scale_kecamatan_list(kab_obj["kecamatan_list"], new_kab_values)
            
        # Daily Stats Update
        if delta_days == 0:
            # Same day
            kab_obj["yesterday_completed"] = prev_kab.get("yesterday_completed", 0)
            kab_obj["yesterday_completed_breakdown"] = prev_kab.get("yesterday_completed_breakdown", {})
            kab_obj["two_days_ago_completed"] = prev_kab.get("two_days_ago_completed", 0)
            kab_obj["two_days_ago_completed_breakdown"] = prev_kab.get("two_days_ago_completed_breakdown", {})
            kab_obj["two_days_ago_is_estimate"] = prev_kab.get("two_days_ago_is_estimate", False)
            
            b_submitted = prev_kab.get("total_submitted", 0) - prev_kab.get("today_completed", 0)
            b_approved = prev_kab.get("total_approved", 0) - get_bd_val(prev_kab.get("today_completed_breakdown"), "APPROVED BY PENGAWAS")
            b_rejected = prev_kab.get("total_rejected", 0) - get_bd_val(prev_kab.get("today_completed_breakdown"), "REJECTED BY PENGAWAS")
            b_pencacah = prev_kab.get("total_submitted_pencacah", 0) - get_bd_val(prev_kab.get("today_completed_breakdown"), "SUBMITTED BY PENCACAH")
            b_respondent = prev_kab.get("total_submitted_respondent", 0) - get_bd_val(prev_kab.get("today_completed_breakdown"), "SUBMITTED RESPONDENT")
            
            kab_obj["new_usaha_today"] = prev_kab.get("new_usaha_today", 0)
            kab_obj["new_rumah_today"] = prev_kab.get("new_rumah_today", 0)
            kab_obj["new_usaha_yesterday"] = prev_kab.get("new_usaha_yesterday", 0)
            kab_obj["new_rumah_yesterday"] = prev_kab.get("new_rumah_yesterday", 0)
        else:
            # Shift dates
            if delta_days == 1:
                kab_obj["two_days_ago_completed"] = prev_kab.get("yesterday_completed", 0)
                kab_obj["two_days_ago_completed_breakdown"] = prev_kab.get("yesterday_completed_breakdown", {})
                kab_obj["yesterday_completed"] = prev_kab.get("today_completed", 0)
                kab_obj["yesterday_completed_breakdown"] = prev_kab.get("today_completed_breakdown", {})
                
                kab_obj["new_usaha_yesterday"] = prev_kab.get("new_usaha_today", 0)
                kab_obj["new_rumah_yesterday"] = prev_kab.get("new_rumah_today", 0)
            elif delta_days == 2:
                kab_obj["two_days_ago_completed"] = prev_kab.get("today_completed", 0)
                kab_obj["two_days_ago_completed_breakdown"] = prev_kab.get("today_completed_breakdown", {})
                kab_obj["yesterday_completed"] = 0
                kab_obj["yesterday_completed_breakdown"] = {}
                
                kab_obj["new_usaha_yesterday"] = 0
                kab_obj["new_rumah_yesterday"] = 0
            else:
                kab_obj["two_days_ago_completed"] = 0
                kab_obj["two_days_ago_completed_breakdown"] = {}
                kab_obj["yesterday_completed"] = 0
                kab_obj["yesterday_completed_breakdown"] = {}
                
                kab_obj["new_usaha_yesterday"] = 0
                kab_obj["new_rumah_yesterday"] = 0
                
            kab_obj["two_days_ago_is_estimate"] = False
            
            b_submitted = prev_kab.get("total_submitted", 0)
            b_approved = prev_kab.get("total_approved", 0)
            b_rejected = prev_kab.get("total_rejected", 0)
            b_pencacah = prev_kab.get("total_submitted_pencacah", 0)
            b_respondent = prev_kab.get("total_submitted_respondent", 0)
            
            kab_obj["new_usaha_today"] = 0
            kab_obj["new_rumah_today"] = 0
            
        today_comp = max(0, total_submitted - b_submitted)
        today_bd = {}
        
        inc_approved = max(0, approved - b_approved)
        if inc_approved > 0:
            today_bd["APPROVED BY PENGAWAS"] = inc_approved
            
        inc_rejected = max(0, rejected - b_rejected)
        if inc_rejected > 0:
            today_bd["REJECTED BY PENGAWAS"] = inc_rejected
            
        inc_pencacah = max(0, submitted_pencacah - b_pencacah)
        if inc_pencacah > 0:
            today_bd["SUBMITTED BY PENCACAH"] = inc_pencacah
            
        inc_respondent = max(0, submitted_respondent - b_respondent)
        if inc_respondent > 0:
            today_bd["SUBMITTED RESPONDENT"] = inc_respondent
            
        kab_obj["today_completed"] = today_comp
        kab_obj["today_completed_breakdown"] = today_bd
        
        new_se_umum.append(kab_obj)
        print(f" -> {kab_name}: prelist={total_prelist}, submitted={total_submitted}, today_completed={today_comp}")
        
    # Calculate Prov totals
    prov_prelist = sum(k.get("total_prelist", 0) for k in new_se_umum)
    prov_new_total = sum(k.get("new_usaha_overall", 0) for k in new_se_umum)
    prov_new_rumah_total = sum(k.get("new_rumah_overall", 0) for k in new_se_umum)
    
    final_js_obj = {
        "updated_at": now_iso,
        "se_umum": new_se_umum,
        "se_ub": current_ipas.get("se_ub", []),
        "se_umum_sls_status": current_ipas.get("se_umum_sls_status", {}),
        "se_ub_sls_status": current_ipas.get("se_ub_sls_status", {}),
        "se_umum_prov_total": prov_prelist,
        "se_ub_prov_total": current_ipas.get("se_ub_prov_total", 0),
        "se_umum_prov_new_total": prov_new_total,
        "se_ub_prov_new_total": current_ipas.get("se_ub_prov_new_total", 0),
        "se_umum_prov_new_rumah_total": prov_new_rumah_total,
        "se_ub_prov_new_rumah_total": current_ipas.get("se_ub_prov_new_rumah_total", 0)
    }
    
    # Save locally to ipas_data.js
    print("Menyimpan ke file lokal ipas_data.js...")
    with open("ipas_data.js", "w", encoding="utf-8") as f:
        f.write(f"window.IPAS_DATA = {json.dumps(final_js_obj, ensure_ascii=False, indent=2)};\n")
    print(" ✅ File ipas_data.js berhasil disimpan.")
    
    # Upload to Supabase
    if supabase:
        try:
            print("Mengunggah data IPAS ke Supabase...")
            supabase.table("dashboard_store").delete().eq("key", "ipas_data").execute()
            supabase.table("dashboard_store").insert({"key": "ipas_data", "value": final_js_obj}).execute()
            print(" ✅ Berhasil mengunggah data IPAS ke Supabase.")
            
            daily_key = f"ipas_data:{now_date_str}"
            supabase.table("dashboard_store").delete().eq("key", daily_key).execute()
            supabase.table("dashboard_store").insert({"key": daily_key, "value": final_js_obj}).execute()
            print(f" ✅ Berhasil mengunggah data IPAS harian ({daily_key}) ke Supabase.")
            
            # Reconstruct daily submission timeline stats
            reconstruct_daily_stats_in_db(supabase)
        except Exception as e:
            print(f"[ERROR] Gagal mengunggah data ke Supabase: {e}")
            
    print("\n🎉 PROSES UPDATE SELESAI SECARA INSTAN!")

if __name__ == "__main__":
    main()
