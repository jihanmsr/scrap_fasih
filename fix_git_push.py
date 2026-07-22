import sys

def modify_file(filename, ending_string):
    with open(filename, "r") as f:
        content = f.read()
    
    if "import subprocess" not in content:
        content = "import subprocess\n" + content
    
    push_code = """
        # Auto-push ke GitHub agar Vercel otomatis update
        print("\\n🚀 Mengunggah data terbaru ke GitHub untuk update Vercel...")
        try:
            subprocess.run(["git", "add", "."], check=True)
            subprocess.run(["git", "commit", "-m", "Auto-update data dari scraper"], check=True)
            subprocess.run(["git", "push", "origin", "main"], check=True)
            print("✅ Berhasil push ke GitHub! Website Vercel akan otomatis terupdate dalam ~30 detik.")
        except Exception as e:
            print(f"⚠️ Gagal push ke GitHub (Mungkin tidak ada perubahan data atau error git): {e}")
            
        print("\\n🎉 PEMBARUAN SELESAI SECARA INSTAN!")
"""
    if "Mengunggah data terbaru ke GitHub" not in content:
        parts = content.rsplit(ending_string, 1)
        if len(parts) == 2:
            content = parts[0] + push_code + "\n        " + ending_string + parts[1]
            with open(filename, "w") as f:
                f.write(content)
            print(f"Modified {filename}")

modify_file("scrape_responsibility.py", "await context.close()")
