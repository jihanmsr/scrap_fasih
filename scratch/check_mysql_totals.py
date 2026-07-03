#!/usr/bin/env python3
"""Check MySQL API totals vs granular data and update ipas_data if needed."""
import json, gzip, base64, os, requests

BASE = '/Users/jihanmaisaroh/scrap_fasih'
sulteng_codes = {'7201','7202','7203','7204','7205','7206','7207','7208','7209','7210','7211','7212','7271'}

# 1. Get from MySQL API
resp = requests.get("https://dds-api.bpssulteng.id/api.php?action=get_dashboard_summary&survey=se_umum&kab=all", timeout=30)
data = resp.json()

seen = {}
for row in data:
    code = str(row.get('code',''))
    if code in sulteng_codes:
        if code not in seen:
            seen[code] = {'total_target': 0, 'belum_selesai': 0}
        seen[code]['total_target'] += int(row.get('total_target') or 0)
        seen[code]['belum_selesai'] += int(row.get('belum_selesai') or 0)

grand_total_mysql = 0
grand_selesai_mysql = 0
print(f"{'CODE':<6} {'MySQL total':>12} {'MySQL selesai':>14}")
print('-'*35)
for code in sorted(seen.keys()):
    t = seen[code]['total_target']
    b = seen[code]['belum_selesai']
    s = t - b
    grand_total_mysql += t
    grand_selesai_mysql += s
    print(f"{code:<6} {t:>12,} {s:>14,}")
print('-'*35)
pct = grand_selesai_mysql/grand_total_mysql*100 if grand_total_mysql else 0
print(f"{'TOTAL':<6} {grand_total_mysql:>12,} {grand_selesai_mysql:>14,} ({pct:.2f}%)")

# 2. Get from granular files
def load_granular(code):
    f = f'{BASE}/granular_assignments_se_umum_{code}.json'
    if not os.path.exists(f): return None
    with open(f) as fp:
        d = json.load(fp)
    return json.loads(gzip.decompress(base64.b64decode(d['compressed_data'])))

print("\n\nGranular file totals:")
print(f"{'CODE':<6} {'Granular total':>15}")
print('-'*25)
grand_total_granular = 0
kab_granular = {}
for code in sorted(sulteng_codes):
    data_g = load_granular(code)
    if not data_g:
        print(f"{code:<6} MISSING")
        continue
    n = len(data_g.get('targets', []))
    grand_total_granular += n
    kab_granular[code] = n
    print(f"{code:<6} {n:>15,}")
print('-'*25)
print(f"{'TOTAL':<6} {grand_total_granular:>15,}")
print(f"\nFASIH shows: 1,225,921 total | 23.91% selesai (~293,000)")
print(f"MySQL API : {grand_total_mysql:,} total | {pct:.2f}% selesai")
print(f"Granular  : {grand_total_granular:,} total")
