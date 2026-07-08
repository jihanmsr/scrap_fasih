import sqlite3

def init_db():
    conn = sqlite3.connect('master_data.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS master_petugas (
        email TEXT PRIMARY KEY,
        nama_petugas TEXT NOT NULL,
        role TEXT
    )
    ''')
    
    conn.commit()
    conn.close()
    print("Database master_data.db dan tabel master_petugas berhasil diinisialisasi.")

if __name__ == "__main__":
    init_db()
