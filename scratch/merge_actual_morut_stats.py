import os
import json
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client

def main():
    script_dir = "/Users/jihanmaisaroh/scrap_fasih"
    csv_path = os.path.join(script_dir, "Morowali_Utara_Progres_Harian.csv")
    json_path = os.path.join(script_dir, "daily_submission_stats.json")
    js_path = os.path.join(script_dir, "daily_submission_stats.js")
    
    if not os.path.exists(csv_path):
        print(f"[ERROR] Morut CSV not found at {csv_path}")
        return
        
    # 1. Read CSV actual stats
    df_csv = pd.read_csv(csv_path)
    csv_morut_dates = set()
    csv_entries = []
    
    for _, row in df_csv.iterrows():
        date_str = str(row["Tanggal"]).strip()
        count = int(row["Submit Harian"])
        csv_morut_dates.add(date_str)
        csv_entries.append({
            "date": date_str,
            "count": count,
            "kab_name": "MOROWALI UTARA",
            "survey_type": "se_umum"
        })
    
    # 2. Read local daily stats (reconstructed)
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            stats = json.load(f)
    else:
        stats = []
        
    print(f"Loaded {len(stats)} entries from {json_path}")
    
    # 3. Merge: Filter out Morut se_umum entries that are in the CSV date range
    merged_stats = []
    for item in stats:
        # Keep if not MOROWALI UTARA, or not se_umum
        if item.get("kab_name") != "MOROWALI UTARA" or item.get("survey_type") != "se_umum":
            merged_stats.append(item)
        else:
            # It is Morut se_umum. Keep only if date is NOT in the CSV (e.g. newer dates like July 2nd or 3rd)
            date_str = item.get("date")
            if date_str not in csv_morut_dates:
                merged_stats.append(item)
                
    # Add CSV actual entries
    merged_stats.extend(csv_entries)
    
    # Sort merged stats by date, then kab_name, then survey_type
    merged_stats.sort(key=lambda x: (x.get("date", ""), x.get("kab_name", ""), x.get("survey_type", "")))
    
    print(f"Total merged entries: {len(merged_stats)}")
    
    # 4. Save locally
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(merged_stats, f, indent=4)
    print(f"Saved merged stats to {json_path}")
    
    with open(js_path, "w", encoding="utf-8") as f:
        f.write(f"window.DAILY_SUBMISSION_STATS = {json.dumps(merged_stats, indent=4)};\n")
    print(f"Saved merged stats to {js_path}")
    
    # 5. Upload to Supabase
    load_dotenv()
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    if SUPABASE_URL and SUPABASE_KEY:
        try:
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            print("Connecting to Supabase to upload merged stats...")
            
            # Update key 'daily_submission_stats'
            supabase.table("dashboard_store").delete().eq("key", "daily_submission_stats").execute()
            supabase.table("dashboard_store").insert({"key": "daily_submission_stats", "value": merged_stats}).execute()
            print("✅ Key 'daily_submission_stats' successfully updated in Supabase!")
            
            # Update key snapshot for today
            today_str = pd.Timestamp.now().strftime("%Y-%m-%d")
            daily_key = f"daily_submission_stats:{today_str}"
            supabase.table("dashboard_store").delete().eq("key", daily_key).execute()
            supabase.table("dashboard_store").insert({"key": daily_key, "value": merged_stats}).execute()
            print(f"✅ Key snapshot '{daily_key}' successfully updated!")
        except Exception as e:
            print(f"[ERROR] Failed to upload to Supabase: {e}")
    else:
        print("[WARNING] Supabase credentials not found in env. Skipping upload.")

if __name__ == "__main__":
    main()
