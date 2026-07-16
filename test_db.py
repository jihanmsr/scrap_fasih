import sqlite3
conn = sqlite3.connect('granular_data.db')
c = conn.cursor()
c.execute("SELECT COUNT(*) FROM granular_records WHERE is_tambahan=1 AND is_usaha=1")
print("Total Usaha:", c.fetchone()[0])
c.execute("SELECT COUNT(*) FROM granular_records WHERE is_tambahan=1 AND is_usaha=0")
print("Total Rumah:", c.fetchone()[0])
