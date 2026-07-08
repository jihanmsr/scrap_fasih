import pandas as pd

csv3_path = "/Users/jihanmaisaroh/scrap_fasih/progress-assignment-fd68e454-ba45-4b85-8205-f3bf777ded24 (3).csv"
df_c3 = pd.read_csv(csv3_path)

# Let's see the columns and calculate sums
print("Columns in CSV 3:", list(df_c3.columns))

# Compute total submitted = APPROVED BY Pengawas + SUBMITTED BY Pencacah + EDITED BY Admin Kabupaten + EDITED BY Pengawas + COMPLETED BY Admin Kabupaten + REJECTED BY Pengawas + REVOKED BY Pengawas + SUBMITTED RESPONDENT + REJECTED BY Admin Kabupaten
# Let's print out the sums of each column to see what we have
cols_to_sum = [c for c in df_c3.columns if c != 'Wilayah']
for col in cols_to_sum:
    print(f"{col}: {df_c3[col].sum()}")

# Calculate total target and total submitted
draft = df_c3.get("DRAFT", 0).fillna(0)
open_val = df_c3.get("OPEN", 0).fillna(0)
submitted_pencacah = df_c3.get("SUBMITTED BY Pencacah", 0).fillna(0) + df_c3.get("EDITED BY Admin Kabupaten", 0).fillna(0) + df_c3.get("EDITED BY Pengawas", 0).fillna(0) + df_c3.get("COMPLETED BY Admin Kabupaten", 0).fillna(0)
submitted_respondent = df_c3.get("SUBMITTED RESPONDENT", 0).fillna(0)
approved = df_c3.get("APPROVED BY Pengawas", 0).fillna(0)
rejected = df_c3.get("REJECTED BY Pengawas", 0).fillna(0) + df_c3.get("REVOKED BY Pengawas", 0).fillna(0) + df_c3.get("REJECTED BY Admin Kabupaten", 0).fillna(0)

total_submitted = submitted_pencacah + submitted_respondent + approved + rejected
total_prelist = draft + open_val + total_submitted

overall_target = total_prelist.sum()
overall_submitted = total_submitted.sum()
print(f"Overall Target: {overall_target}, Overall Submitted: {overall_submitted}, Pct: {(overall_submitted/overall_target)*100:.6f}%")
