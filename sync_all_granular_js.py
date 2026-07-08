import os
import subprocess
import sys

def run_script(script_path):
    print(f"\n--- Menjalankan {os.path.basename(script_path)} ---")
    try:
        subprocess.run([sys.executable, script_path], check=True)
        print(f"✅ Sukses: {os.path.basename(script_path)}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Gagal: {os.path.basename(script_path)}")
        sys.exit(1)

def main():
    script_dir = "/Users/jihanmaisaroh/scrap_fasih"
    
    scripts = [
        "scratch/export_petugas_progress.py",
        "scratch/export_mitra.py",
        "scratch/export_new_businesses.py",
        "scratch/create_daily_summary.py",
        "scratch/generate_fast_rekap_report.py"
    ]
    
    for s in scripts:
        full_path = os.path.join(script_dir, s)
        if os.path.exists(full_path):
            run_script(full_path)
        else:
            print(f"⚠️ Melewati {s} (file tidak ditemukan)")
            
    print("\n✅ SELESAI! Semua file JS (petugas_progress.js, new_businesses_data.js, daily_summary.js) dan Laporan CSV telah diperbarui sesuai data Granular terbaru.")

if __name__ == '__main__':
    main()
