import json

with open("merge_granulars.py", "r") as f:
    code = f.read()

target1 = """    # Kumpulkan statistik untuk dashboard
    assign_umum = {}
    assign_ub = {"7200": {"kode_kab": "7200", "nama_kab": "SULAWESI TENGAH", "total": 0, "assigned": 0, "have_not_assigned": 0}}"""

replacement1 = """    # Kumpulkan statistik untuk dashboard
    assign_umum = {}
    assign_ub = {"7200": {"kode_kab": "7200", "nama_kab": "SULAWESI TENGAH", "total": 0, "assigned": 0, "have_not_assigned": 0, "timestamp": datetime.now().isoformat()}}"""

code = code.replace(target1, replacement1)

target2 = """    # Add timestamps
    now_str = datetime.now().isoformat()
    for v in assign_umum.values(): v["timestamp"] = now_str
    for v in assign_ub.values(): v["timestamp"] = now_str"""

replacement2 = """    # Add timestamps from files
    # We will find the updated_at from granular_assignments_*.json
    files = glob.glob("granular_assignments_se_umum_*.json")
    for fpath in files:
        try:
            kab_code = fpath.split("_")[-1].split(".")[0]
            with open(fpath, "r") as f:
                d = json.load(f)
                up_at = d.get("updated_at")
                if up_at and kab_code in assign_umum:
                    assign_umum[kab_code]["timestamp"] = up_at
        except:
            pass
            
    files_ub = glob.glob("granular_assignments_se_ub_*.json")
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
            v["timestamp"] = now_str"""

code = code.replace(target2, replacement2)

with open("merge_granulars.py", "w") as f:
    f.write(code)
print("Patched merge_granulars.py!")
