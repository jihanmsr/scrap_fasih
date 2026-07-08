import openpyxl
import pandas as pd

excel_path = "/Users/jihanmaisaroh/scrap_fasih/Progres Sulteng Fasih SM SE2026.xlsx"
try:
    wb = openpyxl.load_workbook(excel_path)
    for sheet_name in ['6 Juli', '7 Juli']:
        df = pd.read_excel(excel_path, sheet_name=sheet_name)
        print(f"\n================ SHEET: {sheet_name} ================")
        print(df.to_string())
except Exception as e:
    print("Error:", e)
