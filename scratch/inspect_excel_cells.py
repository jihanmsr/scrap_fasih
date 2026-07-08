import openpyxl

excel_path = "/Users/jihanmaisaroh/scrap_fasih/Progres Sulteng Fasih SM SE2026.xlsx"
wb = openpyxl.load_workbook(excel_path)
for sheet_name in ['6 Juli', '7 Juli']:
    sheet = wb[sheet_name]
    print(f"\n================ SHEET: {sheet_name} ================")
    # Print the first 3 rows and check for formulas
    for row in list(sheet.iter_rows(values_only=False))[:15]:
        row_vals = [cell.value for cell in row]
        if any(v is not None for v in row_vals):
            # Print cell coordinate and cell value/formula
            print([f"{cell.coordinate}: {cell.value}" for cell in row if cell.value is not None])
