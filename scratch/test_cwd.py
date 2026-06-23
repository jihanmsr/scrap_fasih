import os
print("CWD:", os.getcwd())
print("Files in CWD:", os.listdir("."))
print("Files matching Detail_Usaha_SE_Umum_*.csv in CWD:", os.listdir(".") if not os.listdir(".") else [f for f in os.listdir(".") if "Detail_Usaha_SE_Umum_" in f])
