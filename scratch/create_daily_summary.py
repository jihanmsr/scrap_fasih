import sqlite3

DB_PATH = '/Users/jihanmaisaroh/scrap_fasih/granular_data.db'
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Drop existing table to ensure fresh data
cursor.execute("DROP TABLE IF EXISTS daily_summary")

# Create new table by aggregating granular_records
query = """
CREATE TABLE daily_summary AS
SELECT 
    date(last_modified) as tanggal,
    kabupaten,
    COUNT(id) as total_aktivitas,
    SUM(CASE WHEN status LIKE '%SUBMIT%' THEN 1 ELSE 0 END) as total_submitted,
    SUM(CASE WHEN status LIKE '%APPROV%' THEN 1 ELSE 0 END) as total_approved,
    SUM(CASE WHEN status LIKE '%REJECT%' OR status LIKE '%REVOK%' THEN 1 ELSE 0 END) as total_rejected,
    SUM(CASE WHEN status LIKE '%DRAFT%' THEN 1 ELSE 0 END) as total_draft,
    SUM(CASE WHEN status LIKE '%OPEN%' THEN 1 ELSE 0 END) as total_open,
    SUM(CASE WHEN is_usaha = 1 THEN 1 ELSE 0 END) as total_usaha_tambahan
FROM granular_records
WHERE last_modified IS NOT NULL AND kabupaten != ''
GROUP BY date(last_modified), kabupaten
ORDER BY date(last_modified) DESC, kabupaten ASC
"""

cursor.execute(query)
conn.commit()

cursor.execute("SELECT COUNT(*) FROM daily_summary")
print(f"Berhasil membuat tabel 'daily_summary' dengan {cursor.fetchone()[0]} baris rekap harian.")
conn.close()
