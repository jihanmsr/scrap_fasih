import pandas as pd

excel_path = "/Users/jihanmaisaroh/scrap_fasih/Progres Sulteng Fasih SM SE2026.xlsx"
csv2_path = "/Users/jihanmaisaroh/scrap_fasih/progress-assignment-fd68e454-ba45-4b85-8205-f3bf777ded24 (2).csv"

# Load Excel
df_6 = pd.read_excel(excel_path, sheet_name="6 Juli")
df_7 = pd.read_excel(excel_path, sheet_name="7 Juli")

print("--- EXCEL 6 JULI SUM ---")
total_target_6 = df_6['Total'].sum()
# In sheet 6 Juli, 'Not Draft + Open' is the submitted/completed count.
total_submitted_6 = df_6['Not Draft + Open'].sum()
pct_6 = (total_submitted_6 / total_target_6) * 100
print(f"Total Target: {total_target_6}, Total Submitted: {total_submitted_6}, Pct: {pct_6:.6f}%")

print("\n--- EXCEL 7 JULI TOTAL ROW (7200.0) ---")
total_row_7 = df_7[df_7['Wilayah'] == 7200.0]
if not total_row_7.empty:
    print(total_row_7[['Wilayah', 'Total', 'Not Draft + Open', 'Persentase']])

# Let's sum the other rows of 7 Juli (excluding 7200.0)
df_7_districts = df_7[(df_7['Wilayah'] != 7200.0) & (df_7['Wilayah'].notna())]
total_target_7_sum = df_7_districts['Total'].sum()
total_submitted_7_sum = df_7_districts['Not Draft + Open'].sum()
print(f"Sum of 7 Juli districts - Target: {total_target_7_sum}, Submitted: {total_submitted_7_sum}, Pct: {(total_submitted_7_sum/total_target_7_sum)*100:.6f}%")

print("\n--- CSV 2 SUM ---")
df_c2 = pd.read_csv(csv2_path, sep=";")
c2_target = df_c2['Column1'].sum()
c2_submitted = df_c2['Column2'].sum()
c2_pct = (c2_submitted / c2_target) * 100
print(f"Total Target (Column1): {c2_target}, Total Submitted (Column2): {c2_submitted}, Pct: {c2_pct:.6f}%")
