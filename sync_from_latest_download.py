import os
import glob
import sys
import subprocess

def main():
    downloads_dir = "/Users/jihanmaisaroh/Downloads"
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 1. Search for progress-assignment CSV files in Downloads
    csv_pattern = os.path.join(downloads_dir, "progress-assignment-*.csv")
    csv_files = glob.glob(csv_pattern)
    
    # Fallback to current directory
    if not csv_files:
        csv_pattern_local = os.path.join(current_dir, "progress-assignment-*.csv")
        csv_files = glob.glob(csv_pattern_local)
        
    if not csv_files:
        print("[ERROR] Tidak ditemukan file CSV progres 'progress-assignment-*.csv' di Downloads maupun di folder kerja.")
        print("Silakan klik ikon CSV pada tabel Rekap Kabupaten/Kota di dashboard FASIH BPS terlebih dahulu.")
        sys.exit(1)
        
    # Sort files by modification time (most recent first)
    csv_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    latest_csv = csv_files[0]
    
    print(f"[INFO] Menemukan file CSV progres terbaru: {latest_csv}")
    print(f"[INFO] Waktu modifikasi: {os.path.getmtime(latest_csv)}")
    
    # 2. Run update_dashboard_from_csv.py
    cmd = ["python3", "update_dashboard_from_csv.py", latest_csv]
    print(f"[INFO] Menjalankan: {' '.join(cmd)}")
    
    res = subprocess.run(cmd, capture_output=True, text=True, cwd=current_dir)
    print(res.stdout)
    if res.stderr:
        print("[ERROR DETAILS]")
        print(res.stderr)
        
    if res.returncode == 0:
        print("\n🎉 SINKRONISASI OFFLINE DARI CSV SELESAI DENGAN SUKSES!")
    else:
        print("\n[ERROR] Sinkronisasi dari CSV gagal.")
        sys.exit(res.returncode)

if __name__ == "__main__":
    main()
