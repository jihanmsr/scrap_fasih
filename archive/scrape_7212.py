import sys
import subprocess

print("=== Menjalankan Scraping SE Umum untuk Kabupaten MOROWALI UTARA (7212) ===")
subprocess.run([sys.executable, "scrape_granular_core.py", "se_umum", "7212"])
