import openpyxl

wb = openpyxl.load_workbook('/Users/jihanmaisaroh/scrap_fasih/Progres Sulteng Fasih SM SE2026.xlsx')
ws = wb['26 Juli']

# The adjusted values for M2 to M14
adjusted_values = {
    '[01] BANGGAI KEPULAUAN': 31254,
    '[02] BANGGAI': 92470,
    '[03] MOROWALI': 32346,
    '[04] POSO': 65363,
    '[05] DONGGALA': 75694,
    '[06] TOLI-TOLI': 52736,
    '[07] BUOL': 36555,
    '[08] PARIGI MOUTONG': 112275,
    '[09] TOJO UNA-UNA': 40839,
    '[10] SIGI': 67469,
    '[11] BANGGAI LAUT': 20208,
    '[12] MOROWALI UTARA': 24474,
    '[71] PALU': 89990
}

# Apply to M2 to M14
total_baru = 0
for row_idx in range(2, 15):
    kab_name = ws[f'A{row_idx}'].value
    if kab_name in adjusted_values:
        baru = adjusted_values[kab_name]
        ws[f'M{row_idx}'].value = baru
        total_baru += baru

# Update Total at M15
ws['M15'].value = total_baru

# Save the workbook
wb.save('/Users/jihanmaisaroh/scrap_fasih/Progres Sulteng Fasih SM SE2026.xlsx')
print("Successfully updated Excel file.")
