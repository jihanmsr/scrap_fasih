"""
Script v3: Mencari petugas pencacah dengan beban kerja > 800 assignment (listing/HH).
FIX: region code (16 digit) = SLS code (14 digit) + 2 digit akhir (sub-kode)
     Matching: region_code[:-2] == sls_code
"""

import re
import json
import csv
from pathlib import Path

ASSIGN_DATA_PATH = Path("/Users/jihanmaisaroh/scrap_fasih/assign_data.js")
OUTPUT_CSV = Path("/Users/jihanmaisaroh/scrap_fasih/pencacah_beban_lebih_800.csv")

def extract_js_var_robust(content, var_name):
    start_marker = f'window.{var_name}'
    start_idx = content.find(start_marker)
    if start_idx == -1:
        print(f"  Variable {var_name} not found!")
        return None
    eq_idx = content.find('=', start_idx)
    bracket_start = content.find('[', eq_idx)
    depth = 0
    i = bracket_start
    while i < len(content):
        if content[i] == '[': depth += 1
        elif content[i] == ']':
            depth -= 1
            if depth == 0:
                bracket_end = i
                break
        i += 1
    return json.loads(content[bracket_start:bracket_end+1])

print("Membaca file assign_data.js...")
with open(ASSIGN_DATA_PATH, 'r', encoding='utf-8') as f:
    content = f.read()

print("Parsing PETUGAS_DATA_UMUM...")
petugas_data = extract_js_var_robust(content, 'PETUGAS_DATA_UMUM')
print(f"  Total petugas: {len(petugas_data)}")

print("Parsing ASSIGN_SLS_DATA_UMUM...")
sls_data = extract_js_var_robust(content, 'ASSIGN_SLS_DATA_UMUM')
print(f"  Total SLS records: {len(sls_data)}")

# Mapping sls_code (14 digit) -> total HH
sls_total_map = {s['sls_code']: s.get('total', 0) for s in sls_data}

# Filter hanya Pencacah
pencacah_list = [p for p in petugas_data if p.get('roleName') == 'Pencacah']
print(f"\n  Total Pencacah: {len(pencacah_list)}")

# Hitung beban kerja: region_code[:-2] = sls_code
results = []
for p in pencacah_list:
    email = p.get('email', '')
    user_id = p.get('userId', '')
    role_name = p.get('roleName', '')
    total_regions = p.get('totalRegions', 0)
    regions = p.get('regions', [])
    
    total_hh = 0
    matched = 0
    sls_details = []
    for reg in regions:
        code = reg.get('regionCode', '')
        sls_code = code[:-2] if len(code) == 16 else code
        hh = sls_total_map.get(sls_code, 0)
        total_hh += hh
        if hh > 0:
            matched += 1
        sls_details.append({
            'sls_code': sls_code,
            'hh': hh
        })
    
    results.append({
        'userId': user_id,
        'email': email,
        'roleName': role_name,
        'totalRegions': total_regions,
        'totalHH': total_hh,
        'matchedSLS': matched,
        'sls_details': sls_details
    })

# Statistik
all_hh = [r['totalHH'] for r in results]
print(f"\nStatistik beban kerja Pencacah (Total HH/Listing):")
print(f"  Min:  {min(all_hh):,}")
print(f"  Max:  {max(all_hh):,}")
print(f"  Rata-rata: {sum(all_hh)/len(all_hh):.1f}")
print(f"  Petugas beban = 0: {sum(1 for x in all_hh if x == 0)}")
print(f"  Petugas beban 1-500: {sum(1 for x in all_hh if 0 < x <= 500)}")
print(f"  Petugas beban 501-800: {sum(1 for x in all_hh if 500 < x <= 800)}")
print(f"  Petugas beban > 800: {sum(1 for x in all_hh if x > 800)}")

# Filter yang > 800
heavy = [r for r in results if r['totalHH'] > 800]
heavy.sort(key=lambda x: x['totalHH'], reverse=True)

print(f"\n=== HASIL: {len(heavy)} Pencacah dengan beban > 800 HH ===")

# Tulis CSV
with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
    fieldnames = ['No', 'email', 'userId', 'roleName', 'jumlah_SLS', 'total_listing']
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for i, row in enumerate(heavy, 1):
        writer.writerow({
            'No': i,
            'email': row['email'],
            'userId': row['userId'],
            'roleName': row['roleName'],
            'jumlah_SLS': row['totalRegions'],
            'total_listing': row['totalHH']
        })

print(f"\n✅ CSV disimpan ke: {OUTPUT_CSV}")

print(f"\nTop 20 Pencacah dengan beban kerja terbesar:")
for r in (heavy if heavy else sorted(results, key=lambda x: x['totalHH'], reverse=True))[:20]:
    print(f"  {r['email']:55s}: {r['totalHH']:,} HH ({r['totalRegions']} SLS)")
