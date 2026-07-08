import pandas as pd
import sqlite3

# Load data detail / pegawai
df = pd.read_csv('/Users/jihanmaisaroh/scrap_fasih/Sulteng_Rekap_Pegawai.csv')
emails_in_data = set(df['Username'].str.lower().str.strip().dropna())

# Load master_petugas
conn = sqlite3.connect('/Users/jihanmaisaroh/scrap_fasih/master_data.db')
cursor = conn.cursor()
cursor.execute("SELECT email, nama_petugas FROM master_petugas")
master_data = {row[0].lower().strip(): row[1] for row in cursor.fetchall()}
conn.close()

# Count matches
found_emails = 0
missing_emails = 0
missing_list = []

for email in emails_in_data:
    # Filter out empty or non-emails
    if "@" not in email:
        continue
    
    if email in master_data:
        found_emails += 1
    else:
        missing_emails += 1
        missing_list.append(email)

print(f"Total email unik di data (Rekap Pegawai): {len([e for e in emails_in_data if '@' in e])}")
print(f"Email yang SUDAH ada namanya di database: {found_emails}")
print(f"Email yang BELUM ada namanya di database: {missing_emails}")
if missing_emails > 0:
    print("Contoh 10 email yang belum ada namanya:")
    for m in missing_list[:10]:
        print(f" - {m}")
