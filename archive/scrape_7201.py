import sys
import subprocess

print("=== Menjalankan Scraping SE Umum untuk Kabupaten BANGGAI KEPULAUAN (7201) ===")
subprocess.run([sys.executable, "scrape_granular_core.py", "se_umum", "7201"])
