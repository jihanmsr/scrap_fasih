import sys
import subprocess

print("=== Menjalankan Scraping SE Umum untuk Kabupaten DONGGALA (7205) ===")
subprocess.run([sys.executable, "scrape_granular_core.py", "se_umum", "7205"])
