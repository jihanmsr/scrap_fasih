import sys
import subprocess

print("=== Menjalankan Scraping SE Umum untuk Kabupaten PARIGI MOUTONG (7208) ===")
subprocess.run([sys.executable, "scrape_granular_core.py", "se_umum", "7208"])
