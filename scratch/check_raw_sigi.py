import json
import base64
import gzip

def check_raw_sigi_for_user():
    # Load users_mapping
    with open("users_mapping.json", "r", encoding="utf-8") as f:
        umap = json.load(f)
        
    uid = "2884299b-a139-4d38-bb33-2558673b733b"
    print(f"Checking for user ID: {uid} (igunmoh@gmail.com)")
    
    with open("granular_assignments_se_umum_7210.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    comp = data.get("compressed_data")
    raw = json.loads(gzip.decompress(base64.b64decode(comp)).decode('utf-8'))
    
    petugas = raw.get("petugas", [])
    print(f"Petugas list size in Sigi partition: {len(petugas)}")
    
    # Check if igunmoh is in petugas
    igun_petugas = [p for p in petugas if "igun" in p[0].lower()]
    print(f"Any petugas matching 'igun' in Sigi: {igun_petugas}")
    
    # Check all target records in partition to see if they reference this user ID
    # Note: partition has t = [tid, code_id, name, stat_idx, pet_idx, reg_idx, epoch_mod, 0, pengawas_idx]
    # But wait, in the raw partition before merge, does it have user IDs or indices?
    # Let's check keys of raw
    print("Raw keys:", list(raw.keys()))
    
if __name__ == "__main__":
    check_raw_sigi_for_user()
