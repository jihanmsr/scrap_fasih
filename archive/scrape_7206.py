import sys
import subprocess

print("=== Menjalankan Scraping SE Umum untuk Kabupaten TOLI-TOLI (7206) ===")
subprocess.run([sys.executable, "scrape_granular_core.py", "se_umum", "7206"])
