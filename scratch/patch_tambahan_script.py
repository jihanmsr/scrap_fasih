import re

with open('scrape_dashboard_via_cdp.py', 'r') as f:
    content = f.read()

tambahan_helper = """
import gzip
import base64
import glob

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

def get_real_tambahan():
    files = glob.glob(os.path.join(script_dir, "granular_assignments_se_umum_*.json"))
    kab_counts = {}
    kec_counts = {}
    for fpath in files:
        if "7211_7271" in fpath or "7201_7209_7210" in fpath or "7204_7205_7206_7207" in fpath or "7202_7208_7212" in fpath:
            continue
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
            comp = data.get("compressed_data")
            if comp:
                raw = json.loads(gzip.decompress(base64.b64decode(comp)).decode('utf-8'))
                targets = raw.get("targets", [])
                regions = raw.get("regions", [])
                for t in targets:
                    code_id = t[1]
                    comp_name = t[2]
                    reg_idx = t[5] if len(t) > 5 else 0
                    if is_tambahan(code_id):
                        jenis_lbl, is_usaha = classify_tambahan_simple(code_id, comp_name)
                        reg_info = regions[reg_idx] if reg_idx < len(regions) else []
                        if len(reg_info) > 3:
                            kab_raw = reg_info[1]
                            kec_raw = reg_info[3].upper().strip()
                            kab_clean = re.sub(r'\\[\\d+\\]', '', kab_raw).replace('[','').replace(']','').strip()
                            kab_clean = " ".join([w for w in kab_clean.split() if not (w.isdigit() or w.startswith("72"))]).upper().strip()
                            
                            if kab_clean not in kab_counts:
                                kab_counts[kab_clean] = {"usaha": 0, "rumah": 0}
                            if is_usaha: kab_counts[kab_clean]["usaha"] += 1
                            else: kab_counts[kab_clean]["rumah"] += 1
                            
                            kec_key = f"{kab_clean}_{kec_raw}"
                            if kec_key not in kec_counts:
                                kec_counts[kec_key] = {"usaha": 0, "rumah": 0}
                            if is_usaha: kec_counts[kec_key]["usaha"] += 1
                            else: kec_counts[kec_key]["rumah"] += 1
        except Exception as e:
            pass
    return kab_counts, kec_counts
"""

content = content.replace("import asyncio", "import asyncio\n" + tambahan_helper)

inject_code = """
        # --- INJECT REAL TAMBAHAN FROM GRANULAR DB ---
        kab_counts, kec_counts = get_real_tambahan()
        for kab in final_js_obj.get("se_umum", []):
            kab_clean = re.sub(r'\\[\\d+\\]', '', kab["kabupaten"]).replace('[','').replace(']','').strip()
            kab_clean = " ".join([w for w in kab_clean.split() if not (w.isdigit() or w.startswith("72"))]).upper().strip()
            kab["new_usaha_overall"] = kab_counts.get(kab_clean, {}).get("usaha", 0)
            kab["new_rumah_overall"] = kab_counts.get(kab_clean, {}).get("rumah", 0)
            
            for kec in kab.get("kecamatan_list", []):
                kec_name = kec.get("kec_name", "").upper().strip()
                kec_name_clean = re.sub(r'\\[\\d+\\]', '', kec_name).replace('[','').replace(']','').strip()
                kec_key = f"{kab_clean}_{kec_name_clean}"
                kec["new_usaha_overall"] = kec_counts.get(kec_key, {}).get("usaha", 0)
                kec["new_rumah_overall"] = kec_counts.get(kec_key, {}).get("rumah", 0)
                
        final_js_obj["se_umum_prov_new_total"] = sum(k.get("new_usaha_overall", 0) for k in final_js_obj.get("se_umum", []))
        final_js_obj["se_umum_prov_new_rumah_total"] = sum(k.get("new_rumah_overall", 0) for k in final_js_obj.get("se_umum", []))
"""

content = content.replace("with open(ipas_data_path, \"w\", encoding=\"utf-8\") as f:", inject_code + "\n    with open(ipas_data_path, \"w\", encoding=\"utf-8\") as f:")

with open('scrape_dashboard_via_cdp.py', 'w') as f:
    f.write(content)

