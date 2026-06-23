import sys
import subprocess

print("=== Menjalankan Scraping SE UB untuk Seluruh Sulawesi Tengah ===")
subprocess.run([sys.executable, "scrape_granular_core.py", "se_ub", "all"])
