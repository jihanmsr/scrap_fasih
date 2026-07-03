import json
import pandas as pd

with open("daily_submission_stats.json", "r") as f:
    stats = json.load(f)

df = pd.DataFrame(stats)
df_morut = df[(df["kab_name"] == "MOROWALI UTARA") & (df["survey_type"] == "se_umum")].sort_values("date")
print("Reconstructed Morut daily stats:")
print(df_morut.to_string(index=False))

df_csv = pd.read_csv("Morowali_Utara_Progres_Harian.csv")
print("\nMorut CSV daily stats (actual from BPS history):")
print(df_csv.to_string(index=False))
