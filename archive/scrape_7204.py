import sys
import subprocess

print("=== Menjalankan Scraping SE Umum untuk Kabupaten POSO (7204) ===")
subprocess.run([sys.executable, "scrape_granular_core.py", "se_umum", "7204"])
