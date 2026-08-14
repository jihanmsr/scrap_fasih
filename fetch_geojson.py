import urllib.request
import json
import ssl

url = "https://raw.githubusercontent.com/superpikar/indonesia-geojson/master/indonesia-regency-kabupaten.geojson"
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

try:
    with urllib.request.urlopen(url, context=ctx) as response:
        data = json.loads(response.read().decode('utf-8'))
        
        sulteng_features = []
        for feature in data.get('features', []):
            prop = feature.get('properties', {})
            # Usually the name is in 'NAME_2' for kabupaten, or 'Propinsi'
            # We can just check if 'SULAWESI TENGAH' is in the properties
            is_sulteng = False
            for k, v in prop.items():
                if isinstance(v, str) and 'SULAWESI TENGAH' in v.upper():
                    is_sulteng = True
                    break
                if k == 'Provinsi' and 'SULAWESI TENGAH' in str(v).upper():
                    is_sulteng = True
                    break
            
            if is_sulteng:
                sulteng_features.append(feature)
        
        sulteng_geojson = {
            "type": "FeatureCollection",
            "features": sulteng_features
        }
        
        print(f"Found {len(sulteng_features)} kabupaten in Sulteng.")
        
        with open('sulteng_kab_geojson.js', 'w', encoding='utf-8') as f:
            f.write('window.SULTENG_GEOJSON = ' + json.dumps(sulteng_geojson) + ';')
except Exception as e:
    print("Error:", e)
