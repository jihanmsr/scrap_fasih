import subprocess
import json
import asyncio
import asyncio as _asyncio
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
    import sqlite3
    import re
    import os
    kab_counts = {}
    kec_counts = {}
    db_path = '/Users/jihanmaisaroh/scrap_fasih/granular_data.db'
    if not os.path.exists(db_path): return kab_counts, kec_counts
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT kabupaten, kecamatan, is_usaha FROM granular_records WHERE is_tambahan=1")
        rows = c.fetchall()
        for row in rows:
            kab_raw = row[0]
            kec_raw = row[1].upper().strip()
            is_usaha = row[2]
            
            kab_clean = re.sub(r'\[\d+\]', '', kab_raw).replace('[','').replace(']','').strip()
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
        conn.close()
    except Exception as e:
        print(f"DB Error: {e}")
    return kab_counts, kec_counts

import os
import sys

import datetime
import re
import socket
from urllib.parse import unquote
from playwright.async_api import async_playwright

from scrape_granular_core import get_authenticated_context, SURVEY_CONFIGS, region_map_full

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

def load_local_ipas_data():
    filepath = "ipas_data.js"
    if not os.path.exists(filepath):
        return None
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        pattern = re.compile(r'window\.IPAS_DATA\s*=\s*(\{.*?\});', re.DOTALL)
        match = pattern.search(content)
        if match:
            return json.loads(match.group(1))
    except Exception as e:
        print(f"[ERROR] Gagal memuat ipas_data.js lokal: {e}")
    return None

def get_bd_val(breakdown, key):
    if not breakdown:
        return 0
    key_upper = key.upper()
    for k, v in breakdown.items():
        if k.upper() == key_upper:
            return v
    return 0

def process_survey_type_data(survey_type, old_data, results_map, region_map_sulteng, delta_days):
    new_data = []
    region_kabupaten = region_map_sulteng.get("kabupaten", {})
    
    for prev_kab in old_data:
        kab_name = prev_kab.get("kabupaten")
        
        # Find region code for this kabupaten
        wilayah_code = None
        for code, name in KAB_MAPPING.items():
            if name == kab_name:
                wilayah_code = code
                break
                
        if not wilayah_code or wilayah_code not in results_map:
            # If no API results for this kabupaten, keep the old object
            new_data.append(prev_kab)
            continue
            
        kec_list = results_map[wilayah_code]
        
        # SAFETY CHECK: If kec_list is empty but we previously had data, KEEP the old data!
        if not kec_list and prev_kab.get("total_prelist", 0) > 0:
            print(f"  [WARNING] API return kosong untuk {kab_name}. Menggunakan data kemarin.")
            new_data.append(prev_kab)
            continue
            
        region_kab_info = region_kabupaten.get(wilayah_code, {})
        
        # Initialize and build the kecamatan list from the region map
        region_kecamatans = region_kab_info.get("kecamatan", {})
        kec_data_map = {}
        for k_code, k_info in region_kecamatans.items():
            name = k_info.get("kec_name", "-")
            if name == "-":
                continue
            short_code = k_code[-3:]
            formatted_name = f"[{short_code}] {name.upper()}"
            kec_data_map[k_code] = {
                "kecamatan": formatted_name,
                "kec_name": formatted_name,
                "total_prelist": 0,
                "total_draft": 0,
                "total_open": 0,
                "total_submitted": 0,
                "total_rejected": 0,
                "total_approved": 0,
                "total_submitted_pencacah": 0,
                "total_submitted_respondent": 0,
                "persentase": 0.0,
                "today_completed": 0,
                "today_completed_breakdown": {},
                "yesterday_completed": 0,
                "yesterday_completed_breakdown": {},
                "two_days_ago_completed": 0,
                "two_days_ago_completed_breakdown": {},
                "breakdown": {}
            }
            
        kab_totals = {
            "total_prelist": 0,
            "total_draft": 0,
            "total_open": 0,
            "total_submitted": 0,
            "total_rejected": 0,
            "total_approved": 0,
            "total_submitted_pencacah": 0,
            "total_submitted_respondent": 0
        }
        
        for kec_item in kec_list:
            kec_code = kec_item.get("label")
            values = kec_item.get("values", [])
            
            val_map = {v.get("label"): v.get("value", 0) for v in values}
            
            draft = val_map.get("DRAFT", 0)
            open_val = val_map.get("OPEN", 0)
            
            submitted_pencacah = (
                val_map.get("SUBMITTED BY Pencacah", 0) + 
                val_map.get("EDITED BY Admin Kabupaten", 0) + 
                val_map.get("EDITED BY Pengawas", 0) + 
                val_map.get("COMPLETED BY Admin Kabupaten", 0)
            )
            submitted_respondent = val_map.get("SUBMITTED RESPONDENT", 0)
            approved = val_map.get("APPROVED BY Pengawas", 0)
            rejected = (
                val_map.get("REJECTED BY Pengawas", 0) + 
                val_map.get("REVOKED BY Pengawas", 0) + 
                val_map.get("REJECTED BY Admin Kabupaten", 0)
            )
            
            total_submitted = submitted_pencacah + submitted_respondent + approved + rejected
            total_prelist = draft + open_val + total_submitted
            persentase = round((total_submitted / total_prelist * 100), 2) if total_prelist > 0 else 0.0
            
            if kec_code in kec_data_map:
                kec_data_map[kec_code].update({
                    "total_prelist": total_prelist,
                    "total_draft": draft,
                    "total_open": open_val,
                    "total_submitted": total_submitted,
                    "total_rejected": rejected,
                    "total_approved": approved,
                    "total_submitted_pencacah": submitted_pencacah,
                    "total_submitted_respondent": submitted_respondent,
                    "persentase": persentase,
                    "breakdown": val_map
                })
            else:
                kec_info = region_kecamatans.get(kec_code, {})
                name = kec_info.get("kec_name") or "-"
                if name == "-" and len(kec_code) >= 7:
                    if total_prelist == 0:
                        continue
                short_code = kec_code[-3:] if len(kec_code) >= 3 else kec_code
                formatted_name = f"[{short_code}] {name.upper()}"
                kec_data_map[kec_code] = {
                    "kecamatan": formatted_name,
                    "kec_name": formatted_name,
                    "total_prelist": total_prelist,
                    "total_draft": draft,
                    "total_open": open_val,
                    "total_submitted": total_submitted,
                    "total_rejected": rejected,
                    "total_approved": approved,
                    "total_submitted_pencacah": submitted_pencacah,
                    "total_submitted_respondent": submitted_respondent,
                    "persentase": persentase,
                    "today_completed": 0,
                    "today_completed_breakdown": {},
                    "yesterday_completed": 0,
                    "yesterday_completed_breakdown": {},
                    "two_days_ago_completed": 0,
                    "two_days_ago_completed_breakdown": {},
                    "breakdown": val_map
                }
                
            # Accumulate to kab_totals
            kab_totals["total_prelist"] += total_prelist
            kab_totals["total_draft"] += draft
            kab_totals["total_open"] += open_val
            kab_totals["total_submitted"] += total_submitted
            kab_totals["total_rejected"] += rejected
            kab_totals["total_approved"] += approved
            kab_totals["total_submitted_pencacah"] += submitted_pencacah
            kab_totals["total_submitted_respondent"] += submitted_respondent
            
        # Convert map to list and sort alphabetically by kecamatan name
        kec_list_final = sorted(kec_data_map.values(), key=lambda x: x["kecamatan"])
        
        # Process delta trackers for each kecamatan
        prev_kec_list = prev_kab.get("kecamatan_list", [])
        prev_kec_map = {k.get("kecamatan"): k for k in prev_kec_list}
        
        for curr_kec in kec_list_final:
            kec_name = curr_kec["kecamatan"]
            prev_kec = prev_kec_map.get(kec_name, {})
            
            if delta_days == 0:
                curr_kec["yesterday_completed"] = prev_kec.get("yesterday_completed", 0)
                curr_kec["yesterday_completed_breakdown"] = prev_kec.get("yesterday_completed_breakdown", {})
                curr_kec["two_days_ago_completed"] = prev_kec.get("two_days_ago_completed", 0)
                curr_kec["two_days_ago_completed_breakdown"] = prev_kec.get("two_days_ago_completed_breakdown", {})
                
                b_submitted = prev_kec.get("total_submitted", 0) - prev_kec.get("today_completed", 0)
                b_approved = prev_kec.get("total_approved", 0) - get_bd_val(prev_kec.get("today_completed_breakdown"), "APPROVED BY PENGAWAS")
                b_rejected = prev_kec.get("total_rejected", 0) - get_bd_val(prev_kec.get("today_completed_breakdown"), "REJECTED BY PENGAWAS")
                b_pencacah = prev_kec.get("total_submitted_pencacah", 0) - get_bd_val(prev_kec.get("today_completed_breakdown"), "SUBMITTED BY PENCACAH")
                b_respondent = prev_kec.get("total_submitted_respondent", 0) - get_bd_val(prev_kec.get("today_completed_breakdown"), "SUBMITTED RESPONDENT")
            else:
                if delta_days == 1:
                    curr_kec["two_days_ago_completed"] = prev_kec.get("yesterday_completed", 0)
                    curr_kec["two_days_ago_completed_breakdown"] = prev_kec.get("yesterday_completed_breakdown", {})
                    curr_kec["yesterday_completed"] = prev_kec.get("today_completed", 0)
                    curr_kec["yesterday_completed_breakdown"] = prev_kec.get("today_completed_breakdown", {})
                elif delta_days == 2:
                    curr_kec["two_days_ago_completed"] = prev_kec.get("today_completed", 0)
                    curr_kec["two_days_ago_completed_breakdown"] = prev_kec.get("today_completed_breakdown", {})
                    curr_kec["yesterday_completed"] = 0
                    curr_kec["yesterday_completed_breakdown"] = {}
                else:
                    curr_kec["two_days_ago_completed"] = 0
                    curr_kec["two_days_ago_completed_breakdown"] = {}
                    curr_kec["yesterday_completed"] = 0
                    curr_kec["yesterday_completed_breakdown"] = {}
                    
                b_submitted = prev_kec.get("total_submitted", 0)
                b_approved = prev_kec.get("total_approved", 0)
                b_rejected = prev_kec.get("total_rejected", 0)
                b_pencacah = prev_kec.get("total_submitted_pencacah", 0)
                b_respondent = prev_kec.get("total_submitted_respondent", 0)
                
            today_comp_kec = max(0, curr_kec["total_submitted"] - b_submitted)
            today_bd_kec = {}
            
            inc_appr_kec = max(0, curr_kec["total_approved"] - b_approved)
            if inc_appr_kec > 0: today_bd_kec["APPROVED BY PENGAWAS"] = inc_appr_kec
                
            inc_rej_kec = max(0, curr_kec["total_rejected"] - b_rejected)
            if inc_rej_kec > 0: today_bd_kec["REJECTED BY PENGAWAS"] = inc_rej_kec
                
            inc_penc_kec = max(0, curr_kec["total_submitted_pencacah"] - b_pencacah)
            if inc_penc_kec > 0: today_bd_kec["SUBMITTED BY PENCACAH"] = inc_penc_kec
                
            inc_resp_kec = max(0, curr_kec["total_submitted_respondent"] - b_respondent)
            if inc_resp_kec > 0: today_bd_kec["SUBMITTED RESPONDENT"] = inc_resp_kec
                
            curr_kec["today_completed"] = today_comp_kec
            curr_kec["today_completed_breakdown"] = today_bd_kec

        # Sum breakdowns for kabupaten
        kab_breakdown = {}
        for k_code, k_obj in kec_data_map.items():
            if "breakdown" in k_obj:
                for k, v in k_obj["breakdown"].items():
                    kab_breakdown[k] = kab_breakdown.get(k, 0) + v
        
        # Calculate totals for kabupaten
        total_prelist = kab_totals["total_prelist"]
        draft = kab_totals["total_draft"]
        open_val = kab_totals["total_open"]
        total_submitted = kab_totals["total_submitted"]
        rejected = kab_totals["total_rejected"]
        approved = kab_totals["total_approved"]
        submitted_pencacah = kab_totals["total_submitted_pencacah"]
        submitted_respondent = kab_totals["total_submitted_respondent"]
        persentase = round((total_submitted / total_prelist * 100), 2) if total_prelist > 0 else 0.0
        
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
            "kecamatan_list": kec_list_final,
            "breakdown": kab_breakdown
        }
        
        # Calculate daily delta_days completed counters
        if delta_days == 0:
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
        
        new_data.append(kab_obj)
        print(f" -> [{survey_type}] {kab_name}: target={total_prelist}, submitted={total_submitted}, today_completed={today_comp}")
        
    return new_data

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

async def run_download_and_update():
    async with async_playwright() as p:
        browser, context, page = await get_authenticated_context(p)
        if not page:
            print("[ERROR] Browser Chrome aktif tidak ditemukan. Harap pastikan Chrome berjalan dengan remote debugging port (9222) dan Anda sudah login ke FASIH.")
            return
            
        current_url = page.url
        if "fasih-sm.bps.go.id/app" not in current_url:
            print(f"[WARNING] Page aktif bukan Dashboard FASIH ({current_url}). Mencari tab FASIH lain...")
            fasih_page = None
            # Prioritize /app/ tab first
            for pg in context.pages:
                if "fasih-sm.bps.go.id/app" in pg.url:
                    fasih_page = pg
                    break
            
            # Fallback to any tab with fasih-sm.bps.go.id
            if not fasih_page:
                for pg in context.pages:
                    if "fasih-sm.bps.go.id" in pg.url:
                        fasih_page = pg
                        break

            if fasih_page:
                page = fasih_page
                await page.bring_to_front()
                print(f"[INFO] Menggunakan tab FASIH: {page.url}")
            else:
                print("[INFO] Tidak ada tab FASIH aktif. Menavigasi ke FASIH untuk menggunakan sesi yang ada...")
                await page.goto("https://fasih-sm.bps.go.id/app/auth/login?redirect_to=https://fasih-sm.bps.go.id/app/surveys", timeout=60000)
                import asyncio as _asyncio
                await _asyncio.sleep(5)
                print(f"[INFO] Halaman sekarang: {page.url}")
                
        print("Koneksi berhasil. Mengambil XSRF-TOKEN...")
        cookies = await context.cookies()
        token_raw = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), "")
        token = unquote(token_raw) if token_raw else ""
        
        if not token or "login" in page.url.lower():
            print("[WARNING] Anda belum login atau sesi expired!")
            print("=========================================================================")
            print("  Silakan pindah ke jendela Chrome dan lakukan LOGIN secara manual.")
            print("  Skrip ini akan otomatis menunggu sampai Anda berhasil masuk (maks 2 menit)...")
            print("=========================================================================")
            try:
                import asyncio as _asyncio
                await page.wait_for_url("**/app/surveys**", timeout=120000)
                await _asyncio.sleep(5)
                # re-fetch cookies after login
                cookies = await context.cookies()
                token_raw = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), "")
                token = unquote(token_raw) if token_raw else ""
            except Exception as e:
                print("[ERROR] Waktu login habis (2 menit) atau halaman ditutup. Silakan ulangi.")
                if browser: await browser.close()
                return

        if not token:
            print("[ERROR] Gagal mendapatkan token setelah login. Menghentikan skrip.")
            if browser: await browser.close()
            return
            
        # Inisialisasi Supabase
        env = load_env()
        supabase_url = env.get("SUPABASE_URL")
        supabase_key = env.get("SUPABASE_KEY")
        
        supabase = None
        if supabase_url and supabase_key:
            try:
                from supabase import create_client
                supabase = create_client(supabase_url, supabase_key)
            except Exception as e:
                print(f"[ERROR] Gagal inisialisasi Supabase: {e}")
                
        # Load current ipas_data
        current_ipas = None
        if supabase:
            try:
                res = supabase.table("dashboard_store").select("value").eq("key", "ipas_data").execute()
                if res.data:
                    current_ipas = res.data[0]['value']

                    if isinstance(current_ipas, str):
                        current_ipas = json.loads(current_ipas)
            except Exception as e:
                print(f"[WARNING] Gagal mengambil ipas_data dari Supabase: {e}")
                
        if not current_ipas:
            current_ipas = load_local_ipas_data()
            
        if not current_ipas:
            print("[ERROR] Gagal memuat data IPAS lama.")
            await browser.close()
            return
            
        # Date Calculations (WITA)
        local_tz = datetime.timezone(datetime.timedelta(hours=8))
        now = datetime.datetime.now(local_tz)
        now_iso = now.strftime("%Y-%m-%dT%H:%M:%S+08:00")
        now_date_str = now.strftime("%Y-%m-%d")
        
        prev_updated_at = current_ipas.get("updated_at", "")
        prev_date_str = prev_updated_at[:10] if prev_updated_at else now_date_str
        
        try:
            prev_date = datetime.datetime.strptime(prev_date_str, "%Y-%m-%d").date()
        except Exception:
            prev_date = now.date()
            
        delta_days = 1
        
        print(f"[INFO] Tanggal saat ini (WITA): {now_date_str}. Tanggal update terakhir: {prev_date_str}. Selisih: {delta_days} hari.")

        url = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/report-progress-assignment"
        
        compiled_results = {} # survey_type -> kab_code -> kec_list
        
        # Batch query all 13 kabupaten for both se_umum and se_ub
        for config in SURVEY_CONFIGS:
            label = config["label"]
            survey_period_id = config["survey_period_id"]
            region1_id = config["region1_id"]
            kab_map = config["kab_region_map"]
            
            print(f"\n[INFO] Mengambil progress assignment untuk {label} dari API BPS...")
            payloads = []
            kab_ordered_codes = sorted(kab_map.keys())
            
            for code in kab_ordered_codes:
                kab_info = kab_map[code]
                payloads.append({
                    "surveyPeriodId": survey_period_id,
                    "assignmentStatusAlias": None,
                    "assignmentErrorStatusType": -1,
                    "data1": None, "data2": None, "data3": None, "data4": None, "data5": None,
                    "data6": None, "data7": None, "data8": None, "data9": None, "data10": None,
                    "regionId": None,
                    "region1Id": region1_id,
                    "region2Id": kab_info["id"],
                    "currentUserId": None,
                    "userIdResponsibility": None
                })
                           
            import httpx
            
            cookie_dict = {c["name"]: c["value"] for c in cookies}
            results = []
            
            
            headers = {
                "Accept": "*/*",
                "Accept-Language": "en-US,en;q=0.9,id-ID;q=0.8,id;q=0.7",
                "Content-Type": "application/json",
                "Origin": "https://fasih-sm.bps.go.id",
                "Priority": "u=1, i",
                "Referer": "https://fasih-sm.bps.go.id/app/surveys/a0429e96-51a5-477b-a415-485f9c153004/fd68e454-ba45-4b85-8205-f3bf777ded24",
                "Sec-Ch-Ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
                "Sec-Ch-Ua-Mobile": "?0",
                "Sec-Ch-Ua-Platform": '"macOS"',
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
                "X-Requested-With": "XMLHttpRequest",
                "x-xsrf-token": token
            }
            async with httpx.AsyncClient(cookies=cookie_dict, timeout=httpx.Timeout(60.0)) as client:
                for payload in payloads:
                    retries = 0
                    max_retries = 10
                    kab_data = None
                    while retries < max_retries:
                        try:
                            headers["x-xsrf-token"] = token
                            payload_str = json.dumps(payload, separators=(',', ':'))
                            r = await client.post(
                                url,
                                content=payload_str,
                                headers=headers
                            )
                            if r.status_code != 200:
                                raise Exception(f"HTTP {r.status_code} - {r.text[:50]}")
                            
                            kab_data = r.json()
                            break # Success!
                        except Exception as e:
                            retries += 1
                            print(f"  [ERROR] Gagal ambil data kabupaten (Percobaan {retries}/{max_retries}): {e}")
                            print("  [INFO] Terdeteksi blokir F5 WAF. Memuat ulang cookie...")
                            try:
                                await page.reload(wait_until="networkidle")
                                new_cookies = await page.context.cookies()
                                cookie_dict = {c["name"]: c["value"] for c in new_cookies}
                                client.cookies.update(cookie_dict)
                                for c in new_cookies:
                                    if c["name"] == "XSRF-TOKEN":
                                        token = unquote(c["value"])
                                        break
                                print("  [INFO] Token baru berhasil didapatkan!")
                            except Exception as refr_e:
                                print(f"  [ERROR] Gagal refresh: {refr_e}")
                            await asyncio.sleep(5)
                            
                    if kab_data:
                        results.append(kab_data)
                    else:
                        results.append({"error": "Gagal total setelah retries."})
            
            # Map results to compiled dict
            compiled_results[label] = {}
            for code, res in zip(kab_ordered_codes, results):
                if isinstance(res, dict) and "error" in res:
                    print(f"  [ERROR] Gagal mengambil data kabupaten {code}: {res['error']}")
                elif isinstance(res, list):
                    # Direct list of kecamatan objects
                    compiled_results[label][code] = res
                elif isinstance(res, dict) and "data" in res:
                    compiled_results[label][code] = res.get("data", [])
                else:
                    print(f"  [WARNING] Response tidak dikenal untuk kabupaten {code}: {res}")
                    compiled_results[label][code] = []
        if browser:
            await browser.close()
        
        print("\nMemulai pemrosesan data...")
        new_se_umum = process_survey_type_data("se_umum", current_ipas.get("se_umum", []), compiled_results["se_umum"], region_map_full, delta_days)
        new_se_ub = process_survey_type_data("se_ub", current_ipas.get("se_ub", []), compiled_results["se_ub"], region_map_full, delta_days)
        
        # Calculate provincial totals
        prov_se_umum_prelist = sum(k.get("total_prelist", 0) for k in new_se_umum)
        prov_se_ub_prelist = sum(k.get("total_prelist", 0) for k in new_se_ub)
        
        prov_se_umum_new = sum(k.get("new_usaha_overall", 0) for k in new_se_umum)
        prov_se_umum_new_rumah = sum(k.get("new_rumah_overall", 0) for k in new_se_umum)
        
        prov_se_ub_new = sum(k.get("new_usaha_overall", 0) for k in new_se_ub)
        prov_se_ub_new_rumah = sum(k.get("new_rumah_overall", 0) for k in new_se_ub)
        
        # Injeksi Delta dari Excel
        # --- AUTOMATIC DELTA CALCULATION ---
        try:
            def apply_auto_delta(survey_data):
                for kab in survey_data:
                    today_comp = kab.get("today_completed", 0)
                    yesterday_comp = kab.get("yesterday_completed", 0)
                    lusa_comp = kab.get("two_days_ago_completed", 0)
                    total_prelist = kab.get("total_prelist", 0)
                    if total_prelist > 0:
                        kab["delta_persen"] = round((today_comp / total_prelist) * 100, 2)
                        kab["delta_kemarin_persen"] = round((yesterday_comp / total_prelist) * 100, 2)
                        kab["delta_lusa_persen"] = round((lusa_comp / total_prelist) * 100, 2)
                    else:
                        kab["delta_persen"] = 0.0
                        kab["delta_kemarin_persen"] = 0.0
                        kab["delta_lusa_persen"] = 0.0
                    
                    for kec in kab.get("kecamatan_list", []):
                        k_today = kec.get("today_completed", 0)
                        k_yest = kec.get("yesterday_completed", 0)
                        k_lusa = kec.get("two_days_ago_completed", 0)
                        k_total = kec.get("total_prelist", 0)
                        
                        if k_total > 0:
                            kec["delta_persen"] = round((k_today / k_total) * 100, 2)
                            kec["delta_kemarin_persen"] = round((k_yest / k_total) * 100, 2)
                            kec["delta_lusa_persen"] = round((k_lusa / k_total) * 100, 2)
                        else:
                            kec["delta_persen"] = 0.0
                            kec["delta_kemarin_persen"] = 0.0
                            kec["delta_lusa_persen"] = 0.0
            
            apply_auto_delta(new_se_umum)
            apply_auto_delta(new_se_ub)
            print(" ✅ Berhasil menghitung delta harian secara otomatis dari data FASIH.")
        except Exception as e:
            print(f" [WARNING] Gagal menghitung delta otomatis: {e}")

        # --- INJECT REAL TAMBAHAN FROM GRANULAR DB ---
        kab_counts, kec_counts = get_real_tambahan()
        import re
        for kab in new_se_umum:
            kab_clean = re.sub(r'\[\d+\]', '', kab["kabupaten"]).replace('[','').replace(']','').strip()
            kab_clean = " ".join([w for w in kab_clean.split() if not (w.isdigit() or w.startswith("72"))]).upper().strip()
            kab["new_usaha_overall"] = kab_counts.get(kab_clean, {}).get("usaha", 0)
            kab["new_rumah_overall"] = kab_counts.get(kab_clean, {}).get("rumah", 0)
            
            for kec in kab.get("kecamatan_list", []):
                kec_name = kec.get("kec_name", "").upper().strip()
                kec_name_clean = re.sub(r'\[\d+\]', '', kec_name).replace('[','').replace(']','').strip()
                kec_key = f"{kab_clean}_{kec_name_clean}"
                kec["new_usaha_overall"] = kec_counts.get(kec_key, {}).get("usaha", 0)
                kec["new_rumah_overall"] = kec_counts.get(kec_key, {}).get("rumah", 0)
                
        prov_se_umum_new = sum(k.get("new_usaha_overall", 0) for k in new_se_umum)
        prov_se_umum_new_rumah = sum(k.get("new_rumah_overall", 0) for k in new_se_umum)
        
        final_js_obj = {
            "updated_at": now_iso,
            "se_umum": new_se_umum,
            "se_ub": new_se_ub,
            "se_umum_sls_status": current_ipas.get("se_umum_sls_status", {}),
            "se_ub_sls_status": current_ipas.get("se_ub_sls_status", {}),
            "se_umum_prov_total": prov_se_umum_prelist,
            "se_ub_prov_total": prov_se_ub_prelist,
            "se_umum_prov_new_total": prov_se_umum_new,
            "se_ub_prov_new_total": prov_se_ub_new,
            "se_umum_prov_new_rumah_total": prov_se_umum_new_rumah,
            "se_ub_prov_new_rumah_total": prov_se_ub_new_rumah
        }
        
        # Write local JS
        with open("ipas_data.js", "w", encoding="utf-8") as f:
            f.write(f"window.IPAS_DATA = {json.dumps(final_js_obj, ensure_ascii=False, indent=2)};\n")
        print(" ✅ File lokal ipas_data.js berhasil diperbarui.")
        
        try:
            import sqlite3
            db_p = '/Users/jihanmaisaroh/scrap_fasih/granular_data.db'
            if os.path.exists(db_p):
                cn = sqlite3.connect(db_p)
                cr = cn.cursor()
                cr.execute("SELECT tanggal, kabupaten, total_aktivitas, total_submitted, total_approved, total_rejected, total_usaha_tambahan FROM daily_summary ORDER BY tanggal ASC, kabupaten ASC")
                rows = cr.fetchall()
                data = [{"tanggal": r[0], "kabupaten": r[1], "total_aktivitas": r[2], "total_submitted": r[3], "total_approved": r[4], "total_rejected": r[5], "total_usaha_tambahan": r[6]} for r in rows]
                cn.close()
                with open("daily_summary.js", "w", encoding="utf-8") as fw:
                    fw.write(f"window.DAILY_SUMMARY = {json.dumps(data, indent=2)};\n")
                print(" ✅ File lokal daily_summary.js berhasil diperbarui.")
        except Exception as e:
            print(f" [WARNING] Gagal update daily_summary.js: {e}")
        
        if supabase:
            try:
                supabase.table("dashboard_store").upsert({"key": "ipas_data", "value": final_js_obj}).execute()
                print(" ✅ Berhasil mengunggah data ke Supabase.")
                
                daily_key = f"ipas_data:{now_date_str}"
                supabase.table("dashboard_store").upsert({"key": daily_key, "value": final_js_obj}).execute()
                print(f" ✅ Berhasil mengunggah data harian ({daily_key}) ke Supabase.")
                
                reconstruct_daily_stats_in_db(supabase)
            except Exception as e:
                print(f"[ERROR] Gagal mengunggah data ke Supabase: {e}")
                
        
        # Auto-push ke GitHub agar Vercel otomatis update
        print("\n🚀 Mengunggah data terbaru ke GitHub untuk update Vercel...")
        try:
            subprocess.run(["git", "add", "ipas_data.js", "daily_summary.js", "fast_master_assign_sls.js", "fast_petugas_progress.js", "fast_petugas_history.js", "petugas_region_map.js"], check=True)
            subprocess.run(["git", "commit", "-m", "Auto-update data dari scraper"], check=True)
            subprocess.run(["git", "push", "origin", "main"], check=True)
            print("✅ Berhasil push ke GitHub! Website Vercel akan otomatis terupdate dalam ~30 detik.")
        except Exception as e:
            print(f"⚠️ Gagal push ke GitHub (Mungkin tidak ada perubahan data atau error git): {e}")
            
        print("\n🎉 PEMBARUAN DASHBOARD SELESAI SECARA INSTAN!")


if __name__ == "__main__":
    asyncio.run(run_download_and_update())
