from python_calamine import CalamineWorkbook
wb = CalamineWorkbook.from_path("/Users/jihanmaisaroh/scrap_fasih/SE2026_66_7205_exportmitra_2026-07-08_095609.xlsx")
data = wb.get_sheet_by_index(0).to_python()
print("HEADERS:", data[0])
