import sys
import subprocess

print("=== Menjalankan Scraping Seluruh Kabupaten (Berurutan) ===")
scripts = [
    "scrape_7201.py",
    "scrape_7202.py",
    "scrape_7203.py",
    "scrape_7204.py",
    "scrape_7205.py",
    "scrape_7206.py",
    "scrape_7207.py",
    "scrape_7208.py",
    "scrape_7209.py",
    "scrape_7210.py",
    "scrape_7211.py",
    "scrape_7212.py",
    "scrape_7271.py",
    "scrape_se_ub.py"
]

for s in scripts:
    subprocess.run([sys.executable, s])

print("=== MENGGABUNGKAN SEMUA HASIL ===")
subprocess.run([sys.executable, "merge_granulars.py"])

print("=== SEMUA PROSES SCRAPING SELESAI ===")
