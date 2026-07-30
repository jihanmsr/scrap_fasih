import json
from scrape_granular_core import region_map_full

# Print structure of region_map_full
print(list(region_map_full.keys()))
kabupatens = region_map_full.get("kabupaten", {})
first_kab_code = list(kabupatens.keys())[0]
print(f"Kab {first_kab_code}:", list(kabupatens[first_kab_code].keys()))
kecamatans = kabupatens[first_kab_code].get("kecamatan", {})
first_kec_code = list(kecamatans.keys())[0]
print(f"Kec {first_kec_code} id:", kecamatans[first_kec_code].get("id"))
