import sys
import subprocess

print("=== Menjalankan Scraping SE Umum untuk Kabupaten BANGGAI LAUT (7211) ===")
subprocess.run([sys.executable, "scrape_granular_core.py", "se_umum", "7211"])
