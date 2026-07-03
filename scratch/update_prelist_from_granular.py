#!/usr/bin/env python3
"""Update total_prelist per kab in ipas_data from granular files, then upload slim to Supabase."""
import json, gzip, base64, os, copy, time
from dotenv import load_dotenv
from supabase import create_client

BASE = '/Users/jihanmaisaroh/scrap_fasih'
load_dotenv(os.path.join(BASE, '.env'))
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

# ── kab code → granular key mapping ──────────────────────────────────────────
kab_code_map = {
    '7201': 'BANGGAI KEPULAUAN', '7202': 'BANGGAI', '7203': 'MOROWALI',
    '7204': 'POSO', '7205': 'DONGGALA', '7206': 'TOLI-TOLI',
    '7207': 'BUOL', '7208': 'PARIGI MOUTONG', '7209': 'TOJO UNA-UNA',
    '7210': 'SIGI', '7211': 'BANGGAI LAUT', '7212': 'MOROWALI UTARA', '7271': 'PALU'
}
# Reverse map: clean name → kab_code
name_to_code = {v: k for k, v in kab_code_map.items()}

import re

def code_from_kab_name(kab_name):
    """Extract kab code from ipas_data name like '[01] BANGGAI KEPULAUAN' → '7201'."""
    m = re.match(r'^\[(\d+)\]', (kab_name or '').strip())
    if m:
        num = m.group(1).zfill(2)
        # Sulteng kab: 01-12 → 720X, 71 → 7271
        if num == '71':
            return '7271'
        elif num.startswith('0') or (num.isdigit() and 1 <= int(num) <= 12):
            return '72' + num
    return None


def load_granular(code):
    """Load granular file and return total count."""
    f = f'{BASE}/granular_assignments_se_umum_{code}.json'
    if not os.path.exists(f):
        return None
    with open(f) as fp:
        d = json.load(fp)
    raw = base64.b64decode(d['compressed_data'])
    data = json.loads(gzip.decompress(raw))
    return len(data.get('targets', []))

# ── Load granular counts ──────────────────────────────────────────────────────
print("Menghitung total per kab dari granular files...")
granular_counts = {}
for code, name in kab_code_map.items():
    n = load_granular(code)
    if n is not None:
        granular_counts[code] = n
        print(f"  {code} {name}: {n:,}")
    else:
        print(f"  {code} {name}: MISSING")

total_granular = sum(granular_counts.values())
print(f"\nGranular total: {total_granular:,}")
print(f"FASIH total  : 1,225,921")
print(f"Gap          : {1225921 - total_granular:,}")

# ── Fetch ipas_data from Supabase ─────────────────────────────────────────────
print("\nMemuat ipas_data dari Supabase...")
sb = create_client(SUPABASE_URL, SUPABASE_KEY)
res = sb.table('dashboard_store').select('value').eq('key', 'ipas_data').execute()
if not res.data:
    print("[ERROR] ipas_data tidak ditemukan!")
    exit(1)
val = res.data[0]['value']
if isinstance(val, str):
    val = json.loads(val)

# ── Patch total_prelist per kab ───────────────────────────────────────────────
print("\nMemperbarui total_prelist per kab...")
se_umum = val.get('se_umum', [])
for kab_item in se_umum:
    kab_raw = kab_item.get('kabupaten', '')
    # Try exact code extraction from [XX] prefix first
    code = code_from_kab_name(kab_raw)
    if code and code in granular_counts:
        old = kab_item.get('total_prelist', 0)
        new_count = granular_counts[code]
        kab_item['total_prelist'] = new_count
        print(f"  [{code}] {kab_raw}: {old:,} → {new_count:,} (+{new_count-old:,})")
    else:
        print(f"  [SKIP] {kab_raw} – kode tidak ditemukan (code_extracted={code})")


# Update prov total
val['se_umum_prov_total'] = total_granular
print(f"\nse_umum_prov_total: {val.get('se_umum_prov_total'):,}")

# ── Save locally ──────────────────────────────────────────────────────────────
local_path = os.path.join(BASE, 'ipas_data.js')
with open(local_path, 'w', encoding='utf-8') as f:
    f.write(f"window.IPAS_DATA = {json.dumps(val, indent=4)};\n")
print(f"✅ Lokal ipas_data.js diperbarui!")

# ── Create slim version for Supabase ─────────────────────────────────────────
val_slim = copy.deepcopy(val)
new_biz_by_kab = {}
for kab_item in val_slim.get('se_umum', []):
    kab_raw_key = kab_item.get('kabupaten', '')
    new_biz_by_kab[kab_raw_key] = kab_item.get('new_businesses', [])
    kab_item['new_businesses'] = []
    for kec_item in kab_item.get('kecamatan_list', []):
        kec_item['new_businesses'] = []

# ── Upload slim to Supabase ───────────────────────────────────────────────────
print("\nMengunggah ipas_data slim ke Supabase...")
for attempt in range(1, 4):
    try:
        sb.table('dashboard_store').delete().eq('key', 'ipas_data').execute()
        sb.table('dashboard_store').insert({'key': 'ipas_data', 'value': val_slim}).execute()
        print("✅ ipas_data slim berhasil di-upload!")
        break
    except Exception as e:
        print(f"[RETRY {attempt}] {e}")
        if attempt < 3:
            time.sleep(10)
        else:
            print("[ERROR] Upload gagal setelah 3 percobaan.")

# ── Upload new_businesses per kab (keep updated) ─────────────────────────────
kab_code_for_nb = {v: k for k, v in {
    'BANGGAI KEPULAUAN': '7201', 'BANGGAI': '7202', 'MOROWALI': '7203',
    'POSO': '7204', 'DONGGALA': '7205', 'TOLI-TOLI': '7206', 'BUOL': '7207',
    'PARIGI MOUTONG': '7208', 'TOJO UNA-UNA': '7209', 'SIGI': '7210',
    'BANGGAI LAUT': '7211', 'MOROWALI UTARA': '7212', 'PALU': '7271'
}.items()}

print("\nMemperbarui new_businesses per kabupaten di Supabase...")
for kab_full, biz_list in new_biz_by_kab.items():
    kab_clean2 = (kab_full or '').upper().strip()
    for prefix in ['KAB. ', 'KABUPATEN ', 'KOTA ']:
        if kab_clean2.startswith(prefix):
            kab_clean2 = kab_clean2[len(prefix):]
    kab_clean2 = kab_clean2.strip()
    kab_code2 = kab_code_for_nb.get(kab_clean2)
    if not kab_code2:
        continue
    nb_key = f"new_businesses_se_umum_{kab_code2}"
    for attempt in range(1, 4):
        try:
            sb.table('dashboard_store').delete().eq('key', nb_key).execute()
            sb.table('dashboard_store').insert({'key': nb_key, 'value': biz_list}).execute()
            print(f"  ✅ {nb_key}: {len(biz_list)} item")
            break
        except Exception as e:
            print(f"  [RETRY {attempt}] {nb_key}: {e}")
            if attempt < 3:
                time.sleep(5)

print("\n✅ Selesai!")
print(f"Total target baru: {total_granular:,} (sebelumnya: 1,186,461)")
print(f"Gap ke FASIH: {1225921 - total_granular:,}")
