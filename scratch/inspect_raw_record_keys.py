import os
import json
import gzip
import base64

script_dir = "/Users/jihanmaisaroh/scrap_fasih"
fpath = os.path.join(script_dir, "granular_assignments_se_umum_7201.json")

if os.path.exists(fpath):
    with open(fpath, "r", encoding="utf-8") as f:
        data = json.load(f)
    comp = data.get("compressed_data")
    if comp:
        # Wait, raw JSON from scrape_granular_core contains raw_se_umum_data?
        # No, raw has "regions", "petugas", "statuses", "targets", "remarks".
        # Targets are compressed lists: [tid, code_id, name, stat_idx, pet_idx, reg_idx, epoch_mod, survey_flag]
        # Let's check if there are raw json files from scraping, or if we can see what fields are fetched from BPS API.
        pass
        
# Let's inspect raw records if we can find any file with raw_se_umum_data or similar
raw_files = glob = "/Users/jihanmaisaroh/scrap_fasih/scratch/captured_payloads.json"
# Or let's see if we can find any .json that is not granular_assignments.
# Let's search for "dateCreated" or "dateModified" in scrape_granular_core.py to see where it parses BPS API.
