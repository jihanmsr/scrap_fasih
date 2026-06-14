"""
Script: Mencari petugas pencacah dengan beban kerja > 800 assignment
via API datatable-all-user-survey-periode (langsung pakai requests + cookies dari curl)

Output: pencacah_beban_lebih_800_api.csv
"""

import requests
import json
import csv
import time
from collections import defaultdict
from pathlib import Path

# ── Konfigurasi ────────────────────────────────────────────────────────────────

URL = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode"

SURVEY_PERIOD_ID = "fd68e454-ba45-4b85-8205-f3bf777ded24"

# Cookie dari curl (paste ulang jika expired)
COOKIES_RAW = (
    "f5avraaaaaaaaaaaaaaaa_session_=AGPNJMOLNCLGCOPGNLMOLCMIPMONNKDKCPIIENOCOJABCBNNIFGCFIBOFJNEGLMAMKIDFCLENADONPINMFEANPDFLNIHFLPKADFFCDJPICNGNEHLIEJCCFBNBGMJPDEJ; "
    "f5_cspm=1234; "
    "f5avraaaaaaaaaaaaaaaa_session_=LJFAKDEIMBNEGIIJFFKGCFFDOHEALJLCLKBIMBIKBEABLPFGIICPIGLIGDBOCOOMHMADLDDAIAEKLDDNOKJAMKFOLNONJFCJJEHOFFCKKBIBLOKDABBFFOOONFPENMON; "
    "_ga=GA1.3.1140734912.1781239400; "
    "XSRF-TOKEN=2aa4543c-db0f-40f3-904c-6ea9c5b907bf; "
    "TS01acc472=01266d26d0131ad4d90a313d8b4e41273a43d8c32b957febe1203f3abb0bef61a21ab7411f72b1c695f3b8577e43ef03d6e8c1d1b7b641b61c14d25448557d7e1657062950e253e23d8fce79b39befd9435f7f493c8dfe98811b565fc218fa383177313677546797685a7fe67f708d5cc19a9d71ad87780e730d180fa8c251913d14b94ee77e1258dcb38c586e0a08591932a4942bcd199a53ee3d080d812d400ef95ddbe973901ca80e52b1c96ab755ed1e21e8bf5b86bb2d01098234e8c01d368d63002f61eaaf257981a24d007d5f717195a0aa; "
    "TS0151fc2b=0167a1c8617a278160e553d265d03646ab0c79bf314f941fae1bf01a505d89745d3dd22519ac889ac5c36aca04e3fe73949a4882e4; "
    "f5avr1146915014aaaaaaaaaaaaaaaa_cspm_=LEJDJNLODGMBMKHFOFMGHPBLPJOIOHHFDDPFCJAPKJFLKJPNOKEHIKNHKKIPMDNKJIMCNJEPAEAMJOBLKKPAKDNBAHKBLCHKAPFLELHEODHIMGKCDINOCAFKJDIGGGEK; "
    "db8ca2b43ed851cc93e71fd5fd72bff7=d45a11eb518a297a8141c49942c33d62; "
    "JSESSIONID=CA227D5C3BA8FDE09C856D04F48EF6F8; "
    "_ga_XXTTVXWHDB=GS2.3.s1781307346$o2$g0$t1781307346$j60$l0$h0; "
    "f5avraaaaaaaaaaaaaaaa_session_=CJOFBMJPHMINOIODOFAAJJEDBMAHPPFNJEMLMBBAPIDBPINHBKHNIJLPIGBAJKMKPMKDBIEHKHBDBIKCBCNADBANIJIPHDKGFFFODDLBCIFIEFKCNJAPHLKEIMHLFMIK; "
    "SESSION=b1ff4eaa-6688-42a7-a425-840eadd69b8e; "
    "TS01bafd94=01266d26d0809775dd819de1f0de9ac4d23d16635baf848eb73b1d845c9d58e54b3450f960e1fcd24652119248ebaeb832fdb81781; "
    "f5avr1980069168aaaaaaaaaaaaaaaa_cspm_=GLKDLKAAPIENAEMODAJPOBCMPAIIINJHLHKDCEEBMKFIPPHAMPFPKIBKHEJGHCHLOBOCDBGCCLAHGIHPFBEACLBAMEJHDEPAKOFHLMAMOKMNKDGMDFGONJIOGIFOLNDC; "
    "TS5d9b593f027=0868f8be6fab2000c1f116a745a8585f55d5dfab4cae919f6702baa9c8af826eda9b3d2f55294f1808078de68c11300047fd916f549826fce83fa258a0dda217a90d8d34e21d58c8e3aa88b3fd835ac24186fd47c765ae7d3f1f771c755bcfd2"
)

XSRF_TOKEN = "2aa4543c-db0f-40f3-904c-6ea9c5b907bf"

OUTPUT_CSV = Path("/Users/jihanmaisaroh/scrap_fasih/pencacah_beban_lebih_800_api.csv")

# ── Parse cookies ───────────────────────────────────────────────────────────────

def parse_cookies(raw: str) -> dict:
    cookies = {}
    for part in raw.split(";"):
        part = part.strip()
        if "=" in part:
            k, v = part.split("=", 1)
            cookies[k.strip()] = v.strip()
    return cookies

COOKIES = parse_cookies(COOKIES_RAW)

HEADERS = {
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9,id-ID;q=0.8,id;q=0.7",
    "Connection": "keep-alive",
    "Content-Type": "application/json",
    "Origin": "https://fasih-sm.bps.go.id",
    "Referer": "https://fasih-sm.bps.go.id/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
    "X-XSRF-TOKEN": XSRF_TOKEN,
    "sec-ch-ua": '"Google Chrome";v="149", "Chromium";v="149", "Not)A;Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
}

# Columns minimal yang diperlukan
COLUMNS = [
    {"data": "id", "orderable": True},
    {"data": "codeIdentity", "orderable": True},
    {"data": "data1", "orderable": True},
    {"data": "data2", "orderable": True},
    {"data": "data3", "orderable": True},
    {"data": "data4", "orderable": True},
    {"data": "data5", "orderable": True},
    {"data": "data6", "orderable": True},
    {"data": "data7", "orderable": True},
    {"data": "data8", "orderable": True},
    {"data": "data9", "orderable": True},
    {"data": "data10", "orderable": True},
]

EXTRA_PARAM = {
    "surveyPeriodId": SURVEY_PERIOD_ID,
    "assignmentErrorStatusType": -1,
    "filterTargetType": "TARGET_ONLY"
}

# ── Helper: fetch satu halaman ──────────────────────────────────────────────────

def fetch_page(start: int, length: int, session: requests.Session, retries: int = 3) -> dict | None:
    payload = {
        "start": start,
        "length": length,
        "columns": COLUMNS,
        "order": [],
        "search": {"value": "", "regex": False},
        "assignmentExtraParam": EXTRA_PARAM,
    }
    for attempt in range(1, retries + 1):
        try:
            resp = session.post(URL, json=payload, headers=HEADERS, cookies=COOKIES, timeout=60)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"  [WARN] Attempt {attempt}/{retries} failed: {e}")
            time.sleep(2 * attempt)
    return None

# ── Main ────────────────────────────────────────────────────────────────────────

def main():
    session = requests.Session()

    print("=" * 60)
    print("Mengambil data total dari API...")
    print("=" * 60)

    # Ambil 1 record dulu untuk tahu totalHit
    first = fetch_page(0, 1, session)
    if not first:
        print("❌ Gagal mengambil data dari API. Cek koneksi / cookie expired.")
        return

    total_hit = first.get("totalHit", 0)
    print(f"✅ Total records (assignments): {total_hit:,}")

    if total_hit == 0:
        print("Tidak ada data. Cek parameter surveyPeriodId atau filterTargetType.")
        return

    # ── Ambil semua data dengan paginasi ────────────────────────────────────────
    PAGE_SIZE = 500  # Jangan terlalu besar supaya tidak timeout
    all_rows = []
    start = 0

    print(f"\nMengambil semua data ({total_hit:,} records, {PAGE_SIZE} per request)...")

    while start < total_hit:
        page_data = fetch_page(start, PAGE_SIZE, session)
        if page_data is None:
            print(f"  ❌ Gagal fetch start={start}, skip.")
            start += PAGE_SIZE
            continue

        rows = page_data.get("searchData", [])
        all_rows.extend(rows)

        pct = min(100, (start + len(rows)) / total_hit * 100)
        print(f"  [{pct:5.1f}%] Fetched {len(all_rows):,} / {total_hit:,} rows (start={start})")

        start += PAGE_SIZE
        time.sleep(0.2)  # sedikit throttle agar tidak overload

    print(f"\n✅ Total rows terkumpul: {len(all_rows):,}")

    # ── Analisis per petugas ─────────────────────────────────────────────────────
    print("\nMenganalisis data per petugas...")

    # Struktur: user_id -> {info, count}
    # Field yang tersedia di response perlu di-inspect dari data aktual
    # Berdasarkan curl: data1..data10 adalah kolom dinamis, codeIdentity = kode petugas

    user_stats = defaultdict(lambda: {
        "codeIdentity": "",
        "name": "",
        "email": "",
        "role": "",
        "kabupaten": "",
        "kecamatan": "",
        "kelurahan": "",
        "count": 0,
        "raw_data": None,
    })

    for row in all_rows:
        uid = row.get("id") or row.get("codeIdentity", "UNKNOWN")
        code_identity = row.get("codeIdentity", "")

        # Coba ambil dari berbagai field yang mungkin ada
        # Inspect row untuk debug
        if user_stats[uid]["raw_data"] is None:
            user_stats[uid]["raw_data"] = row

        user_stats[uid]["codeIdentity"] = code_identity

        # Field data1..data10 — mapping tergantung API
        # Coba beberapa kandidat nama field umum
        for key in ["name", "fullName", "nama", "data1"]:
            if row.get(key):
                user_stats[uid]["name"] = row[key]
                break

        for key in ["email", "data2"]:
            if row.get(key):
                user_stats[uid]["email"] = row[key]
                break

        for key in ["roleName", "role", "currentSurveyRoleName", "data3"]:
            if row.get(key):
                user_stats[uid]["role"] = row[key]
                break

        user_stats[uid]["count"] += 1

    # ── Inspect struktur row pertama ─────────────────────────────────────────────
    if all_rows:
        print("\n--- Struktur row pertama (untuk debug) ---")
        sample = all_rows[0]
        for k, v in sample.items():
            val_str = str(v)[:120]
            print(f"  {k}: {val_str}")
        print("---")

    # ── Filter > 800 ─────────────────────────────────────────────────────────────
    results = [
        {**info, "id": uid}
        for uid, info in user_stats.items()
        if info["count"] > 800
    ]
    results.sort(key=lambda x: x["count"], reverse=True)

    print(f"\n{'='*60}")
    print(f"HASIL: {len(results)} petugas dengan assignment > 800")
    print(f"{'='*60}")

    # Statistik
    all_counts = [info["count"] for info in user_stats.values()]
    if all_counts:
        print(f"  Total petugas unik : {len(all_counts):,}")
        print(f"  Min assignment     : {min(all_counts):,}")
        print(f"  Max assignment     : {max(all_counts):,}")
        print(f"  Rata-rata          : {sum(all_counts)/len(all_counts):.1f}")
        print(f"  > 800              : {sum(1 for c in all_counts if c > 800)}")

    # ── Print top 30 ─────────────────────────────────────────────────────────────
    print("\nTop 30 petugas dengan beban terbanyak:")
    for i, r in enumerate(results[:30], 1):
        print(f"  {i:3d}. [{r['codeIdentity']}] {r['name'][:40]:<40s} | {r['role']:<20s} | {r['count']:,} assignments")

    # ── Tulis CSV ─────────────────────────────────────────────────────────────────
    if results:
        with open(OUTPUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
            fieldnames = ["No", "codeIdentity", "name", "email", "role", "jumlah_assignment"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for i, r in enumerate(results, 1):
                writer.writerow({
                    "No": i,
                    "codeIdentity": r["codeIdentity"],
                    "name": r["name"],
                    "email": r["email"],
                    "role": r["role"],
                    "jumlah_assignment": r["count"],
                })
        print(f"\n✅ CSV tersimpan: {OUTPUT_CSV}")
    else:
        print("\nTidak ada petugas dengan assignment > 800.")

    # ── Dump raw pertama untuk inspeksi field ────────────────────────────────────
    debug_path = Path("/Users/jihanmaisaroh/scrap_fasih/scratch/heavy_assignment_debug.json")
    sample_rows = all_rows[:5]
    with open(debug_path, "w", encoding="utf-8") as f:
        json.dump(sample_rows, f, ensure_ascii=False, indent=2)
    print(f"📄 Sample rows (5) tersimpan: {debug_path}")

if __name__ == "__main__":
    main()
