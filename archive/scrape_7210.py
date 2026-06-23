import sys
import subprocess

print("=== Menjalankan Scraping SE Umum untuk Kabupaten SIGI (7210) ===")
subprocess.run([sys.executable, "scrape_granular_core.py", "se_umum", "7210"])
