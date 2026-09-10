import os
import re
import json
import glob
import time
import pandas as pd

def main():
    start_time = time.time()
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, " 9 September - Keluarga Hilang")
    output_js = os.path.join(base_dir, "data_hilang_keluarga.js")
    progress_file = os.path.join(base_dir, "fast_petugas_progress.js")

    print("=" * 60)
    print(" UPDATE DATA KELUARGA HILANG - 9 SEPTEMBER 2026")
    print("=" * 60)

    # 1. Load PPL & PML mapping from fast_petugas_progress.js
    ppl_map = {}
    pml_map = {}
    if os.path.exists(progress_file):
        print(f"Loading petugas mapping from {os.path.basename(progress_file)}...")
        try:
            with open(progress_file, "r", encoding="utf-8") as f:
                text = f.read()
            progress_data = json.loads(text.split("=", 1)[1].rsplit(";", 1)[0])

            for email, d in progress_data.get("Pencacah", {}).items():
                for sls in d.get("sls_details", {}):
                    ppl_map[sls] = email

            for email, d in progress_data.get("Pengawas", {}).items():
                for sls in d.get("sls_details", {}):
                    pml_map[sls] = email

            print(f"  -> {len(ppl_map):,} SLS mapped to PPL")
            print(f"  -> {len(pml_map):,} SLS mapped to PML")
        except Exception as e:
            print(f"  [Warning] Failed to parse {progress_file}: {e}")
    else:
        print("  [Warning] fast_petugas_progress.js not found, skipping PPL/PML mapping.")

    # 2. Read and deduplicate all CSV files
    csv_files = sorted(glob.glob(os.path.join(data_dir, "*.csv")))
    if not csv_files:
        print(f"[Error] No CSV files found in {data_dir}!")
        return

    print(f"\nReading {len(csv_files)} CSV files from '{os.path.basename(data_dir)}'...")
    dfs = []
    for f in csv_files:
        fname = os.path.basename(f)
        try:
            df = pd.read_csv(f, dtype=str)
            print(f"  - {fname}: {len(df):,} rows")
            dfs.append(df)
        except Exception as e:
            print(f"  - [Error reading {fname}]: {e}")

    all_df = pd.concat(dfs, ignore_index=True)
    print(f"\nTotal rows raw: {len(all_df):,}")

    # Deduplicate by link_fasih
    dedup_df = all_df.drop_duplicates(subset=["link_fasih"]).copy()
    print(f"Total unique rows after deduplication: {len(dedup_df):,}")

    # 3. Helpers
    def extract_code(text):
        if pd.isna(text):
            return ""
        m = re.search(r"\[(\d+)\]", str(text))
        return m.group(1) if m else ""

    pindah_pattern = re.compile(
        r"(?i)\b(pindah|rt\s*\d+|rw\s*\d+|sls|desa|kecamatan|kabupaten|luar|merantau|dusun|seberang|tinggal\s+di|ke\s+[a-z]+)\b"
    )

    # 4. Transform records
    print("\nProcessing records...")
    records = []
    for _, row in dedup_df.iterrows():
        kab_code = extract_code(row.get("kab", ""))
        kec_code = extract_code(row.get("kec", ""))
        desa_code = extract_code(row.get("desa", ""))

        sls_raw = row.get("kode_sls", "")
        try:
            sls_clean = str(int(float(sls_raw))) if pd.notna(sls_raw) and str(sls_raw).strip() != "" else "0"
        except:
            sls_clean = "0"
        sls_str = sls_clean.zfill(6)

        rc = f"72{kab_code}{kec_code}{desa_code}{sls_str}" if (kab_code and kec_code and desa_code) else None

        info = row.get("Info_Penulusuran")
        info_clean = (
            str(info).strip()
            if pd.notna(info) and str(info).strip() not in ["-", "nan", "'-", ""]
            else None
        )

        is_pindah = "Ya" if (info_clean and pindah_pattern.search(info_clean)) else "Tidak"

        nik_val = row.get("nik") if pd.notna(row.get("nik")) else ""
        no_kk_val = row.get("no_kk") if pd.notna(row.get("no_kk")) else ""
        nik_kk_val = nik_val if nik_val else no_kk_val

        item = {
            "kab": row.get("kab") if pd.notna(row.get("kab")) else "",
            "kec": row.get("kec") if pd.notna(row.get("kec")) else "",
            "desa": row.get("desa") if pd.notna(row.get("desa")) else "",
            "kode_sls": int(sls_clean) if sls_clean.isdigit() else sls_raw,
            "nama_sls": row.get("nama_sls") if pd.notna(row.get("nama_sls")) else "",
            "no_kk": no_kk_val,
            "nik_kk": nik_kk_val,
            "nama_kepala_keluarga": row.get("nama_kepala_keluarga") if pd.notna(row.get("nama_kepala_keluarga")) else "",
            "ppl_master": ppl_map.get(rc) or row.get("Petugas") or None,
            "pml_master": pml_map.get(rc) or None,
            "indikasi_pindah_sls": is_pindah,
            "link_fasih": row.get("link_fasih") if pd.notna(row.get("link_fasih")) else "",
        }
        if info_clean:
            item["Info_Penulusuran"] = info_clean
        # omit None values
        item = {k: v for k, v in item.items() if v is not None}
        records.append(item)

    print(f"Total processed records: {len(records):,}")

    # 5. Write to data_hilang_keluarga.js
    print(f"Writing to {output_js}...")
    with open(output_js, "w", encoding="utf-8") as f:
        f.write("window.dataHilangKeluarga = ")
        json.dump(records, f, separators=(',', ':'), ensure_ascii=False)
        f.write(";\n")

    size_mb = os.path.getsize(output_js) / (1024 * 1024)
    print(f"  -> File created successfully: {size_mb:.2f} MB")

    # 6. Update cache buster in index.html
    index_html = os.path.join(base_dir, "index.html")
    if os.path.exists(index_html):
        with open(index_html, "r", encoding="utf-8") as f:
            content = f.read()

        pattern = r'<script src="data_hilang_keluarga\.js(?:\?v=[^"]*)?"><\/script>'
        replacement = f'<script src="data_hilang_keluarga.js?v=20260909_v1"></script>'

        if re.search(pattern, content):
            new_content = re.sub(pattern, replacement, content)
            with open(index_html, "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f"Updated index.html cache buster for data_hilang_keluarga.js")

    elapsed = time.time() - start_time
    print(f"\n[DONE] Completed successfully in {elapsed:.2f} seconds!")

if __name__ == "__main__":
    main()
