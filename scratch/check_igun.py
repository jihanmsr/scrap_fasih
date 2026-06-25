import json
import base64
import gzip

def check_igun():
    with open("granular_assignments.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    comp = data.get("compressed_data")
    raw = json.loads(gzip.decompress(base64.b64decode(comp)).decode('utf-8'))
    
    petugas = raw.get("petugas", [])
    targets = raw.get("targets", [])
    statuses = raw.get("statuses", [])
    regions = raw.get("regions", [])
    
    # Find index of igunmoh@gmail.com in petugas
    igun_indices = [i for i, p in enumerate(petugas) if p[0] == "igunmoh@gmail.com"]
    print(f"Igun email index in petugas: {igun_indices}")
    
    if not igun_indices:
        print("igunmoh@gmail.com not found in petugas master list!")
        return
        
    igun_idx = igun_indices[0]
    
    # Filter targets for igun_idx
    igun_targets = []
    for t in targets:
        # t = [tid, code_id, name, stat_idx, pet_idx, reg_idx, epoch_mod, survey_flag, pengawas_idx]
        if t[4] == igun_idx:
            igun_targets.append(t)
            
    print(f"Total targets for igunmoh@gmail.com: {len(igun_targets)}")
    for t in igun_targets[:20]:
        status = statuses[t[3]]
        reg = regions[t[5]]
        print(f"  Target Code: {t[1]} | Name: {t[2]} | Status: {status} | Reg: {reg[1]}/{reg[3]}/{reg[5]}")

if __name__ == "__main__":
    check_igun()
