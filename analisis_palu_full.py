import json
import time
import requests
import geopandas as gpd
from shapely.geometry import Point, shape

def get_buildings_in_bbox(bbox):
    # bbox is (min_lon, min_lat, max_lon, max_lat)
    overpass_url = "http://overpass-api.de/api/interpreter"
    overpass_query = f"""
    [out:json][timeout:180];
    (
      way["building"]({bbox[1]},{bbox[0]},{bbox[3]},{bbox[2]});
      relation["building"]({bbox[1]},{bbox[0]},{bbox[3]},{bbox[2]});
    );
    out center;
    """
    try:
        headers = {'User-Agent': 'BPS_Sulteng_SE2026_Script/1.0'}
        response = requests.post(overpass_url, data={'data': overpass_query}, headers=headers, timeout=200)
        response.raise_for_status()
        data = response.json()
        points = []
        for element in data.get('elements', []):
            if 'center' in element:
                points.append(Point(element['center']['lon'], element['center']['lat']))
            elif 'lon' in element and 'lat' in element:
                points.append(Point(element['lon'], element['lat']))
        return points
    except Exception as e:
        print(f"Error querying Overpass: {e}")
        return []

print("Membaca peta SLS...")
with open('petasls.geojson', 'r') as f:
    geojson_data = json.load(f)

# Extract features for Kota Palu and construct 16-digit ID
palu_features = []
for feature in geojson_data['features']:
    props = feature['properties']
    if props.get('nmkab') == 'PALU':
        # Construct 16-digit code: 72 + kdkab + kdkec + kddesa + kdsls + kdsubsls
        kdkab = props.get('kdkab', '')
        kdkec = props.get('kdkec', '')
        kddesa = props.get('kddesa', '')
        kdsls = props.get('kdsls', '')
        kdsubsls = props.get('kdsubsls', '')
        idsls = f"72{kdkab}{kdkec}{kddesa}{kdsls}{kdsubsls}"
        feature['properties']['idsls'] = idsls
        palu_features.append(feature)

print(f"Ditemukan {len(palu_features)} SLS di Kota Palu.")

# Create GeoDataFrame for Palu SLS
gdf_sls = gpd.GeoDataFrame.from_features(palu_features)
gdf_sls.crs = "EPSG:4326"

# Group by Kecamatan to get bounding boxes
kecamatans = gdf_sls['nmkec'].unique()
print(f"Ditemukan {len(kecamatans)} Kecamatan: {kecamatans}")

all_building_points = []

for kec in kecamatans:
    print(f"\nMemproses Kecamatan: {kec}")
    gdf_kec = gdf_sls[gdf_sls['nmkec'] == kec]
    # Get total bounds: (minx, miny, maxx, maxy)
    bounds = gdf_kec.total_bounds
    
    print(f"  Fetching buildings from Overpass API (bbox: {bounds})...")
    pts = get_buildings_in_bbox(bounds)
    print(f"  -> {len(pts)} bangunan ditemukan.")
    all_building_points.extend(pts)
    
    # Sleep to avoid rate limiting
    time.sleep(3)

print(f"\nTotal {len(all_building_points)} bangunan ditarik dari seluruh Kota Palu.")

# Create GeoDataFrame for buildings
print("Melakukan Spatial Join (mencocokkan titik bangunan ke dalam poligon SLS)...")
gdf_buildings = gpd.GeoDataFrame(geometry=all_building_points, crs="EPSG:4326")

# sjoin: points within polygons
# This returns a dataframe where each point has the attributes of the polygon it falls into
joined = gpd.sjoin(gdf_buildings, gdf_sls, how="inner", predicate="within")

# Group by idsls and count
building_counts = joined.groupby('idsls').size().to_dict()

# Create final dictionary mapping idsls -> count
print("Menyusun data akhir...")
final_mapping = {}
for index, row in gdf_sls.iterrows():
    idsls = str(row['idsls'])
    count = building_counts.get(idsls, 0)
    final_mapping[idsls] = count

output_js = f"window.PALU_SATELIT_DATA = {json.dumps(final_mapping)};"

print("Menyimpan ke dashboard_satelit/palu_data.js...")
with open('dashboard_satelit/palu_data.js', 'w') as f:
    f.write(output_js)

print("Selesai! Data bangunan Kota Palu berhasil di-generate.")
