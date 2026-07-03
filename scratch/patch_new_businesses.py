import os
import json
import base64
import gzip
import re
from datetime import datetime, timezone, timedelta
from supabase import create_client
from dotenv import load_dotenv

def is_tambahan(code_identity):
    if not code_identity:
        return False
    cleaned = code_identity.strip()
    if not cleaned.startswith("72"):
        return True
    parts = [p.strip() for p in cleaned.split(" - ")]
    if len(parts) < 2:
        return False
    source = parts[1].upper()
    known_sources = {"DTSEN", "UMK", "UM", "UMB", "UMKM", "SE2026", "SE26", "PDRB", "PAPI", "CAWI", "CAPI", "UB"}
    if source in known_sources:
        return False
    if source.startswith("SE26") or source.startswith("SE2026"):
        return False
    return True

def classify_tambahan_simple(code_id, name):
    code_id_upper = (code_id or "").upper()
    name_upper = (name or "").upper()
    if "BANGUNAN KOSONG" in name_upper or "RUMAH KOSONG" in name_upper or "KOSONG" in name_upper or "BANGUNAN KOSONG" in code_id_upper or "RUMAH KOSONG" in code_id_upper:
        return "Bangunan/Rumah Kosong", False
    if "1. YA" in code_id_upper or "1.YA" in code_id_upper or "1. YA" in name_upper or "1.YA" in name_upper:
        return "Keluarga Usaha", True
    if "2. TIDAK" in code_id_upper or "2.TIDAK" in code_id_upper or "2. TIDAK" in name_upper or "2.TIDAK" in name_upper:
        return "Keluarga (Bukan Usaha)", False
    if "KELUARGA" in name_upper:
        return "Keluarga", False
    return "Usaha Baru", True

def clean_kab_name(kab_raw):
    if not kab_raw:
        return "UNKNOWN"
    cleaned = re.sub(r'\[\d+\]', '', kab_raw)
    cleaned = cleaned.replace('[', '').replace(']', '')
    words = [word for word in cleaned.split() if not (word.isdigit() or (word.startswith("72") and len(word)==4))]
    return " ".join(words).upper().strip()

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_dir = os.path.dirname(script_dir)
    
    kab_new_businesses = {}
    kab_codes = ["7201", "7202", "7203", "7204", "7205", "7206", "7207", "7208", "7209", "7210", "7211", "7212", "7271"]
    
    print("Mendata seluruh target tambahan (new businesses) dari data granular...")
    for code in kab_codes:
        file_name = f"granular_assignments_se_umum_{code}.json"
        json_path = os.path.join(workspace_dir, file_name)
        if os.path.exists(json_path):
            print(f" -> Membuka {file_name}...")
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                comp = data.get("compressed_data")
                raw = json.loads(gzip.decompress(base64.b64decode(comp)).decode('utf-8'))
                
                statuses_list = raw.get("statuses", [])
                targets = raw.get("targets", [])
                regions_list = raw.get("regions", [])
                
                for t in targets:
                    code_id = t[1]
                    comp_name = t[2]
                    stat_idx = t[3]
                    reg_idx = t[5] if len(t) > 5 else 0
                    
                    if is_tambahan(code_id):
                        epoch_val = t[6] if len(t) > 6 else 0
                        date_lbl = "older"
                        if epoch_val > 0:
                            try:
                                dt_sec = epoch_val / 1000.0 if epoch_val > 10**11 else float(epoch_val)
                                dt_utc = datetime.fromtimestamp(dt_sec, tz=timezone.utc)
                                wita_offset = timezone(timedelta(hours=8))
                                dt_wita = dt_utc.astimezone(wita_offset)
                                wita_date_str = dt_wita.strftime("%Y-%m-%d")
                                
                                today_wita = datetime.now(wita_offset).strftime("%Y-%m-%d")
                                yesterday_wita = (datetime.now(wita_offset) - timedelta(days=1)).strftime("%Y-%m-%d")
                                
                                if wita_date_str == today_wita:
                                    date_lbl = "today"
                                elif wita_date_str == yesterday_wita:
                                    date_lbl = "yesterday"
                            except:
                                pass
                                
                        jenis_lbl, is_usaha = classify_tambahan_simple(code_id, comp_name)
                        status_str = statuses_list[stat_idx] if stat_idx < len(statuses_list) else "-"
                        
                        reg_info = regions_list[reg_idx] if reg_idx < len(regions_list) else []
                        kab_raw = reg_info[1] if len(reg_info) > 1 else "UNKNOWN"
                        kab_clean = clean_kab_name(kab_raw)
                        
                        kec_name = reg_info[3].upper().strip() if len(reg_info) > 3 else "-"
                        
                        biz_item = {
                            "name": comp_name,
                            "code": code_id,
                            "date": date_lbl,
                            "status": status_str,
                            "type": "usaha" if is_usaha else "rumah",
                            "kecName": kec_name,
                            "jenis": jenis_lbl
                        }
                        kab_new_businesses.setdefault(kab_clean, []).append(biz_item)
            except Exception as e:
                print(f"[ERROR] Gagal memproses {file_name}: {e}")
                
    load_dotenv()
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    if SUPABASE_URL and SUPABASE_KEY:
        try:
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            print("\nMenarik 'ipas_data' dari Supabase untuk di-patch...")
            res_ipas = supabase.table('dashboard_store').select('value').eq('key', 'ipas_data').execute()
            if res_ipas.data:
                val = res_ipas.data[0]['value']
            else:
                # Fallback: cari snapshot terbaru
                print("[INFO] Key 'ipas_data' tidak ditemukan. Mencari snapshot terbaru...")
                snapshots = supabase.table('dashboard_store').select('key,value').ilike('key', 'ipas_data:20%').execute()
                if snapshots.data:
                    latest = sorted(snapshots.data, key=lambda r: r['key'], reverse=True)[0]
                    print(f"[INFO] Menggunakan snapshot: {latest['key']}")
                    val = latest['value']
                else:
                    print("[ERROR] Tidak ada snapshot ipas_data ditemukan. Batalkan.")
                    val = None
            if val is not None:
                if isinstance(val, str):
                    val = json.loads(val)
                if not isinstance(val, dict):
                    print("[ERROR] ipas_data bukan dict. Batalkan.")
                    val = None
            if val is not None:
                se_umum = val.get("se_umum", [])
                for kab_item in se_umum:
                    kab_raw = kab_item.get("kabupaten", "")
                    kab_clean = clean_kab_name(kab_raw)
                    
                    scraped_biz = kab_new_businesses.get(kab_clean, [])
                    kab_item["new_businesses"] = scraped_biz
                    
                    kab_item["new_usaha_today"] = sum(1 for b in scraped_biz if b["type"] == "usaha" and b["date"] == "today")
                    kab_item["new_usaha_yesterday"] = sum(1 for b in scraped_biz if b["type"] == "usaha" and b["date"] == "yesterday")
                    kab_item["new_rumah_today"] = sum(1 for b in scraped_biz if b["type"] == "rumah" and b["date"] == "today")
                    kab_item["new_rumah_yesterday"] = sum(1 for b in scraped_biz if b["type"] == "rumah" and b["date"] == "yesterday")
                    kab_item["new_usaha_overall"] = sum(1 for b in scraped_biz if b["type"] == "usaha")
                    kab_item["new_rumah_overall"] = sum(1 for b in scraped_biz if b["type"] == "rumah")
                    
                    kec_list = kab_item.get("kecamatan_list", [])
                    for kec_item in kec_list:
                        kec_name = (kec_item.get("kec_name") or "").upper().strip()
                        kec_biz = [b for b in scraped_biz if b["kecName"] == kec_name]
                        kec_item["new_businesses"] = kec_biz
                        kec_item["new_usaha_today"] = sum(1 for b in kec_biz if b["type"] == "usaha" and b["date"] == "today")
                        kec_item["new_usaha_yesterday"] = sum(1 for b in kec_biz if b["type"] == "usaha" and b["date"] == "yesterday")
                        kec_item["new_rumah_today"] = sum(1 for b in kec_biz if b["type"] == "rumah" and b["date"] == "today")
                        kec_item["new_rumah_yesterday"] = sum(1 for b in kec_biz if b["type"] == "rumah" and b["date"] == "yesterday")
                    
                    print(f"  {kab_raw}: {len(scraped_biz)} tambahan")
                
                # Update prov-level totals (se_umum_prov_new_total & se_umum_prov_new_rumah_total)
                total_prov_usaha = sum(kab.get("new_usaha_overall", 0) for kab in se_umum)
                total_prov_rumah = sum(kab.get("new_rumah_overall", 0) for kab in se_umum)
                val["se_umum_prov_new_total"] = total_prov_usaha
                val["se_umum_prov_new_rumah_total"] = total_prov_rumah
                print(f"\n✅ Provinsi: Total tambahan usaha = {total_prov_usaha}, rumah = {total_prov_rumah}")
                
                # Simpan lokal dulu (dengan new_businesses penuh untuk fallback)
                with open(os.path.join(workspace_dir, "ipas_data.js"), "w", encoding="utf-8") as f:
                    f.write(f"window.IPAS_DATA = {json.dumps(val, indent=4)};\n")
                print("✅ File lokal ipas_data.js berhasil diperbarui!")
                
                # Buat versi slim untuk Supabase (strip new_businesses array besar dari tiap item)
                import copy, time
                val_slim = copy.deepcopy(val)
                new_biz_by_kab = {}  # simpan new_businesses per kab untuk upload terpisah
                for kab_item in val_slim.get("se_umum", []):
                    kab_raw_key = kab_item.get("kabupaten", "")
                    # Simpan list new_businesses sebelum strip
                    new_biz_by_kab[kab_raw_key] = kab_item.get("new_businesses", [])
                    kab_item["new_businesses"] = []  # strip dari payload utama
                    for kec_item in kab_item.get("kecamatan_list", []):
                        kec_item["new_businesses"] = []  # strip juga dari kecamatan
                
                # Upload ke Supabase dengan retry - payload slim
                max_retries = 3
                for attempt in range(1, max_retries + 1):
                    try:
                        print(f"Mengunggah ipas_data slim ke Supabase (percobaan {attempt}/{max_retries})...")
                        supabase.table("dashboard_store").delete().eq("key", "ipas_data").execute()
                        supabase.table("dashboard_store").insert({"key": "ipas_data", "value": val_slim}).execute()
                        print("✅ Key 'ipas_data' (slim) berhasil di-patch di Supabase!")
                        break
                    except Exception as e:
                        print(f"[RETRY {attempt}] Gagal upload ipas_data: {e}")
                        if attempt < max_retries:
                            print("Menunggu 15 detik sebelum retry...")
                            time.sleep(15)
                        else:
                            print("[ERROR] Semua percobaan upload ipas_data gagal.")
                
                # Upload new_businesses per kabupaten sebagai key terpisah
                # Format key: new_businesses_se_umum_<kab_clean>
                # contoh: new_businesses_se_umum_BANGGAI KEPULAUAN
                print("\nMengunggah new_businesses per kabupaten...")
                kab_code_map = {
                    "BANGGAI KEPULAUAN": "7201", "BANGGAI": "7202", "MOROWALI": "7203",
                    "POSO": "7204", "DONGGALA": "7205", "TOLI-TOLI": "7206", "BUOL": "7207",
                    "PARIGI MOUTONG": "7208", "TOJO UNA-UNA": "7209", "SIGI": "7210",
                    "BANGGAI LAUT": "7211", "MOROWALI UTARA": "7212", "PALU": "7271"
                }
                for kab_full, biz_list in new_biz_by_kab.items():
                    kab_clean = clean_kab_name(kab_full)
                    kab_code = kab_code_map.get(kab_clean, kab_clean.lower().replace(" ", "_"))
                    nb_key = f"new_businesses_se_umum_{kab_code}"
                    for attempt in range(1, max_retries + 1):
                        try:
                            supabase.table("dashboard_store").delete().eq("key", nb_key).execute()
                            supabase.table("dashboard_store").insert({"key": nb_key, "value": biz_list}).execute()
                            print(f"  ✅ {nb_key}: {len(biz_list)} item")
                            break
                        except Exception as e:
                            print(f"  [RETRY {attempt}] Gagal upload {nb_key}: {e}")
                            if attempt < max_retries:
                                time.sleep(10)
                            else:
                                print(f"  [ERROR] Gagal upload {nb_key}.")
        except Exception as e:
            print(f"[ERROR] Gagal patch Supabase: {e}")

if __name__ == "__main__":
    main()
