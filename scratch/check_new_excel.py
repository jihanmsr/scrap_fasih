import pandas as pd
import glob

files = glob.glob("SE2026_66_*.xlsx")
for f in files:
    try:
        df = pd.read_excel(f, sheet_name=0)
        print(f"--- {f} ---")
        print(df.columns.tolist())
        print(df.head(2).to_string())
    except Exception as e:
        print(f"Error reading {f}: {e}")
