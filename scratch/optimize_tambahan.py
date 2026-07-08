import json
import os
import glob
import re

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
        return "rumah"
    return "usaha"

def get_tambahan_counts():
    files = glob.glob("granular_assignments_se_umum_*.json")
    kab_counts = {}
    kec_counts = {}
    
    for fpath in files:
        with open(fpath, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                for item in data:
                    if is_tambahan(item.get("codeIdentity")):
                        jenis = classify_tambahan_simple(item.get("codeIdentity"), item.get("name"))
                        kab_code = item.get("assignmentRegionCode", "")[:4]
                        kec_code = item.get("assignmentRegionCode", "")[:7]
                        
                        if kab_code not in kab_counts:
                            kab_counts[kab_code] = {"usaha": 0, "rumah": 0}
                        kab_counts[kab_code][jenis] += 1
                        
                        if kec_code not in kec_counts:
                            kec_counts[kec_code] = {"usaha": 0, "rumah": 0}
                        kec_counts[kec_code][jenis] += 1
            except Exception as e:
                print(f"Error reading {fpath}: {e}")
                
    return kab_counts, kec_counts

kab, kec = get_tambahan_counts()
print("Kab Counts:", kab)
