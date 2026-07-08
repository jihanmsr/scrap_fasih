import sqlite3, json

def export_daily():
    conn = sqlite3.connect('/Users/jihanmaisaroh/scrap_fasih/granular_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT tanggal, kabupaten, total_aktivitas, total_submitted, total_approved, total_rejected, total_usaha_tambahan FROM daily_summary ORDER BY tanggal ASC, kabupaten ASC")
    rows = cursor.fetchall()
    
    daily_list = []
    for r in rows:
        daily_list.append({
            "tanggal": r[0],
            "kabupaten": r[1],
            "total_aktivitas": r[2],
            "total_submitted": r[3],
            "total_approved": r[4],
            "total_rejected": r[5],
            "total_usaha_tambahan": r[6]
        })
    with open('/Users/jihanmaisaroh/scrap_fasih/daily_summary.js', 'w', encoding='utf-8') as fw:
        fw.write(f"window.DAILY_SUMMARY = {json.dumps(daily_list, indent=4)};\n")
    print(f"Exported {len(daily_list)} rows to daily_summary.js!")

if __name__ == '__main__':
    export_daily()
