import json
import gzip
import base64
import re

def main():
    with open('assign_data.js', 'r', encoding='utf-8') as f:
        assign_content = f.read()

    # Load window.PETUGAS_DATA_UMUM
    start_match = re.search(r'window\.PETUGAS_DATA_UMUM\s*=\s*\[', assign_content)
    petugas_umum = []
    if start_match:
        start_idx = start_match.end() - 1
        end_ref_match = re.search(r'window\.PETUGAS_DATA_UB', assign_content)
        if end_ref_match:
            end_ref_idx = end_ref_match.start()
            array_str = assign_content[start_idx:end_ref_idx].strip()
            if array_str.endswith(';'):
                array_str = array_str[:-1].strip()
            if array_str.endswith(';'):
                array_str = array_str[:-1].strip()
            fixed_str = re.sub(r',\s*([\]}])', r'\1', array_str)
            petugas_umum = json.loads(fixed_str)

    # Load window.PETUGAS_DATA_UB
    start_match_ub = re.search(r'window\.PETUGAS_DATA_UB\s*=\s*\[', assign_content)
    petugas_ub = []
    if start_match_ub:
        start_idx = start_match_ub.end() - 1
        # The file ends shortly after this array or contains some other functions
        # Let's search for next window. or end of file
        end_ref_match = re.search(r'window\.', assign_content[start_idx:])
        if end_ref_match:
            end_ref_idx = start_idx + end_ref_match.start()
        else:
            end_ref_idx = len(assign_content)
        array_str = assign_content[start_idx:end_ref_idx].strip()
        # Find index of last ']'
        last_bracket = array_str.rfind(']')
        if last_bracket != -1:
            array_str = array_str[:last_bracket+1]
        fixed_str = re.sub(r',\s*([\]}])', r'\1', array_str)
        try:
            petugas_ub = json.loads(fixed_str)
        except Exception as e:
            print("Failed loading UB petugas:", e)
            
    print(f"Loaded {len(petugas_umum)} general officers (UMUM).")
    print(f"Loaded {len(petugas_ub)} UB officers.")
    
    # Let's combine them
    all_petugas = {}
    for p in petugas_umum:
        all_petugas[p.get('username', '').lower()] = p
    for p in petugas_ub:
        u = p.get('username', '').lower()
        if u not in all_petugas:
            all_petugas[u] = p
            
    # Read granular assignments
    with open('granular_assignments.json', 'r', encoding='utf-8') as f:
        granular_data = json.load(f)

    base64_str = granular_data['compressed_data']
    compressed_bytes = base64.b64decode(base64_str)
    decompressed = gzip.decompress(compressed_bytes).decode('utf-8')
    payload = json.loads(decompressed)

    targets = payload['targets']
    regions = payload['regions']
    petugas = payload['petugas'] # list of [username, fullname]

    # Filter targets in Banggai Kepulauan
    bk_region_indices = set()
    for idx, r in enumerate(regions):
        kab_name = r[1]
        if "BANGGAI KEPULAUAN" in kab_name.upper():
            bk_region_indices.add(idx)

    bk_targets = [t for t in targets if t[5] in bk_region_indices]
    
    target_count_by_officer_idx = {}
    for t in bk_targets:
        p_idx = t[4]
        if p_idx != -1:
            target_count_by_officer_idx[p_idx] = target_count_by_officer_idx.get(p_idx, 0) + 1

    print(f"\nAnalyzing active officers assigned to targets in BK:")
    found_count = 0
    not_found = []
    
    for p_idx_str, count in target_count_by_officer_idx.items():
        p_idx = int(p_idx_str)
        username, fullname = petugas[p_idx]
        username_lower = username.lower()
        
        if username_lower in all_petugas:
            found_count += 1
        else:
            not_found.append((username, fullname, count))
            
    print(f"Total: {len(target_count_by_officer_idx)}")
    print(f"Found in PETUGAS_DATA_UMUM or UB: {found_count}")
    print(f"Not found: {len(not_found)}")
    
    # Where are the not_found officers coming from?
    # Let's check other JS files in the project. For example: sync_data.js, data.js
    # Let's search for some of the not_found usernames in sync_data.js and data.js
    if not_found:
        print("\nChecking if not_found usernames are in data.js or sync_data.js...")
        try:
            with open('data.js', 'r', encoding='utf-8') as f:
                data_js = f.read()
            print("data.js read successfully.")
        except Exception as e:
            data_js = ""
            print("Failed to read data.js:", e)
            
        try:
            with open('sync_data.js', 'r', encoding='utf-8') as f:
                sync_js = f.read()
            print("sync_data.js read successfully.")
        except Exception as e:
            sync_js = ""
            print("Failed to read sync_data.js:", e)
            
        for username, fullname, count in not_found[:5]:
            in_data = username in data_js
            in_sync = username in sync_js
            print(f"  {username}: count={count}, in data.js={in_data}, in sync_data.js={in_sync}")

        # Let's see if we can identify roles (PPL or PML) of these missing officers.
        # How?
        # In BPS, roles can sometimes be inferred:
        # PPL is Pencacah Lapangan / Mitra. PML is Pengawas Lapangan / Organik/Mitra Senior.
        # Is there any email pattern, or do we have their role info in another place?
        # Let's search where PETUGAS_DATA is populated in app.js or check if there is an API metadata database.
        # Wait, let's run this script first!

if __name__ == '__main__':
    main()
