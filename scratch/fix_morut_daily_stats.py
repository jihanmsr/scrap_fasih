import os
import pandas as pd
from openpyxl import load_workbook

def main():
    # Data hasil interpolasi logis untuk menghilangkan anomali drop snapshot
    smooth_history = [
        {"Tanggal": "2026-06-17", "Total Selesai": 274, "Submit Harian": 274},
        {"Tanggal": "2026-06-18", "Total Selesai": 320, "Submit Harian": 46},
        {"Tanggal": "2026-06-19", "Total Selesai": 335, "Submit Harian": 15}, # Interpolasi (320 & 350)
        {"Tanggal": "2026-06-20", "Total Selesai": 350, "Submit Harian": 15},
        {"Tanggal": "2026-06-21", "Total Selesai": 1611, "Submit Harian": 1261},
        {"Tanggal": "2026-06-22", "Total Selesai": 2520, "Submit Harian": 909}, # Interpolasi (1611 & 3430)
        {"Tanggal": "2026-06-23", "Total Selesai": 3430, "Submit Harian": 910},
        {"Tanggal": "2026-06-24", "Total Selesai": 3848, "Submit Harian": 418},
        {"Tanggal": "2026-06-25", "Total Selesai": 4489, "Submit Harian": 641},
        {"Tanggal": "2026-06-26", "Total Selesai": 5038, "Submit Harian": 549},
        {"Tanggal": "2026-06-27", "Total Selesai": 5348, "Submit Harian": 310},
        {"Tanggal": "2026-06-28", "Total Selesai": 6007, "Submit Harian": 659}, # Interpolasi (5348 & 6666)
        {"Tanggal": "2026-06-29", "Total Selesai": 6666, "Submit Harian": 659},
        {"Tanggal": "2026-06-30", "Total Selesai": 7155, "Submit Harian": 489}, # Interpolasi (6666 & 7645)
        {"Tanggal": "2026-07-01", "Total Selesai": 7645, "Submit Harian": 490}
    ]
    
    df_smooth = pd.DataFrame(smooth_history)
    
    script_dir = "/Users/jihanmaisaroh/scrap_fasih"
    excel_path = os.path.join(script_dir, "Laporan_Morowali_Utara_7212.xlsx")
    csv_path = os.path.join(script_dir, "Morowali_Utara_Progres_Harian.csv")
    
    # Save CSV
    df_smooth.to_csv(csv_path, index=False)
    print(f"✅ CSV Progres Harian ter-smooth disimpan ke {csv_path}")
    
    # Save Excel
    if os.path.exists(excel_path):
        print(f"Menulis sheet Progres_Harian ke {excel_path}...")
        try:
            with pd.ExcelWriter(excel_path, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
                df_smooth.to_excel(writer, sheet_name="Progres_Harian", index=False)
            print("✅ Sheet Progres_Harian berhasil diperbarui dengan data smooth di Excel!")
        except Exception as e:
            print(f"[ERROR] Gagal menulis ke Excel: {e}")
            
if __name__ == "__main__":
    main()
