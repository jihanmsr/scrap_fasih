import json
import base64
import gzip
import glob
import os

def search_all_partitions():
    files = glob.glob("granular_assignments_se_umum_*.json")
    print(f"Searching {len(files)} partitions...")
    
    for fpath in files:
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        comp = data.get("compressed_data")
        raw = json.loads(gzip.decompress(base64.b64decode(comp)).decode('utf-8'))
        
        petugas = raw.get("petugas", [])
        for p_idx, p in enumerate(petugas):
            if "igun" in p[0].lower():
                print(f"Found in {fpath}: index {p_idx} -> {p}")
                
if __name__ == "__main__":
    search_all_partitions()
