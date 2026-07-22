import sys

filename = "scrape_dashboard_via_cdp.py"
with open(filename, "r") as f:
    content = f.read()

if "import subprocess" not in content:
    content = "import subprocess\n" + content

push_code = """
        # Auto-push ke GitHub agar Vercel otomatis update
        print("\\n🚀 Mengunggah data terbaru ke GitHub untuk update Vercel...")
        try:
            subprocess.run(["git", "add", "ipas_data.js", "daily_summary.js", "fast_master_assign_sls.js", "fast_petugas_progress.js", "fast_petugas_history.js", "petugas_region_map.js"], check=True)
            subprocess.run(["git", "commit", "-m", "Auto-update data dari scraper"], check=True)
            subprocess.run(["git", "push", "origin", "main"], check=True)
            print("✅ Berhasil push ke GitHub! Website Vercel akan otomatis terupdate dalam ~30 detik.")
        except Exception as e:
            print(f"⚠️ Gagal push ke GitHub (Mungkin tidak ada perubahan data atau error git): {e}")
            
        print("\\n🎉 PEMBARUAN DASHBOARD SELESAI SECARA INSTAN!")
"""

content = content.replace('print("\\n🎉 PEMBARUAN DASHBOARD SELESAI SECARA INSTAN!")', push_code)

with open(filename, "w") as f:
    f.write(content)
