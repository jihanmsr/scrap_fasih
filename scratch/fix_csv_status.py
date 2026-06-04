import pandas as pd
import os

csv_path = "/Users/jihanmaisaroh/scrap_fasih/all_email_history.csv"
if not os.path.exists(csv_path):
    print("CSV not found.")
    exit()

df = pd.read_csv(csv_path)

status_priority = {'bounced': 6, 'dropped': 5, 'deferred': 4, 'delivered': 3, 'processed': 2, 'queued': 1}

# Group by code and update Global Status
def get_best_status(group):
    best_score = -1
    best_status = "-"
    for st in group['Status History']:
        if pd.isna(st):
            continue
        st_lower = str(st).lower()
        score = status_priority.get(st_lower, 0)
        if score > best_score:
            best_score = score
            best_status = st
    
    # If no valid status, keep original logic or "-"
    if best_status == "-":
        return group['Status terakhir'].iloc[-1]
    return best_status

# Apply to dataframe
for code, group in df.groupby("Kode Identitas"):
    if code == "-":
        continue
    best = get_best_status(group)
    df.loc[df["Kode Identitas"] == code, "Status terakhir"] = best

df.to_csv(csv_path, index=False)
print("Berhasil memperbaiki Global Status di CSV berdasarkan prioritas Delivered > Queued!")
