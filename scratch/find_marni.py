from python_calamine import CalamineWorkbook
import glob

files = glob.glob("/Users/jihanmaisaroh/scrap_fasih/SE2026_66_*.xlsx")
for f in files:
    try:
        wb = CalamineWorkbook.from_path(f)
        data = wb.get_sheet_by_index(0).to_python()
        for row in data:
            for cell in row:
                if 'marniksanudin4' in str(cell).lower():
                    print(f"FOUND IN {f}: {row}")
    except Exception as e:
        pass
