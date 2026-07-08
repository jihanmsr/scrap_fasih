import pandas as pd
import json
import os

CSV_PATH = '/Users/jihanmaisaroh/scrap_fasih/Sulteng_Rekap_Pegawai.csv'
JS_PATH = '/Users/jihanmaisaroh/scrap_fasih/petugas_progress.js'

def export():
    df = pd.read_csv(CSV_PATH)
    petugas_map = {}
    for idx, row in df.iterrows():
        email = str(row.get('Username', '')).strip().lower()
        if not email:
            continue
        petugas_map[email] = {
            'target': int(row.get('Total Target', 0)),
            'submitted_pencacah': int(row.get('Submitted by Pencacah', 0)),
            'submitted_respondent': int(row.get('Submitted Respondent', 0)),
            'approved': int(row.get('Approved by Pengawas', 0)),
            'rejected': int(row.get('Rejected by Pengawas', 0)),
            'draft': int(row.get('Draft', 0)),
            'open': int(row.get('Open', 0))
        }
    
    with open(JS_PATH, 'w', encoding='utf-8') as f:
        f.write(f"window.PETUGAS_PROGRESS_MAP = {json.dumps(petugas_map, indent=4)};\n")
    print(f"Exported {len(petugas_map)} petugas progress to {JS_PATH}")

if __name__ == '__main__':
    export()
