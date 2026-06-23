with open('scrape_granular_core.py', 'r', encoding='utf-8') as f:
    code = f.read()

import re

# Add loading users mapping
target = '''    print(f"[INFO] Token and cookies fetched. Current URL: {page.url}")'''

replacement = '''    print(f"[INFO] Token and cookies fetched. Current URL: {page.url}")
    users_mapping = {}
    import json
    try:
        with open("users_mapping.json", "r") as f:
            users_mapping = json.load(f)
    except:
        pass'''

if target in code:
    code = code.replace(target, replacement)
else:
    print("Failed to patch users mapping load!")

# Add extraction of pengawas
# In SE_UMUM loop
target_umum = '''        stat_idx = get_status_idx(status)
        
        compressed_targets.append([
            tid, code_id, name, stat_idx, pet_idx, reg_idx, epoch_mod, 0
        ])'''

replacement_umum = '''        stat_idx = get_status_idx(status)
        
        pengawas_id = None
        for resp in r.get("assignmentResponsibility", []):
            if resp.get("currentSurveyRoleName") == "Pengawas":
                pengawas_id = resp.get("currentUserId")
                break
        
        pengawas_username = "-"
        pengawas_fullname = "-"
        if pengawas_id and pengawas_id in users_mapping:
            pengawas_username = users_mapping[pengawas_id]["username"]
            pengawas_fullname = users_mapping[pengawas_id]["fullname"]
            
        pengawas_idx = get_petugas_idx(pengawas_username, pengawas_fullname)
        
        compressed_targets.append([
            tid, code_id, name, stat_idx, pet_idx, reg_idx, epoch_mod, 0, pengawas_idx
        ])'''

code = code.replace(target_umum, replacement_umum)

# In SE_UB loop
target_ub = '''        stat_idx = get_status_idx(status)
        
        compressed_targets.append([
            tid, code_id, name, stat_idx, pet_idx, reg_idx, epoch_mod, 1
        ])'''

replacement_ub = '''        stat_idx = get_status_idx(status)
        
        pengawas_id = None
        for resp in r.get("assignmentResponsibility", []):
            if resp.get("currentSurveyRoleName") == "Pengawas":
                pengawas_id = resp.get("currentUserId")
                break
        
        pengawas_username = "-"
        pengawas_fullname = "-"
        if pengawas_id and pengawas_id in users_mapping:
            pengawas_username = users_mapping[pengawas_id]["username"]
            pengawas_fullname = users_mapping[pengawas_id]["fullname"]
            
        pengawas_idx = get_petugas_idx(pengawas_username, pengawas_fullname)
        
        compressed_targets.append([
            tid, code_id, name, stat_idx, pet_idx, reg_idx, epoch_mod, 1, pengawas_idx
        ])'''

code = code.replace(target_ub, replacement_ub)

with open('scrape_granular_core.py', 'w', encoding='utf-8') as f:
    f.write(code)
print("Patched scrape_granular_core.py to extract Pengawas!")
