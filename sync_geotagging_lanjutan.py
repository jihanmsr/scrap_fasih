"""
sync_geotagging_lanjutan.py
Sinkronisasi titik-titik geotagging dari API Kak Ical (ause.bpssulteng.id)
untuk semua kabupaten monitoring lanjutan: Palu, Banggai, Poso, Donggala, Sigi, Morowali Utara.
Menyimpan ke palu_geotagging_data.js agar titik-titik langsung muncul secara instan di peta.
"""

import json
import time
import os
import requests
import urllib3
from concurrent.futures import ThreadPoolExecutor, as_completed

urllib3.disable_warnings()

API_IP_URL = "https://103.5.51.154/api/sqllab_geotagging/sls"
HEADERS = {
    "Content-Type": "application/json",
    "Host": "ause.bpssulteng.id",
    "User-Agent": "BPS-Monitoring-Lanjutan/1.0"
}

def load_existing_cache():
    cache = {}
    if os.path.exists('palu_geotagging_data.js'):
        try:
            with open('palu_geotagging_data.js', 'r', encoding='utf-8') as f:
                c = f.read()
                start = c.find('{')
                end = c.rfind('}') + 1
                if start != -1 and end != -1:
                    cache = json.loads(c[start:end])
        except Exception as e:
            print(f"Error loading existing cache: {e}")
    return cache

def load_target_sls():
    with open('monitoring_lanjutan_data.js', 'r', encoding='utf-8') as f:
        c = f.read()
    start = c.find('{')
    end = c.rfind('}') + 1
    data = json.loads(c[start:end])
    
    feats = data.get('features', [])
    targets = []
    
    for f in feats:
        p = f.get('properties', {})
        op = p.get('open', 0)
        dr = p.get('draft', 0)
        ba = p.get('banr', 0)
        bk = p.get('bangkos', 0)
        
        # Priority score
        score = (op * 20) + (dr * 10) + (ba * 8) + (1 if bk >= 15 else 0)
        if op > 0 or dr > 0 or ba > 0 or bk >= 15:
            targets.append((score, p))
            
    # Sort descending by priority
    targets.sort(key=lambda x: x[0], reverse=True)
    return [p for _, p in targets]

def fetch_single_sls(p):
    idsls = p.get('idsls', '')
    kdkab = p.get('kdkab', '71')
    kdkec = p.get('kdkec', '')
    kddesa = p.get('kddesa', '')
    kdsls = (p.get('kdsls', '') + p.get('kdsubsls', '00'))
    
    payload = {
        "kdkab": kdkab,
        "kdkec": kdkec,
        "kddesa": kddesa,
        "kdsls": kdsls
    }
    
    for attempt in range(2):
        try:
            resp = requests.post(API_IP_URL, json=payload, headers=HEADERS, verify=False, timeout=15)
            if resp.status_code == 200:
                res_json = resp.json()
                raw_features = res_json.get('data', {}).get('features', [])
                needed_keys = {
                    'data1', 'ada_bang_usaha_value', 'ada_keluarga_value', 
                    'jumlah_usaha_ditemukan', 'jumlah_usaha', 'assignment_status_alias', 
                    'alamat_prelist', 'no_bang'
                }
                features = []
                for f in raw_features:
                    geom = f.get('geometry')
                    p = f.get('properties') or {}
                    trimmed_p = {k: p[k] for k in needed_keys if k in p and p[k] is not None}
                    features.append({
                        'geometry': geom,
                        'properties': trimmed_p
                    })
                return idsls, features, None
            else:
                return idsls, None, f"status {resp.status_code}"
        except Exception as e:
            if attempt == 1:
                return idsls, None, str(e)
            time.sleep(0.5)

def save_cache(cache):
    temp_file = 'palu_geotagging_data.js.tmp'
    with open(temp_file, 'w', encoding='utf-8') as f:
        f.write("window.PALU_GEOTAGGING_CACHE = " + json.dumps(cache, ensure_ascii=False) + ";\n")
    os.replace(temp_file, 'palu_geotagging_data.js')

def main():
    cache = load_existing_cache()
    print(f"Loaded existing cache: {len(cache)} SLS")
    
    all_targets = load_target_sls()
    print(f"Total priority SLS found in monitoring data: {len(all_targets)}")
    
    # Filter SLS yang belum ada di cache atau masih kosong
    to_fetch = [s for s in all_targets if s.get('idsls') not in cache or not cache[s.get('idsls')]]
    print(f"SLS to fetch: {len(to_fetch)}")
    
    if not to_fetch:
        print("All priority SLS are already cached!")
        return

    # Kita utamakan dulu yang non-Palu (02, 04, 05, 10, 12) lalu Palu
    to_fetch.sort(key=lambda s: (0 if s.get('kdkab') != '71' else 1, -(s.get('open', 0)*20 + s.get('draft', 0)*10 + s.get('banr', 0)*8)))

    success_count = 0
    saved_count = 0
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {executor.submit(fetch_single_sls, s): s for s in to_fetch}
        for future in as_completed(futures):
            s = futures[future]
            idsls, feats, err = future.result()
            if feats is not None:
                cache[idsls] = feats
                pts = sum(1 for feat in feats if feat.get('geometry'))
                success_count += 1
                saved_count += 1
                print(f"[{success_count}/{len(to_fetch)}] Kab {s.get('kdkab')} | {idsls} ({s.get('nmsls')}, {s.get('nmdesa')}): {len(feats)} records ({pts} points)")
            else:
                print(f"[FAILED] Kab {s.get('kdkab')} | {idsls}: {err}")
                
            if saved_count >= 15:
                save_cache(cache)
                saved_count = 0

    save_cache(cache)
    duration = time.time() - start_time
    print(f"\nDone in {duration:.1f}s! Total SLS in geotagging cache: {len(cache)}")

if __name__ == '__main__':
    main()
