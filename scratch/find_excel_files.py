import glob
import os

script_dir = "/Users/jihanmaisaroh/scrap_fasih"
print("All files ending with .xlsx in script_dir:")
print(glob.glob(os.path.join(script_dir, "*.xlsx")))
print("All files ending with .xlsx in script_dir/scratch:")
print(glob.glob(os.path.join(script_dir, "scratch", "*.xlsx")))
