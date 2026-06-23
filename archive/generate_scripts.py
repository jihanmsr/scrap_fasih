import os

kab_codes = [
    ("7201", "BANGGAI KEPULAUAN"),
    ("7202", "BANGGAI"),
    ("7203", "MOROWALI"),
    ("7204", "POSO"),
    ("7205", "DONGGALA"),
    ("7206", "TOLI-TOLI"),
    ("7207", "BUOL"),
    ("7208", "PARIGI MOUTONG"),
    ("7209", "TOJO UNA-UNA"),
    ("7210", "SIGI"),
    ("7211", "BANGGAI LAUT"),
    ("7212", "MOROWALI UTARA"),
    ("7271", "PALU")
]

template = """import sys
import subprocess

print("=== Menjalankan Scraping SE Umum untuk Kabupaten {name} ({code}) ===")
subprocess.run([sys.executable, "scrape_granular_core.py", "se_umum", "{code}"])
"""

for code, name in kab_codes:
    filename = f"scrape_{code}.py"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(template.format(code=code, name=name))
    print(f"Created {filename}")
    
# SE UB Script
ub_template = """import sys
import subprocess

print("=== Menjalankan Scraping SE UB untuk Seluruh Sulawesi Tengah ===")
subprocess.run([sys.executable, "scrape_granular_core.py", "se_ub", "all"])
"""
with open("scrape_se_ub.py", "w", encoding="utf-8") as f:
    f.write(ub_template)
print("Created scrape_se_ub.py")

# Master All Script
all_template = """import sys
import subprocess

print("=== Menjalankan Scraping Seluruh Kabupaten (Berurutan) ===")
scripts = [
"""
for code, _ in kab_codes:
    all_template += f'    "scrape_{code}.py",\n'
all_template += '    "scrape_se_ub.py"\n]\n\n'
all_template += """for s in scripts:
    subprocess.run([sys.executable, s])
print("=== SEMUA PROSES SCRAPING SELESAI ===")
"""
with open("scrape_sulteng_all.py", "w", encoding="utf-8") as f:
    f.write(all_template)
print("Created scrape_sulteng_all.py")
