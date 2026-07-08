import sqlite3
import csv
import sys

def import_csv(file_path):
    conn = sqlite3.connect('master_data.db')
    cursor = conn.cursor()
    
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        # Handle different column names (email/username, nama/nama_petugas)
        for row in reader:
            email = row.get('email') or row.get('Username') or row.get('username')
            nama = row.get('nama') or row.get('Nama Pegawai') or row.get('nama_petugas')
            role = row.get('role') or row.get('Role') or ''
            
            if email and nama:
                cursor.execute('''
                    INSERT INTO master_petugas (email, nama_petugas, role)
                    VALUES (?, ?, ?)
                    ON CONFLICT(email) DO UPDATE SET
                        nama_petugas=excluded.nama_petugas,
                        role=excluded.role
                ''', (email, nama, role))
                
    conn.commit()
    conn.close()
    print(f"Data dari {file_path} berhasil diimpor ke master_petugas.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        import_csv(sys.argv[1])
    else:
        print("Usage: python3 import_petugas.py <file.csv>")
