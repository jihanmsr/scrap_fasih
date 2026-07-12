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
    if roleKey in progress_map:
        roleData = progress_map[roleKey]
        for email, pMapData in roleData.items():
            regions = region_map.get(email.lower())
            isPetugasInKabupaten = False
            
            if kabFilter != 'all' and region_map:
                if regions and len(regions) > 0:
                    for rc in regions:
                        if rc and rc.startswith('72' + kabPrefix):
                            isPetugasInKabupaten = True
                            break
            else:
                isPetugasInKabupaten = True
                
            if not isPetugasInKabupaten:
                continue
                
            arr.append({
                'name': email,
                'email': email,
                'role': roleKey
            })

print(f"Before filter: {len(arr)}")
currentPetugasTab = 'Pencacah'
arr = [p for p in arr if p['name'] != 'Belum Ada Petugas' and p['name'] != 'CAWI / Mandiri (Tanpa Petugas)' and p['role'] == currentPetugasTab]
print(f"After filter: {len(arr)}")

