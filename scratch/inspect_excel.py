import pandas as pd

file_path = "/Users/jihanmaisaroh/scrap_fasih/Rekap Mitra SE2026.xlsx"
try:
    xl = pd.ExcelFile(file_path)
    print("Sheets:", xl.sheet_names)
    
    for sheet in xl.sheet_names:
        print(f"\n--- Sheet: {sheet} ---")
        df = pd.read_excel(file_path, sheet_name=sheet, nrows=5)
        print("Columns:")
        print(df.columns.tolist())
        print("\nHead:")
        print(df.head())
except Exception as e:
    print(f"Error reading excel: {e}")
