"""
Script v2: Mencari petugas pencacah dengan beban kerja > 800 assignment (listing/HH).
Cara kerja:
  1. Ambil PETUGAS_DATA_UMUM: tiap petugas punya list `regions` (kode SLS yang di-assign)
  2. Ambil ASSIGN_SLS_DATA_UMUM: tiap SLS punya `total` (jumlah listing)
  3. Untuk setiap pencacah, jumlahkan `total` dari semua SLS yang ada di `regions`-nya
  4. Filter yang beban kerjanya > 800
"""

import re
import json
import csv
from pathlib import Path
from collections import defaultdict

ASSIGN_DATA_PATH = Path("/Users/jihanmaisaroh/scrap_fasih/assign_data.js")
OUTPUT_CSV = Path("/Users/jihanmaisaroh/scrap_fasih/pencacah_beban_lebih_800.csv")

def extract_js_var_robust(content, var_name):
    start_marker = f'window.{var_name}'
    start_idx = content.find(start_marker)
    if start_idx == -1:
        print(f"  Variable {var_name} not found!")
        return None
    
    eq_idx = content.find('=', start_idx)
    if eq_idx == -1:
        return None
    
    bracket_start = content.find('[', eq_idx)
    if bracket_start == -1:
        return None
    
    depth = 0
    i = bracket_start
    while i < len(content):
        if content[i] == '[':
            depth += 1
        elif content[i] == ']':
            depth -= 1
            if depth == 0:
                bracket_end = i
                break
        i += 1
    
    json_str = content[bracket_start:bracket_end+1]
    return json.loads(json_str)

print("Membaca file assign_data.js...")
with open(ASSIGN_DATA_PATH, 'r', encoding='utf-8') as f:
    content = f.read()

print("Parsing PETUGAS_DATA_UMUM...")
petugas_data = extract_js_var_robust(content, 'PETUGAS_DATA_UMUM')
print(f"  Total petugas: {len(petugas_data)}")

print("Parsing ASSIGN_SLS_DATA_UMUM...")
sls_data = extract_js_var_robust(content, 'ASSIGN_SLS_DATA_UMUM')
print(f"  Total SLS records: {len(sls_data)}")

# Buat mapping sls_code -> total HH
sls_total_map = {}
for sls in sls_data:
    code = sls.get('sls_code', '')
    if code:
        sls_total_map[code] = sls.get('total', 0)

print(f"  SLS dengan data total: {len(sls_total_map)}")

# Filter hanya Pencacah
pencacah_list = [p for p in petugas_data if p.get('roleName') == 'Pencacah']
print(f"\n  Total Pencacah: {len(pencacah_list)}")

# Hitung beban kerja per pencacah
results = []
for p in pencacah_list:
    email = p.get('email', '')
    username = p.get('username', '')
    user_id = p.get('userId', '')
    role_name = p.get('roleName', '')
    total_regions = p.get('totalRegions', 0)
    regions = p.get('regions', [])
    
    # Hitung total HH dari semua region yang di-assign
    total_hh = 0
    matched = 0
    for reg in regions:
        code = reg.get('regionCode', '')
        hh = sls_total_map.get(code, 0)
        total_hh += hh
        if hh > 0:
            matched += 1
    
    results.append({
        'userId': user_id,
        'email': email,
        'username': username,
        'roleName': role_name,
        'totalRegions': total_regions,
        'totalHH': total_hh,
        'matchedSLS': matched
    })

# Statistik
all_hh = [r['totalHH'] for r in results]
print(f"\nStatistik beban kerja Pencacah (Total HH/Listing):")
print(f"  Min: {min(all_hh)}")
print(f"  Max: {max(all_hh)}")
print(f"  Rata-rata: {sum(all_hh)/len(all_hh):.1f}")
print(f"  Petugas dengan beban = 0: {sum(1 for x in all_hh if x == 0)}")
print(f"  Petugas dengan beban > 0: {sum(1 for x in all_hh if x > 0)}")
print(f"  Petugas dengan beban > 500: {sum(1 for x in all_hh if x > 500)}")
print(f"  Petugas dengan beban > 800: {sum(1 for x in all_hh if x > 800)}")

# Filter yang > 800
heavy = [r for r in results if r['totalHH'] > 800]
heavy.sort(key=lambda x: x['totalHH'], reverse=True)

print(f"\n=== HASIL: {len(heavy)} Pencacah dengan beban > 800 HH ===")

if heavy:
    # Tulis CSV
    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['No', 'email', 'userId', 'roleName', 'totalRegions', 'totalHH_assigned']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for i, row in enumerate(heavy, 1):
            writer.writerow({
                'No': i,
                'email': row['email'],
                'userId': row['userId'],
                'roleName': row['roleName'],
                'totalRegions': row['totalRegions'],
                'totalHH_assigned': row['totalHH']
            })
    print(f"\n✅ CSV disimpan ke: {OUTPUT_CSV}")
    
    print(f"\nTop 20 Pencacah dengan beban kerja terbesar:")
    for r in heavy[:20]:
        print(f"  {r['email']:50s}: {r['totalHH']:,} HH ({r['totalRegions']} SLS)")
else:
    print("\nTidak ada Pencacah dengan beban kerja > 800 HH")
    print("\nTop 20 terbesar:")
    top20 = sorted(results, key=lambda x: x['totalHH'], reverse=True)[:20]
    for r in top20:
        print(f"  {r['email']:50s}: {r['totalHH']:,} HH ({r['totalRegions']} SLS)")
