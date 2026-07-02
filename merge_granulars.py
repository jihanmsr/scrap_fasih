import os
import json
import glob
import base64
import gzip
import time
from datetime import datetime, timezone, timedelta
from supabase import create_client

def load_supabase_config():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "supabase_config.js")
    with open(config_path, "r") as f:
        content = f.read()
    import re
    url_match = re.search(r'SUPABASE_URL\s*=\s*["\']([^"\']+)["\']', content)
    key_match = re.search(r'SUPABASE_KEY\s*=\s*["\']([^"\']+)["\']', content)
    if not key_match:
        key_match = re.search(r'SUPABASE_ANON_KEY\s*=\s*["\']([^"\']+)["\']', content)
    
    url = url_match.group(1) if url_match else ""
    key = key_match.group(1) if key_match else ""
    return create_client(url, key)

def get_wita_date_string(epoch_secs):
    if not epoch_secs:
        return None
    try:
        dt_utc = datetime.fromtimestamp(epoch_secs, tz=timezone.utc)
        wita_offset = timezone(timedelta(hours=8))
        dt_wita = dt_utc.astimezone(wita_offset)
        return dt_wita.strftime("%Y-%m-%d")
    except Exception:
        return None

def save_key_to_supabase(supabase, key, value, max_retries=3):
    """Upload key-value ke Supabase dengan upsert dan chunked upload untuk payload besar."""
    compressed = value.get("compressed_data", "") if isinstance(value, dict) else ""
    CHUNK_LIMIT = 3 * 1024 * 1024  # 3MB per chunk

    if compressed and len(compressed) > CHUNK_LIMIT:
        chunks = [compressed[i:i+CHUNK_LIMIT] for i in range(0, len(compressed), CHUNK_LIMIT)]
        total_chunks = len(chunks)

        for ci, chunk in enumerate(chunks):
            chunk_key = f"{key}__chunk_{ci}"
            chunk_val = {
                "compressed_data": chunk,
                "chunk_index": ci,
                "total_chunks": total_chunks,
                "updated_at": value.get("updated_at", "") if isinstance(value, dict) else ""
            }
            for attempt in range(max_retries):
                try:
                    supabase.table("dashboard_store").upsert(
                        {"key": chunk_key, "value": chunk_val},
                        on_conflict="key"
                    ).execute()
                    break
                except Exception as e:
                    if attempt < max_retries - 1:
                        wait = 2 ** attempt
                        print(f"  [RETRY {attempt+1}] Chunk {ci}/{total_chunks} gagal, coba lagi dalam {wait}s: {e}")
                        time.sleep(wait)
                    else:
                        raise

        # Upload metadata record
        meta_val = {k: v for k, v in value.items() if k != "compressed_data"}
        meta_val["is_chunked"] = True
        meta_val["total_chunks"] = total_chunks
        meta_val["compressed_data"] = ""
        supabase.table("dashboard_store").upsert(
            {"key": key, "value": meta_val},
            on_conflict="key"
        ).execute()
        return

    # Upload normal dengan upsert (tidak perlu delete dulu)
    for attempt in range(max_retries):
        try:
            supabase.table("dashboard_store").upsert(
                {"key": key, "value": value},
                on_conflict="key"
            ).execute()
            return
        except Exception as e:
            if attempt < max_retries - 1:
                wait = 2 ** attempt
                print(f"  [RETRY {attempt+1}] Upload {key} gagal, coba lagi dalam {wait}s: {e}")
                time.sleep(wait)
            else:
                raise

def merge_granulars():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    print("[MERGE] Menggabungkan file partisi granular_assignments_*.json...")
    files = glob.glob(os.path.join(script_dir, "granular_assignments_*.json"))
    if not files:
        print("[MERGE] Tidak ada file partisi untuk digabungkan.")
        return

    # Master lists and dicts
    master_regions = []
    regions_map = {} # tuple -> master_idx

    master_petugas = []
    petugas_map = {} # tuple -> master_idx

    master_statuses = []
    statuses_map = {} # string -> master_idx

    master_targets = []
    
    # We might have duplicates if different scripts overlap or run multiple times.
    # To avoid target duplication, we map target_id -> index in master_targets
    targets_map = {}

    for fpath in files:
        print(f" -> Membaca {fpath}...")
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            comp = data.get("compressed_data")
            if not comp: continue
            
            raw = json.loads(gzip.decompress(base64.b64decode(comp)).decode('utf-8'))
            
            p_regions = raw.get("regions", [])
            p_petugas = raw.get("petugas", [])
            p_statuses = raw.get("statuses", [])
            p_targets = raw.get("targets", [])
            
            # Map old index to new master index for this file
            reg_idx_map = {}
            for i, r in enumerate(p_regions):
                k = tuple(r)
                if k not in regions_map:
                    regions_map[k] = len(master_regions)
                    master_regions.append(r)
                reg_idx_map[i] = regions_map[k]
                
            pet_idx_map = {}
            for i, p in enumerate(p_petugas):
                k = tuple(p)
                if k not in petugas_map:
                    petugas_map[k] = len(master_petugas)
                    master_petugas.append(p)
                pet_idx_map[i] = petugas_map[k]
                
            stat_idx_map = {}
            for i, s in enumerate(p_statuses):
                k = s
                if k not in statuses_map:
                    statuses_map[k] = len(master_statuses)
                    master_statuses.append(s)
                stat_idx_map[i] = statuses_map[k]
                
            # Now map targets
            for t in p_targets:
                # t = [tid, code_id, name, stat_idx, pet_idx, reg_idx, epoch_mod, survey_flag, pengawas_idx]
                tid = t[0]
                pengawas_idx = pet_idx_map.get(t[8], -1) if len(t) > 8 else -1
                new_t = [
                    t[0],
                    t[1],
                    t[2],
                    stat_idx_map.get(t[3], -1),
                    pet_idx_map.get(t[4], -1),
                    reg_idx_map.get(t[5], -1),
                    t[6],
                    t[7],
                    pengawas_idx
                ]
                
                # Update or insert
                if tid in targets_map:
                    # Update if newer
                    existing_idx = targets_map[tid]
                    existing_t = master_targets[existing_idx]
                    if new_t[6] > existing_t[6]: # compare epoch_mod
                        master_targets[existing_idx] = new_t
                else:
                    targets_map[tid] = len(master_targets)
                    master_targets.append(new_t)
                    
        except Exception as e:
            print(f"[ERROR] Gagal memproses {fpath}: {e}")

    print(f"[MERGE] Selesai menggabungkan. Total target gabungan: {len(master_targets)}")
    
    # Optional: We might want to preserve remarks. Currently we don't extract remarks from parts.
    # If necessary, we can extract them. But for now, we just merge targets.
    
    merged_payload = {
        "updated_at": datetime.now().isoformat(),
        "regions": master_regions,
        "petugas": master_petugas,
        "statuses": master_statuses,
        "targets": master_targets,
        "remarks": {} # could aggregate if we saved it in parts
    }
    
    raw_json_str = json.dumps(merged_payload, ensure_ascii=False)
    compressed_bytes = gzip.compress(raw_json_str.encode('utf-8'))
    base64_str = base64.b64encode(compressed_bytes).decode('utf-8')
    
    # Save the merged master file
    with open(os.path.join(script_dir, "granular_assignments.json"), "w", encoding="utf-8") as f:
        json.dump({"compressed_data": base64_str, "updated_at": datetime.now().isoformat()}, f, indent=2)
        
    with open(os.path.join(script_dir, "granular_assignments.js"), "w", encoding="utf-8") as f:
        f.write("window.COMPRESSED_GRANULAR_ASSIGNMENTS = [\n")
        chunk_size = 500000
        for i in range(0, len(base64_str), chunk_size):
            chunk = base64_str[i:i+chunk_size]
            f.write(f"  '{chunk}',\n")
        f.write("].join('');\n")
        f.write(f"window.GRANULAR_ASSIGNMENTS_UPDATED_AT = '{datetime.now().isoformat()}';\n")
        
    print("✅ Master granular_assignments berhasil di-generate!")
    
    # === GENERATE assign_data.js & SLS/PETUGAS AGGREGATES ===
    # Kumpulkan statistik untuk dashboard
    assign_umum = {}
    assign_ub = {"7200": {"kode_kab": "7200", "nama_kab": "SULAWESI TENGAH", "total": 0, "assigned": 0, "have_not_assigned": 0, "timestamp": datetime.now().isoformat()}}
    
    # We need region mapping
    region_map_file = os.path.join(script_dir, "region_map_sulteng.json")
    try:
        with open(region_map_file, "r", encoding="utf-8") as f:
            rmap = json.load(f)
            for k, v in rmap.items():
                kab_name = v.get("kab_name", "") if isinstance(v, dict) else v
                assign_umum[k] = {"kode_kab": k, "nama_kab": kab_name, "total": 0, "assigned": 0, "have_not_assigned": 0}
    except:
        pass

    sls_umum_dict = {}
    sls_ub_dict = {}
    pet_umum_dict = {}
    pet_ub_dict = {}
    daily_counts_dict = {}
        
    for item in master_targets:
        survey = "se_umum" if item[7] == 0 else "se_ub"
        status = master_statuses[item[3]]
        
        reg_idx = item[5]
        reg = master_regions[reg_idx] if (reg_idx >= 0 and reg_idx < len(master_regions)) else ["-"]*8
        kab_code = reg[0] if len(reg) > 0 else "-"
        kab_name = reg[1] if len(reg) > 1 else "-"
        kec_name = reg[3] if len(reg) > 3 else "-"
        desa_name = reg[5] if len(reg) > 5 else "-"
        sls_code = reg[6] if len(reg) > 6 else "-"
        sls_name = reg[7] if len(reg) > 7 else "-"
        
        pet_idx = item[4]
        pet_username = "-"
        pet_fullname = "-"
        if pet_idx >= 0 and pet_idx < len(master_petugas):
            pet_username = master_petugas[pet_idx][0]
            pet_fullname = master_petugas[pet_idx][1]
            
        is_assigned = (pet_username != "-" and pet_username != "")

        # 0. Daily aggregation for non-OPEN statuses (Submissions/Approvals)
        status_upper = status.upper()
        epoch_mod = item[6]
        if status_upper != "OPEN" and status_upper != "DRAFT" and epoch_mod > 0:
            wita_date = get_wita_date_string(epoch_mod)
            if wita_date:
                agg_key = (wita_date, kab_name, survey)
                daily_counts_dict[agg_key] = daily_counts_dict.get(agg_key, 0) + 1
        
        # 1. Update Kabupaten aggregate
        if survey == "se_umum":
            if kab_code in assign_umum:
                assign_umum[kab_code]["total"] += 1
                if not is_assigned:
                    assign_umum[kab_code]["have_not_assigned"] += 1
                else:
                    assign_umum[kab_code]["assigned"] += 1
        elif survey == "se_ub":
            assign_ub["7200"]["total"] += 1
            if not is_assigned:
                assign_ub["7200"]["have_not_assigned"] += 1
            else:
                assign_ub["7200"]["assigned"] += 1
                
        # 2. Update SLS aggregate
        if sls_code != "-" and sls_code != "":
            sls_dict = sls_umum_dict if survey == "se_umum" else sls_ub_dict
            if sls_code not in sls_dict:
                sls_dict[sls_code] = {
                    "sls_code": sls_code,
                    "sls_name": sls_name,
                    "desa_name": desa_name,
                    "kec_name": kec_name,
                    "kab_name": kab_name,
                    "total": 0,
                    "assigned": 0,
                    "unassigned": 0,
                    "sync_count": 0,
                    "completed": 0,
                    "officers": set()
                }
            sls_item = sls_dict[sls_code]
            sls_item["total"] += 1
            if is_assigned:
                sls_item["assigned"] += 1
                ofc_str = f"{pet_fullname} ({pet_username})" if pet_fullname and pet_fullname != "-" else pet_username
                sls_item["officers"].add(ofc_str)
            else:
                sls_item["unassigned"] += 1
            
            # Count completed (NOT OPEN and NOT DRAFT)
            if status_upper != "OPEN" and status_upper != "DRAFT":
                sls_item["completed"] += 1
                
        # 3. Update Petugas aggregate
        if is_assigned:
            pet_dict = pet_umum_dict if survey == "se_umum" else pet_ub_dict
            if pet_username not in pet_dict:
                pet_dict[pet_username] = {
                    "username": pet_username,
                    "fullname": pet_fullname,
                    "regions": set()
                }
            if sls_code != "-" and sls_code != "":
                pet_dict[pet_username]["regions"].add((sls_code + "00", sls_name))
                 
    # Add timestamps from files
    files = glob.glob(os.path.join(script_dir, "granular_assignments_se_umum_*.json"))
    for fpath in files:
        try:
            kab_code = os.path.basename(fpath).split("_")[-1].split(".")[0]
            with open(fpath, "r") as f:
                d = json.load(f)
                up_at = d.get("updated_at")
                if up_at and kab_code in assign_umum:
                    assign_umum[kab_code]["timestamp"] = up_at
        except:
            pass
            
    files_ub = glob.glob(os.path.join(script_dir, "granular_assignments_se_ub_*.json"))
    if files_ub:
        try:
            with open(files_ub[0], "r") as f:
                d = json.load(f)
                up_at = d.get("updated_at")
                if up_at:
                    assign_ub["7200"]["timestamp"] = up_at
        except:
            pass
            
    now_str = datetime.now().isoformat()
    for v in assign_umum.values():
        if "timestamp" not in v:
            v["timestamp"] = now_str
    for v in assign_ub.values():
        if "timestamp" not in v:
            v["timestamp"] = now_str

    # Format lists for output
    processed_sls_umum = []
    for k, v in sls_umum_dict.items():
        v["officers"] = list(v["officers"])
        processed_sls_umum.append(v)
        
    processed_sls_ub = []
    for k, v in sls_ub_dict.items():
        v["officers"] = list(v["officers"])
        processed_sls_ub.append(v)
        
    processed_petugas_umum = []
    for k, v in pet_umum_dict.items():
        regions_list = [{"regionCode": rc, "regionName": rn} for rc, rn in v["regions"]]
        processed_petugas_umum.append({
            "username": v["username"],
            "fullname": v["fullname"],
            "regions": regions_list,
            "totalRegions": len(regions_list)
        })
        
    processed_petugas_ub = []
    for k, v in pet_ub_dict.items():
        regions_list = [{"regionCode": rc, "regionName": rn} for rc, rn in v["regions"]]
        processed_petugas_ub.append({
            "username": v["username"],
            "fullname": v["fullname"],
            "regions": regions_list,
            "totalRegions": len(regions_list)
        })

    # Generate assign_data.js
    js_content  = f"window.ASSIGN_DATA_UMUM = {json.dumps(list(assign_umum.values()), indent=4, ensure_ascii=False)};\n"
    js_content += f"window.ASSIGN_DATA_UB   = {json.dumps(list(assign_ub.values()),   indent=4, ensure_ascii=False)};\n"
    js_content += f"window.ASSIGN_SLS_DATA_UMUM = {json.dumps(processed_sls_umum, indent=4, ensure_ascii=False)};\n"
    js_content += f"window.ASSIGN_SLS_DATA_UB   = {json.dumps(processed_sls_ub,   indent=4, ensure_ascii=False)};\n"
    js_content += f"window.PETUGAS_DATA_UMUM = {json.dumps(processed_petugas_umum, indent=4, ensure_ascii=False)};\n"
    js_content += f"window.PETUGAS_DATA_UB   = {json.dumps(processed_petugas_ub,   indent=4, ensure_ascii=False)};\n"
    js_content += """
{
    const activeSubtab = localStorage.getItem('active_assign_subtab') || 'se2026';
    if (activeSubtab === 'se2026') {
        window.ASSIGN_DATA = window.ASSIGN_DATA_UMUM || [];
        window.ASSIGN_SLS_DATA = window.ASSIGN_SLS_DATA_UMUM || [];
        window.PETUGAS_DATA = window.PETUGAS_DATA_UMUM || [];
    } else {
        window.ASSIGN_DATA = window.ASSIGN_DATA_UB || [];
        window.ASSIGN_SLS_DATA = window.ASSIGN_SLS_DATA_UB || [];
        window.PETUGAS_DATA = window.PETUGAS_DATA_UB || [];
    }
}
"""
       # Write assign_data.js
    assign_data_path = os.path.join(script_dir, "assign_data.js")
    with open(assign_data_path, "w", encoding="utf-8") as f:
        f.write(js_content)
    print("✅ Generate ulang assign_data.js berhasil (via granular)!")

    # === GENERATE daily_submission_stats ===
    daily_stats_data = []
    for (date_str, kab_name, s_type), cnt in daily_counts_dict.items():
        daily_stats_data.append({
            "date": date_str,
            "kab_name": kab_name,
            "survey_type": s_type,
            "count": cnt
        })

    stats_json_path = os.path.join(script_dir, "daily_submission_stats.json")
    with open(stats_json_path, "w", encoding="utf-8") as f:
        json.dump(daily_stats_data, f, indent=2)
    print(f"✅ Data timeline harian gabungan disimpan secara lokal ke {stats_json_path}")

    stats_js_path = os.path.join(script_dir, "daily_submission_stats.js")
    with open(stats_js_path, "w", encoding="utf-8") as f:
        f.write(f"window.DAILY_SUBMISSION_STATS = {json.dumps(daily_stats_data, indent=2)};\n")
    print(f"✅ Data timeline harian gabungan disimpan secara lokal ke {stats_js_path}")

    # === UPLOAD daily_submission_stats ke Supabase ===
    try:
        supabase = load_supabase_config()
        # 1. Update daily_submission_stats
        supabase.table("dashboard_store").delete().eq("key", "daily_submission_stats").execute()
        supabase.table("dashboard_store").insert({"key": "daily_submission_stats", "value": daily_stats_data}).execute()
        print("✅ Berhasil mengunggah daily_submission_stats (gabungan) ke Supabase!")
        
        # 2. Save daily snapshot for daily submission stats
        today_str = datetime.now().strftime("%Y-%m-%d")
        daily_stats_key = f"daily_submission_stats:{today_str}"
        try:
            supabase.table("dashboard_store").delete().eq("key", daily_stats_key).execute()
            supabase.table("dashboard_store").insert({"key": daily_stats_key, "value": daily_stats_data}).execute()
            print(f"✅ Berhasil mengunggah data harian timeline ({daily_stats_key}) ke Supabase.")
        except Exception as ex:
            print(f"[ERROR] Gagal mengunggah data harian timeline snapshot ke Supabase: {ex}")
    except Exception as e:
        print(f"[ERROR] Gagal mengunggah daily_submission_stats ke Supabase: {e}")
    
    # === UPLOAD assign_data ke Supabase ===
    def compress_sls(sls_list):
        return [
            [
                item.get("sls_code"),
                item.get("sls_name"),
                item.get("desa_name"),
                item.get("kec_name"),
                item.get("kab_name"),
                item.get("total"),
                item.get("assigned"),
                item.get("unassigned"),
                item.get("sync_count", 0),
                item.get("officers", [])
            ]
            for item in sls_list
        ]

    assign_payload = {
        "updated_at": datetime.now().isoformat(),
        "assign_data_umum": list(assign_umum.values()),
        "assign_data_ub": list(assign_ub.values()),
        "assign_sls_data_umum": compress_sls(processed_sls_umum),
        "assign_sls_data_ub": compress_sls(processed_sls_ub),
        "petugas_data_umum": processed_petugas_umum,
        "petugas_data_ub": processed_petugas_ub
    }
    
    try:
        raw_payload_str = json.dumps(assign_payload, ensure_ascii=False)
        compressed_payload = base64.b64encode(gzip.compress(raw_payload_str.encode('utf-8'))).decode('utf-8')
        db_payload = {
            "is_compressed": True,
            "compressed_data": compressed_payload
        }
        
        supabase = load_supabase_config()
        save_key_to_supabase(supabase, "assign_data", db_payload)
        print("✅ Berhasil mengunggah assign_data (terkompresi) ke Supabase!")
        
        # Upload daily historical key
        today_str = datetime.now().strftime("%Y-%m-%d")
        daily_key = f"assign_data:{today_str}"
        try:
            save_key_to_supabase(supabase, daily_key, db_payload)
            print(f"✅ Berhasil mengunggah data harian Assign ({daily_key}) ke Supabase.")
        except Exception as ex:
            print(f"[ERROR] Gagal mengunggah data harian Assign ke Supabase: {ex}")
    except Exception as e:
        print(f"[ERROR] Gagal mengunggah assign_data ke Supabase: {e}")
        
    # Upload partitions to Supabase
    try:
        supabase = load_supabase_config()
        print("[MERGE] Mengunggah data partisi ke Supabase...")
        
        # Upload se_ub partition if it exists
        se_ub_path = os.path.join(script_dir, "granular_assignments_se_ub.json")
        if os.path.exists(se_ub_path):
            try:
                with open(se_ub_path, "r", encoding="utf-8") as f:
                    d = json.load(f)
                comp = d.get("compressed_data")
                if comp:
                    payload = {
                        "compressed_data": comp,
                        "updated_at": d.get("updated_at", datetime.now().isoformat())
                    }
                    save_key_to_supabase(supabase, "granular_assignments_se_ub", payload)
                    print(" ✅ Berhasil mengunggah partisi se_ub ke Supabase.")
            except Exception as ex:
                print(f" [ERROR] Gagal mengunggah partisi se_ub ke Supabase: {ex}")
                
        # Upload each se_umum partition
        all_partition_success = True
        failed_partitions = []
        for fpath in sorted(glob.glob(os.path.join(script_dir, "granular_assignments_se_umum_*.json"))):
            key = "unknown"
            try:
                basename = os.path.basename(fpath)
                kab_code = basename.split("_")[-1].split(".")[0] # e.g. 7201
                key = f"granular_assignments_se_umum_{kab_code}"
                with open(fpath, "r", encoding="utf-8") as f:
                    d = json.load(f)
                comp = d.get("compressed_data")
                if comp:
                    mb_size = len(comp) / (1024*1024)
                    print(f" -> Upload {key} ({mb_size:.1f} MB)...")
                    payload = {
                        "compressed_data": comp,
                        "updated_at": d.get("updated_at", datetime.now().isoformat())
                    }
                    save_key_to_supabase(supabase, key, payload)
                    print(f" ✅ Berhasil mengunggah partisi {key} ke Supabase.")
            except Exception as ex:
                print(f" [ERROR] Gagal mengunggah partisi {key} ke Supabase: {ex}")
                all_partition_success = False
                failed_partitions.append(key)
                
        if all_partition_success:
            print("✅ SINKRONISASI PARTISI SUPABASE BERHASIL!")
        else:
            print(f"⚠️  SINKRONISASI PARTISI SELESAI DENGAN {len(failed_partitions)} GAGAL: {', '.join(failed_partitions)}")
            print("    Partisi yang gagal perlu di-upload ulang secara manual.")
    except Exception as e:
        print(f"[ERROR] Gagal mengunggah partisi ke Supabase: {e}")
 
    # Fallback/Optional: Try to upload the giant master, but don't crash if it timeouts
    try:
        supabase = load_supabase_config()
        print("[MERGE] Mencoba mengunggah master granular_assignments (backup) ke Supabase...")
        granular_store_value = {
            "compressed_data": base64_str,
            "updated_at": datetime.now().isoformat()
        }
        save_key_to_supabase(supabase, "granular_assignments", granular_store_value)
        print("✅ SINKRONISASI MASTER SUPABASE BERHASIL!")
    except Exception as e:
        print(f"[WARNING] Gagal mengunggah master ke Supabase (karena batasan ukuran/timeout, partisi di atas tetap aman): {e}")

if __name__ == "__main__":
    merge_granulars()
