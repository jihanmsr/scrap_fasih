import os
import re
import csv
import glob
import subprocess
import string
import pandas as pd
import subprocess
import string

def clean_name(name_str):
    # Remove titles
    name_str = re.sub(r'II\.[AB]\s+', '', name_str)
    # Remove common titles
    titles = ['Dr.', 'Ir.', 'Drs.', 'S.T.', 'M.Si.', 'M.T', 'SE.', 'S.Hut.', 'SH', 'M.Kes', 'S.STP.', 'M.A.P', 'SE', 'M.M', 'M.Pd', 'SH.', 'LL.M', 'SKM,', 'M.SA', 'S.Sos.', 'M.Si', 'M.H', 'AP.', 'dr.', 'drg.']
    # Removing anything with a dot or comma or known titles
    parts = name_str.split(',')
    name_only = parts[0]
    words = name_only.split()
    clean_words = []
    for w in words:
        if '.' not in w and w not in titles:
            clean_words.append(w)
    
    clean = " ".join(clean_words).strip().upper()
    return clean

# Get text from pdf
pdf_path = "/Users/jihanmaisaroh/scrap_fasih/Dokumen_BKD1786333105_Pejabat JPT Agustus 2026.pdf"
result = subprocess.run(["pdftotext", pdf_path, "-"], capture_output=True, text=True)
pdf_text = result.stdout

# Extract names
names_raw = re.findall(r'II\.[AB]\s+[A-Za-z., ]+', pdf_text)
pejabat_names = []
for nr in names_raw:
    clean = clean_name(nr)
    if clean:
        pejabat_names.append((nr.strip(), clean))

print(f"Extracted {len(pejabat_names)} names from PDF.")

# Now search in Keluarga Hilang CSVs
csv_folder = "/Users/jihanmaisaroh/scrap_fasih/Keluarga Hilang/"
csv_files = glob.glob(csv_folder + "*.csv")

matches = []

for file in csv_files:
    with open(file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            nama_kk = row.get('nama_kepala_keluarga', '').upper()
            if not nama_kk:
                continue
            
            # check if any pejabat matches
            for raw, clean in pejabat_names:
                if clean == nama_kk.strip():
                    matches.append({
                        'pejabat_raw': raw,
                        'pejabat_clean': clean,
                        'csv_file': os.path.basename(file),
                        'nama_kk': nama_kk,
                        'kab': row.get('kab'),
                        'kec': row.get('kec'),
                        'desa': row.get('desa'),
                        'status': row.get('status_keluarga'),
                        'link': row.get('link_fasih')
                    })

print(f"Found {len(matches)} potential matches.")

# Convert to DataFrames
df_matches = pd.DataFrame(matches)
df_pejabat = pd.DataFrame(pejabat_names, columns=['pejabat_raw', 'pejabat_clean'])

output_excel = "/Users/jihanmaisaroh/scrap_fasih/hasil_matching_pejabat_keluarga_hilang.xlsx"

with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
    df_matches.to_excel(writer, sheet_name='Hasil Matching', index=False)
    df_pejabat.to_excel(writer, sheet_name='List Pejabat', index=False)

print(f"Results saved to {output_excel}")

