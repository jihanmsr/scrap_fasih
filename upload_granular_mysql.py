import json
import os
import gzip
import base64
import urllib.request
import ssl
import time

# Konfigurasi
API_URL = "https://103.5.51.154/api.php?action=upsert_granular"
CHUNK_SIZE = 500

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def upload_chunk(chunk):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(API_URL, method='POST')
            req.add_header('Content-Type', 'application/json')
            req.add_header('Host', 'dds-api.bpssulteng.id')
            data = json.dumps(chunk).encode('utf-8')
            with urllib.request.urlopen(req, data=data, context=ctx, timeout=30) as response:
                res_body = response.read().decode('utf-8')
                res = json.loads(res_body)
                if res.get('success'):
                    return True
                else:
                    print(f"Server error: {res.get('error')}")
                    time.sleep(2)
        except Exception as e:
            print(f"Network error: {e}")
            time.sleep(2)
    return False

def main():
    print("Mulai proses migrasi Granular Targets ke MySQL...")
    # Cari semua file partisi
    files = [f for f in os.listdir('.') if f.startswith('granular_assignments_') and f.endswith('.json')]
    
    total_uploaded = 0
    try:
        with open('region_map_sulteng_full.json', 'r', encoding='utf-8') as rm:
            full_map = json.load(rm)
            region_map = {}
            for kab_code, kab_data in full_map.get("kabupaten", {}).items():
                region_map[kab_code] = kab_data.get("kab_name")
                for kec_code, kec_data in kab_data.get("kecamatan", {}).items():
                    region_map[kec_code] = kec_data.get("kec_name")
                    for desa_code, desa_data in kec_data.get("desa", {}).items():
                        region_map[desa_code] = desa_data.get("desa_name")
    except Exception as e:
        print(f"Error loading region_map_sulteng_full.json: {e}")
        region_map = {}
        
    for f in files:
        print(f"\nMemproses file: {f}")
        with open(f, 'r') as file:
            d = json.load(file)
            
        raw = gzip.decompress(base64.b64decode(d['compressed_data']))
        data = json.loads(raw)
        
        survey_type = d.get('survey_type', 'se_umum')
        regions = data.get('regions', [])
        petugas = data.get('petugas', [])
        statuses = data.get('statuses', [])
        targets = data.get('targets', [])
        
        chunk = []
        for t in targets:
            if len(t) < 6: continue
            
            reg_idx = t[5]
            if reg_idx >= 0 and reg_idx < len(regions):
                reg = regions[reg_idx]
                kab_code = reg[0]
                kab_name = reg[1]
                kec_code = reg[2]
                kec_name = reg[3]
                desa_code = reg[4]
                desa_name = reg[5]
                sls_code = reg[6]
                sls_name = reg[7]
            else:
                continue
                
            # Hilangkan kode kabupaten dari nama kabupaten
            kab_clean = " ".join([word for word in kab_name.split() if not (word.isdigit() or (word.startswith("72") and len(word)==4))]).upper()
            
            stat_idx = t[3]
            status_str = statuses[stat_idx] if stat_idx < len(statuses) else 'UNKNOWN'
            
            pet_idx = t[4]
            if pet_idx >= 0 and pet_idx < len(petugas):
                pet = petugas[pet_idx]
                petugas_username = pet[0]
                petugas_fullname = pet[1]
            else:
                petugas_username = '-'
                petugas_fullname = '-'
            
            row = {
                'assignment_id': t[0],
                'survey_type': survey_type,
                'kab_code': kab_code,
                'kab_name': kab_clean,
                'kec_code': kec_code,
                'kec_name': kec_name,
                'desa_code': desa_code,
                'desa_name': desa_name,
                'sls_code': sls_code,
                'sls_name': sls_name,
                'target_id': t[1],
                'target_name': t[2],
                'status': status_str,
                'petugas_username': petugas_username,
                'petugas_fullname': petugas_fullname
            }
            chunk.append(row)
            
            if len(chunk) >= CHUNK_SIZE:
                if upload_chunk(chunk):
                    total_uploaded += len(chunk)
                    print(f"\rUploaded {total_uploaded} targets...", end='')
                chunk = []
                
        if chunk:
            if upload_chunk(chunk):
                total_uploaded += len(chunk)
                print(f"\rUploaded {total_uploaded} targets...", end='')
    
    print(f"\nSelesai! Total {total_uploaded} targets berhasil diupload ke MySQL.")

if __name__ == "__main__":
    main()
