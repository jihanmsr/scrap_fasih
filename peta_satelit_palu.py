import json
import requests
import folium
from shapely.geometry import shape, Point
import time
import os

print("Membaca peta SLS...")
with open('petasls.geojson', 'r') as f:
    geojson_data = json.load(f)

# Filter untuk Kota Palu, misalnya Kecamatan MANTIKULORE (karena Palu besar sekali)
palu_features = []
for feature in geojson_data['features']:
    props = feature['properties']
    if props.get('nmkab') == 'PALU' and props.get('nmkec') == 'MANTIKULORE':
        palu_features.append(feature)

print(f"Ditemukan {len(palu_features)} SLS di MANTIKULORE, Kota Palu.")

# Kita limit 5 SLS saja agar API Overpass tidak lama & timeout
limit = 5
selected_features = palu_features[:limit]
print(f"Memproses {limit} SLS sebagai sampel pemetaan satelit...")

def get_buildings_in_bbox(bbox):
    # bbox format: (min_lon, min_lat, max_lon, max_lat)
    # Overpass expects: (south, west, north, east) -> (min_lat, min_lon, max_lat, max_lon)
    overpass_url = "http://overpass-api.de/api/interpreter"
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
        response = requests.post(overpass_url, data={'data': overpass_query}, headers=headers, timeout=30)
        if response.status_code != 200:
            return []
            
        data = response.json()
        points = []
        for element in data.get('elements', []):
            if 'center' in element:
                points.append((element['center']['lon'], element['center']['lat']))
            elif 'lat' in element and 'lon' in element:
                points.append((element['lon'], element['lat']))
        return points
    except Exception as e:
        print(f"Error: {e}")
        return []

# Initialize map centered around Palu with Google Satellite Imagery
m = folium.Map(
    location=[-0.8917, 119.8707], 
    zoom_start=14,
    tiles='https://mt0.google.com/vt/lyrs=s&hl=en&x={x}&y={y}&z={z}',
    attr='Google Satellite'
)

for i, feature in enumerate(selected_features):
    props = feature['properties']
    kode_sls = f"72{props.get('kdkab','')}{props.get('kdkec','')}{props.get('kddesa','')}{props.get('kdsls','')}{props.get('kdsubsls','')}"
    
    geom = shape(feature['geometry'])
    bbox = geom.bounds 
    
    print(f"[{i+1}/{limit}] Fetching buildings for {props.get('nmdesa')} - {props.get('nmsls')}...")
    
    # Add SLS Polygon to Map
    folium.GeoJson(
        feature,
        name=props.get('nmsls'),
        style_function=lambda x: {'fillColor': '#3b82f6', 'color': '#3b82f6', 'weight': 2, 'fillOpacity': 0.2},
        tooltip=f"{props.get('nmsls')} (Kode: {kode_sls})"
    ).add_to(m)
    
    # Get building points
    building_points = get_buildings_in_bbox(bbox)
    
    buildings_inside = []
    for pt in building_points:
        point_obj = Point(pt[0], pt[1])
        if geom.contains(point_obj):
            buildings_inside.append(pt)
            
    print(f"  -> {len(buildings_inside)} bangunan ditemukan di dalam poligon.")
    
    # Add building points to Map
    for pt in buildings_inside:
        folium.CircleMarker(
            location=[pt[1], pt[0]], # folium uses (lat, lon)
            radius=3,
            color='#10b981',
            fill=True,
            fill_color='#10b981',
            fill_opacity=0.7
        ).add_to(m)
        
    time.sleep(2) # Respect Overpass API rate limits

# Save Map
output_path = os.path.join('dashboard_satelit', 'peta_satelit_palu.html')
m.save(output_path)
print(f"Peta satelit berhasil dibuat: {output_path}")
