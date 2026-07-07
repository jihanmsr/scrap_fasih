import os
import json
import gzip
import base64
import datetime
from supabase import create_client

KAB_MAP = {
    "7201": "BANGGAI KEPULAUAN",
    "7202": "BANGGAI",
    "7203": "MOROWALI",
    "7204": "POSO",
    "7205": "DONGGALA",
    "7206": "TOLI-TOLI",
    "7207": "BUOL",
    "7208": "PARIGI MOUTONG",
    "7209": "TOJO UNA-UNA",
    "7210": "SIGI",
    "7211": "BANGGAI LAUT",
    "7212": "MOROWALI UTARA",
    "7271": "PALU"
}

def get_wita_date_string(epoch_sec):
    if not epoch_sec or epoch_sec <= 0:
        return None
    # Convert epoch (seconds) to datetime in WITA (UTC+8)
    dt = datetime.datetime.fromtimestamp(epoch_sec, datetime.timezone.utc)
    wita = dt + datetime.timedelta(hours=8)
    return wita.strftime("%Y-%m-%d")

def main():
    env = {}
    with open(".env", "r") as f:
        for line in f:
            if "=" in line:
                k, v = line.strip().split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
                
    url = env.get("SUPABASE_URL")
    key = env.get("SUPABASE_KEY")
    supabase = create_client(url, key)
    
    print("Fetching 'granular_assignments' chunk info...")
    res = supabase.table("dashboard_store").select("value").eq("key", "granular_assignments").execute()
    if not res.data:
        print("[ERROR] Key 'granular_assignments' tidak ditemukan di Supabase.")
        return
        
    val = res.data[0]["value"]
    if not isinstance(val, dict) or not val.get("is_chunked"):
        print("[ERROR] Key 'granular_assignments' tidak di-chunk.")
        return
        
    total_chunks = val.get("total_chunks")
    print(f"Mengunduh {total_chunks} chunk dari Supabase...")
    
    chunk_keys = [f"granular_assignments__chunk_{i}" for i in range(total_chunks)]
    chunk_data = []
    
    # Download chunks sequentially or concurrently (here sequentially for safety)
    for idx, ck in enumerate(chunk_keys):
        print(f" -> Mengunduh chunk {idx + 1}/{total_chunks} ({ck})...")
        cres = supabase.table("dashboard_store").select("value").eq("key", ck).execute()
        if cres.data:
            cval = cres.data[0]["value"]
            if isinstance(cval, str):
                cval = json.loads(cval)
            comp_part = cval.get("compressed_data", "")
            chunk_data.append(comp_part)
            
    compressed_str = "".join(chunk_data)
    print(f"Total panjang string compressed: {len(compressed_str)}")
    
    # Decompress payload
    print("Decompressing payload...")
    raw_bytes = base64.b64decode(compressed_str)
    decomp = gzip.decompress(raw_bytes).decode('utf-8')
    payload = json.loads(decomp)
    
    master_targets = payload.get("targets", [])
    master_statuses = payload.get("statuses", [])
    master_regions = payload.get("regions", [])
    
    print(f"Selesai decompress. Master targets count: {len(master_targets)}")
    
    # Map targets
    daily_counts = {} # key: (date, kab_name, survey_type) -> count
    
    for item in master_targets:
        # item = [tid, code_id, name, stat_idx, pet_idx, reg_idx, epoch_mod, survey_flag, pengawas_idx]
        status = master_statuses[item[3]]
        status_upper = status.upper()
        
        # Check if submitted
        if status_upper != "OPEN" and status_upper != "DRAFT" and item[6] > 0:
            date_str = get_wita_date_string(item[6])
            survey_type = "se_umum" if item[7] == 0 else "se_ub"
            
            # Extract kabupaten name from region info
            reg_idx = item[5]
            if reg_idx >= 0 and reg_idx < len(master_regions):
                reg_code = master_regions[reg_idx][0] if len(master_regions[reg_idx]) > 0 else "-"
                kab_code = reg_code[0:4]
                kab_name = KAB_MAP.get(kab_code, "-")
            else:
                kab_name = "-"
                
            if date_str and kab_name != "-":
                key = (date_str, kab_name, survey_type)
                daily_counts[key] = daily_counts.get(key, 0) + 1
                
    # Build list structure
    daily_stats_data = []
    for (d, kab, s_type), cnt in daily_counts.items():
        daily_stats_data.append({
            "date": d,
            "kab_name": kab,
            "survey_type": s_type,
            "count": cnt
        })
        
    # Sort by date and kabupaten name
    daily_stats_data.sort(key=lambda x: (x["date"], x["kab_name"]))
    print(f"Berhasil memproses {len(daily_stats_data)} entri timeline harian.")
    print("Contoh 5 entri pertama:")
    for x in daily_stats_data[:5]:
        print(f"  {x}")
        
    # Upload to Supabase under 'daily_submission_stats'
    print("Mengunggah 'daily_submission_stats' ke Supabase...")
    supabase.table("dashboard_store").delete().eq("key", "daily_submission_stats").execute()
    supabase.table("dashboard_store").insert({
        "key": "daily_submission_stats",
        "value": daily_stats_data
    }).execute()
    print(" ✅ 'daily_submission_stats' berhasil diperbarui di Supabase!")
    
    # Save local fallback copies
    script_dir = "/Users/jihanmaisaroh/scrap_fasih"
    with open(os.path.join(script_dir, "daily_submission_stats.json"), "w", encoding="utf-8") as f:
        json.dump(daily_stats_data, f, indent=2)
    with open(os.path.join(script_dir, "daily_submission_stats.js"), "w", encoding="utf-8") as f:
        f.write(f"window.DAILY_SUBMISSION_STATS = {json.dumps(daily_stats_data, indent=2)};\n")
    print(" ✅ File lokal daily_submission_stats (.json & .js) berhasil diperbarui!")

if __name__ == "__main__":
    main()
