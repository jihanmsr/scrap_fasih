import pandas as pd
df = pd.read_excel("Biodata_Mitra Afirmasi_Rekap Nilam Sari Sulteng (1).xlsx", sheet_name=0, header=None)
print(df.head(10).to_string())
