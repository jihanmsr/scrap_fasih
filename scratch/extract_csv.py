import pandas as pd
import re

file_path = "/Users/jihanmaisaroh/scrap_fasih/Sulteng_Pertanian.csv"
output_path = "/Users/jihanmaisaroh/scrap_fasih/Sulteng_Pertanian_Extracted.xlsx"

print("Loading data...")
df = pd.read_csv(file_path, dtype=str)

# Function to extract keys from the pseudo-JSON string
def extract_fields(val):
    if pd.isna(val):
        return pd.Series({'prelist_subsektor': '', 'prelist_label': '', 'prelist_source': ''})
    
    # Extract all occurrences of subsektor=..., label=..., source=...
    subsektors = re.findall(r'subsektor=([^,}]+)', val)
    labels = re.findall(r'label=([^,}]+)', val)
    sources = re.findall(r'source=([^,}]+)', val)
    
    return pd.Series({
        'prelist_subsektor': ' | '.join([s.strip() for s in subsektors if s.strip() != 'null']),
        'prelist_label': ' | '.join([l.strip() for l in labels if l.strip() != 'null']),
        'prelist_source': ' | '.join([s.strip() for s in sources if s.strip() != 'null'])
    })

print("Extracting columns...")
# Apply extraction
extracted_df = df['nama_usaha_prelist'].apply(extract_fields)

# Concatenate with original dataframe
df_final = pd.concat([df, extracted_df], axis=1)

# Reorder columns slightly to put the extracted ones next to nama_usaha_prelist
cols = df_final.columns.tolist()
idx = cols.index('nama_usaha_prelist')
# Move extracted columns to right after nama_usaha_prelist
new_cols = cols[:idx+1] + ['prelist_subsektor', 'prelist_label', 'prelist_source'] + [c for c in cols[idx+1:] if c not in ['prelist_subsektor', 'prelist_label', 'prelist_source']]
df_final = df_final[new_cols]

print("Saving to Excel...")
# Using xlsxwriter or openpyxl. Let's just save as a semicolon separated CSV since it's 280k rows, Excel can open it if separated by semicolon, and saving to xlsx for 280k rows might take some time and memory.
# Actually, saving as CSV with semicolon is faster and guarantees no merging.
output_csv_path = "/Users/jihanmaisaroh/scrap_fasih/Sulteng_Pertanian_Extracted.csv"
df_final.to_csv(output_csv_path, sep=';', index=False)
print(f"Saved successfully to {output_csv_path}")

