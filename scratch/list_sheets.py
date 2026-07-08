import os
import openpyxl
import pandas as pd

for f in os.listdir("/Users/jihanmaisaroh/scrap_fasih"):
    if f.endswith(".xlsx") and not f.startswith("~$"):
        path = os.path.join("/Users/jihanmaisaroh/scrap_fasih", f)
        try:
            wb = openpyxl.load_workbook(path, read_only=True)
            print(f"File: {f}, Sheets: {wb.sheetnames}")
        except Exception as e:
            print(f"Error {f}: {e}")
