"""
sync_geotagging_palu.py
Mengambil titik-titik geotagging lapangan dari API resmi:
https://ause.bpssulteng.id/api/sqllab_geotagging/sls
dan menyimpannya ke palu_geotagging_data.js untuk visualisasi instan di peta monitoring.
"""

import json
import time
import requests
import os

API_URL = "https://ause.bpssulteng.id/api/sqllab_geotagging/sls"

def get_priority_sls():
    with open('palu_monitoring_data.js', 'r', encoding='utf-8') as f:
        content = f.read().split('=', 1)[1].strip().rstrip(';')
        data = json.loads(content)
    
    features = data.get('features', [])
    # Prioritaskan SLS yang OPEN > 0 atau DRAFT > 0, lalu yang gap-nya tinggi
    priority = []
    for feat in features:
        p = feat.get('properties', {})
        open_val = p.get('open', 0)
        draft_val = p.get('draft', 0)
        gap_cv = p.get('gap_cv', 0)
        score = (open_val * 10) + (draft_val * 3) + max(0, gap_cv)
        priority.append((score, p))
    
    priority.sort(key=lambda x: x[0], reverse=True)
    return [p for _, p in priority]

def fetch_sls_geotagging(p):
    idsls = p.get('idsls', '')
    kdkab = "71"
    kdkec = p.get('kdkec', '')
    kddesa = p.get('kddesa', '')
    kdsls = (p.get('kdsls', '') + p.get('kdsubsls', '00'))
    
    payload = {
        "kdkab": kdkab,
        "kdkec": kdkec,
        "kddesa": kddesa,
        "kdsls": kdsls
    }
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "BPS-Palu-Monitoring/1.0"
    }
    
    try:
        resp = requests.post(API_URL, json=payload, headers=headers, timeout=30)
        if resp.status_code == 200:
            res_json = resp.json()
            features = res_json.get('data', {}).get('features', [])
            return features
        else:
            print(f"Failed {idsls}: status {resp.status_code}")
            return None
    except Exception as e:
        print(f"Error fetching {idsls}: {e}")
        return None

def main():
    existing_cache = {}
    if os.path.exists('palu_geotagging_data.js'):
        try:
            with open('palu_geotagging_data.js', 'r', encoding='utf-8') as f:
                content = f.read().split('=', 1)[1].strip().rstrip(';')
                existing_cache = json.loads(content)
        except Exception:
            existing_cache = {}
            
    print(f"Existing cached SLS: {len(existing_cache)}")
    
    sls_list = get_priority_sls()
    # Target semua SLS yang masih OPEN > 0 atau DRAFT > 0
    target_sls = [s for s in sls_list if s.get('open', 0) > 0 or s.get('draft', 0) > 0]
    
    print(f"Fetching geotagging for all {len(target_sls)} Open/Draft SLS in Palu...")
    
    count = 0
    for s in target_sls:
        idsls = s.get('idsls')
        if idsls in existing_cache and len(existing_cache[idsls]) > 0:
            continue
            
        print(f"Fetching {idsls} ({s.get('nmsls')}, {s.get('nmdesa')} - Open: {s.get('open')}, Draft: {s.get('draft')})...")
        feats = fetch_sls_geotagging(s)
        if feats is not None:
            existing_cache[idsls] = feats
            points_count = sum(1 for f in feats if f.get('geometry'))
            print(f"  -> Got {len(feats)} records ({points_count} with GPS coordinates)")
            count += 1
            
            # Simpan bertahap setiap 5 SLS
            if count % 5 == 0:
                with open('palu_geotagging_data.js', 'w', encoding='utf-8') as f:
                    f.write("window.PALU_GEOTAGGING_CACHE = " + json.dumps(existing_cache, ensure_ascii=False) + ";\n")
            time.sleep(0.3)
            
    # Simpan hasil ke palu_geotagging_data.js
    with open('palu_geotagging_data.js', 'w', encoding='utf-8') as f:
        f.write("window.PALU_GEOTAGGING_CACHE = " + json.dumps(existing_cache, ensure_ascii=False) + ";\n")
        
    print(f"\nDone! Total SLS in geotagging cache: {len(existing_cache)}")

if __name__ == '__main__':
    main()
