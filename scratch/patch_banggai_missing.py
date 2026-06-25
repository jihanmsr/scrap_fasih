import asyncio
import json
import os
import sys
import gzip
import base64
import httpx
from datetime import datetime
from playwright.async_api import async_playwright

# Setup paths to import from parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrape_granular_core import (
    get_authenticated_context,
    safe_post,
    fetch_targets_with_drilldown,
    parse_date_to_epoch,
    resolve_pcl_pml,
    DATATABLE_URL,
    region_map_full
)

SURVEY_PERIOD_ID = "fd68e454-ba45-4b85-8205-f3bf777ded24" # SE UMUM
REGION1_ID = "5214ecb2-bef1-4a86-9446-451cf430928e" # SULTENG

async def main():
    print("==============================================================")
    print("   Surgical Patch for Banggai (7202) Missing Targets")
    print("==============================================================")
    
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target_json_path = os.path.join(script_dir, "granular_assignments_se_umum_7202.json")
    
    if not os.path.exists(target_json_path):
        print(f"[ERROR] File {target_json_path} tidak ditemukan! Pastikan scrape granular Banggai selesai terlebih dahulu.")
        return
        
    print(f"[INFO] Memuat file partisi Banggai: {target_json_path}...")
    with open(target_json_path, "r", encoding="utf-8") as f:
        partition_data = json.load(f)
        
    compressed_data = partition_data.get("compressed_data")
    if not compressed_data:
        print("[ERROR] Data terkompresi tidak ditemukan di file JSON.")
        return
        
    print("[INFO] Mendekompresi data...")
    raw_json_str = gzip.decompress(base64.b64decode(compressed_data)).decode('utf-8')
    raw_payload = json.loads(raw_json_str)
    
    regions_list = raw_payload.get("regions", [])
    petugas_list = raw_payload.get("petugas", [])
    statuses_list = raw_payload.get("statuses", [])
    targets = raw_payload.get("targets", [])
    
    print(f"[INFO] Terbaca: {len(regions_list)} wilayah, {len(petugas_list)} petugas, {len(statuses_list)} status, {len(targets)} target.")
    
    # Load users_mapping.json
    users_mapping = {}
    users_mapping_path = os.path.join(script_dir, "users_mapping.json")
    if os.path.exists(users_mapping_path):
        with open(users_mapping_path, "r", encoding="utf-8") as f:
            users_mapping = json.load(f)
            
    # Mappings to reverse indices
    # regions_list item: [kab_code, kab_name, kec_code, kec_name, desa_code, desa_name, sls_code, sls_name, subsls_code, subsls_name]
    # Group existing targets by desa_code
    existing_by_desa = {} # desa_code -> list of target rows
    for t in targets:
        reg_idx = t[5]
        reg_info = regions_list[reg_idx]
        desa_code = reg_info[4]
        existing_by_desa.setdefault(desa_code, []).append(t)
        
    # Get all unique desas in Banggai from regions_list
    desas_in_partition = {} # desa_code -> (desa_name, desa_id, kec_name)
    # We find desa_id by matching against region_map_full
    kab_data = region_map_full.get("kabupaten", {}).get("7202", {})
    for kec_code, kec_data in kab_data.get("kecamatan", {}).items():
        kec_name = kec_data.get("kec_name")
        for desa_code, desa_data in kec_data.get("desa", {}).items():
            desa_name = desa_data.get("desa_name")
            desa_id = desa_data.get("desa_id")
            if desa_id:
                desas_in_partition[desa_code] = (desa_name, desa_id, kec_name)
                
    print(f"[INFO] Terdeteksi {len(desas_in_partition)} desa dari metadata regional Banggai.")
    
    # Connect to Playwright/Chrome
    async with async_playwright() as p:
        try:
            browser, context, page = await get_authenticated_context(p)
            print("[INFO] Browser Chromium berhasil dihubungkan.")
        except Exception as e:
            print(f"[ERROR] Gagal menghubungkan ke browser: {e}")
            return

        cookies = await context.cookies()
        cookie_dict = {c["name"]: c["value"] for c in cookies}
        token_raw = cookie_dict.get("XSRF-TOKEN", "")
        from urllib.parse import unquote
        token = unquote(token_raw) if token_raw else ""
        
        if not token:
            print("[ERROR] Sesi tidak ditemukan. Pastikan Anda sudah login di Chrome.")
            return
            
        sem = asyncio.Semaphore(5)
        limits = httpx.Limits(max_keepalive_connections=10, max_connections=20)
        
        async with httpx.AsyncClient(limits=limits, timeout=60.0) as client:
            client.headers.update({
                "Content-Type": "application/json",
                "X-XSRF-TOKEN": token,
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/json, text/plain, */*"
            })
            for c in cookies:
                client.cookies.set(
                    c['name'],
                    c['value'],
                    domain=c.get('domain', 'fasih-sm.bps.go.id'),
                    path=c.get('path', '/')
                )

            # Dictionary mappings for indices to help insert new targets
            regions_dict = {tuple(r): i for i, r in enumerate(regions_list)}
            petugas_dict = {tuple(p): i for i, p in enumerate(petugas_list)}
            statuses_dict = {s: i for i, s in enumerate(statuses_list)}
            
            def get_region_idx(comp, fallback_kab_name):
                region = comp.get("region", {})
                lvl1 = region.get("level1", {}) or {}
                lvl2 = lvl1.get("level2", {}) or {}
                lvl3 = lvl2.get("level3", {}) or {}
                lvl4 = lvl3.get("level4", {}) or {}
                lvl5 = lvl4.get("level5", {}) or {}
                lvl6 = lvl5.get("level6", {}) or {}
                
                kab_code = lvl2.get("fullCode") or ""
                kab_name = lvl2.get("name") or fallback_kab_name
                kec_code = lvl3.get("fullCode") or ""
                kec_name = lvl3.get("name") or "-"
                desa_code = lvl4.get("fullCode") or ""
                desa_name = lvl4.get("name") or "-"
                sls_code = lvl5.get("fullCode") or ""
                sls_name = lvl5.get("name") or "-"
                subsls_code = lvl6.get("fullCode") or ""
                subsls_name = lvl6.get("name") or "-"
                
                key = (kab_code, kab_name, kec_code, kec_name, desa_code, desa_name, sls_code, sls_name, subsls_code, subsls_name)
                if key not in regions_dict:
                    regions_dict[key] = len(regions_list)
                    regions_list.append(list(key))
                return regions_dict[key]
                
            def get_petugas_idx(username, fullname):
                if not username:
                    return -1
                key = (username, fullname or "-")
                if key not in petugas_dict:
                    petugas_dict[key] = len(petugas_list)
                    petugas_list.append(list(key))
                return petugas_dict[key]
                
            def get_status_idx(status):
                if not status:
                    status = "-"
                status_clean = status.strip().upper()
                if status_clean not in statuses_dict:
                    statuses_dict[status_clean] = len(statuses_list)
                    statuses_list.append(status_clean)
                return statuses_dict[status_clean]

            # We will gather totalHit from BPS API for each Desa to compare with local count
            print("\nMengecek kelengkapan data tiap desa di FASIH...", flush=True)
            
            incomplete_desas = []
            checked_count = 0
            
            for desa_code, (desa_name, desa_id, kec_name) in desas_in_partition.items():
                # Query 1 record to get totalHit
                payload = {
                    "start": 0, "length": 1, "columns": [{"data": "id"}], "order": [], "search": {"value": "", "regex": False},
                    "assignmentExtraParam": {
                        "region1Id": REGION1_ID, "surveyPeriodId": SURVEY_PERIOD_ID,
                        "assignmentErrorStatusType": -1, "filterTargetType": "", "region4Id": desa_id
                    }
                }
                
                res = await safe_post(client, page, context, sem, DATATABLE_URL, payload)
                if not res or "_error" in res:
                    print(f"  [ERROR] Gagal mengecek total untuk Desa {desa_name}. Skip.", flush=True)
                    continue
                    
                total_hits_api = res.get("totalHit", 0)
                local_count = len(existing_by_desa.get(desa_code, []))
                
                checked_count += 1
                if checked_count % 20 == 0 or checked_count == len(desas_in_partition):
                    print(f"  [CHECK PROGRESS] Sudah memeriksa {checked_count}/{len(desas_in_partition)} desa...", flush=True)
                
                # If local_count is less than BPS total_hits_api, or if we have exactly 1000 targets (often means truncated)
                if local_count < total_hits_api or (local_count == 1000 and total_hits_api > 1000):
                    print(f"  [PATCH] Desa {kec_name} -> {desa_name} [{desa_code}] incomplete: Lokal={local_count} vs FASIH={total_hits_api}", flush=True)
                    incomplete_desas.append((desa_code, desa_name, desa_id, kec_name, total_hits_api))
                else:
                    # print(f"  [OK] Desa {kec_name} -> {desa_name} complete: {local_count}/{total_hits_api}")
                    pass
                    
            print(f"\n[SUMMARY] Terdeteksi {len(incomplete_desas)} desa incomplete yang butuh di-patch.", flush=True)
            
            if not incomplete_desas:
                print("🎉 Semua desa sudah lengkap 100%! Tidak ada data yang perlu di-patch.", flush=True)
                return

            patched_targets = []
            # Keep copy of targets that do NOT belong to incomplete desas
            incomplete_desa_codes = {item[0] for item in incomplete_desas}
            for t in targets:
                reg_idx = t[5]
                reg_info = regions_list[reg_idx]
                desa_code = reg_info[4]
                if desa_code not in incomplete_desa_codes:
                    patched_targets.append(t)

            # Now, fetch complete targets for incomplete desas using SLS-based partitioning
            for idx, (desa_code, desa_name, desa_id, kec_name, total_hits_api) in enumerate(incomplete_desas):
                print(f"\n[{idx+1}/{len(incomplete_desas)}] Scraping Ulang Desa: {kec_name} -> {desa_name} ({total_hits_api} target)...", flush=True)
                
                new_records = await fetch_targets_with_drilldown(
                    client, page, context, sem,
                    SURVEY_PERIOD_ID, REGION1_ID,
                    4, desa_id, desa_code, desa_name, "SE Umum"
                )
                
                print(f"  -> Berhasil menarik {len(new_records)} target.", flush=True)
                
                # Format new records into compressed format and add
                for r in new_records:
                    tid = r.get("id")
                    code_id = r.get("codeIdentity")
                    name = r.get("data1") or "-"
                    status = r.get("assignmentStatusAlias") or "OPEN"
                    
                    responsibilities = r.get("assignmentResponsibility")
                    if responsibilities and isinstance(responsibilities, list):
                        for resp in responsibilities:
                            if resp.get("currentSurveyRoleName") == "Pencacah":
                                pcl_status = resp.get("assignmentResponsibilityStatusId")
                                if pcl_status and pcl_status.upper() == "SUBMITTED":
                                    if "Pengawas" in status or status.upper() == "APPROVED":
                                        status = "SUBMITTED BY Pencacah"
                                break
 
                    date_mod_str = r.get("dateModified")
                    epoch_mod = parse_date_to_epoch(date_mod_str)
                    
                    reg_idx = get_region_idx(r, "SULAWESI TENGAH")
                    stat_idx = get_status_idx(status)
                    
                    pcl_username, pcl_fullname, pml_username, pml_fullname = resolve_pcl_pml(r, users_mapping)
                    pet_idx = get_petugas_idx(pcl_username, pcl_fullname)
                    pengawas_idx = get_petugas_idx(pml_username, pml_fullname)
                    
                    # [tid, code_id, name, stat_idx, pet_idx, reg_idx, epoch_mod, survey_type, pengawas_idx]
                    patched_targets.append([
                        tid, code_id, name, stat_idx, pet_idx, reg_idx, epoch_mod, 0, pengawas_idx
                    ])

                # De-duplicate patched_targets by target ID progressively
                unique_targets = {}
                for t in patched_targets:
                    tid = t[0]
                    if tid not in unique_targets:
                        unique_targets[tid] = t
                    else:
                        # Keep the one with higher epoch_mod
                        if t[6] > unique_targets[tid][6]:
                            unique_targets[tid] = t
                final_targets = list(unique_targets.values())

                # Save back to partition file progressively so we don't lose work on crash/restart
                new_payload = {
                    "updated_at": datetime.now().isoformat(),
                    "regions": regions_list,
                    "petugas": petugas_list,
                    "statuses": statuses_list,
                    "targets": final_targets
                }
                
                raw_str = json.dumps(new_payload, ensure_ascii=False)
                compressed_bytes = gzip.compress(raw_str.encode('utf-8'))
                base64_str = base64.b64encode(compressed_bytes).decode('utf-8')
                
                with open(target_json_path, "w", encoding="utf-8") as f:
                    json.dump({
                        "compressed_data": base64_str, 
                        "updated_at": datetime.now().isoformat(),
                        "survey_type_filter": "se_umum",
                        "kab_code_filter": "7202"
                    }, f, indent=2)
                print(f"  [SAVE PROGRESS] Data berhasil disimpan secara progresif ke {target_json_path}", flush=True)

            # De-duplicate patched_targets by target ID (final)
            unique_targets = {}
            for t in patched_targets:
                tid = t[0]
                if tid not in unique_targets:
                    unique_targets[tid] = t
                else:
                    if t[6] > unique_targets[tid][6]:
                        unique_targets[tid] = t
            final_targets = list(unique_targets.values())
            print(f"\n[PATCH DONE] Total target final setelah di-patch: {len(final_targets)} (Sebelumnya: {len(targets)})", flush=True)
            
            # Save back to partition file (final write)
            new_payload = {
                "updated_at": datetime.now().isoformat(),
                "regions": regions_list,
                "petugas": petugas_list,
                "statuses": statuses_list,
                "targets": final_targets
            }
            
            raw_str = json.dumps(new_payload, ensure_ascii=False)
            compressed_bytes = gzip.compress(raw_str.encode('utf-8'))
            base64_str = base64.b64encode(compressed_bytes).decode('utf-8')
            
            with open(target_json_path, "w", encoding="utf-8") as f:
                json.dump({
                    "compressed_data": base64_str, 
                    "updated_at": datetime.now().isoformat(),
                    "survey_type_filter": "se_umum",
                    "kab_code_filter": "7202"
                }, f, indent=2)
            print(f"✅ Data hasil patch berhasil disimpan ke {target_json_path}")
            
            # Write JS fallback version
            js_out_filename = os.path.join(script_dir, "granular_assignments_se_umum_7202.js")
            with open(js_out_filename, "w", encoding="utf-8") as f:
                f.write("window.PARTITION_SE_UMUM_7202 = {\n")
                f.write(f"  \"compressed_data\": \"{base64_str}\",\n")
                f.write(f"  \"updated_at\": \"{datetime.now().isoformat()}\"\n")
                f.write("};\n")
            print(f"✅ Data JS hasil patch berhasil disimpan ke {js_out_filename}")
            
            # Call merge_granulars.py
            print("\nMemanggil merge_granulars.py untuk menggabungkan partisi...")
            import subprocess
            subprocess.run([sys.executable, os.path.join(script_dir, "merge_granulars.py")], cwd=script_dir)
            print("🎉 PATCHING BANGGAI & SINKRONISASI SELESAI!")

if __name__ == "__main__":
    asyncio.run(main())
