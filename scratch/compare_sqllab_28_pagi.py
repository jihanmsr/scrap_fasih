import pandas as pd

try:
    sqllab = pd.read_csv('/Users/jihanmaisaroh/scrap_fasih/sqllab_5_monitoring_jumlah_usaha_berdasarkan_status_keberadaannya_perpetugas_20260729T070546.csv')
    sqllab['email'] = sqllab['email'].astype(str).str.lower().str.strip()
    
    # Read the morning Excel file from Downloads
    excel_path = '/Users/jihanmaisaroh/Downloads/Rekap_Petugas_SE_Umum_BANGGAI_KEPULAUAN_Wilayah_2026-07-28.xlsx'
    df = pd.read_excel(excel_path)
    
    email_col = 'Email / Username'
    df[email_col] = df[email_col].astype(str).str.lower().str.strip()
    
    target_col = 'Total Target'
        
    merged = pd.merge(sqllab, df, left_on='email', right_on=email_col, how='left')
    
    # Remove duplicate emails in df if any, or aggregate them
    df_grouped = df.groupby(email_col).agg({target_col: 'sum'}).reset_index()
    merged2 = pd.merge(sqllab, df_grouped, left_on='email', right_on=email_col, how='left')
    
    print(f"\nBerhasil diload dari {excel_path}")
    print(f"Total baris SQL Lab: {len(sqllab)}")
    print(f"Total baris yang bisa dimapping: {merged2[email_col].notna().sum()}")
    print("\nTotal Usaha di SQL Lab:", merged2['total_usaha'].sum())
    print(f"Total Target di Rekap Pagi ({target_col}):", merged2[target_col].sum())
    
except Exception as e:
    print(f"Error: {e}")
