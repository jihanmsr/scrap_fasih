import json
import re

with open('fast_petugas_progress.js') as f:
    text = f.read().replace('window.PETUGAS_PROGRESS_MAP = ', '').strip().rstrip(';')
    progress_map = json.loads(text)

with open('petugas_region_map.js') as f:
    text = f.read().replace('window.PETUGAS_REGION_MAP = ', '').strip().rstrip(';')
    region_map = json.loads(text)

kabFilter = "[01] BANGGAI KEPULAUAN"
kabPrefixMatch = re.search(r'\[(\d+)\]', kabFilter)
kabPrefix = kabPrefixMatch.group(1) if kabPrefixMatch else ''

arr = []
for roleKey in ['Pencacah', 'Pengawas']:
    roleData = progress_map.get(roleKey, {})
    for email, pMapData in roleData.items():
        regions = region_map.get(email.lower())
        isPetugasInKabupaten = False
        if regions and len(regions) > 0:
            for rc in regions:
                if rc and rc.startswith('72' + kabPrefix):
                    isPetugasInKabupaten = True
                    break
        
        if not isPetugasInKabupaten:
            continue
            
        arr.append({
            'email': email,
            'role': roleKey
        })

print(f"Total in arr: {len(arr)}")
arr = [p for p in arr if p['role'] == 'Pencacah']
print(f"Total Pencacah: {len(arr)}")
