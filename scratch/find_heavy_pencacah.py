"""
Script untuk mencari petugas pencacah dengan beban kerja lebih dari 800 assignment.
Sumber data: assign_data.js - PETUGAS_DATA_UMUM dan ASSIGN_SLS_DATA_UMUM

Beban kerja dihitung dari total listing/HH yang di-assign ke petugas tersebut
melalui data ASSIGN_SLS_DATA_UMUM (field `officers` di tiap SLS).
"""

import re
import json
import csv
from pathlib import Path
from collections import defaultdict

ASSIGN_DATA_PATH = Path("/Users/jihanmaisaroh/scrap_fasih/assign_data.js")
OUTPUT_CSV = Path("/Users/jihanmaisaroh/scrap_fasih/pencacah_beban_lebih_800.csv")

def extract_js_var(content, var_name):
    """Extract JS array variable from content."""
    pattern = rf'window\.{var_name}\s*=\s*(\[.*?\]);\s*(?:window\.|$)'
    match = re.search(pattern, content, re.DOTALL)
    if match:
        return json.loads(match.group(1))
    return None

def extract_js_var_robust(content, var_name):
    """Extract JS array variable using line-by-line approach."""
    # Find start of the variable
    start_marker = f'window.{var_name}'
    start_idx = content.find(start_marker)
    if start_idx == -1:
        print(f"  Variable {var_name} not found!")
        return None
    
    # Find the = sign
    eq_idx = content.find('=', start_idx)
    if eq_idx == -1:
        return None
    
    # Find the opening [
    bracket_start = content.find('[', eq_idx)
    if bracket_start == -1:
        return None
    
    # Find matching ]
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
if petugas_data is None:
    print("ERROR: Gagal parse PETUGAS_DATA_UMUM")
    exit(1)
print(f"  Total petugas: {len(petugas_data)}")

# Filter hanya Pencacah
pencacah_list = [p for p in petugas_data if p.get('roleName') == 'Pencacah']
print(f"  Total Pencacah: {len(pencacah_list)}")

print("Parsing ASSIGN_SLS_DATA_UMUM untuk menghitung beban kerja (total listing per petugas)...")
sls_data = extract_js_var_robust(content, 'ASSIGN_SLS_DATA_UMUM')
if sls_data is None:
    print("WARNING: Gagal parse ASSIGN_SLS_DATA_UMUM, akan gunakan totalRegions sebagai proxy")
    sls_data = []

# Bangun mapping officer_email -> total HH assignment
print(f"  Total SLS records: {len(sls_data)}")
officer_hh_map = defaultdict(int)  # email -> total HH assigned
officer_sls_count = defaultdict(int)  # email -> jumlah SLS

for sls in sls_data:
    officers = sls.get('officers', [])
    if officers:
        total_hh = sls.get('total', 0)
        assigned_hh = sls.get('assigned', 0)
        n_officers = len(officers)
        for officer in officers:
            email = officer.get('email') or officer.get('username') or str(officer)
            # Beban per petugas = total / jumlah petugas di SLS ini
            share = assigned_hh / n_officers if n_officers > 0 else 0
            officer_hh_map[email] += share
            officer_sls_count[email] += 1

print(f"  Petugas yang punya assignment dari SLS data: {len(officer_hh_map)}")

# Jika SLS data tidak punya info officers yang berguna, fallback ke totalRegions
use_regions = len(officer_hh_map) == 0

# Buat dataframe hasil
results = []
for p in pencacah_list:
    email = p.get('email', '')
    username = p.get('username', '')
    user_id = p.get('userId', '')
    total_regions = p.get('totalRegions', 0)
    
    if use_regions:
        beban_kerja = total_regions
        sumber = 'totalRegions'
    else:
        beban_kerja = round(officer_hh_map.get(email, 0) + officer_hh_map.get(username, 0))
        sumber = 'total_HH_assigned'
    
    results.append({
        'userId': user_id,
        'email': email,
        'username': username,
        'roleName': p.get('roleName', ''),
        'totalRegions': total_regions,
        'beban_kerja': beban_kerja,
        'sumber_beban': sumber
    })

# Filter yang > 800
heavy = [r for r in results if r['beban_kerja'] > 800]
heavy.sort(key=lambda x: x['beban_kerja'], reverse=True)

print(f"\n=== HASIL ===")
print(f"Total Pencacah: {len(results)}")
print(f"Pencacah dengan beban > 800: {len(heavy)}")

if use_regions:
    print("\n⚠️  Menggunakan totalRegions sebagai beban kerja (SLS officers data kosong)")
    print("   Artinya: jumlah SLS/wilayah yang di-assign ke petugas ini")
else:
    print("\n✅ Menggunakan total HH yang di-assign dari data SLS")

# Statistik
if results:
    all_beban = [r['beban_kerja'] for r in results]
    print(f"\nStatistik beban kerja Pencacah:")
    print(f"  Min: {min(all_beban):.0f}")
    print(f"  Max: {max(all_beban):.0f}")
    print(f"  Rata-rata: {sum(all_beban)/len(all_beban):.1f}")

# Tulis CSV
if heavy:
    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['No', 'email', 'userId', 'roleName', 'totalRegions', 'beban_kerja']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for i, row in enumerate(heavy, 1):
            writer.writerow({
                'No': i,
                'email': row['email'],
                'userId': row['userId'],
                'roleName': row['roleName'],
                'totalRegions': row['totalRegions'],
                'beban_kerja': row['beban_kerja']
            })
    print(f"\n✅ CSV disimpan ke: {OUTPUT_CSV}")
    print(f"\nTop 10 Pencacah dengan beban kerja terbesar:")
    for r in heavy[:10]:
        print(f"  {r['email']}: {r['beban_kerja']:.0f}")
else:
    print("\nTidak ada Pencacah dengan beban kerja > 800")
    print("Cek distribusi 10 terbesar:")
    top10 = sorted(results, key=lambda x: x['beban_kerja'], reverse=True)[:10]
    for r in top10:
        print(f"  {r['email']}: {r['beban_kerja']:.0f} ({r['sumber_beban']})")
