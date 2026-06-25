"""
Update kolom nama_krt di anomali_data dengan nama usaha dari granular data
berdasarkan assignment_id match
"""
import json, gzip, base64, os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()
supabase: Client = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])

print("🔄 Building assignment_id → nama_usaha lookup dari granular files...")
granular_files = [f for f in os.listdir('.') if f.startswith('granular_assignments_se_umum_') and f.endswith('.json')]

lookup = {}
for fname in granular_files:
    with open(fname) as f:
        d = json.load(f)
    raw = gzip.decompress(base64.b64decode(d['compressed_data']))
    data = json.loads(raw)
    targets = data.get('targets', [])
    for t in targets:
        if isinstance(t, list) and len(t) >= 3 and t[0] and t[2]:
            lookup[t[0]] = t[2]

print(f"   ✅ {len(lookup):,} entries di lookup")

print("\n📥 Mengambil semua data anomali dari Supabase...")
result = supabase.table('anomali_data').select('id, assignment_id, nama_krt').execute()
rows = result.data
print(f"   ✅ {len(rows)} baris anomali")

# Match dan update
updates = []
matched = 0
for row in rows:
    aid = row.get('assignment_id', '')
    if aid and aid in lookup:
        nama = lookup[aid]
        if nama and nama != '-' and nama != row.get('nama_krt', ''):
            updates.append({'id': row['id'], 'nama_krt': nama})
            matched += 1

print(f"\n✅ {matched}/{len(rows)} baris berhasil di-match dengan nama usaha")

if updates:
    print(f"📤 Mengupdate {len(updates)} baris...")
    batch_size = 50
    for i in range(0, len(updates), batch_size):
        batch = updates[i:i+batch_size]
        for upd in batch:
            try:
                supabase.table('anomali_data').update({'nama_krt': upd['nama_krt']}).eq('id', upd['id']).execute()
            except Exception as e:
                print(f"  ❌ ID {upd['id']}: {e}")
        print(f"   ✅ Updated {min(i+batch_size, len(updates))}/{len(updates)}")
    print("\n🎉 SELESAI! Nama usaha berhasil diisi dari granular data.")
else:
    print("\n⚠️  Tidak ada yang di-match. Cek assignment_id di anomali_data.")
    # Debug: show sample
    print("\nSample assignment_id di anomali_data:")
    for row in rows[:5]:
        aid = row.get('assignment_id', '')
        print(f"  '{aid}' → {'FOUND: ' + lookup.get(aid,'') if aid in lookup else 'NOT FOUND'}")
