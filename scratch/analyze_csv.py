import pandas as pd
import re

# Read the CSV
file_path = "/Users/jihanmaisaroh/scrap_fasih/Sulteng_Pertanian.csv"
df = pd.read_csv(file_path, on_bad_lines='warn')

print("Columns:", df.columns.tolist())
print(df[['assignment_id', 'nama_usaha_prelist']].head(5))

# Let's see if there are missing or merged columns by checking the number of columns per row
print("Shape:", df.shape)

