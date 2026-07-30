import re

def process_kecamatan_deltas(new_kec_list, prev_kec_list, delta_days):
    prev_kec_map = {k["kecamatan"]: k for k in prev_kec_list}
    
    for curr_obj in new_kec_list:
        kec_name = curr_obj["kecamatan"]
        prev_obj = prev_kec_map.get(kec_name, {})
        
        # calculate_delta_counters logic goes here
        # (similar to what is done for kabupaten)
