import json
import requests
import pandas as pd
from shapely.geometry import shape, Point
import time

print("Membaca peta SLS...")
with open('petasls.geojson', 'r') as f:
    geojson_data = json.load(f)

print("Mem-filter untuk Kecamatan Bahodopi, Kabupaten Morowali...")
bahodopi_features = []
for feature in geojson_data['features']:
    props = feature['properties']
    # Di json, nmkab dan nmkec biasanya uppercase. Kita cek 'MOROWALI' dan 'BAHODOPI'
    if props.get('nmkab') == 'MOROWALI' and props.get('nmkec') == 'BAHODOPI':
        bahodopi_features.append(feature)

print(f"Ditemukan {len(bahodopi_features)} SLS di Kecamatan Bahodopi.")

print("Membaca data Prelist dari Excel...")
# Baca semua sheet atau sheet pertama
prelist_df = pd.read_excel('Prioritas_Penyisiran_Keluarga_SE2026_15Sep.xlsx')
prelist_df['Kode SLS (16 digit)'] = prelist_df['Kode SLS (16 digit)'].astype(str)

results = []

def get_buildings_in_bbox(bbox):
    # bbox format is (min_lon, min_lat, max_lon, max_lat)
    overpass_url = "http://overpass-api.de/api/interpreter"
    # Overpass expects: (south, west, north, east) => (min_lat, min_lon, max_lat, max_lon)
    overpass_query = f"""
    [out:json];
    (
      way["building"]({bbox[1]},{bbox[0]},{bbox[3]},{bbox[2]});
      relation["building"]({bbox[1]},{bbox[0]},{bbox[3]},{bbox[2]});
    );
    out center;
    """
    try:
        headers = {'User-Agent': 'BPS_Sulteng_SE2026_Script/1.0'}
        response = requests.post(overpass_url, data={'data': overpass_query}, headers=headers)
        if response.status_code != 200:
            print(f"  [API Error] Status: {response.status_code}")
            return []
            
        data = response.json()
        points = []
        for element in data.get('elements', []):
            if 'center' in element:
                points.append(Point(element['center']['lon'], element['center']['lat']))
            elif 'lat' in element and 'lon' in element:
                points.append(Point(element['lon'], element['lat']))
        return points
    except Exception as e:
        print(f"  [Error] {e}")
        return []

# Jika total SLS sangat banyak, kita beri limit untuk sampel agar tidak kelamaan (misal max 50 SLS)
# Tapi karena Bahodopi mungkin tidak terlalu banyak (beberapa ratus), kita coba proses semuanya.
# Untuk mempercepat demo, kita filter SLS yang ada di prelist saja!

sls_in_prelist = prelist_df['Kode SLS (16 digit)'].tolist()

processed_count = 0
for i, feature in enumerate(bahodopi_features):
    props = feature['properties']
    
    # Construct 16-digit code: Prov(72) + Kab(03) + Kec(021) + Desa(004) + SLS(0004) + SubSLS(06)
    # Kadang di property KDKAB itu "03", KDKEC "021", dll.
    kode_sls = f"72{props['kdkab']}{props['kdkec']}{props['kddesa']}{props['kdsls']}{props['kdsubsls']}"
    
    if kode_sls not in sls_in_prelist:
        continue # Skip SLS yang tidak masuk daftar penyisiran
        
    geom = shape(feature['geometry'])
    bbox = geom.bounds # (min_lon, min_lat, max_lon, max_lat)
    
    processed_count += 1
    print(f"[{processed_count}] Fetching buildings for {props['nmdesa']} - {props['nmsls']} (Kode: {kode_sls})...")
    
    building_points = get_buildings_in_bbox(bbox)
    
    # Hitung jumlah titik bangunan yang jatuh di DALAM poligon SLS
    buildings_inside = [pt for pt in building_points if geom.contains(pt)]
    count = len(buildings_inside)
    
    print(f"  -> Ditemukan {count} bangunan di dalam poligon.")
    
    results.append({
        'Kode SLS (16 digit)': kode_sls,
        'Estimasi Bangunan Satelit': count
    })
    
    time.sleep(2) # Jeda 2 detik agar tidak di-block oleh Overpass API

print("Memproses DataFrame...")
results_df = pd.DataFrame(results)

if not results_df.empty:
    merged_df = pd.merge(prelist_df, results_df, on='Kode SLS (16 digit)', how='left')
    
    output_filename = 'Hasil_Satelit_Bahodopi.xlsx'
    merged_df.to_excel(output_filename, index=False)
    print(f"BERHASIL! File disimpan ke {output_filename}")
else:
    print("Tidak ada hasil yang diproses (mungkin tidak ada SLS Bahodopi di Prelist).")
