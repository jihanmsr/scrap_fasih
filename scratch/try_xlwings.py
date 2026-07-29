import xlwings as xw

wb = xw.Book('/Users/jihanmaisaroh/scrap_fasih/Progres Sulteng Fasih SM SE2026.xlsx')
ws = wb.sheets['26 Juli']
print(ws.range('O2').formula)
wb.close()
