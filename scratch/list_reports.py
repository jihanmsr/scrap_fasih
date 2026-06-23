import glob
import os

script_dir = "/Users/jihanmaisaroh/scrap_fasih"
print("Laporan Excel files:")
print(glob.glob(os.path.join(script_dir, "Laporan_*.xlsx")))
print("Detail Usaha CSV files:")
print(glob.glob(os.path.join(script_dir, "Detail_Usaha_*.csv")))
