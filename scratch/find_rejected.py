import json
import gzip
import base64

def main():
    try:
        with open("granular_assignments.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            
        compressed = data["compressed_data"]
        raw_json_str = gzip.decompress(base64.b64decode(compressed)).decode('utf-8')
        payload = json.loads(raw_json_str)
        
        statuses = payload["regions"] # Wait, let's verify keys: regions, petugas, statuses, targets
        print("Keys:", list(payload.keys()))
        
        statuses = payload.get("statuses", [])
        print("Statuses:", statuses)
        
        # Find index for REJECTED and REVOKED
        rejected_indices = [i for i, s in enumerate(statuses) if "REJECT" in s or "REVOK" in s]
        print("Rejected/Revoked Indices:", [(i, statuses[i]) for i in rejected_indices])
        
        targets = payload.get("targets", [])
        print(f"Total targets: {len(targets)}")
        
        rejected_targets = []
        for t in targets:
            # target structure: [tid, code_id, name, stat_idx, pet_idx, reg_idx, epoch_mod, survey_type]
            stat_idx = t[3]
            if stat_idx in rejected_indices:
                rejected_targets.append(t)
                
        print(f"Total rejected/revoked targets: {len(rejected_targets)}")
        if rejected_targets:
            print("Sample rejected/revoked targets:")
            for t in rejected_targets[:10]:
                print(f"ID: {t[0]}, Code: {t[1]}, Name: {t[2]}, Status: {statuses[t[3]]}")
                
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
