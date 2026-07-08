import re

with open('scrape_fast_progress.py', 'r') as f:
    content = f.read()

# Add sqlite3 lookup helper at the top
helper = """
import sqlite3
def get_petugas_name_from_db(email, default_name):
    try:
        conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'master_data.db'))
        c = conn.cursor()
        c.execute("SELECT nama_petugas FROM master_petugas WHERE email = ?", (email,))
        row = c.fetchone()
        conn.close()
        if row and row[0]:
            return row[0]
    except:
        pass
    return default_name

"""

content = content.replace("import datetime", helper + "import datetime")

# Modify formatted_petugas_umum
target_umum = """                "username": username,
                "fullname": u.get("fullname") or u.get("name") or username,"""

replace_umum = """                "username": username,
                "fullname": get_petugas_name_from_db(username, u.get("fullname") or u.get("name") or username),"""

content = content.replace(target_umum, replace_umum)

# Modify formatted_petugas_ub
target_ub = """                "username": username,
                "fullname": u.get("fullname") or u.get("name") or username,"""

replace_ub = """                "username": username,
                "fullname": get_petugas_name_from_db(username, u.get("fullname") or u.get("name") or username),"""

content = content.replace(target_ub, replace_ub)

with open('scrape_fast_progress.py', 'w') as f:
    f.write(content)

