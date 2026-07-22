import sys

filename = "scrape_dashboard_via_cdp.py"
with open(filename, "r") as f:
    content = f.read()

old_logic = """        # --- AUTOMATIC DELTA CALCULATION ---
        try:
            def apply_auto_delta(survey_data):
                for kab in survey_data:
                    today_comp = kab.get("today_completed", 0)
                    total_prelist = kab.get("total_prelist", 0)
                    if total_prelist > 0:
                        delta = (today_comp / total_prelist) * 100
                        kab["delta_persen"] = round(delta, 2)
                    else:
                        kab["delta_persen"] = 0.0"""

new_logic = """        # --- AUTOMATIC DELTA CALCULATION ---
        try:
            def apply_auto_delta(survey_data):
                for kab in survey_data:
                    today_comp = kab.get("today_completed", 0)
                    yesterday_comp = kab.get("yesterday_completed", 0)
                    lusa_comp = kab.get("two_days_ago_completed", 0)
                    total_prelist = kab.get("total_prelist", 0)
                    if total_prelist > 0:
                        kab["delta_persen"] = round((today_comp / total_prelist) * 100, 2)
                        kab["delta_kemarin_persen"] = round((yesterday_comp / total_prelist) * 100, 2)
                        kab["delta_lusa_persen"] = round((lusa_comp / total_prelist) * 100, 2)
                    else:
                        kab["delta_persen"] = 0.0
                        kab["delta_kemarin_persen"] = 0.0
                        kab["delta_lusa_persen"] = 0.0"""

if old_logic in content:
    content = content.replace(old_logic, new_logic)
    with open(filename, "w") as f:
        f.write(content)
    print("Updated scrape_dashboard_via_cdp.py")
else:
    print("Could not find old logic in scrape_dashboard_via_cdp.py")
