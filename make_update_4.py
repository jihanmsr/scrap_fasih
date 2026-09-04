import re

with open('/Users/jihanmaisaroh/scrap_fasih/update_1sept_all.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Change directories
content = content.replace("update_1sept", "update_4")
content = content.replace("1 SEPTEMBER", "4 SEPTEMBER")

# 2. Change file paths
content = content.replace("'Rekap Progress Petugas 01_09.xlsx'", "os.path.join(UPDATE_DIR, 'rekap_progress_petugas (6).xlsx')")
content = content.replace("'rekap_sbr_utp_keluarga (5).xlsx'", "'rekap_sbr_utp_keluarga (6).xlsx'")
content = content.replace("'Rekap Progress Petugas 01_09.xlsx'", "'rekap_progress_petugas (6).xlsx'")
content = content.replace("'Rekap SBR, UTP, Keluarga_20260901.xlsx'", "'Rekap SBR, UTP, Keluarga_20260904.xlsx'")
content = content.replace("'Laporan_Rekap_KabKot_SBR_UTP_Keluarga_01_09.xlsx'", "'Laporan_Rekap_KabKot_SBR_UTP_Keluarga_04_09.xlsx'")
content = content.replace("'fast_petugas_all_2026-09-01.csv'", "'fast_petugas_all_2026-09-04.csv'")

# 3. Rewrite update_sls_open function to empty everything
sls_open_code = """def update_sls_open(df_prog=None):
    print("\\n" + "="*60)
    print("  [3/3] UPDATE MENU SLS OPEN (OPEN_SUBSLS_DATA & HIGHLIGHTED) -> 0")
    print("="*60)
    
    with open(os.path.join(BASE_DIR, 'open_subsls_data.js'), 'w', encoding='utf-8') as f:
        f.write('window.OPEN_SUBSLS_DATA = [];')

    with open(os.path.join(BASE_DIR, 'highlighted_subsls.js'), 'w', encoding='utf-8') as f:
        f.write('window.HIGHLIGHTED_SUBSLS = {};')

    with open(os.path.join(BASE_DIR, 'highlighted_subsls.json'), 'w', encoding='utf-8') as f:
        f.write('{}')

    print("    OK open_subsls_data.js & highlighted_subsls.js Dikosongkan (0).")
"""

content = re.sub(r'def update_sls_open\(.*?\):.*?(?=# ============================================================)', sls_open_code + '\n\n', content, flags=re.DOTALL)

with open('/Users/jihanmaisaroh/scrap_fasih/update_4_all.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Generated update_4_all.py")
