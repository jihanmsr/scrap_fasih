import json

def run():
    input_file = "/Users/jihanmaisaroh/Downloads/fast_petugas_palu.json"
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            all_results = json.load(f)
    except FileNotFoundError:
        print(f"Error: File {input_file} tidak ditemukan. Pastikan Anda sudah menjalankan script di Console Chrome dan mendownloadnya!")
        return

    petugas_map = {}
    for row in all_results:
        email = row.get("email", "").strip().lower()
        if not email: continue
        
        if email not in petugas_map:
            petugas_map[email] = {
                "target": 0, "submitted_pencacah": 0, "submitted_respondent": 0,
                "approved": 0, "rejected": 0, "draft": 0, "open": 0
            }
            
        for r_sum in row.get("regionSummary", []):
            petugas_map[email]["target"] += r_sum.get("total", 0)
            for st in r_sum.get("statusBreakdown", []):
                s_name = st.get("status", "").upper()
                s_count = st.get("count", 0)
                if s_name == "OPEN": petugas_map[email]["open"] += s_count
                elif s_name == "DRAFT": petugas_map[email]["draft"] += s_count
                elif s_name == "SUBMITTED BY PENCACAH": petugas_map[email]["submitted_pencacah"] += s_count
                elif s_name == "SUBMITTED RESPONDENT": petugas_map[email]["submitted_respondent"] += s_count
                elif "APPROVED" in s_name: petugas_map[email]["approved"] += s_count
                elif "REJECTED" in s_name: petugas_map[email]["rejected"] += s_count

    js_file = "/Users/jihanmaisaroh/scrap_fasih/petugas_progress.js"
    with open(js_file, "w", encoding="utf-8") as f:
        f.write(f"window.PETUGAS_PROGRESS_MAP = {json.dumps(petugas_map, indent=4)};\n")
    print(f"[SUCCESS] Javascript map berhasil diupdate di {js_file} berdasarkan data FAST!")

if __name__ == "__main__":
    run()
